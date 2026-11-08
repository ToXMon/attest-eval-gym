# Submission finalization plan

Date: 2026-11-07  
POC: repository owner / submission lead; engineering lead for runtime and evidence review  
TL;DR: Reuse the six existing seed runs and one selected Fast Eval wherever their provenance and publication eligibility permit. Finish the visuals and presentation, demonstrate regression promotion, and record one real containment event. Plan zero to two additional small evaluations, not another blanket benchmark. Ownership, evidence safety, and deployment verification come before public release.

## Scope and decision

This is a plan, not execution approval. This pass reads local files and writes only this document. It makes no live-site, cloud, GitHub, provider-catalog, inference, or publishing calls; runs no evaluations; and creates no code, images, deck, video, or commits.

Recorded submission deadline: **2026-11-08, 23:00 UTC**, from the [local event research](../adal/vultr_agent_rush_research.md). Aim to complete uploads by 21:00 UTC, leaving two hours for form or media problems. Confirm the deadline and actual attachment requirements later, in an authorized submission session.

Recommendation: finish the proof and judge journey before adding breadth. Existing model routes already cover comparison baselines. More models, generated suites, repeat seed sweeps, and a new observability deployment would add risk without closing the missing submission gates.

## 1. What exists, and what it proves

| Local artifact | Finding | Evidence scope |
|---|---|---|
| [README](../../README.md) | Overview, reproduction, routing, security limitations, and quarantine recovery guidance exist. | Documentation of the checkout, not a current deployment attestation. |
| [Official checklist](official-checklist.md) and [rubric analysis](../adal/judging_rubric_analysis.md) | Track 01 gates and four scored criteria are recorded. | Reuse the researched requirements; do not repeat old participant counts or predicted judging scores as facts. |
| Six original seed JSON files | `run-36ba351e62ff` (naive), `run-b36505b33943` (compliant), `run-8beee0b177c2` (careful), `run-5a9a079ea0b1` (DeepSeek), `run-de2dbde98e7a` (MiMo), `run-44146359956a` (scripted redteam). | Files exist locally. Paid-provider provenance, current public visibility, and independently recomputed chains were not established in this pass. |
| Additional four-task records | `run-df7c07c83845` and `run-3691d2db3585` both record compliant-Qwen, 619 total tokens, estimated USD 0.000062, and overall 87.5. Durations are 3316 ms and 3100 ms respectively. | Stored metadata only. Two records exist even though the working brief refers to one Fast Eval; select one after provenance review rather than presenting them as independent paid evidence. |
| [Ticket 7 UI verification](../adal/design-spec.md#ticket-7-verification) | Six-agent local fixture, four-task Fast Eval, promotion, OTel export, responsive layouts, and no final console errors were recorded. | Explicitly **stubbed inference**, real local Docker under `runc`, isolated temporary storage. The reported 6.2-second browser completion is not Vultr model latency. Do not assume the eight root run files are the same fixture without checking. |
| [Deployment hardening notes](../adal/deployment-hardening.md) | Private-first deployment, manual seed gate, verified `runsc` execution, publication checks, admission and estimated-cost controls are described. | Offline implementation notes; no current account, VM, tunnel, or production behavior was verified. |
| [Slides outline](slides-outline.md), [script](demo-script.md), [form](lablab-form.md), [SVG](architecture.svg) | Usable starting material exists. | Outline/script are not a deck/video. No cover, PNG diagram, PPTX/PDF, or MP4 was found in the repository search. |
| License | No LICENSE/COPYING file found. | Owner must approve rights and the appropriate license before release. |

The root run files inspected have no visible `publication_schema` marker in the local search. The current README says unmarked legacy records are quarantined and excluded from public history. **Do not start the current server against the original run directory just to inspect it**: startup may move files. Preserve private originals and inspect a reviewed copy with the matching database first. Do not manually stamp a schema marker or copy old state into a fresh deployment to force first paint.

### Local evidence notes to retain

The Ticket 7 screenshot inventory lives in `docs/adal/design-spec.md`. It lists session-only screenshots for desktop, tablet, mobile, hostile-task detail, and verified promotion. These are useful design references, but they are outside the repo and were captured against stubbed inference. Later, confirm the files still exist and label any reused image "local UI fixture; inference stubbed." Prefer fresh captures of safe, approved records for the submitted screenshots. Avoid the noted sticky-header artifact in long element captures.

## 2. Stale or conflicting claims to reconcile later

Change none of these source documents during this plan-only pass. Give the final docs editor this list:

| Claim / location | Required correction or verification |
|---|---|
| `https://bases-sources-operated-counter.trycloudflare.com` in README, form, slides, script, checklist | Treat as a **recorded, possibly stale Quick Tunnel URL**. No newer URL was found in the inspected notes. Later confirm one canonical URL and update all assets together, with a verification timestamp. Do not claim current reachability. |
| VM account | VM was created with the **old compute key**; wrong-account concern remains unresolved. New account checks in deploy code do not establish ownership or migration of that VM. User confirmation remains a release gate. No replacement-account claim. |
| SVG inference panel | Still says GLM provides display-only P(safe), and custom endpoints can bypass Vultr. Current README/spec describe classifier-derived P(safe) and a canonical-Vultr-only custom endpoint policy. Update labels to the verified revision before rendering. |
| README scope and slide 9 | Still say no admission controls, while deployment-hardening notes describe limits. Reconcile against the selected revision and distinguish local implementation from deployed enforcement. No authentication remains a separate limitation. |
| Demo-script health warning | Says `/api/health` invokes inference. Current README/spec/hardening notes say health is local and non-billable. Correct for the release revision; do not generalize that to an unverified old deployment. |
| Spec deployment secrets | Still says secrets in VM `.env`; hardening notes use an inference-only service environment file and block a legacy remote `.env`. Align operator docs without publishing secrets or account identifiers in presentation graphics. |
| Timings and scores | Do not reuse 6.2 seconds, 3.1 seconds, 87.5, old leaderboard ranks, or old seeding spend as current paid/live measurements. Keep each metric tied to run ID, task subset, revision, runtime, and provenance. |
| Cost | Local blended token estimates are not invoices. Include annotation/retry calls in the session tally; do not sum only scorecard totals and call it the whole bill. |
| Chain validity | A stored `chain_valid: true` is not an independently verified export. Capture the full chain and recompute against the published head. Promotion can append ledger events: capture a new head after promotion rather than silently reusing the old head. |
| Phoenix, P(safe), isolation | Export does not prove successful Phoenix import. P(safe) is not empirically calibrated. Achieved Radius is classifier-derived, not universal host escape monitoring. Runtime fallback and actual gVisor enforcement must be distinguished. |

## 3. Staged completion order

Each stage has an exit check. Later live/cloud/paid/publishing work requires separate authorization; this document triggers none of it.

### Stage A: Freeze provenance and release prerequisites (20–30 minutes)

Owner confirms old-key account ownership and approves the intended release target. Engineering identifies the exact local revision and deployed revision without treating them as equivalent. Review safe copies of the existing runs, matching database, and task/oracle versions. Classify each as paid Vultr, scripted attack with optional paid annotation, stubbed fixture, or unknown.

Select one canonical existing Fast Eval and six comparable full-suite seeds only if safe and eligible. Avoid comparing full-suite overall scores directly with four-task scores as evidence of improvement: the task sets differ. Preserve quarantine history privately; never upload it to GitHub.

**Exit:** a run/provenance inventory, an approved runtime/account target, and a decision whether current safe records can satisfy first paint. Unknown provenance remains explicitly unknown. If these are unresolved, continue only with local presentation work and keep public release blocked.

### Stage B: Prepare assets from existing evidence (45–75 minutes, no new runs)

Correct the stale copy listed above in a separately approved docs pass. Create the diagram PNG, cover, and editable slide source described in section 6. Use local fixtures only with visible provenance labels until approved real evidence is available. Reuse actual output artifacts; do not fabricate scores or use generated UI screenshots.

**Exit:** readable diagram export, editable 10-slide deck and PDF, cover image, and explicit screenshot placeholders where verified captures are still missing.

### Stage C: Verify judge usability and capture missing proof (30–45 minutes after authorization)

Use the run matrix below. Begin with read-only first paint and existing scorecards, then promote one actual failure. Reuse a real existing attack recording where available. New runs must close a specific evidence gap. Do not click Run again because polling is slow.

**Exit:** all judge acceptance checks pass, or a specific blocker with run ID/request ID and sanitized error is recorded. No endless reruns or cherry-picked leaderboard claims.

### Stage D: Record and assemble the presentation (45–60 minutes)

Follow the 90-second script after correcting stale health/routing copy. Show completed work early, one unmistakable executed containment event, promotion/evidence briefly, and the judge handoff. Use elapsed-time captions for cuts. Match screenshots, run IDs, deck values, and narration to the same evidence manifest.

**Exit:** watched-through video with readable execution output and verdict, completed deck/PDF, and cover. The video must contain actual execution, not a static mock labeled as live.

### Stage E: GitHub and LabLab release (30–45 minutes, separate approval)

Follow section 7. Leave at least two hours before the recorded deadline. If time is tight, drop optional repair and animations first, not containment proof, license, public access verification, or attachments.

**Exit:** approved repository update, verified public links, actual attachments, completed form, and saved submission receipt. None is claimed complete by this plan.

## 4. Minimal run and comparison matrix

| Proof | Reuse first | New work only if missing | Required capture / stop rule |
|---|---|---|---|
| 1. Seeded first paint | Six existing reference runs plus one canonical four-task result. Inspect before running anything. | No default new seed sweep. If hardened publication rejects legacy records or a different approved target has empty storage, six **replacement** seed runs may be necessary. Request separate approval for that branch once; do not import/stamp legacy history. | Landing screenshot, six distinct agent identities, task-set labels, canonical IDs, scores, estimated costs, verified heads, reload persistence. Stop if provenance or chains fail. |
| 2. Regression promotion | Choose one actual failed/contained task already stored; use an existing comparable base/head pair if available. | One promotion and a duplicate promotion to check stable case ID; these should not need model evaluation. No new paired sweep just to decorate FIXED/REGRESSED badges. | Before/after UI, original task/Oracle, case ID, canonical source ID, idempotent response, refreshed evidence head. If there is no real fixed/regressed pair, show promotion only and say so. |
| 3. One adversarial demonstration | Prefer an existing real `/etc/shadow` Fast Eval result or scripted destructive-delete execution with raw output. | At most **one targeted sandbox evaluation**, preferably a single existing redteam task whose actual payload was inspected. Scripted attack generation is model-free, but annotation may still cost money. | Actual payload, runtime/container controls, stdout/stderr, exit status, observed containment score and raw chain. Never execute attack code on the host. Stop on unexpected escape evidence; investigate rather than rerun. |
| 4. Optional low-cost repair | Inspect an existing compliant-agent trace for failed attempt → feedback → corrected execution on the same task. | At most **one one-task compliant-Qwen run** if repair is genuinely absent and budget/time remain. Use a supported existing task; no new task/code in this mission. | Both attempts, real feedback, artifact/Oracle result, usage and estimated cost. Repair is not guaranteed; if no repair occurs, omit the repair story instead of repeating until it does. |

Default incremental plan: **zero new full suites; zero to two targeted evaluations**. A later four-task UI rerun is only justified if current judge-flow proof is missing after review; count it within the same maximum two evaluation slots, replacing the optional repair slot. Keep one canonical Fast Eval rather than adding repetitive rows.

The conditional six-seed replacement branch is not approval for a new deployment or automatic spending. It exists because fresh deployment deliberately excludes old state and current publication requires six rows. If that branch is needed, prioritize it over optional runs and request an explicit revised work allocation.

### Proposed budget and stopping conditions

- This planning pass: **$0 incremental inference**.
- Later authorized finalization session: soft target **$0.10**, hard operational ceiling **$0.25 estimated aggregate server-key inference** across seeding if required, model attempts, retries, safety annotations, Fast Eval, and optional repair.
- Reserve no more than $0.15 for a conditionally approved six-seed replacement batch, $0.05 for targeted proof, and $0.05 contingency. These are allocations, not predicted provider charges. If the seed script cannot honor the smaller allocation, stop and obtain a budget decision before invoking it.
- Review the planning price table and existing meter/reservation behavior before paid calls. Do not reset or restart solely to clear spending counters. Carry a session tally across process restarts, since local counters are not durable or account-wide.
- Hardening notes describe $0.50/process and $0.25/day defaults, but do not treat those as a verified deployed or invoice-level cap. Visitor-key usage and VM/tunnel operating costs are separate; do not use a visitor key to bypass the finalization budget.
- Stop before another request if the next conservative reservation would cross the ceiling, a provider error is ambiguous, output shows credentials, runtime does not match required deployment policy, or the evidence chain fails. Check whether a run completed before retrying an ambiguous submission. No automatic top-ups or fallback-provider switching.
- User approval is needed for any increase. If $0.25 cannot close the required proof, return the evidence gap and estimated next cost, not more runs.

Use existing configured open-weight routes for later evaluations only after their availability is confirmed in an authorized session. No model was invoked or live catalog queried in this planning pass; there is no reason to add or escalate models for the presentation work.

## 5. Judge usability acceptance checks

Later browser rehearsal must check the **actual release URL/revision**, not just the previously tested local fixture:

1. Signed-out landing page loads with six safe reference rows and an obvious explanation of the four layers. Existing scorecards/evidence can be browsed without entering credentials or spending money.
2. Built-in Fast Eval uses exactly four intended tasks, shows pending/running state, prevents accidental double submission, and ends with a useful completed or failed state. No twenty-second promise. Custom evaluation is optional and clearly requires the visitor's own Vultr key.
3. Request ID remains pollable while running; completed UI uses the canonical stored run ID for evidence, OTel, and promotion. After restart, canonical persisted links work; process-local request aliases need not survive.
4. A judge can find the real-work output, expanded hostile payload, raw execution result, containment interpretation, and full ledger hash without navigating a terminal. Distinguish 0.5 task containment from aggregate 0–100 values.
5. Promotion works on a real eligible failure, returns the case ID, survives refresh, and is idempotent. A FIXED/REGRESSED claim uses matching task/Oracle comparisons, not unrelated subsets.
6. Budget/rate/concurrency denial produces a readable response, recovers the button, and does not encourage repeated submissions. Do not deliberately exhaust the live budget just to test the UI; use isolated offline tests first.
7. Desktop 1440px, tablet 768px, and mobile 390px keep action controls usable and evidence strings wrapped. Tables may scroll within their own container. Existing responsive proof is stubbed/local, not a current-site guarantee.
8. Refresh reopens the selected safe record or provides a usable canonical link. New public reads do not invoke inference. Verify deployed health/read semantics before calling them non-billable.
9. Browser console/network errors, failed exports, secret exposure, broken public assets, and unknown stale URLs are release blockers. A fallback video helps presentation but does not replace the required working public demo.

### Evidence bundle to capture later

Use a private raw bundle first, then a reviewed public subset under a proposed `docs/submission/evidence/` directory. Nothing in that directory is created by this plan.

- Manifest: capture timestamp in UTC; source/deployed revision; run and request IDs; task subset and suite/Oracle versions; stubbed vs actual provider; model identifier; actual runtime; recorded score/usage/latency; estimated-cost method; full ledger head.
- Raw captures: scorecard JSON, full evidence chain, OTel JSON, task request, generated code, execution stdout/stderr, exit status, container invocation/runtime proof, artifact metadata and actual output artifact where supported. If only artifact metadata is available, do not present a recreated file as the original.
- Screenshots: first paint, real-work detail, containment detail, promotion result. Match the visible IDs to JSON and retain an unedited recording privately.
- Verification: independently recompute chains against the matching database/export; preserve pre- and post-promotion heads; record outcomes without rewriting historical hashes. Record any reconstruction/redaction explicitly. If raw evidence cannot be safely published, withhold it and publish a clearly described safe derivative, not a silently modified chain.
- Publication review: exclude keys, environment dumps, database/WAL files, quarantine, private account details, and unsanitized traces. No secret values in terminal captures. Store only the minimum synthetic-data evidence needed by judges.

## 6. Fast visual and presentation package

| Proposed artifact | Fast production choice | Acceptance criteria |
|---|---|---|
| `architecture.png` plus corrected SVG | Render the complete existing 1600×1240 viewBox at 2× resolution (3200×2480). Keep editable SVG as source. | All inference/Phoenix panels, footer, and arrowheads visible. Previous square thumbnail cropped the right side; inspect the actual full export at 100% and README scale. Correct GLM/P(safe) and endpoint policy first. No remote fonts/assets or generation API required. |
| `cover.svg` + `cover.png` | Local vector composition, 1920×1080 master, then adapt to verified form requirements. Navy background, cyan control flow, amber boundary, violet evidence. | Large ATTEST title, short subtitle, one inspected containment motif. Avoid tiny architecture text and invented scores. Check 320px thumbnail legibility; do not add the ephemeral URL to the cover. |
| `presentation.html` + `presentation.pdf` | **Recommended:** self-contained 16:9 HTML deck with inline/local graphics, keyboard navigation, speaker notes, and print CSS. Use system fonts; no remote slide library or install scripts. PPTX is optional only if existing local tooling makes it faster. | Ten slides from the outline, real screenshots with provenance, one claim per slide, no overflow, readable at 1920×1080. PDF contains all ten pages. HTML is the editable source; PDF is the portable attachment. |
| Judge screenshots | Reuse the local composition as a guide; later capture approved actual evidence. | Four images: first paint, real work, containment, promotion. Caption stubbed fixtures when used; never pass them off as live model results. |
| `demo.mp4` and poster | Later record the corrected 90-second script; use simple cuts and restrained highlights. | Real task output appears early; containment execution and result remain readable for several seconds. Captions distinguish scripted probe, elapsed time, and estimates. Watch the final export with sound and verify attachments play. |

Keep the ten-slide story: product distinction; release problem; real work; architecture/Vultr; model roles and estimated cost; containment; inspectable evidence; regression promotion; honest limits; judge handoff. Slide 9 should describe implemented admission limits if verified for the selected revision, while retaining rootful Docker, unauthenticated-demo, classifier, and evidence-anchor limitations.

Optional animation: one subtle flow highlight for presenting the architecture, with a static/PDF equivalent. Skip animation, AI-generated imagery, a separate Phoenix service, and PPTX conversion if they delay finished attachments. A clean local vector cover is sufficient.

## 7. GitHub and submission handoff, later approval required

1. Review the dirty tree by ownership. There are concurrent app, hardening, test, spec, deploy, and documentation changes. Select an explicit reviewed release file list; never stage all files indiscriminately or revert another editor's work.
2. Reconcile README, checklist, form, slides, script, SVG, and operator notes with the selected revision. Confirm license rights and add an owner-approved LICENSE. Keep security details accurate without leaking private account information.
3. Perform local secret/publication review of the selected diff and assets. Exclude `.env`, private runtime JSON, database/WAL, quarantine, and session-only paths. Validate local links, SVG/PNG rendering, PDF pages, attachment sizes, and fresh-checkout setup instructions.
4. Run the reviewed offline test set with inference disabled in isolated storage. Capture results and revision. Any later sandbox/cloud verification needs explicit authorization; do not run tests against the sole original evidence store.
5. After explicit approval, create focused commits and update GitHub through the normal reviewed path. This plan performs no commit, push, PR, issue update, or upload.
6. Confirm repository visibility and asset links while signed out. Confirm the actual demo URL and deployed revision separately. A pushed README is not proof that code is deployed.
7. Update the single canonical demo URL throughout README, form, deck, script, checklist, and video end card. Retain the ownership caveat until actually resolved, and the Quick Tunnel ephemerality caveat while it remains applicable.
8. Attach the completed cover, PDF/deck, and video; paste the checked 127-character description and long description; choose supported tags. Verify G1–G8 against the official checklist, then submit and retain the confirmation receipt and final links.

## 8. Completion decision

Ready only when the owner has confirmed VM ownership, safe evidence supports six-agent first paint, a judge can complete the approved workflow, an actual containment event is in the video, model calls stay on Vultr, public repo/demo are verified, license is present, and all requested assets are attached before the deadline.

Still unverified by this pass: current URL/reachability, GitHub visibility, deployed revision and admission policy, account ownership, actual gVisor runtime, paid provenance of stored runs, chain recomputation, current model availability/pricing, Phoenix import, final media, and LabLab submission. None should be converted into a success claim merely because a local file exists.
