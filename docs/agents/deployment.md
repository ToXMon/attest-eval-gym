# Deployment: ATTEST live demo

Setup token note: the Cloudflare API token used for 2026-11-08 tunnel/DNS setup is exposed in session storage and should be revoked after setup. Runtime credentials are separate: the tunnel token lives only on the host at `/etc/attest/demo-tunnel.token` (root, 600). Never commit, print, or log either.

## Public URLs

- Canonical demo: https://demo.attestgym.com — named Cloudflare Tunnel `attest-demo`, proxied CNAME to the tunnel, ingress `demo.attestgym.com → http://127.0.0.1:8000`, catch-all 404 for every other hostname routed to this tunnel.
- The root domain attestgym.com is not routed. Adding it needs explicit user authorization.
- Quick Tunnel https://numbers-era-deeper-divorce.trycloudflare.com still serves the same app (unit `attest-cloudflared.service`), but Quick Tunnel URLs rotate on restart. Use the demo URL for the submission.

## Approved identifiers (no secrets here)

| What | Value |
|---|---|
| Host | 66.135.13.202 (Vultr), SSH key `~/.ssh/attest_contact_bullynothub`, user root |
| App | uvicorn `attest.server:app` on 127.0.0.1:8000, systemd unit `attest.service` |
| App env | `REQUIRE_GVISOR=1`, DB `/var/lib/attest/attest.db`, runs `/var/lib/attest/runs`, env file `/etc/attest/inference.env` |
| Tunnels | named `attest-demo` id `3971afd8-e840-4467-85bc-a1732d3361f9`; Quick Tunnel via `attest-cloudflared.service` |
| DNS | zone attestgym.com, account `093e3649f8f043b3be54feb38d8aa62e`, record `demo` CNAME proxied |
| Connector service | `attest-demo-tunnel.service` runs `cloudflared tunnel run --token-file /etc/attest/demo-tunnel.token --no-autoupdate` (no `--url`; remote ingress owns routing) |

## Decision table

| Change | Where it lives | How |
|---|---|---|
| UI / backend code | GitHub checkout on the Vultr host | Edit in repo, commit, pull on host, targeted deploy below. No auto-sync exists between GitHub and the host; assume nothing deployed until you deploy it. |
| DNS, hostname, ingress | Cloudflare account (API or dashboard) | Zone attestgym.com. Ingress is remote-managed per tunnel via `PUT /accounts/.../cfd_tunnel/{id}/configurations`. |
| Tunnel connector / services | Vultr host | systemd units; restart `attest-demo-tunnel.service` freely, it is stateless. |
| Run data / ledger | Vultr host `/var/lib/attest` | Append-only via the app. Never reset, never point a new DB at it casually. |

Authority vs observation: facts in this file were observed directly on the host and via the Cloudflare API on 2026-11-08. Anything marked "assumed" is not; re-verify with the discovery commands before relying on it after other sessions have been active.

## Deploying updates without breaking the live demo

- UI-only (attest/web/index.html): atomic replace on the host (`cp` to backup, `install` new file, no service restart). The app serves the file from disk per request.
- Backend code: rsync/git-pull the changed modules, then `systemctl restart attest.service`. This restarts the app and drops in-flight runs; capture run count first, do it outside the concurrent evaluation windows, and keep the DB untouched. Restart never recreates or resets attest.db.
- Never restart `attest.service` or `attest-cloudflared.service` during an active evaluation without saying so; concurrent agents hold run IDs against those processes.
- Never run selftest or live inference as part of deploy verification. Validation is health/board/ops GET reads only.

## Validation (read-only, copy-pasteable)

```sh
curl -s https://demo.attestgym.com/api/health            # {"ok":true,"runtime":"runsc",...}
curl -s https://demo.attestgym.com/api/leaderboard       # 200
curl -s https://demo.attestgym.com/api/ops/runs          # 200
curl -s https://numbers-era-deeper-divorce.trycloudflare.com/api/health   # quick tunnel still alive
ssh root@66.135.13.202 systemctl show attest attest-cloudflared attest-demo-tunnel -p ActiveState,MainPID
```

Full offline regression (selftest, piptest, apitest, hardeningtest, agenttest) passed with exit 0 on 2026-11-08 after this setup; deploy verification itself stays read-only GETs.

## Rollback (in order)

1. Delete the `demo` CNAME record in zone attestgym.com; hostname traffic drains.
2. `systemctl disable --now attest-demo-tunnel` so the connector stops and the tunnel has zero active connections (the API refuses tunnel deletion while a connector is running).
3. `DELETE /accounts/093e3649f8f043b3be54feb38d8aa62e/cfd_tunnel/3971afd8-e840-4467-85bc-a1732d3361f9`.
4. Remove the unit file and `/etc/attest/demo-tunnel.token`, then `systemctl daemon-reload`.
The app itself never needs rollback for this change; it was not restarted. Quick Tunnel (`attest-cloudflared.service`) stays as is.

## Troubleshooting

- Demo 502 from Cloudflare edge: connector down. Check `systemctl status attest-demo-tunnel` and `journalctl -u attest-demo-tunnel -n 50`. It restarts on failure with 5s backoff.
- Demo resolves but nothing else changed: local DNS cache; test with `curl --resolve demo.attestgym.com:443:104.21.72.228`.
- App 500s after a deploy: `journalctl -u attest.service -n 100`; roll back the module, the DB is never touched by deploys.
- Service flapping on boot: the token file must exist and be readable by root (`stat -c '%a %U' /etc/attest/demo-tunnel.token` = `600 root`).
