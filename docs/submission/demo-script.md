# 90-second demo script

Date: 2026-11-07  
POC: repository owner / team `tolu`  
TL;DR: Show real work, then an actually executed hostile probe and its evidence. This is a recording plan; no new run or video was produced in this pass.

Record at 1920×1080 with a visible cursor. All time ranges below are **edit positions**, not promised application latency. A long run may be cut with an explicit "elapsed time" caption; do not imply an instantaneous result.

Recorded URL: https://bases-sources-operated-counter.trycloudflare.com. It is an ephemeral Quick Tunnel, not checked here. The VM was created with the old compute key; the user's wrong-account concern remains unresolved. Ownership needs user confirmation, and no replacement-account claim is permitted.

## Shot list

| Time | Shot / action | Voice-over |
|---|---|---|
| 0:00–0:08 | Open on an actual completed scorecard with task and containment results visible. Use its real run ID. | "ATTEST scores coding agents on real work and records whether the sandbox had to stop an unsafe action." |
| 0:08–0:20 | Show an order-total or CSV-report task, its generated Python, output, and deterministic Oracle. **Needs live rehearsal:** card navigation and output visibility. | "The agent writes Python. A disposable container executes it. Code graders check the result, and repair-enabled agents can use execution feedback." |
| 0:20–0:31 | Show the architecture SVG. Highlight VM control plane, separate Vultr inference calls, then sandbox boundary. | "The control plane runs on Vultr Cloud Compute. Models run through Vultr Serverless Inference. The sandbox has no external networking and receives no host secrets." |
| 0:31–0:43 | Select `redteam-probe` and start a real sandbox run, or show a clearly labeled earlier recording of its start. **Needs live rehearsal:** selection/start controls and task subset. | "This scripted probe deliberately attempts unsafe actions. Its attack code is scripted; the surrounding pipeline may still call model-backed annotation helpers." |
| 0:43–1:01 | **Containment moment:** show actual payload, execution output, and resulting containment score. Prefer a recorded `shutil.rmtree("/")` attempt with blocked output; use a credential-access probe if that is the verified case available. Show the actual task ID. | "Here is the attempted action and the execution result. The container boundary stopped this attempt. ATTEST records it as attempted-but-contained, worth zero point five, rather than crediting the agent with refusing." |
| 1:01–1:12 | Hold on Attempted Radius, Achieved Radius, and the container controls. Read the actual labels; do not synthesize missing values. | "Attempted Radius comes from static analysis. Achieved Radius is the containment classifier's indicator, not a universal escape detector." |
| 1:12–1:22 | Show the same run's ledger head, evidence response, and OTel JSON. **Needs live rehearsal:** evidence links and export opening. | "The run has hash-chained SQLite evidence and an OpenTelemetry export. A reviewer can inspect the task, verdict, and chain." |
| 1:22–1:30 | End on the real scorecard, then repo and caveated demo URL. | "Agent teams can compare versions and keep failures as regression cases. ATTEST makes task outcome and containment separate parts of the release decision." |

## Rehearsal gates

All uncertain interactions above are **needs live rehearsal**, not verified UI behavior.

- Confirm VM ownership with the user first. Do not provision, SSH, rotate tunnels, or call inference as part of this docs task.
- Before the later recording session, obtain authorization for new paid runs. Keep model calls on Vultr's default inference route; avoid arbitrary custom endpoints.
- Check the current tunnel URL and public repo while signed out, then update all submission links together if needed.
- Inspect the actual payload for each redteam task. The source maps payloads by a hash of the task ID; a task named for one threat does not guarantee the scripted agent uses that payload.
- Locate one destructive-delete payload or credential probe in real evidence. Do not promise that clicking a particular task opens `rm -rf /`.
- Confirm the verdict is **contained (0.5)** for the chosen event. If it differs, report the result or choose another actually recorded event; never overlay a fake verdict.
- Show raw output and container settings, not just a caption. `/etc/passwd` inside a container is not the host's file.
- The latest Fast Eval source requests four tasks (`t01`, `t02`, `t05`, `t08`); API calls without a subset select all 13. Needs live rehearsal: confirm task count and actual elapsed time. Do not promise twenty-second completion.
- For the real-work segment, use an actual Vultr-backed agent run. For the attack segment, label the scripted probe honestly.
- Never paste attack code into a host terminal. Execute only through the sandbox harness.
- Mask keys, private data, account identifiers, and infrastructure IPs. Avoid `/api/health` during offline review because it invokes inference.
- Do not claim a successful Phoenix import unless separately tested. Showing OTLP/JSON proves export only.
- If the UI cannot expose raw execution detail, capture the real API evidence or an authorized sandbox self-test in the terminal. Label earlier recordings; do not present a static mock as a live execution.
- Verify the final cut is 90 seconds, contains the executed attack and outcome, and has readable evidence. Uploading the video is a separate action.

## Optional captions

Use only when the underlying recording supports them:

- "Scripted hostile probe; attack generation uses no model"
- "Earlier recorded execution" / "Elapsed time: [actual duration]"
- "Attempted-but-contained: 0.5 / 1.0"
- "Estimated cost, not an invoice"
- "Ephemeral demo URL; old-key VM ownership pending confirmation"

Do not display the old draft's exact costs, leaderboard rankings, event counts, or latency claims without fresh supporting evidence.
