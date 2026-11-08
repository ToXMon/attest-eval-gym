# Plan: independent evaluator — demo.attestgym.com tunnel build

Date: 2026-11-08 (deadline 23:00 UTC). Evaluator: AdaL (domain-evaluator).
Input reviewed: `docs/adal/domain-builder-plan.md` (v. 2026-11-08, "plan — no mutations yet").
Scope: critique + verification plan only. **No mutations, no secrets, no SSH changes, no source edits** in this mission. Final eval is a separate later mission.

## Verdict

Plan is **approvable with 5 required fixes** (below). None are blocking disagreements; all are concrete, cheap amendments the builder should apply before execution. No change to goals, isolation strategy, or rollback approach.

## Critique

### 1. Idempotence — required fix
Step 1 (create tunnel `attest-demo`) is not rerun-safe: a second execution creates a duplicate tunnel. Fix: before POST, `GET /accounts/{acct}/cfd_tunnel?name=attest-demo`; reuse the existing tunnel ID if found (a deleted-but-listed tunnel in state `deleted` must be ignored). Same for DNS: `GET /zones/{zone}/dns_records?name=demo.attestgym.com` first — update the existing record instead of POSTing (Cloudflare rejects duplicate proxied CNAMEs, which would leave step 4 half-done). Host side is naturally idempotent if the unit file write is atomic (`install -m 600` to temp + `mv`).

### 2. DNS conflicts — required fix
Discovery says demo "resolves to nothing (000)", but that is a resolution check, not a zone-record check — a stale/proxied A or CNAME `demo` record could exist and shadow the new CNAME (or block it). Fix: explicit zone-record lookup in step 4, and gate on: exactly one `demo` record post-change, type CNAME, target `<tunnel-id>.cfargotunnel.com`, proxied=true. Any *other* pre-existing demo record must be reported, not silently overwritten.

### 3. Partial-failure ordering — required fix (order is correct, failure handling missing)
Current order (tunnel → token → service → DNS → ingress config → validate) has one bad window: if the service fails to go active after DNS exists but before ingress config, the named tunnel is up and routable with default catch-all behavior. Two amendments:
- Apply the ingress configuration (step 5) **before** the DNS route (step 4): config-then-DNS means the hostname is never live with the wrong catch-all. (API PUT configurations works on a not-yet-routed tunnel.)
- Define resume points: tunnel created but service failed → reuse tunnel ID, fix host side, skip creation. DNS live but service down → 502 from Cloudflare (proxied), self-evident in validation gate V5.
- Orphan cleanup gate: if the run aborts after tunnel creation, either finish or delete the tunnel; do not leave a nameless-state tunnel behind (final state check V7).

### 4. Catch-all 404 blast radius — required clarification
The ingress config is per-tunnel, so the Quick Tunnel is genuinely unaffected (correct). But the plan must state the 404 rule applies to **any hostname routed to `attest-demo`**, and the validation must prove isolation in both directions: unknown host via the named tunnel → 404 (numeric gate), and the Quick Tunnel URL → still 200 health (isolation gate). Also confirm the `--url` flag and a remote-managed configuration don't conflict: with token-file run + remote config, any local `--url` is overridden by ingress — the builder should either drop `--url` from the unit (ingress owns routing) or keep it as harmless default; pick one and document which.

### 5. Token handling — approve with one addition
Root-600 token file, no shell args/logs/repo: good. Addition: verify post-write with `stat -c '%a %U' /etc/attest/demo-tunnel.token` = `600 root` as an explicit gate (V3), and ensure the token never appears in `journalctl` output (cloudflared logs the tunnel ID, not the token — verify in gate V6 by grepping journal for the token prefix).

## Numeric / live verification gates (for the final-eval mission)

| # | Gate | Numeric criterion | Mode |
|---|------|-------------------|------|
| V1 | App untouched | `attest.service` active; health `{"ok":true,"runtime":"runsc"}` on 127.0.0.1:8000; run count identical pre/post (baseline captured first) | live, host-local |
| V2 | Process isolation | Exactly 2 cloudflared processes (`pgrep -a cloudflared` count = 2); both distinct PIDs; `attest-cloudflared.service` uptime unchanged (not restarted) | live, host |
| V3 | Token hygiene | `stat` on token file = `600 root`; `grep -r` token prefix over unit file, repo tree, commit diff = 0 hits | numeric |
| V4 | Service health | `systemctl is-active attest-demo-tunnel` = active; `Restart=on-failure` + `RestartSec=5` present in unit | live |
| V5 | Demo URL live | `GET https://demo.attestgym.com/api/health` → HTTP 200, JSON `ok:true`; TLS valid; response header `server: cloudflare` (proxied, not direct-to-origin) | live |
| V6 | Catch-all + isolation | `GET https://demo.attestgym.com/` serves app; unknown-hostname request to same tunnel → 404; Quick Tunnel `numbers-era-...trycloudflare.com/api/health` still 200 with same run count as V1 | live |
| V7 | Cloudflare state | Tunnel list shows exactly one `attest-demo`, status healthy/active connections ≥ 1; zone has exactly one `demo` record: CNAME → `<id>.cfargotunnel.com`, proxied true; no other records changed (diff record list vs baseline) | live API, read-only |
| V8 | Docs/commit scope | `git diff --stat` vs baseline shows only `docs/agents/deployment.md`, `AGENTS.md` (1 line), `README.md` (1 line); commit pushed to master; no `.env` or token material in diff (`git show --stat` + grep) | numeric |

## Documentation navigation checklist (durable docs the evaluator must verify exist and resolve)

- [ ] `docs/agents/deployment.md` exists and answers, each in ≤ 1 hop from its top: which host/key (key *location* only, never contents), which services (`attest`, `attest-cloudflared`, `attest-demo-tunnel`), which tunnels (quick vs named) and which URL each serves.
- [ ] Cloudflare side documented: zone, account ID reference, tunnel name/ID, DNS record, where the token file lives (`/etc/attest/demo-tunnel.token`) — path only, no secret value.
- [ ] Vultr side documented: app port, DB path, `REQUIRE_GVISOR=1` note.
- [ ] "Safe updates vs restart" section: what may be restarted (`attest-demo-tunnel` only), what must never be restarted (`attest.service` during eval window, `attest-cloudflared.service`), and how to update code/data without touching the app process.
- [ ] Rollback section matches the builder plan (delete CNAME → delete tunnel → stop/disable/remove unit+token) with the note that app rollback is a no-op by construction.
- [ ] Validation commands from gates V1–V8 copy-pasteable.
- [ ] `AGENTS.md` has the single pointer line; `README.md` demo URL line updated; no doc contains the Quick Tunnel URL as the primary demo URL after cutover.
- [ ] **No live selftest** appears in docs as part of deployment validation — health/runs reads only; explicit line saying selftest/live inference is out of scope for deploy verification.

## Execution constraints (both missions)

- Read-only on host and Cloudflare in this mission; all mutations deferred to the final eval after user go-ahead.
- Concurrent procurement work is sacrosanct: baseline-capture before any future mutation (run count, service uptimes, DNS record list) so V1/V2/V7 can prove zero collateral.
- No `attest.service` or `attest-cloudflared.service` restarts ever, in any plan variant.

## Blocking disagreements

None. The five fixes above are amendments, not vetoes; the builder may proceed once they are folded into `domain-builder-plan.md` (idempotent lookups, config-before-DNS, token stat gate, `--url`-vs-ingress decision, resume points).