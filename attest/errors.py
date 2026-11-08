"""Public-safe errors: never retain provider bodies, URLs, headers, or causes."""

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import fields, is_dataclass, replace
import re

_ACTIVE_SECRETS = ContextVar("active_redaction_secrets", default=())


def active_secrets(*extra):
    return tuple(sorted({s for s in (*_ACTIVE_SECRETS.get(), *extra) if isinstance(s, str) and s}, key=len, reverse=True))


def redact_secrets(text, secrets):
    keys = active_secrets(*secrets)
    if not keys:
        return text
    return re.sub("|".join(re.escape(key) for key in keys), lambda match: "[REDACTED]", text)


def redact_value(value, secrets=()):
    if isinstance(value, str):
        return redact_secrets(value, secrets)
    if isinstance(value, dict):
        return {redact_value(k, secrets): redact_value(v, secrets) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return type(value)(redact_value(v, secrets) for v in value)
    if is_dataclass(value) and not isinstance(value, type):
        return replace(value, **{f.name: redact_value(getattr(value, f.name), secrets)
                                 for f in fields(value) if f.init})
    return value


@contextmanager
def secret_scope(*secrets):
    token = _ACTIVE_SECRETS.set(active_secrets(*secrets))
    try:
        yield
    finally:
        _ACTIVE_SECRETS.reset(token)


def reject_secret_output(text, *secrets):
    if any(key in text for key in active_secrets(*secrets)):
        raise PublicError("credential_output_rejected")


_CODES = frozenset({
    "provider_http_error", "provider_network_error", "provider_invalid_response",
    "provider_missing_key", "provider_request_failed", "agent_runtime_error",
    "run_worker_failed", "invalid_request", "internal_error", "credential_output_rejected",
})


class PublicError(RuntimeError):
    def __init__(self, code: str, status: int | None = None):
        self.code = code if code in _CODES else "internal_error"
        self.status = status if type(status) is int and 100 <= status <= 599 else None
        super().__init__(self.code + (f":{self.status}" if self.status else ""))


def safe_error(exc: BaseException, fallback: str = "agent_runtime_error") -> str:
    if type(exc) is PublicError:
        return str(PublicError(exc.code, exc.status))
    return str(PublicError(fallback))


def safe_outcome_error(value: str) -> str:
    if not value or value == "agent declined to write code":
        return value
    code, _, status = value.partition(":")
    if code in _CODES and (not status or status.isascii() and status.isdigit()):
        return str(PublicError(code, int(status) if status else None))
    return "agent_runtime_error"
