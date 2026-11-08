# Deployment hardening

Date: 2026-11-07
POC: deployment lead
TL;DR: deployment stays private until manual baseline seeding and verification. No old database or runs are transferred.

## Operator configuration

Supply `VULTR_API_KEY` and `VULTR_INFERENCE_API_KEY` in the caller environment. The deploy script never reads `.env`. Set `ATTEST_SSH_KEY_FILE` and pass `--ssh-key-id` (or set `ATTEST_SSH_KEY_ID`). An unencrypted dedicated private key is required for unattended public-key derivation.

The script requires `/v2/account` to return email exactly `contact@bullynothub.com`. This is the default when `ATTEST_EXPECTED_ACCOUNT_EMAIL` is unset; explicitly empty or different configured values are rejected before credentials or remote calls. Missing or mismatched account email fails closed. Dry-run prints the required account without reading credentials. Reusing a tagged instance requires `--reuse-instance-id`, fresh same-key account inventory and instance detail checks. Paginated or ambiguous inventories fail closed.

`bash scripts/deploy.sh --dry-run` prints a path-only offline upload manifest and the proposed gates. Source transfer is limited to `attest/`, `scripts/`, and `requirements.txt`, with state, secrets, images, symlinks and caches excluded.

The service reads only `/etc/attest/inference.env` (0600). Data lives at `ATTEST_DB=/var/lib/attest/attest.db` and `ATTEST_RUNS_DIR=/var/lib/attest/runs`. The compute key stays local and is unset before deploy subprocesses. A legacy remote `/opt/attest/.env` blocks deployment; the operator must review and remove it and rotate any exposed credential separately.

## Publication

Deployment requires cloud-init done, Docker advertising runsc, an actual successful sandbox execution under runsc, and successful loopback health. It stops/disables an existing tunnel before these checks. Runtime fallback is refused whenever `REQUIRE_GVISOR=1`.

The script prints a manual, paid seed command using the service's exact data paths and inference-only environment file. It never runs this command. Restart the service after manual seeding so persisted records load, then rerun with `--reuse-instance-id` and `--open-public`. Publication requires at least six leaderboard rows, loaded records with valid stored and independently verified ledger chains, and successful HTTPS tunnel health. Failed HTTPS verification stops the tunnel. Tunnel startup is deliberately not enabled at boot; publication must be verified again after reboot.

The service binds `127.0.0.1`, uses one worker, disables uvicorn proxy-header interpretation, and applies `NoNewPrivileges`, `ProtectSystem=full`, `ProtectHome`, and a private umask. It still runs as root with access to rootful Docker. This is not rootless Docker or a separate host execution broker.

## Public limits

HTTP admission covers POST `/api/run`, POST `/api/suite`, and GET `/api/selftest`:

- Two concurrent jobs, including the full background run lifetime.
- Six admissions per client IP per rolling minute, shared across these endpoints.
- 100 admitted jobs per UTC day in the process.
- At most 16 tasks per run or generated suite, preserving the existing 13-task seeded evaluation. Duplicate selected tasks are rejected.
- 32 KiB request bodies, a 10-second body-read deadline, and a 2,000-character suite topic.
- At most 100 cached suites.

Only loopback cloudflared requests may supply `CF-Connecting-IP` when `ATTEST_TRUST_LOCAL_TUNNEL=1`. Visitor `X-Forwarded-For` is ignored. Never expose uvicorn directly or expand this trust to arbitrary peers.

All shared server-key transport attempts reserve conservative prompt-byte plus output-token estimates before sending, including retries. Ambiguous failures and missing usage keep their reservation. Higher reported usage increases the tally and blocks subsequent calls when exhausted. Defaults are $0.50 per process and $0.25 per UTC day, configurable via `ATTEST_PROCESS_BUDGET_USD` and `ATTEST_DAY_BUDGET_USD`. Limits are in-memory and reset at process restart. Dollar conversion uses the existing planning price table, not a provider invoice: verify prices before public use. Unexpected provider overbilling or usage above a reservation cannot be reversed after a request. This is not an account-wide financial cap. Visitor-key calls still share compute admission limits.

Direct Python route calls used by local tests bypass HTTP admission. Real server-key transport still enforces the spending budget. Read-only health never probes paid inference.

## Lead decisions before deployment

Confirm access to the required account `contact@bullynothub.com`, the dedicated SSH key, budget amounts and price table. Choose whether in-memory single-worker counters are sufficient for the short demo; durable cross-restart/account-wide limits need a separate change. Approve the remaining rootful Docker privilege boundary. Confirm the manual seed results are valid demonstrations before opening the tunnel. No live account, SSH, cloud-init, gVisor host, or public tunnel has been verified by this offline work.
