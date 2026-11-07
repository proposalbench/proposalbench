"""Minimal model access for systems and judges: AWS Bedrock (Converse API) and Google GenAI.

Every call returns token usage and the stop reason, and infrastructure failures (throttling,
5xx, timeouts) are retried at most three times with each retry logged, so that runs can report
retries separately from model failures.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Any, Literal

from dotenv import load_dotenv

load_dotenv()

Provider = Literal["bedrock", "google"]

# Model family by model-id fragment, used for judge independence. Order matters: the first
# fragment found in the lower-cased model id wins.
FAMILIES: list[tuple[str, str]] = [
    ("anthropic", "anthropic"),
    ("claude", "anthropic"),
    ("gpt-oss", "openai"),
    ("openai", "openai"),
    ("gpt", "openai"),
    ("gemini", "google"),
    ("gemma", "google"),
    ("kimi", "moonshot"),
    ("moonshot", "moonshot"),
    ("glm", "zhipu"),
    ("zai.", "zhipu"),
    ("deepseek", "deepseek"),
    ("mistral", "mistral"),
    ("magistral", "mistral"),
    ("grok", "xai"),
    ("xai.", "xai"),
    ("minimax", "minimax"),
    ("qwen", "qwen"),
    ("llama", "meta"),
]


def family_of(model_id: str) -> str:
    m = model_id.lower()
    for fragment, fam in FAMILIES:
        if fragment in m:
            return fam
    raise ValueError(f"unknown model family for {model_id!r}; add it to llm.FAMILIES")


@dataclass(frozen=True)
class ModelSpec:
    provider: Provider
    model_id: str
    max_output_tokens: int = 32000
    temperature: float | None = 0.0
    region: str = "us-east-1"

    @property
    def family(self) -> str:
        return family_of(self.model_id)


@dataclass
class Completion:
    text: str
    model_id: str
    input_tokens: int
    output_tokens: int
    stop_reason: str  # "end" | "max_tokens" | other provider reason
    latency_s: float
    retries: list[dict[str, Any]] = field(default_factory=list)

    @property
    def truncated(self) -> bool:
        return self.stop_reason == "max_tokens"


class InfrastructureError(RuntimeError):
    """The provider failed after all retries; not attributable to the model's output."""


MAX_RETRIES = 3
GOOGLE_TIMEOUT_MS = 900_000


@lru_cache(maxsize=4)
def _bedrock(region: str):
    import boto3
    from botocore.config import Config

    profile = os.getenv("AWS_PROFILE") or None
    session = boto3.Session(profile_name=profile)
    cfg = Config(read_timeout=900, connect_timeout=30, retries={"max_attempts": 1})
    return session.client("bedrock-runtime", region_name=region, config=cfg)


def _google():
    from google import genai
    from google.genai import types

    # Without a timeout a stalled connection blocks forever (observed in the pilot).
    return genai.Client(
        api_key=os.environ["GOOGLE_API_KEY"],
        http_options=types.HttpOptions(timeout=GOOGLE_TIMEOUT_MS),
    )


def _is_transient(exc: Exception) -> bool:
    name = type(exc).__name__
    text = str(exc)
    transient_names = {
        "ThrottlingException",
        "ServiceUnavailableException",
        "ReadTimeoutError",
        "ConnectTimeoutError",
        "ReadTimeout",
        "ConnectTimeout",
        "TimeoutException",
        "ModelNotReadyException",
        "InternalServerException",
        "ServerError",
        "EndpointConnectionError",
    }
    return name in transient_names or any(
        s in text
        for s in (
            "Throttling",
            "Too many requests",
            "503",
            "502",
            "500",
            "429",
            "timed out",
            "RESOURCE_EXHAUSTED",
            "UNAVAILABLE",
        )
    )


def _bedrock_call(spec: ModelSpec, system: str | None, messages: list[dict], max_tokens: int):
    inference: dict[str, Any] = {"maxTokens": max_tokens}
    if spec.temperature is not None:
        inference["temperature"] = spec.temperature
    kwargs: dict[str, Any] = {
        "modelId": spec.model_id,
        "messages": [{"role": m["role"], "content": [{"text": m["content"]}]} for m in messages],
        "inferenceConfig": inference,
    }
    if system:
        kwargs["system"] = [{"text": system}]
    r = _bedrock(spec.region).converse(**kwargs)
    blocks = r["output"]["message"]["content"]
    text = "".join(b.get("text", "") for b in blocks)
    usage = r.get("usage", {})
    stop = {"end_turn": "end", "stop_sequence": "end", "max_tokens": "max_tokens"}.get(
        r.get("stopReason", ""), r.get("stopReason", "")
    )
    return text, usage.get("inputTokens", 0), usage.get("outputTokens", 0), stop


def _google_call(spec: ModelSpec, system: str | None, messages: list[dict], max_tokens: int):
    from google.genai import types

    contents = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part(text=m["content"])],
        )
        for m in messages
    ]
    cfg = types.GenerateContentConfig(
        system_instruction=system,
        max_output_tokens=max_tokens,
        temperature=spec.temperature,
    )
    # Keep the client referenced for the whole call: a temporary genai.Client is finalised
    # mid-request, which closes its HTTP connection.
    client = _google()
    r = client.models.generate_content(model=spec.model_id, contents=contents, config=cfg)
    text = r.text or ""
    um = r.usage_metadata
    reason = r.candidates[0].finish_reason.name if r.candidates else "UNKNOWN"
    stop = {"STOP": "end", "MAX_TOKENS": "max_tokens"}.get(reason, reason.lower())
    out_tokens = (um.candidates_token_count or 0) + (um.thoughts_token_count or 0) if um else 0
    return text, (um.prompt_token_count or 0) if um else 0, out_tokens, stop


def complete(
    spec: ModelSpec,
    messages: list[dict],
    system: str | None = None,
    max_tokens: int | None = None,
) -> Completion:
    """One model call; ``messages`` are ``{"role": "user"|"assistant", "content": str}``."""
    call = _bedrock_call if spec.provider == "bedrock" else _google_call
    max_tokens = max_tokens or spec.max_output_tokens
    retries: list[dict[str, Any]] = []
    for attempt in range(MAX_RETRIES + 1):
        start = time.monotonic()
        try:
            text, tin, tout, stop = call(spec, system, messages, max_tokens)
            return Completion(
                text, spec.model_id, tin, tout, stop, time.monotonic() - start, retries
            )
        except Exception as exc:
            if (
                spec.temperature is not None
                and "temperature" in str(exc)
                and ("doesn't support" in str(exc) or "not support" in str(exc))
            ):
                # Some reasoning models reject sampling parameters; use the provider default.
                spec = ModelSpec(
                    spec.provider, spec.model_id, spec.max_output_tokens, None, spec.region
                )
                retries.append(
                    {"attempt": attempt + 1, "error": "temperature unsupported; dropped"}
                )
                continue
            if not _is_transient(exc) or attempt == MAX_RETRIES:
                if _is_transient(exc):
                    raise InfrastructureError(f"{spec.model_id}: {exc}") from exc
                raise
            retries.append({"attempt": attempt + 1, "error": f"{type(exc).__name__}: {exc}"[:300]})
            time.sleep(min(60, 5 * 2**attempt))
    raise AssertionError("unreachable")


_JSON_BLOCK = re.compile(r"\{.*\}", re.S)


def parse_json_object(text: str) -> dict:
    """Extract the outermost JSON object from a model reply (tolerates code fences and prose)."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        m = _JSON_BLOCK.search(text)
        candidate = m.group(0) if m else text
    return json.loads(candidate)
