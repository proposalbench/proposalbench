import pytest

from proposalbench.llm import family_of, parse_json_object


@pytest.mark.parametrize(
    ("model", "family"),
    [
        ("us.anthropic.claude-opus-4-6-v1", "anthropic"),
        ("openai.gpt-oss-120b-1:0", "openai"),
        ("gemini-3.1-pro-preview", "google"),
        ("us.moonshotai.kimi-k3", "moonshot"),
        ("zai.glm-5", "zhipu"),
        ("deepseek.v3.2", "deepseek"),
        ("mistral.mistral-large-3-675b-instruct", "mistral"),
        ("minimax.minimax-m2.5", "minimax"),
        ("qwen.qwen3-next-80b-a3b", "qwen"),
    ],
)
def test_family_of(model, family):
    assert family_of(model) == family


def test_family_of_unknown_raises():
    with pytest.raises(ValueError):
        family_of("acme-model-1")


def test_parse_json_object_variants():
    assert parse_json_object('```json\n{"a": 1}\n```') == {"a": 1}
    assert parse_json_object('Here you go: {"a": {"b": [1, 2]}} done') == {"a": {"b": [1, 2]}}
