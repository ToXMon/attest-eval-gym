"""Fixed provider policy for the public eval server's inference transports."""

import urllib.error
import urllib.parse
import urllib.request

VULTR_BASE_URL = "https://api.vultrinference.com/v1"


def validate_provider_url(value: str) -> str:
    """Accept only the provider API base, never a user-selected HTTP origin."""
    try:
        url = urllib.parse.urlsplit(value)
        valid = (
            value == value.strip()
            and not any(ord(c) < 33 or ord(c) == 127 for c in value)
            and url.scheme == "https"
            and url.hostname == "api.vultrinference.com"
            and url.username is None and url.password is None
            and url.port in (None, 443)
            and url.path.rstrip("/") == "/v1"
            and not url.query and not url.fragment
            and "\\" not in value
        )
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("Custom endpoints must use https://api.vultrinference.com/v1 (HTTPS port 443 only).")
    return VULTR_BASE_URL


class NoRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise urllib.error.HTTPError(req.full_url, code, "Inference redirects are disabled", headers, fp)


def provider_opener():
    # Do not let environment proxy settings change the approved destination.
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirects())
