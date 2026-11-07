"""Vultr Serverless Inference client.

OpenAI-compatible, base URL https://api.vultrinference.com/v1.
Every model call in this project goes through here -- Track 1 of the hackathon
requires it, and the whole catalogue is open-weight.

    from .llm import inference
    inference.chat("qwen3.8-flash-next", "hello")
    inference.chat_json("qwen3.8-flash-next", "return {ok:true}")
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any

BASE_URL = os.environ.get("VULTR_INFERENCE_BASE_URL", "https://api.vultrinference.com/v1")
API_KEY = os.environ.get("VULTR_INFERENCE_API_KEY", "")

# Default routing (see docs/adal/vultr_agent_rush_research.md for the live catalogue).
MODEL_SUITE = "qwen3.8-flash-next"          # suite generation, agent under test
MODEL_STRONG = "glm-5.3-flash"              # stronger reference agent
MODEL_VISION = "nemotron-3-nano-omni-30b-a3b-reasoning"
MODEL_SAFETY = "nemotron-3.5-content-safety"
MODEL_DECIDER = "pplx-decider-v1.2"


class InferenceError(RuntimeError):
    pass


@dataclass
class Usage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def to_dict(self) -> dict:
        return {
            "prompt_tokens": self.prompt_tokens,
            "completion_tokens": self.completion_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class Completion:
    text: str
    model: str
    usage: Usage = field(default_factory=Usage)
    raw: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return bool(self.text)


def _post(path: str, payload: dict, *, timeout: int = 120, retries: int = 3) -> dict:
    if not API_KEY:
        raise InferenceError(
            "VULTR_INFERENCE_API_KEY is not set. Create a Serverless Inference "
            "subscription in the Vultr console and export the key."
        )
    url = f"{BASE_URL.rstrip('/')}/{path.lstrip('/')}"
    data = json.dumps(payload).encode("utf-8")
    last_err: Exception | None = None

    for attempt in range(retries):
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")[:400]
            last_err = InferenceError(f"{exc.code} from {path}: {body}")
            if exc.code in (400, 401, 403, 404):
                raise last_err  # not worth retrying
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last_err = InferenceError(f"network error calling {path}: {exc}")
        time.sleep(1.5 * (attempt + 1))

    raise last_err or InferenceError(f"failed to call {path}")


def _usage_from(raw: dict) -> Usage:
    u = raw.get("usage") or {}
    return Usage(
        prompt_tokens=int(u.get("prompt_tokens") or 0),
        completion_tokens=int(u.get("completion_tokens") or 0),
        total_tokens=int(u.get("total_tokens") or 0),
    )


def chat(
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.2,
    max_tokens: int | None = None,
    response_format: dict | None = None,
    timeout: int = 120,
    retries: int = 3,
) -> Completion:
    """Plain chat completion."""
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens:
        payload["max_tokens"] = max_tokens
    if response_format:
        payload["response_format"] = response_format

    raw = _post("chat/completions", payload, timeout=timeout, retries=retries)
    try:
        text = raw["choices"][0]["message"].get("content") or ""
    except (KeyError, IndexError, TypeError) as exc:
        raise InferenceError(f"unexpected response shape: {str(raw)[:300]}") from exc
    return Completion(text=text, model=model, usage=_usage_from(raw), raw=raw)


def chat_json(
    model: str,
    messages: list[dict],
    *,
    temperature: float = 0.2,
    max_tokens: int | None = None,
    timeout: int = 120,
    retries: int = 3,
) -> Any:
    """Chat completion that must return JSON.

    Falls back to extracting the first JSON object/array from the text when the
    model wraps it in prose or a code fence.
    """
    resp = chat(
        model,
        messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "json_object"},
        timeout=timeout,
        retries=retries,
    )
    return parse_json(resp.text)


def parse_json(text: str) -> Any:
    """Best-effort extraction of a JSON value from model output."""
    if text is None:
        raise InferenceError("empty model output")
    raw = text.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Strip a markdown code fence.
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

    # First balanced object or array in the text.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = raw.find(opener)
        if start == -1:
            continue
        depth = 0
        in_str = False
        escape = False
        for i in range(start, len(raw)):
            ch = raw[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(raw[start:i + 1])
                    except json.JSONDecodeError:
                        break
    raise InferenceError(f"model output was not valid JSON: {raw[:200]}")


def list_models() -> list[dict]:
    """Public model catalogue (no key required upstream, but we use ours anyway)."""
    req = urllib.request.Request(f"{BASE_URL.rstrip('/')}/models", headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8")).get("data", [])
    except Exception:
        return []


def probe(model: str = MODEL_SUITE) -> dict:
    """Check that the endpoint and the model answer. Used by the health endpoint."""
    try:
        resp = chat(model, [{"role": "user", "content": "Reply with exactly: OK"}], max_tokens=16, timeout=45, retries=2)
        return {"model": model, "ok": bool(resp.text), "sample": resp.text.strip()[:40],
                "usage": resp.usage.to_dict()}
    except Exception as exc:
        return {"model": model, "ok": False, "error": str(exc)[:200]}


# --- module-level convenience --------------------------------------------------

class _Inference:
    def chat(self, model: str, prompt: str, **kw) -> Completion:
        return chat(model, [{"role": "user", "content": prompt}], **kw)

    def chat_json(self, model: str, prompt: str, **kw) -> Any:
        return chat_json(model, [{"role": "user", "content": prompt}], **kw)

    def system_json(self, model: str, system: str, prompt: str, **kw) -> Any:
        return chat_json(model, [{"role": "system", "content": system},
                                 {"role": "user", "content": prompt}], **kw)

    def probe(self, model: str = MODEL_SUITE) -> dict:
        return probe(model)


inference = _Inference()
