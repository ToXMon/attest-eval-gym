# Plan: demo.attestgym.com named tunnel (domain-builder)

Date: 2026-11-08 (deadline 23:00 UTC). Status: **plan — no mutations yet**.
Operator: AdaL (domain-builder). Approval gate: user says go before any SSH mutation, commit or push.

## Goal

`https://demo.attestgym.com` serves the existing ATTEST app as a stable public URL, in parallel with the running Quick Tunnel, touching nothing the concurrent procurement evaluator depends on.

## Discovered state (observed 2026-11-08, all read-only)

- Host `66.135.13.202`, key `~/.ssh/attest_contact_bullynothub`. App: uvicorn on `127.0.0.1:8000` (systemd `attest.service`, REQUIRE_GVISOR=1, DB `/var/lib/attest/attest.db`).
- Existing tunnel: systemd `attest-cloudflared.service` runs `cloudflared tunnel --url http://127.0.0.1:8000` → Quick Tunnel `https://numbers-era-deeper-divorce.trycloudflare.com`. **Do not restart or edit this unit.**
- cloudflared 2026.10.7 supports `tunnel run --token-file` (verified in `--help` on host).
- Cloudflare: token active; zone `attestgym.com` active, account `093e3649f8f043b3be54feb38d8aa62e`; tunnel list 200, **zero existing tunnels**.
- Live health on Quick Tunnel: `{"ok":true,"runtime":"runsc","runs":9}`, `/api/ops/runs` 200 with completed runs. `demo.attestgym.com` currently resolves to nothing (000).
- Working tree at `6225678`; concurrent sessions own slides/demo_suite files — do not touch.

## Steps (v2 — incorporates domain-evaluator-plan.md fixes 1–5)

0. **Baseline capture** (pre-mutation): run count from `/api/health`, `attest.service` + `attest-cloudflared.service` PIDs/start times, full DNS record list for the zone. Attribute any later change to its owner before flagging.
1. **Tunnel, GET-first (fix 1)**: `GET /accounts/{acct}/cfd_tunnel?name=attest-demo`; reuse existing ID unless its status is `deleted`. POST create only when absent.
2. **Token file on host**: write tunnel token to `/etc/attest/demo-tunnel.token` via stdin transfer, `chmod 600` root-only. Verify `stat` = `600 root` (gate V3). No token in repo, logs, or shell args.
3. **Ingress config BEFORE DNS (fix 3)**: `PUT /accounts/{acct}/cfd_tunnel/{id}/configurations` ingress `[{hostname: demo.attestgym.com, service: http://127.0.0.1:8000}, {service: http_status:404}]`. The 404 catch-all applies to any hostname routed to this tunnel; Quick Tunnel unaffected (per-tunnel config).
4. **Parallel service** `/etc/systemd/system/attest-demo-tunnel.service`: `cloudflared tunnel run --token-file /etc/attest/demo-tunnel.token --no-autoupdate` — **no `--url` flag (fix 4)**: remote-managed ingress owns routing, so local `--url` would conflict. `Restart=on-failure`, `RestartSec=5`. Independent of `attest-cloudflared.service`. Verify connector healthy via tunnel connections (≥1) before DNS.
5. **DNS route, GET-first (fixes 1–2)**: `GET /zones/{zone}/dns_records?name=demo.attestgym.com`. If a conflicting record exists: **stop and report it, do not overwrite** (user instruction). Otherwise POST `demo` CNAME → `<tunnel-id>.cfargotunnel.com`, proxied true. Demo record only.
6. **Validate**: TLS valid; `GET https://demo.attestgym.com/api/health` → 200 `ok:true runtime:runsc`, `server: cloudflare` header; `/api/board` + `/api/ops/runs` 200; Quick Tunnel still 200 with run count attributable vs baseline; token absent from journal/unit/repo grep (V3/V6); `attest-cloudflared.service` PID/start time unchanged. Note (concurrency caveat): exact process counts and run-count equality are attributed, not asserted blind — other sessions may be live.
7. **Durable docs + scoped commit**:
   - `docs/agents/deployment.md`: decision table (UI/backend edits from GitHub checkout on Vultr, no auto-sync unless proved; DNS/ingress authority in Cloudflare; runtime connector on Vultr; data paths/backups), discovery commands, approved IDs (host/key path/port/tunnel ID, no tokens), UI atomic update vs targeted backend deploy preserving DB, restart/rollback, troubleshooting, authority-vs-observation rule, never reset production or live selftest, root domain unrouted unless authorized, token revocation note (setup token vs runtime token file).
   - `AGENTS.md`: one pointer line (trigger: deploying, updating domain, troubleshooting live → read deployment.md).
   - `README.md`: replace only the stale top recorded-URL line with `https://demo.attestgym.com`.
   - Scoped explicit commit + push, inspect diff for secrets, no force. Stop if concurrent staged work touches these files.

**Resume points (fix 3)**: tunnel created but service failed → reuse ID, fix host side. DNS live but service down → proxied 502, visible in validation. Aborted after tunnel creation → finish or delete; no orphan tunnel left.

## Rollback

- DNS: delete only the `demo` CNAME record.
- Tunnel: `DELETE /accounts/.../cfd_tunnel/{id}` (empty state, nothing shared).
- Host: `systemctl stop disable attest-demo-tunnel`, remove unit + token file. App and Quick Tunnel never restarted, so app rollback is a no-op by construction.

## Validation checks

- Both tunnels healthy simultaneously; run count identical before/after.
- `demo.attestgym.com` TLS valid, proxied (orange cloud), 404 on unknown hostnames via catch-all.
- Scoped diff check: only deployment.md, AGENTS.md, README.md changed in commit.
- No secrets in any committed file, log, or shell history; token file root-only on host.

## Risks

- Concurrent evaluator uses the Quick Tunnel URL — preserved by not touching its unit; risk is only accidental restart of `attest-cloudflared.service`, which the plan never does.
- Token write permission untested; if `POST /cfd_tunnel` or config PUT returns 403, stop and report — do not use `cloudflared login` interactively on the host without asking.
- Quick Tunnel dies on any restart by nature; the named tunnel is the mitigation, not a dependency.
