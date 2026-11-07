from datetime import date

import pytest

from proposalbench.tasks.schema import (
    Call,
    CallItem,
    Eligibility,
    Enforcement,
    LengthContract,
    Provenance,
    RequiredSection,
)

CANARY = "PROPOSALBENCH-CANARY 00000000-0000-4000-8000-000000000000"


def make_call(max_words: int = 1000, enforcement: Enforcement = Enforcement.inadmissible, **lc):
    return Call(
        id="call-test",
        scheme="horizon_ria",
        language="en",
        title="Test call",
        topic_code="PB-TEST-01",
        length_contract=LengthContract(
            max_words=max_words, enforcement=enforcement, source_note="test", **lc
        ),
        required_sections=[
            RequiredSection(id="1", title="Excellence"),
            RequiredSection(id="1.1", title="Objectives and ambition", parent="1"),
            RequiredSection(id="2", title="Impact"),
            RequiredSection(
                id="3",
                title="Quality and efficiency of the implementation",
                aliases=["Implementation"],
            ),
        ],
        expected_outcomes=[CallItem(id="EO1", text="Outcome one")],
        eligibility=Eligibility(budget_in_narrative=False),
        provenance=Provenance(author="human", author_family="human", created=date(2026, 10, 30)),
        canary=CANARY,
    )


@pytest.fixture
def call():
    return make_call()


@pytest.fixture(name="make_call")
def make_call_fixture():
    return make_call


# Real service credentials in .env must not change test behaviour: an empty variable that
# already exists is not overridden by load_dotenv, and reads as "not configured".
_SERVICE_KEYS = ("OPENALEX_API_KEY", "CROSSREF_MAILTO", "SEMANTIC_SCHOLAR_API_KEY", "EXA_API_KEY")


@pytest.fixture(autouse=True)
def _no_service_credentials(monkeypatch):
    for key in _SERVICE_KEYS:
        monkeypatch.setenv(key, "")
