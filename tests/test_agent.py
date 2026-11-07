from __future__ import annotations

import json
from dataclasses import replace

import httpx
import pytest
from typer.testing import CliRunner

from proposalbench import cli
from proposalbench.checks.admissibility import counted_text
from proposalbench.evidence.http import EvidenceClient
from proposalbench.llm import Completion, InfrastructureError, ModelSpec
from proposalbench.parse.sections import count_words, parse_proposal
from proposalbench.systems import agent
from proposalbench.systems.base import SubmissionMeta, load
from proposalbench.systems.registry import load_system
from proposalbench.tasks.loader import ResolvedTask
from proposalbench.tasks.schema import RequiredSection

SPEC = ModelSpec("google", "gemini-3.1-pro-preview", max_output_tokens=4096)
OWN = "Author, Ada (2024). Applicant pilot study. Dossier Journal. DOI: 10.99999/pb.pilot"
CALL = """Write in English. Required headings, in order: Specific Aims; Research Strategy,
with children Significance and Approach. Establish feasibility with a quantitative measure.
The overall limit is 700 words, Specific Aims 180 and Research Strategy 500 (including children).
Tables and citations count, references and title do not. No tolerance."""
FILES = {
    "call.md": CALL,
    "dossier/publications.md": "# Publications\n\n1. " + OWN,
    "dossier/resources.md": "Ada has a microscope; access to the sequencing facility is pending.",
    "brief.md": "Use the microscope. The call takes precedence over these notes.",
    "instructions.md": "Write the proposal in English with References; do not invent facts.",
}


def plan_data():
    headings = ["Specific Aims", "Research Strategy", "Significance", "Approach"]
    return {
        "language": "English",
        "max_words": 700,
        "counted_headings": [],
        "exempt_tables": False,
        "sections": [
            {
                "heading": h,
                "level": 2 if i < 2 else 3,
                "max_words": [180, 500, None, None][i],
                "word_budget": [160, 0, 140, 300][i],
                "points": ["Measure feasibility"],
                "requirements": ["Establish feasibility"],
                "dossier_facts": ["Ada has a microscope"],
                "dossier_files": ["dossier/resources.md"],
            }
            for i, h in enumerate(headings)
        ],
        "queries": [
            {
                "query": f"microscopy feasibility {i}",
                "purpose": "Support assay design",
                "sections": ["Specific Aims", "Approach"],
            }
            for i in range(6)
        ],
        "dossier_publications": [{"source": "dossier/publications.md", "reference": OWN}],
    }


def prose(words, citations=""):
    sentence = (
        "Ada will measure microscopy reliability during month six using independent cultures. "
    )
    return " ".join((sentence * (words // 10 + 1)).split()[:words]) + ". " + citations


class Hidden:
    def __getattribute__(self, name):
        raise AssertionError(f"agent accessed hidden field {name}")


class Rig:
    def __init__(self, monkeypatch, tmp_path):
        monkeypatch.setenv("OPENALEX_API_KEY", "")  # empty: .env must not refill it
        self.task = ResolvedTask(
            Hidden(),
            Hidden(),
            Hidden(),
            tmp_path / "pilot/tasks/example",
            tmp_path / "calls/example",
            tmp_path / "dossiers/example",
        )
        # Freeze the public bundle at the existing export boundary. Everything else on the real
        # ResolvedTask (including its id property) still hits exploding hidden objects.
        monkeypatch.setattr(agent, "bundle_files", lambda task: list(FILES.items()))
        self.system = agent.ReferenceAgent("test-agent", SPEC, tmp_path / "cache.sqlite")
        self.calls = []
        self.requests = []
        self.plan = plan_data()
        self.overrides = {}
        self.http_error = False
        self.empty_search = False
        self.selection = ["C1", "C2", "C3"]
        self.network = httpx.MockTransport(self.transport)

        def client(cache, **kwargs):
            return EvidenceClient(
                cache, transport=self.network, retries=0, sleep=lambda _: None, **kwargs
            )

        monkeypatch.setattr(agent, "EvidenceClient", client)
        monkeypatch.setattr(agent, "complete", self.complete)

    def transport(self, request):
        self.requests.append(request)
        assert request.url.host == "api.crossref.org"
        if self.http_error:
            return httpx.Response(503)
        works = [
            {
                "DOI": f"10.1234/work{i}",
                "title": [f"Microscopy reliability study {i}"],
                "type": "journal-article" if i < 4 else "posted-content",
                "author": [{"family": "Researcher"}, {"family": "Scientist"}],
                "published": {"date-parts": [[2023]]},
                "container-title": ["Methods Journal"],
                "abstract": (
                    "<jats:p>Independent cultures establish microscopy reliability.</jats:p>"
                ),
            }
            for i in range(1, 5)
        ]
        return httpx.Response(200, json={"message": {"items": [] if self.empty_search else works}})

    def complete(self, spec, messages, system):
        prompt = messages[-1]["content"]
        step = prompt.splitlines()[0]
        context = json.loads(prompt.splitlines()[-1])
        self.calls.append((step, context))
        assert system == agent.SYSTEM_PROMPT
        if step in self.overrides:
            output = self.overrides[step]
            if isinstance(output, Exception):
                raise output
            if callable(output):
                output = output(context)
        elif step == "PLAN":
            output = self.plan
        elif step == "SELECT":
            assert len(context["candidates"]) == 3
            assert all(
                "Independent cultures" in w["abstract"] for w in context["candidates"].values()
            )
            output = {"selected": self.selection}
        elif step == "CRITIQUE":
            assert "## References" in context["proposal"]
            output = {"issues": [{"heading": "Specific Aims", "issues": ["Specify timing"]}]}
        else:
            heading = context["section"]["heading"]
            if step == "SHORTEN":
                words = context["target_words"] - 3
            elif step == "REVISE":
                words = 170
            else:
                words = {
                    "Specific Aims": 160,
                    "Research Strategy": 0,
                    "Significance": 180,
                    "Approach": 600,
                }[heading]
            citations = {
                "Specific Aims": "[D1] [R2]",
                "Research Strategy": "",
                "Significance": "[R1]",
                "Approach": "[R2] [R1]",
            }[heading]
            output = {
                "text": prose(words, citations) if words else "",
                "summary": f"{heading}: Ada measures reliability in month six.",
            }
        if isinstance(output, Completion):
            return output
        return Completion(
            json.dumps(output) if not isinstance(output, str) else output,
            spec.model_id,
            100,
            25,
            "end",
            0.01,
            retries=[{"attempt": 1, "error": "test retry"}],
        )

    def run(self):
        return self.system.generate(self.task, 1)


@pytest.fixture
def rig(monkeypatch, tmp_path):
    instance = Rig(monkeypatch, tmp_path)
    yield instance
    instance.system.close()


def test_pipeline_hidden_guard_citations_length_and_usage(rig, make_call):
    sub = rig.run()
    assert sub.meta.status == "ok", sub.meta.notes
    parsed = parse_proposal(sub.proposal)
    assert [s.title for s in parsed.body_sections()] == [s["heading"] for s in rig.plan["sections"]]
    assert parsed.references_block.splitlines()[0] == "[1] " + OWN
    assert "[2] Researcher; Scientist (2023). Microscopy reliability study 2." in sub.proposal
    assert "[3] Researcher; Scientist (2023). Microscopy reliability study 1." in sub.proposal
    assert "https://doi.org/10.1234/work2" in parsed.references_block
    assert "https://doi.org/10.1234/work1" in parsed.references_block
    assert "work3" not in sub.proposal  # selected but uncited
    assert "[R" not in sub.proposal and "[D" not in sub.proposal
    assert "[1] [2]" in parsed.body_text()
    call = make_call(
        max_words=700,
        tolerance=0,
        exempt=["title", "references"],
        per_section_max_words={"1": 180, "2": 500},
    )
    call = call.model_copy(
        update={
            "required_sections": [
                RequiredSection(id="1", title="Specific Aims"),
                RequiredSection(id="2", title="Research Strategy"),
            ]
        }
    )
    plan = agent.Plan.model_validate(rig.plan)
    total, section_counts = agent.length_counts(plan, sub.proposal)
    assert total == count_words(counted_text(parsed, call)) <= 700
    assert section_counts[0] <= 180  # Specific Aims
    assert section_counts[1] <= 500  # Research Strategy
    steps = [step for step, _ in rig.calls]
    assert steps.count("REVISE") == 1
    assert steps.count("SHORTEN") == 1
    assert len(rig.calls) == 14
    for step, context in rig.calls:
        if step == "REVISE":
            assert context["section"]["heading"] == "Specific Aims"
        if step == "DRAFT" and context["section"]["heading"] == "Approach":
            assert len(context["previous_summaries"]) == 3
            assert context["dossier"]["dossier/resources.md"] == FILES["dossier/resources.md"]
    usage = sub.meta.models[0]
    assert (usage.calls, usage.input_tokens, usage.output_tokens) == (14, 1400, 350)
    assert len(sub.meta.retries) == 14
    assert sub.meta.wall_time_s is not None
    assert (sub.meta.task_id, sub.meta.split) == ("example", "pilot")
    trace = json.loads(sub.meta.notes[-1])["agent"]
    assert len(trace["library"]) == 3
    assert len(trace["queries"]) == 6
    assert trace["queries"][0]["retrieved"] == {"crossref": 4}
    assert rig.system.cache_path.exists()
    assert len(rig.requests) == 6
    # A second sample reuses the on-disk response cache without network calls.
    rig.run()
    assert len(rig.requests) == 6
    assert SubmissionMeta.from_json(sub.meta.to_json()) == sub.meta


@pytest.mark.parametrize("bad", ["", "I cannot help", "{}", '{"sections": []}'])
def test_invalid_plan_is_model_failure(rig, bad):
    rig.overrides["PLAN"] = bad
    sub = rig.run()
    assert sub.meta.status == "model_failure"
    assert sub.meta.models[0].calls == 2  # one retry told what was wrong
    assert not rig.requests


@pytest.mark.parametrize("stop", ["content_filtered", "refusal", "max_tokens"])
def test_refused_or_truncated_output(rig, stop):
    rig.overrides["PLAN"] = Completion("{}", SPEC.model_id, 7, 2, stop, 0.01)
    sub = rig.run()
    assert sub.meta.status == "model_failure"
    assert sub.meta.models[0].input_tokens == 14  # the retry is also accounted


@pytest.mark.parametrize(
    ("citation", "in_text"),
    [
        ("[R999]", None),  # a key outside the library: removed after the repair fails
        ("[D42]", None),
        ("[37]", None),  # a numeric citation would point at the wrong reference
        ("[Smith2024]", "(Smith2024)"),  # a bracket remark becomes a parenthesis
        ("(Smith, 2024)", "(Smith, 2024)"),  # left as written, for the evaluator to see
        ("10.1234/unknown", "10.1234/unknown"),
    ],
)
def test_unapproved_citations_never_reach_the_numbering(rig, citation, in_text):
    rig.overrides["DRAFT"] = {"text": prose(160, citation), "summary": "Test summary."}
    sub = rig.run()
    assert sub.meta.status == "ok", sub.meta.notes
    assert citation not in sub.proposal or citation == in_text
    if in_text:
        assert in_text in sub.proposal


def test_headings_and_remarks_in_section_prose_are_normalised():
    text = agent.normalize_section_text(
        "### Aim 1\nText [R1, R2].\n\n**Work package 2**\n\nMore [note: excluded].\n\n"
        "**Risks:**\n\n- one\n- two\n\nKeep [[TO COMPLETE: x]] and [link](http://x)."
    )
    assert parse_proposal(text).sections == []
    assert "**Aim 1.** Text [R1] [R2]." in text
    assert "**Work package 2.** More (note: excluded)." in text
    assert "**Risks.**\n- one" in text
    assert "[[TO COMPLETE: x]]" in text and "[link](http://x)" in text


def test_fabricated_dossier_metadata_is_dropped(rig):
    rig.plan["dossier_publications"][0]["reference"] = "Invented author and title"
    sub = rig.run()
    assert "Invented author and title" not in sub.proposal
    trace = json.loads(sub.meta.notes[-1])["agent"]
    assert any("not verbatim" in d for d in trace["plan_dropped"])


def test_invalid_selection_is_not_silently_accepted(rig):
    rig.selection = ["C999"]
    sub = rig.run()
    trace = json.loads(sub.meta.notes[-1])["agent"]
    assert trace["library"] == {}  # the unknown candidate never became a source
    assert any("R1" in s["removed"] for s in trace["salvaged"])  # nor did keys citing it


def test_no_relevant_results_is_valid(rig):
    rig.empty_search = True
    rig.overrides["SELECT"] = {"selected": []}
    rig.overrides["DRAFT"] = lambda c: {
        "text": "" if c["section"]["heading"] == "Research Strategy" else prose(150, "[D1]"),
        "summary": "Applicant pilot supports feasibility.",
    }
    rig.overrides["CRITIQUE"] = {"issues": []}
    sub = rig.run()
    assert sub.meta.status == "ok"
    assert "10.1234" not in sub.proposal
    assert sub.meta.models[0].calls == 12


def test_two_length_rounds_never_truncate(rig):
    rig.overrides["SHORTEN"] = lambda c: {"text": c["current_text"], "summary": "Unchanged"}
    sub = rig.run()
    # Submitted as is: the harness's length contract, not the agent, decides the consequence.
    assert sub.meta.status == "ok"
    assert "shortening rounds" in sub.meta.notes[0]
    assert "beyond the length limit" not in sub.proposal
    assert count_words(parse_proposal(sub.proposal).body_text()) > 700
    shortened = [c["section"]["heading"] for step, c in rig.calls if step == "SHORTEN"]
    assert max(shortened.count(h) for h in set(shortened)) <= 2


@pytest.mark.parametrize("dependency", ["model", "retrieval"])
def test_infrastructure_raises_with_completed_usage(rig, dependency):
    if dependency == "model":
        rig.overrides["SELECT"] = InfrastructureError("provider unavailable")
    else:
        rig.http_error = True
    with pytest.raises(InfrastructureError) as caught:
        rig.run()
    sub = caught.value.submission
    assert sub.meta.status == "infrastructure_failure"
    assert sub.meta.models[0].calls == 1
    assert sub.meta.wall_time_s is not None
    assert json.loads(sub.meta.notes[-1])["agent"]["calls"][0]["step"] == "PLAN"


def test_counted_subtrees_and_exempt_tables_match_harness(make_call):
    data = plan_data()
    data["counted_headings"] = ["Research Strategy"]
    data["exempt_tables"] = True
    plan = agent.Plan.model_validate(data)
    proposal = agent.assemble(
        plan,
        ["uncounted " * 300, "intro", "significance", "text\n\n| table |\n| --- |\n| values |"],
        {},
    )
    call = make_call(counted_sections=["2"], exempt=["title", "references", "tables"])
    call = call.model_copy(
        update={"required_sections": [RequiredSection(id="2", title="Research Strategy")]}
    )
    total, parts = agent.length_counts(plan, proposal)
    assert total == count_words(counted_text(parse_proposal(proposal), call))
    assert total < 10
    assert parts[1] > total - count_words("Research Strategy")  # keyed by plan index


def test_budget_scaling_respects_parent_ceilings():
    data = plan_data()
    for section in data["sections"]:
        section["word_budget"] = 1000
    plan = agent.Plan.model_validate(data)
    agent._prepare_plan(plan, FILES)
    assert sum(s.word_budget for s in plan.sections) <= 630
    assert plan.sections[0].word_budget <= 162
    assert sum(s.word_budget for s in plan.sections[1:]) <= 450


def test_configs_and_version_cover_generation_parameters(tmp_path):
    for name in ("claude-opus-4.6", "gemini-3.1-pro"):
        system = load_system(f"agent-{name}")
        assert isinstance(system, agent.ReferenceAgent)
        assert system.spec == load_system(f"direct-{name}").spec
    system = agent.ReferenceAgent("test", SPEC, tmp_path / "cache.sqlite")
    version = system.version()
    system.spec = replace(SPEC, temperature=0.4)
    assert system.version() != version


def test_cli_preserves_usage_on_failure_and_overrides_cache(rig, monkeypatch, tmp_path):
    from types import SimpleNamespace

    from proposalbench.systems import base, registry

    task = SimpleNamespace(id="example", task=SimpleNamespace(split=SimpleNamespace(value="pilot")))
    monkeypatch.setattr(cli.Repository, "all", lambda self, split: [task])
    monkeypatch.setattr(registry, "load_system", lambda _: rig.system)
    directory = tmp_path / "submission"
    monkeypatch.setattr(base, "submission_dir", lambda *args: directory)
    monkeypatch.setattr(base, "task_version", lambda _task: "v")
    rig.http_error = True
    original = rig.system.generate
    monkeypatch.setattr(rig.system, "generate", lambda task, sample: original(rig.task, sample))
    cache = tmp_path / "override.sqlite"
    result = CliRunner().invoke(
        cli.app,
        [
            "run",
            "--system",
            "test",
            "--samples",
            "1",
            "--workers",
            "1",
            "--agent-cache",
            str(cache),
        ],
    )
    assert result.exit_code == 0, result.output
    sub = load(directory)
    assert sub.meta.status == "infrastructure_failure"
    assert sub.meta.models[0].calls == 1
    assert cache.exists()
    assert rig.system._client is None


def test_library_cap_with_twelve_queries(rig):
    rig.plan["queries"] *= 2
    for i, query in enumerate(rig.plan["queries"]):
        rig.plan["queries"][i] = {**query, "query": f"query {i}"}

    def transport(request):
        response = rig.transport(request)
        data = response.json()
        query = request.url.params["query.bibliographic"].replace(" ", "")
        for work in data["message"]["items"]:
            work["DOI"] += query
        return httpx.Response(200, json=data)

    rig.network = httpx.MockTransport(transport)
    sub = rig.run()
    assert sub.meta.status == "ok"
    trace = json.loads(sub.meta.notes[-1])["agent"]
    assert len(trace["queries"]) == 12
    assert len(trace["library"]) == 30
    assert trace["queries"][-1]["selected"] == []
    assert all(len(q["selected"]) <= 3 for q in trace["queries"])


def test_openalex_only_enabled_with_key(rig, monkeypatch):
    without_key = rig.system.version()
    monkeypatch.setenv("OPENALEX_API_KEY", "test-key")
    assert rig.system.version() != without_key
    seen = []

    def transport(request):
        if request.url.host == "api.crossref.org":
            return rig.transport(request)
        assert request.url.host == "api.openalex.org"
        assert request.url.params["api_key"] == "test-key"
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": "https://openalex.org/W1",
                        "doi": "https://doi.org/10.1234/work1",
                        "title": "Microscopy reliability study 1",
                        "type": "review",
                        "authorships": [
                            {"author": {"display_name": "Researcher"}},
                            {"author": {"display_name": "Scientist"}},
                        ],
                        "publication_year": 2023,
                        "primary_location": {"source": {"display_name": "Methods Journal"}},
                        "abstract_inverted_index": {
                            "Independent": [0],
                            "cultures": [1],
                            "matter.": [2],
                        },
                    }
                ]
            },
        )

    rig.network = httpx.MockTransport(transport)
    sub = rig.run()
    assert sub.meta.status == "ok"
    assert len(seen) == 6
    trace = json.loads(sub.meta.notes[-1])["agent"]
    assert trace["queries"][0]["retrieved"] == {"crossref": 4, "openalex": 1}
    assert len(trace["library"]) == 3
    assert "test-key" not in sub.meta.to_json()


def test_abstract_enrichment_uses_existing_helper(rig):
    seen = []

    def transport(request):
        if request.url.host == "api.crossref.org":
            data = rig.transport(request).json()
            for work in data["message"]["items"]:
                work.pop("abstract")
            return httpx.Response(200, json=data)
        assert request.url.host == "api.semanticscholar.org"
        seen.append(request)
        doi = request.url.path.split("DOI:", 1)[1]
        return httpx.Response(
            200,
            json={
                "paperId": "test",
                "externalIds": {"DOI": doi},
                "abstract": "Independent cultures establish microscopy reliability.",
            },
        )

    rig.network = httpx.MockTransport(transport)
    sub = rig.run()
    assert sub.meta.status == "ok"
    assert len(seen) == 3  # repeated candidates use the evidence cache
    assert (
        "Independent cultures"
        in json.loads(sub.meta.notes[-1])["agent"]["library"]["R1"]["work"]["abstract"]
    )


def test_section_with_bad_citation_is_repaired_once(rig):
    def draft(context):
        cite = "(Smith, 2024)" if "problems_in_previous_reply" not in context else "[R1]"
        return {"text": prose(160, cite), "summary": "Test summary."}

    rig.overrides["DRAFT"] = draft
    sub = rig.run()
    assert sub.meta.status == "ok"
    assert "(Smith, 2024)" not in sub.proposal
    trace = json.loads(sub.meta.notes[-1])["agent"]
    assert trace["repairs"] and trace["repairs"][0]["step"] == "DRAFT"


@pytest.mark.parametrize(
    "text",
    [
        "VAELTHES (2023) delivered the pilot.",
        "the Paris Agreement (2015) and Horizon Europe (2025)",
        "workshop (Madrid 2025) and pilot (M6, 2027 at the latest)",
        "(EU 2021/695)",
    ],
)
def test_projects_and_programmes_with_years_are_not_citations(text):
    assert not agent.OTHER_CITATION.search(text)


@pytest.mark.parametrize(
    "text",
    [
        "(Smith, 2024)",
        "(Smith et al., 2024)",
        "(see Smith and Jones, 2024; Lee, 2021)",
        "Smith et al. (2024)",
        "Smith and Jones (2024)",
        "[R1, R2]",
    ],
)
def test_author_year_citations_are_still_rejected(text):
    assert agent.OTHER_CITATION.search(text)


@pytest.mark.parametrize("key", ["[R10]", "[R123]", "[D12]"])
def test_multi_digit_keys_are_keys(key):
    assert not agent.OTHER_CITATION.search(f"as shown {key} and [R2]")


def nsf_like_plan(child_parents=("Project Summary", "Project Description")):
    data = plan_data()
    sections = []
    for parent in child_parents:
        sections.append(dict(data["sections"][0], heading=parent, level=2, max_words=None))
        for child in ("Intellectual Merit", "Broader Impacts"):
            sections.append(dict(data["sections"][2], heading=child, level=3, word_budget=50))
    data["sections"] = sections
    for q in data["queries"]:
        q["sections"] = ["Intellectual Merit"]
    return agent.Plan.model_validate(data)


def test_a_heading_repeated_under_two_parts_is_allowed():
    assert agent._plan_problems(nsf_like_plan()) == []
    same_parent = nsf_like_plan(("Project Description", "Project Description"))
    assert any("same parent" in p for p in agent._plan_problems(same_parent))


def test_length_counts_match_repeated_headings_by_position():
    plan = nsf_like_plan()
    plan.sections[4].max_words = 10  # the Project Description's Intellectual Merit
    texts = ["summary", "short", "short", "description", "word " * 40, "impacts"]
    _, parts = agent.length_counts(plan, agent.assemble(plan, texts, {}))
    assert parts == {4: 40}


def test_a_refused_selection_skips_only_that_query(rig):
    seen = []

    def select(context):
        seen.append(1)
        if len(seen) <= 2:  # the first query's selection and its one retry
            return Completion("", SPEC.model_id, 7, 1, "content_filtered", 0.01)
        return {"selected": rig.selection}

    rig.overrides["SELECT"] = select
    sub = rig.run()
    assert sub.meta.status == "ok", sub.meta.notes
    trace = json.loads(sub.meta.notes[-1])["agent"]
    assert "skipped" in trace["queries"][0] and "skipped" not in trace["queries"][1]


def test_a_planned_reference_list_is_removed_not_fatal():
    data = plan_data()
    data["sections"].append(dict(data["sections"][0], heading="References", max_words=None))
    data["counted_headings"] = ["Specific Aims", "References"]
    plan = agent.Plan.model_validate(data)
    assert agent._plan_problems(plan) == []
    dropped = agent._prepare_plan(plan, FILES)
    assert "reference-list section removed: References" in dropped
    assert [s.heading for s in plan.sections][-1] == "Approach"
    assert plan.counted_headings == ["Specific Aims"]


def test_openalex_can_be_turned_off_for_the_agent(rig, monkeypatch):
    monkeypatch.setenv("OPENALEX_API_KEY", "test-key")
    with_openalex = rig.system.version()
    rig.system.openalex = False
    assert rig.system.version() != with_openalex
    sub = rig.run()
    assert sub.meta.status == "ok", sub.meta.notes
    assert "openalex" not in sub.meta.tools
    assert all(r.url.host != "api.openalex.org" for r in rig.requests)
    assert load_system("agent-claude-opus-4.6").openalex is False


def test_a_failed_revision_keeps_the_checked_draft(rig):
    rig.overrides["REVISE"] = "not json"
    sub = rig.run()
    assert sub.meta.status == "ok", sub.meta.notes
    trace = json.loads(sub.meta.notes[-1])["agent"]
    assert trace["revision_skipped"]
