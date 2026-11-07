"""The ``direct`` baseline: one prompt with every input file, continued until the model stops.

The prompt is deliberately plain: it hands the model exactly the files every system receives
and the shared instructions, with no extra coaching.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from proposalbench.llm import Completion, InfrastructureError, ModelSpec, complete
from proposalbench.systems.base import ModelUsage, Submission, SubmissionMeta, content_hash
from proposalbench.tasks.loader import ResolvedTask
from proposalbench.tasks.render_instructions import render_instructions

SYSTEM_PROMPT = "You write research funding proposals."

FILE_BLOCK = '<file name="{name}">\n{content}\n</file>'

USER_PROMPT = """\
The files below are everything you have about this funding application.

{files}

Follow the instructions in `instructions.md` and write the proposal now.
"""

CONTINUE_PROMPT = (
    "Your previous reply stopped at the output limit. Continue the proposal exactly where it "
    "stopped, without repeating any text and without any preface."
)
MAX_CONTINUATIONS = 6
MIN_PROPOSAL_CHARS = 1500


def bundle_files(task: ResolvedTask) -> list[tuple[str, str]]:
    files = [("call.md", task.call_text)]
    files += [(f"dossier/{p}", t) for p, t in task.dossier_texts().items()]
    if task.brief_text:
        files.append(("brief.md", task.brief_text))
    files.append(("instructions.md", render_instructions(task)))
    return files


def build_prompt(task: ResolvedTask) -> str:
    files = "\n\n".join(FILE_BLOCK.format(name=n, content=c.strip()) for n, c in bundle_files(task))
    return USER_PROMPT.format(files=files)


@dataclass
class DirectSystem:
    id: str
    spec: ModelSpec

    def version(self) -> str:
        return content_hash(SYSTEM_PROMPT, USER_PROMPT, CONTINUE_PROMPT, self.spec.model_id)

    def generate(self, task: ResolvedTask, sample: int) -> Submission:
        usage = ModelUsage(self.spec.model_id, self.spec.family)
        meta = SubmissionMeta(
            self.id, self.version(), task.id, task.task.split.value, sample, "ok", models=[usage]
        )
        messages = [{"role": "user", "content": build_prompt(task)}]
        parts: list[str] = []
        start = time.monotonic()
        try:
            for i in range(MAX_CONTINUATIONS + 1):
                c: Completion = complete(self.spec, messages, system=SYSTEM_PROMPT)
                usage.calls += 1
                usage.input_tokens += c.input_tokens
                usage.output_tokens += c.output_tokens
                meta.retries += c.retries
                parts.append(c.text)
                if not c.truncated:
                    break
                if i == MAX_CONTINUATIONS:
                    meta.notes.append("output still truncated after maximum continuations")
                    break
                messages += [
                    {"role": "assistant", "content": c.text},
                    {"role": "user", "content": CONTINUE_PROMPT},
                ]
                meta.notes.append(f"continuation {i + 1}")
        except InfrastructureError as exc:
            meta.status = "infrastructure_failure"
            meta.notes.append(str(exc)[:500])
        meta.wall_time_s = round(time.monotonic() - start, 1)
        proposal = "".join(parts)
        if meta.status == "ok" and len(proposal.strip()) < MIN_PROPOSAL_CHARS:
            meta.status = "model_failure"
            meta.notes.append("no substantive proposal text returned")
        return Submission(proposal, meta)
