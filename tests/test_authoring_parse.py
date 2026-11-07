import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "authoring"))
from synthesize import parse_reply


def test_single_object_with_prose_and_fences():
    assert parse_reply('Here it is:\n```json\n{"a": 1, "b": {"c": 2}}\n```') == {
        "a": 1,
        "b": {"c": 2},
    }


def test_unit_followed_by_separate_rejected_object_is_merged():
    reply = '{"files": [{"path": "cv.md"}], "facts": []}\n\n{"rejected": [{"reason": "x"}]}'
    assert parse_reply(reply) == {
        "files": [{"path": "cv.md"}],
        "facts": [],
        "rejected": [{"reason": "x"}],
    }


def test_overlapping_objects_keep_the_largest():
    reply = '{"brief": "short"} then the full one: {"brief": "a much longer brief", "traps": []}'
    assert parse_reply(reply) == {"brief": "a much longer brief", "traps": []}


def test_braces_in_prose_before_the_json_are_skipped():
    assert parse_reply('Note {not json} here. {"verdict": "accept", "issues": []}') == {
        "verdict": "accept",
        "issues": [],
    }


def test_no_json_raises():
    with pytest.raises(ValueError):
        parse_reply("no object here")
