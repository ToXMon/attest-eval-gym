# Recovery builder plan

Date: 2026-11-08
POC: repository owner / single OpenAI builder
TL;DR: Resume the requested UI/UX redesign, not the already-completed ticket 7 wiring or the proposal-only local-agent adapter. After approval to leave this recovery-only phase, change only `attest/web/index.html` and `docs/adal/design-spec.md`, then verify locally with isolated fixtures. Deployment, paid evaluations, commits, publishing, and adapter implementation remain outside this scope.

## Recovered intent and evidence

The checkout began clean on `master` at `554764b`. The contract's old “tickets 7–8 remain” entry predates `3aa6a0e` (hardening, integration plans, submission assets) and `554764b` (model-versus-agent copy). Its historical provisioning block is not a current deployment diagnosis.

Relevant persisted requests, in order (timestamps as recorded; no timezone conversion assumed):

| Request | Evidence |
|---|---|
| Assess existing-agent onboarding, then write a one-day implementation plan; both explicitly say “Do not code yet.” | Session `cef3a4d7-8922-459f-9983-100160236548`, transcript records 169 and 179, Nov 7 23:01 / 23:04 |
| “Make only the small UI/design wording correction…” | Same transcript, record 195, Nov 8 08:55; reflected in `554764b` |
| “we need to upgrade the UI/UX … using openrouter and huggingface as reference examples” and the reference-site workflow for “a unique design system for attest” | Session `580e4179-c83c-4b34-aa51-0bb97e764e3d`, transcript record 284, Nov 8 09:05 |
| “we only have access to openai models … kill the other workers … continue and finish what i asked”; then “please contnue this work. clean up the workers there are so many.” | Same transcript, records 328 / 332, Nov 8 10:18 / 10:32 |

Transcripts are local files under `/Users/tolushekoni/.adal/sessions/conversation_<session-id>.jsonl`; record numbers above are JSONL line numbers. The later redesign request follows the narrow copy fix, so the copy-only turn does not cancel the redesign. It also does not authorize implementing the adapter.

Recent worker metadata (`a4c78a58-568a-43b7-8bc0-e2210eeb7549`, `f598b3c5-37ef-44b8-9511-5233acc7792f`, `38b7db3d-9fbb-4c94-bd76-b730468a2b7c`) records interrupted/restarted design assignments, restricted to those two UI/design files. These are delegated assignments, not additional user approvals or completion evidence. Their consistent direction was a compact original “ATTEST instrument console,” credible evidence beside the main action, and the leaderboard beginning in the desktop first viewport. Reference research was already done; do not repeat broad browsing.

The recovery brief and current contract report all 12 prior workers stopped. This pass did not restart or independently control them. Use one OpenAI builder as explicitly requested; no alternate-provider trials or new worker fan-out are needed. Architecture graph tooling is unavailable; do not install it.

## Already done versus unfinished

- Ticket 7: four-task Fast Eval, pending request-ID polling and canonical stored-ID handoff, leaderboard refresh, scorecards, promotion, evidence/OTel, responsive layouts. `docs/adal/design-spec.md` records successful local tests/browser rehearsal with **stubbed inference and real Docker/runc**, not live Vultr timing.
- Model-mode copy is corrected in `attest/web/index.html:241–255`: built-in agent, approved Vultr model mode, key-custody disclosure, explicit full-agent exclusion, and a planned/unavailable local-adapter callout.
- Backend hardening exists: approved-provider policy, credential redaction/rejection, safe-publication/quarantine, admission and process-local spend limits. Implementation does not establish deployed enforcement.
- Submission files include README, script/form/checklist, SVG/PNG diagram and cover, HTML/PDF slides. The finalization plan's earlier “no PNG/PDF found” inventory is superseded by `3aa6a0e`; do not recreate those assets by default. Final media, evidence provenance, license and submission receipt remain unverified.
- The newer reference-led redesign has no landed implementation evidence. Current `design-spec.md` still describes the older Hallmark/mint direction, and `index.html:10–23` retains those tokens. The tree was clean, with the last UI commit being the wording fix.
- No `attest/byo.py`, `scripts/byo_agent.py`, wrapper, BYO test, routes or solver hook exists in the discovered source inventory. `byo-agent-implementation-plan.md` supersedes the earlier pairing protocol with manifest → local generation → batch submit; it remains a proposal.

## Recommended surgical scope

1. Before editing, inspect the current UI and the known baseline screenshot from session `580e…` (`screenshots/shot-1794146788-2649ee.jpg`), if still present. Use a separate local fixture, never the existing service or original evidence store.
2. Update `docs/adal/design-spec.md` with measurable palette/type/spacing/component/accessibility decisions and reference takeaways. Borrow OpenRouter's comparison density and pricing/policy clarity, and Hugging Face's task/discovery structure; do not copy branding or imply community features ATTEST lacks.
3. Implement in `attest/web/index.html` only: compact action-led hero, restrained graphite/neutral instrument surfaces, one strong accent, and a truthful evidence panel. Bring real leaderboard content into the desktop first viewport. Use local CSS/SVG and system fonts, with no framework, build step, runtime font or asset dependency.
4. Preserve existing DOM hooks and vanilla-JS behavior: `refreshBoard`, `selectRun`, `loadScorecard`, `loadEvidence`, `renderScorecard`, `doCompare`, `promote`, and the Fast Eval/selftest controls. Dynamic text stays escaped. No backend, frozen contract, task, provider-policy, or sandbox edits.
5. Preserve the exact Four Eval Layer vocabulary, Capability/Regression Evals, Two-Layer Defense, cost-estimate and classifier limitations. Clearly separate built-in versus Vultr model evaluation; visitor keys go to this server. Existing-agent support stays planned/unavailable. Preview data must come from the API or carry an unmistakable illustrative/fixture label.
6. Critique and iterate against screenshots, then return the two changed paths, actual checks, screenshot paths and remaining limitations. Do not expand into deck/video work or fix unrelated backend concerns opportunistically.

## Interfaces and deferred risks

The frozen contract is `docs/adal/spec.md`; architecture and gate context are `plan.md` and `judging_rubric_analysis.md`. Preserve the implemented Fast Eval payload from `design-spec.md`: compliant agent, task IDs `t01,t02,t05,t08`, `public:true`. Poll the POST request ID; use the completed canonical run ID for evidence, OTel and promotion.

If separately authorized later, adapter work needs an ADR and more than a UI patch:
- `agent.py:368–479` owns rejection, source analysis, sandbox execution and repairs; extract shared artifact execution without global solver monkeypatching.
- `gym.py:249–372` hardcodes `solve`, token estimates, cost aggregation and optional paid annotations. External-mode metrics cannot truthfully reuse those defaults.
- `gym.py:580–650` aggregates numeric metrics and groups rows by caller-visible name; external provenance, nullable metrics and separate comparable groups need explicit handling.
- `server.py:222–230` swallows persistence failures; `start_run:303–345` inserts into memory before persistence. An adapter must not claim durable completion through that path unchanged.
- `admission.py:107–162` protects only three exact existing routes. New BYO routes would otherwise miss body/rate controls.

These are future integration prerequisites, not blockers to the two-file redesign. Keep sandbox isolation and the canonical Vultr allowlist unchanged.

## Done criteria and validation

The complete discovered script-based regression suite is:

```text
python3 scripts/selftest.py
python3 scripts/piptest.py
.venv/bin/python scripts/apitest.py
.venv/bin/python scripts/hardeningtest.py
git diff --check
```

Run only in the later implementation phase, with Vultr compute/inference credentials absent, safety annotation disabled, isolated storage and no real inference transports. Do not import the server against root `runs/`: startup can quarantine legacy evidence. `apitest` and `hardeningtest` arrange temporary run storage; `piptest` uses fixed `/tmp/attest-piptest.db`, so run it serially and account for that shared test file. Docker is real for selftest/piptest/apitest; mocked inference is not mocked sandboxing. Expected baseline: 10/10 attacks contained, 15/15 oracle cases correct, and every script exits zero. Local runc success does not verify production gVisor.

Browser checks on the actual local build:
- Screenshots at 1440×900, 768×1024 and 390×844; no document horizontal overflow or clipped controls; tables scroll within their containers.
- Value proposition, runtime status, primary action and model/full-agent distinction are immediately legible; leaderboard begins in the desktop first viewport.
- Keyboard focus, disclosures, labels, reduced motion and readable contrast work. No console errors or failed local assets.
- Exercise leaderboard/detail, compare/promotion and evidence/OTel with isolated fixtures. One local Fast Eval must use stubbed inference, dispatch exactly four tasks, show pending/completed/failed states, prevent duplicate launch and refresh the canonical scorecard/board. If a safe fixture cannot be prepared within scope, explicitly report this flow untested.
- Compare final diff to the two-file allowlist; no secrets, fabricated scores, hidden feature removal or unsupported live claims.

This recovery pass ran only `git diff --check`, clean-tree/history inspections, and Python/Docker CLI version checks (Python 3.12.8, Docker CLI 29.1.3). It did not run the suite, check daemon readiness, start a server, capture a browser, or verify live deployment.

## Separate release blockers and clarification

Read-only local records show historical VM `64.176.197.242` and an older `bases-sources-operated-counter.trycloudflare.com` URL. Recent design-worker metadata records a different candidate, `preserve-myrtle-summary-crossing.trycloudflare.com`. Neither was checked here; do not choose a canonical public URL from stale notes. Deployed revision, approved account ownership, actual runsc enforcement, six safe persisted baseline rows and chain/provenance remain unverified. No SSH, cloud API, paid inference or live-site action was taken.

Track 01 release still needs confirmed public repo/demo, real containment video, required documentation, approved license, verified Vultr routing/runtime and submission receipt by the recorded Nov 8 23:00 UTC deadline. External-artifact mode cannot attest a judge's local inference routing.

No product clarification is necessary for the next local UI task: the latest specific request is recoverable. This mission deliberately stops at planning. Approval to begin that implementation phase is the next boundary; live deployment/spending/publishing and adapter implementation require separate explicit scope. Owner confirmation of the target account and release URL is needed only before release work.

## Response to evaluator plan

Accepted for the later implementation/review phase. These clarifications supersede any looser browser-fixture wording above; they do not authorize coding now.

- Keep the implementation allowlist at `attest/web/index.html` and `docs/adal/design-spec.md`, with no backend changes. Treat this as a hierarchy/layout redesign of existing sections, not a blank-slate rewrite. Inventory retained labels, selectors and behavior in the design spec. Compare the implementation delta against the recorded pre-implementation baseline: the separately requested recovery planning documents are not application changes and must not be deleted merely to satisfy a whole-tree diff check.
- Accept screenshots at 1440×900, 768×1024 and 390×844, including initial desktop and populated scorecard/evidence states. At desktop, the primary action, runtime/inference status, mode distinction and start of the API-backed leaderboard must be visible without scrolling. At every size require `document.documentElement.scrollWidth <= window.innerWidth`, readable reflow and locally scrollable tables. Clipping or hiding inaccessible controls does not count as a pass.
- Accept measured contrast of at least 4.5:1 for normal text, 3:1 for large text and 3:1 for focus indicators against adjacent colors. Inspect representative computed body/muted, link, status, border/focus and disabled colors. Disabled controls are exempt from WCAG's minimum contrast requirement, but their legibility remains a design review check. Require logical keyboard operation, accessible names/state, associated form labels and reduced motion. Require zero uncaught console errors, failed local assets or unexpected network requests.
- Accept truthful fixture/data requirements. Remove the unsupported useful-JavaScript-off-content claim from the design spec during implementation; document actual loading/offline behavior. Six rows and runtime/live status are conditional on API data. Synthetic rows and screenshots must visibly say fixture/illustrative, never imply paid runs, production enforcement or real evidence. Preserve escaped dynamic text, text-rendered evidence, exact layer vocabulary, estimated-cost and classifier limitations, and planned/unavailable adapter status.
- Replace the earlier browser Fast Eval proposal with a locally served static page and deterministic intercepted API responses. Intercept reads, OTel and every action route before interaction; block unmatched requests. Never attach to a live/default application service or execute browser-triggered runs, attacks or promotions. Specific correction: the current selftest action is **GET `/api/selftest`**, despite having side effects; intercept it by its actual method, not just POST. Mock POST run/promotion and record requests. If interception cannot be guaranteed, mark the interaction unverified.
- Accept the full behavioral matrix: healthy/offline and empty/populated states; click/keyboard row selection; canonical-ID evidence/OTel links; fixed/regressed/unchanged comparisons; mocked promotion; hostile strings as text; missing versus zero values; built-in and model-mode payloads; exact built-in task IDs and `public:true`; running/completed/failed polling; disabled/recovered controls; one POST per deliberate launch with duplicate launch blocked. Preserve the coupled hero endpoint and disclosure model/key controls, blank-endpoint built-in behavior, approved-host policy and visitor-key custody disclosure. Synthetic browser checks verify UI behavior, not server enforcement.
- Keep all four regression scripts separate from browser fixtures, with credentials absent, annotation disabled and test-owned storage only. Run serially where fixed `/tmp` databases are shared; inspect test-owned paths without touching original evidence. These scripts can execute real Docker even with stubbed inference. Record actual exits and distinguish local runtime checks from gVisor, paid inference or deployment claims.

The later evaluator report should retain screenshots, computed contrast/keyboard results, fixture request logs, network/console findings, commands/exits and skipped checks in its requested report location. No numeric or behavioral criterion conflicts with the two-file scope. No browser, integration test, deployment or application-code change was performed for this planning response.
