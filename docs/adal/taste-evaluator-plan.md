# Taste pass evaluator plan

Date: 2026-11-08
POC: claude-ui-reviewer (independent evaluator, Claude Opus 5.5 at the user's explicit request)
TL;DR: This plan is for judging the Claude taste pass on `attest/web/index.html` from a hackathon judge's seat. It compares a frozen "before" with the builder's "after" on five scored critique dimensions, a measured inventory of type, boxes and copy, first-viewport positions, a 3 size × 2 theme responsive matrix, and a full mocked replay of every existing evaluation flow. Every API call is intercepted, including `GET /api/selftest`. The lead runs the four regression scripts serially; the evaluator only reads their results. It covers planning only: no source edits, no evaluation run yet. The builder plan (`docs/adal/taste-builder-plan.md`) has not been written yet, so any threshold below that conflicts with it gets settled with the lead before build.

## Ground truth and scope

Sources: `~/.adal/engineer/contracts/2026-11-contract.md` (recovery checklist items 1–35 and the 2026-11-08 taste entry), `docs/adal/recovery-evaluator-plan.md`, `docs/adal/judging_rubric_analysis.md`, `docs/adal/design-spec.md`, `docs/adal/spec.md` and the current page.

The implementation allowlist stays `attest/web/index.html` and `docs/adal/design-spec.md`. The builder may restructure the page completely within that file. The API shapes, `attest/tasks.py`, the model and host policy, score meanings and the backend stay frozen. The modified files under `docs/submission/` and the untracked cover images belong to other work and must come out of the pass byte-identical.

### Frozen baseline

The working tree is dirty: the recovery UI is uncommitted on top of `554764b`. So the "before" for this pass is the current file, not HEAD. I froze it outside the repo so builder edits cannot destroy it:

- `~/.adal/engineer/tasks/attest-ui-taste/baseline/index.html`, sha256 `e340dec057ef9574880cd5570192d802244f737a9899a6b74bad52358479fff4`
- `baseline/design-spec.md`, `baseline/HEAD` (`554764b`), `baseline/SHA256SUMS` (also covers the five `docs/submission` files and both cover PNGs)
- `baseline/hooks.json`: 48 element IDs referenced in markup or `$("#…")`, and 17 named functions

The baseline gets measured with the same harness and fixtures as the after build, served from its own temporary directory. Before and after must never share a server, origin or storage.

### How the skills apply

I read taste-skill 2.5.1, open-design `critique` and `kill-ai-slop` (SKILL.md plus `references/taxonomy.md`). What I take from them: critique's five dimensions, scoring discipline and Keep/Fix/Quick-wins lists; kill-ai-slop's 35-tell taxonomy as the inventory checklist; and taste-skill's equal edges, a single system, copy rules (buttons as verb and object, headings that name things, one fact with one wording), 44px tap targets and its ban on violet and invented figures.

What I explicitly do not apply: one section per screen, hero-fills-the-screen, mandatory hero entrance and dealt moments, photographs, shader effects, hover lifts, random palette and layout dealing, `.taste-skill` gate files, and the critique skill's HTML report with a radar chart. ATTEST is a workbench that judges scan, and those rules are written for marketing sites. I won't install, copy or run any skill script (`gate.mjs`, `scan.mjs`, `check.mjs` and the rest). The checks below are my own browser measurements and greps.

## What a judge must get from the first screen

The rubric scores presentation as "clarity of a working system": one screen, one number, something a judge can interact with, and the wedge stated plainly ("we score your agent, including whether it stays contained"). It also asks for model and cost visibility and for failing tasks to be easy to find. I turn that into a five-second test, done on a 1440×900 screenshot before reading any code. I write down what the page says it proves, what I can click, which number matters, and where the evidence is. After passes only if all four are answerable from the screenshot, and each answer matches what the API fixtures and docs support.

## 1. Five critique dimensions, scored before and after

I score each dimension 0–10, using critique's bands (0–4 broken, 5–6 functional, 7–8 strong, 9–10 exceptional). Every score comes with 30–80 words of evidence naming selectors, line numbers or screenshot regions. The score is the worst sustained band and never an average. I score the baseline first and write it down, then score the after build before I read the builder's self-assessment.

| Dimension | What I look at in ATTEST |
|---|---|
| Philosophy consistency | One register for the workbench. Accent, mono and status colour each follow one rule everywhere. No leftover marketing voice beside instrument UI |
| Visual hierarchy | First, second and third reads at 1440, 768 and 390. Whether the single most important number and the primary action win. Whether tables are scannable |
| Detail execution | Column alignment, tabular numerals, wrapping of long hashes and IDs, edge alignment, radius and border consistency, empty, loading and error states |
| Functionality | All mocked flows from section 5, keyboard and focus, theme persistence, nothing clipped |
| Innovation | Whether one move belongs to ATTEST specifically (for example the containment ladder or evidence chain as the visual anchor) and is earned, not grafted on. A 5 is acceptable here |

Baseline notes I will have to back up with screenshots when I score: two ordinal kickers (`01 / Evaluation console`, `02 /`) and numbered method steps; two slogan couplets ("Useful code. Inspectable boundaries.", "Code proposes. Oracles decide.") plus the "don't demo vibes" tagline; four layer cards each topped in a different hue, violet included; 3px coloured left borders on defence and task cards; metric cells boxed inside boxed task cards; 16 distinct font sizes, from 9px to 2rem; 29 monospace declarations, including labels written as prose; and count-up animation on scores. The first leaderboard row starts at 876px in a 900px viewport, so the board is barely in view.

## 2. Inventory of type, boxes and copy

I take the same measurements on baseline and after, at 1440×900 in both themes, with the populated fixture and one task card expanded. Static counts come from the file. Rendered counts come from `getComputedStyle` on visible elements.

### Typography
- Distinct computed `font-size` values on visible text, with the steps between them
- Smallest rendered size, and the elements that use it
- Font families actually used and their sources (system or file); any external font request
- Number of elements set in monospace whose text is prose (four or more words, not an ID, hash, number, path or code)
- Uppercase or letter-spaced labels
- Whether numeric columns use `tabular-nums`

### Boxes
- "Boxes": visible elements with a border on three or more sides, or a background different from their parent's, plus padding
- Deepest box-in-box nesting on the page
- Coloured side and top accent borders
- Translucent tint backgrounds (`oklch(... / a)` or rgba with alpha below 1) outside selection and focus
- Distinct non-zero radius values, and nested corners that don't nest (taxonomy #21)
- Shadows, by count and blur size
- Hard-coded colours that bypass theme tokens, `!important` rules and inline `style=` attributes (baseline: 31 hex values in CSS, 9 `!important`, 18 inline styles)

### Copy
- Word count of the first 1440×900 viewport
- Every kicker, ordinal, slogan, two-fragment headline, em dash in UI prose, "NOT"-style capitals and decorative glyph (`→ ▸ ▾ ◐ ✓ ✕ ● ▼ ▲`), each with its location and a slop or keep decision
- Every button label checked as a verb plus object
- A claim table: every factual sentence on the page, mapped to its source (code, spec, README or API field) or marked unsupported. One unsupported claim fails the pass
- Facts stated twice in different wording (in the baseline, the footer repeats the host-secrets sentence)
- Required vocabulary present verbatim: Router / Tool Selection Layer; Trajectory & Convergence Layer; Outcome Layer; Containment Layer; Attempted Radius; Achieved Radius; Two-Layer Defense; Capability Evals; Regression Evals; all four ladder levels with their scores
- Required limitations present and visible near the data they qualify: estimated USD is not a charge; P(safe) and Achieved Radius are classifier-derived and not proof of isolation; the visitor key goes to this server; both modes run ATTEST's code-generation agent and not the visitor's own agent; the local adapter is planned and unavailable; JavaScript is needed to load data

## 3. Positions of the key action and the leaderboard

I measure `getBoundingClientRect()` with the populated fixture (6 rows, matching the seeded count) and again with a single row, in both themes, with reduced motion on so count-ups don't skew anything:

- Primary run button (`#b-fasteval` or its documented replacement): top and bottom, and whether its label changes with the endpoint field
- Runtime and inference status, the built-in versus Vultr-model distinction, and the attack-corpus control
- Leaderboard header row top, how many data rows are fully visible, and whether the score and containment columns fit without horizontal scroll at 1440
- Height of the sticky header, and whether it covers anything scrolled or focused

At 768×1024 and 390×844 I record the same values in screens scrolled (y divided by viewport height).

## 4. Responsive matrix: 1440×900, 768×1024, 390×844 in light and dark

That gives six configurations. Each one is captured in four states: initial healthy, populated scorecard with a task expanded, evidence tab (or section), and offline. Screenshots go to `~/.adal/engineer/tasks/attest-ui-taste/shots/{before,after}/{w}x{h}-{theme}-{state}.png`. A fixture banner injected by the harness, not by the page, marks every shot as synthetic data.

For each configuration and state:
- Overflow: `document.documentElement.scrollWidth <= innerWidth`, and no visible element's right edge past the viewport unless it sits inside a scroll container
- Clipping: no control or label cut off by `overflow:hidden`, text-overflow or a fixed height; long hashes, run IDs and the 66-character fixture hash stay readable
- Tap size: interactive controls outside running text at least 44×44 CSS px at 390, as the earlier plan required
- Contrast: I check every visible text node, not a sample. For each I composite ancestor backgrounds, including alpha, and compute the WCAG ratio. The thresholds are 4.5:1 for normal text and 3:1 for large text, borders that identify controls, status dots and focus rings. Disabled controls are exempt but still recorded. Results are kept separately for each theme. Where layering defeats the computation, I take a pixel sample from the screenshot
- Focus: I Tab through the whole page and record the order, accessible names and states. Each step needs a visible ring with at least 3:1 contrast against the colours next to it, not hidden under the sticky header, and every control must be reachable and operable (theme switch, tabs or nav, rows, disclosures, task headers, selects, promote)
- Semantics: if tabs remain, they need `role="tab"` with `aria-selected` or an equivalent current-state pattern (the baseline has neither). Labels must stay programmatically tied to `ep`, `c-name`, `c-model` and `c-key`
- Reduced motion: no count-up, row entrance or ladder animation, and no content left hidden

Theme behaviour, each in a fresh browser context:
1. No stored value, OS light, then OS dark: the page follows the OS. A live OS change applies only while there is no override
2. Choosing the opposite of the OS persists across a reload and across an OS change
3. With `localStorage` throwing on both get and set, the page renders and the switch still works in memory
4. An `addInitScript` hook records `data-theme` and the body's background on the first animation frame under conflicting stored and OS values: the first painted frame must already be the resolved theme
5. If the builder adds a third "System" choice, choosing it removes the stored value and follows the OS again. If the switch stays two-state, I record that there is no way back to following the system short of clearing storage. That is a limitation, not a failure, unless the lead decides otherwise
6. Toggling the theme during a mocked poll, with fields filled, a task expanded and compare selects chosen, changes no state and sends no request

## 5. Full mocked regression of the evaluation flows

### Harness
- Serve a copy of the HTML under test from a temporary directory with `python3 -m http.server --bind 127.0.0.1 <random port>`. Never start `attest.server` or import it with default storage
- Attach to the shared browser in my own window and open a new context per test (viewport, `colorScheme`, `reducedMotion`, fresh storage). If the CDP connection can't create contexts, use a unique port for each run and clear only that origin
- `context.route('**/*')`: serve the static HTML, answer every `/api/**` path from fixtures, and abort and log anything else, external fonts and CDNs included. Every request is written to a log with its method, URL and body
- I write my own fixtures. The builder's `ui-fixture.js` and the taste worker's `route.js` are read only to confirm route coverage, never reused, so the two sides don't share blind spots
- If a flow can't be exercised safely this way, it is marked untested, never improvised against a real service

### Routes and data
All fixture values are visibly synthetic (names start with `FIXTURE`, keys read `FIXTURE-KEY-NOT-REAL`).

| Route | Variants |
|---|---|
| GET `/api/health` | `runsc` and `runc`, key configured or not, `attacks:10`; 503 offline |
| GET `/api/leaderboard` | empty; 1 row; 6 rows including a hostile `agent_name` (`<img src=x onerror=window.__x=1>`), an 80-character name, mean 0, null metrics, missing `p_safe` (which triggers a per-row run fetch), chain valid, broken and null; 503 |
| GET `/api/run/{id}` | complete run with t01 pass, t02 partial, t05 adversarial fail, t08 contained with capability classes, a 66-character ledger hash, one missing `otel` and one `javascript:` otel path (both must fall back to `/api/run/{id}/otel.json`); `pending → running → completed` and `→ failed` sequences; a canonical ID that differs from the launch ID |
| GET `/api/evidence/{id}` | JSON containing hostile strings; 500 |
| GET `/api/compare` | fixed, regressed, unchanged-and-base-passed, new, and `base_passed:null` rows; 500 |
| POST `/api/run` | records the body and returns a fixture `run_id` |
| POST `/api/regression/promote` | `created:true`, then `created:false`, then 500 (the button must re-enable) |
| GET `/api/selftest` | fulfilled with 10 results, one escaped. It is never forwarded: this GET runs real attacks on a live server |
| GET `/api/run/{id}/otel.json` | fixture JSON, opened in a new page; only the target URL is asserted |

### Assertions
These come from contract items 22–29, re-run against the after build:
- Healthy, loading, empty and offline states read correctly, with no runtime or count claimed when the API is offline
- Clicking and pressing Enter or Space on a row opens the matching scorecard. Because `selectRun` and the attack-corpus handler pick the scorecard tab with `$$(".t")[1]`, reordering or removing tabs breaks them silently, so this is checked on every layout variant
- Evidence and OTel links use the canonical completed ID
- Compare renders fixed, regressed and unchanged rows under Capability Evals and Regression Evals; promotion shows the mocked case ID and recovers from errors
- `window.__x` stays undefined, hostile text renders as text, missing values show as unavailable, and zero shows as 0
- A blank endpoint POSTs exactly `{agent:{name:"compliant"},tasks:["t01","t02","t05","t08"],public:true}`
- An approved non-blank endpoint POSTs the name, model, key and `style:"compliant"` payload, and the button label changes to model mode. The fixture key appears only in that one POST body: not in any URL, other request, console line, storage or DOM text after submit
- Launch disables the button. A double click and repeated Enter produce exactly one POST. Running, completed and failed polling each end with the button re-enabled. The 180-second timeout path is tested with `page.clock` if the attached browser supports it, otherwise marked untested
- Attack corpus: exactly one GET `/api/selftest`, rendered from the fixture, with HELD and ESCAPED states visible
- Hooks: all 48 IDs and 17 functions in `baseline/hooks.json` still exist, or the builder documents a mapping with equivalent behaviour that I can verify. `node --check` passes on both extracted inline scripts
- Console: zero uncaught errors and warnings on healthy runs; in the offline fixture only the expected 503 resource errors appear; no request is left unmatched or aborted beyond the ones I expect

## 6. Regression scripts and static checks

The lead runs these one at a time, never in parallel, with Vultr credentials absent and `ATTEST_ANNOTATE=0`:

```text
python3 scripts/selftest.py
python3 scripts/piptest.py
.venv/bin/python scripts/apitest.py
.venv/bin/python scripts/hardeningtest.py
git diff --check
```

I don't run the four scripts myself. They execute real Docker or runc sandbox paths and use fixed `/tmp` databases, so two runs at once would collide. I review the lead's log for each exit code, 10/10 attacks and 15/15 oracles, and an all-green pipeline, API and hardening run. They are local code regressions. They don't verify gVisor, deployment or paid inference. I do run these read-only checks myself: `git diff --name-only` (only the two allowlisted files plus planning docs), `shasum -c baseline/SHA256SUMS` limited to the `docs/submission` lines, a secret grep of the diff and the logs, and `git status` to confirm there are no commits.

## Proposed acceptance

These are proposals; the lead can trade any threshold against the builder plan. "Fails" means the pass is not accepted until fixed or explicitly waived by the lead with a reason.

**Critique**
- A1. After scores at least 7 on Philosophy, Hierarchy, Detail and Functionality, and no dimension below its baseline score. Innovation at least 5
- A2. The five-second test is answered entirely from the 1440×900 after screenshot in both themes

**Inventory**
- A3. At most 6 distinct rendered font sizes outside code blocks, adjacent steps at least 1.2× apart, nothing smaller than 12px
- A4. At most two families, one sans and one mono, both system stacks or something the lead approved. Zero external font or asset requests. Zero prose set in monospace
- A5. Box nesting at most 2 deep. Zero coloured side or top accent borders. Zero decorative translucent tints. At most two non-zero radius values. At most one shadow (the toast)
- A6. Zero ordinal kickers, slogan couplets, em dashes in UI prose or decorative glyphs. Status words carry state without needing their colour. Every button is a verb plus an object
- A7. The claim table has zero unsupported claims. All required vocabulary and limitation statements are present (contract 18–20)
- A8. Zero hard-coded colours outside the two theme token blocks, except where the builder documents a token-derived reason. Fewer `!important` rules and inline styles than baseline (9 and 18)

**Positions at 1440×900, both themes, 6-row fixture**
- A9. The primary action and the built-in versus Vultr-model distinction are fully visible, with the action's top at 520px or less
- A10. Runtime and inference status are visible without scrolling
- A11. The leaderboard header top is at 600px or less and at least 3 data rows are fully visible (baseline: the first row starts at 876px). Score and containment columns are visible without horizontal scroll
- A12. At 390×844 the primary action is inside the first screen and the leaderboard begins within two screens

**Responsive and accessibility, all six configurations**
- A13. Zero document overflow, zero clipped controls, zero failures on the 44px tap targets at 390
- A14. Zero text-contrast failures across the exhaustive scan in each theme. Focus rings and control boundaries at 3:1 or better
- A15. Full keyboard pass: logical order, every control reached and operated, focus never under the sticky header, correct names and states
- A16. All theme checks 1–6 pass, with no wrong-theme first frame

**Flows and regression**
- A17. Every assertion in section 5 passes, or is marked untested with a reason (only the timeout path may be untested)
- A18. The lead's serial regression log is all green, the diff is allowlist-only, the `docs/submission` hashes are unchanged, no secrets appear, and there are no commits, deployment or paid calls

## Risks

1. **Silent hook breakage from restructuring.** Tab activation is index-based (`$$(".t")[1]` in `selectRun` and the attack-corpus handler), sections are toggled by `#s-*` IDs, and `.subtab.on` drives compare rendering. Merging tabs into one scrolling workbench can leave the scorecard empty with no error. Mitigation: replay the flows on every variant, and require the builder to replace index lookups with explicit selectors.
2. **Typography versus the allowlist.** A real type identity may tempt the builder toward a hosted web font. That adds an external request, and a font file would be a third file outside the allowlist. The lead should rule on this before build. My default is that it fails A4.
3. **Copy rewrite drops or invents claims.** Tightening copy is where the limitation sentences disappear and runtime claims ("gVisor isolated", "five models") slip in, while the live runtime may be runc. Mitigation: A7's claim table, and runtime shown only from `/api/health`.
4. **A fixture that looks like evidence.** Screenshots full of plausible rows could end up in the submission as if they were real. Mitigation: `FIXTURE` names, the injected banner, a check that the page itself ships no sample rows, and shots kept outside the repo.
5. **Live side effects.** `GET /api/selftest` runs the attack corpus even though it's a GET. The route table and the abort-everything-else default cover it. I never point the harness at the production URL or a running local server.
6. **Theme flash and storage.** Moving or rewriting the head script can bring back a wrong-theme first paint. In the shared browser, storage leaks between tests on the same origin. Mitigation: a fresh context or unique port per test, and the first-frame probe.
7. **Measurement noise.** Count-ups, row entrances and font loading shift boxes. Mitigation: measure under reduced motion and after `document.fonts.ready`, then take one normal-motion pass to look only for jank.
8. **Subjective scores.** The critique dimensions are judgement. Mitigation: baseline scored before the after build exists, evidence citations, worst-band scoring, and a mean above 8 treated as a sign that I'm inflating.
9. **Dirty tree.** The recovery UI isn't committed. A builder `git checkout` or `git stash` would lose it along with the `docs/submission` edits. The frozen baseline lets that be detected and recovered, but the builder should be told not to touch git state.
10. **Skill rules that conflict.** taste-skill's screen-height sections, effects, photographs and gate workflow would turn the workbench into a landing page. They are excluded on purpose, and the builder plan should say the same.
11. **Results that look too clean.** For every pass/fail table I open at least two underlying screenshots or DOM reads, following the browser rule: a check that didn't throw hasn't necessarily landed.

## Later report

The report goes to `~/.adal/engineer/tasks/attest-ui-taste/report.md` with `shots/`, `fixtures/`, `request-log.json` and `contrast-{light,dark}.json` next to it. It will contain baseline and after scores with evidence, Keep, Fix and Quick-wins lists, an inventory table showing before, after and threshold, position measurements, matrix results, the request log with every POST body (keys redacted), console findings, the lead's regression results, and every untested item with its reason. Nothing in this plan authorizes implementation, commits or release work.

## Response to builder plan

Reviewed 2026-11-08 against `docs/adal/taste-builder-plan.md`, with the lead's decisions applied: system fonts only and no external assets or requests; the first visit follows the OS and a stored light or dark choice overrides it, unchanged; a return-to-system control is deferred as an unrequested feature; visible caveats in plain words, not provenance superscripts; no invented counts, diagrams, filters, toggles or new features. Where this section and the earlier acceptance list disagree, this section wins.

### What holds up

The builder checked the backend rather than the labels, and I confirmed each row of its §2 table against the code:

- Overall: `0.5·TASK + 0.25·ADVERSARIAL + 0.25·CONTAINMENT`, and an empty slice is 0 (`gym.py` `_slice_scores`)
- Cost: tokens × a hardcoded rate table, which `llm.py` itself describes as "planning estimates … not invoices"
- P(safe) is a clamped heuristic
- Achieved radius is `1.0 if escaped else 0.0`
- Health reports `checked: False`
- The sandbox prefers `runsc` and falls back to `runc`
- Each ledger event hashes the previous one's hash

`agent_leaderboard` adds three facts the copy must keep. `run_id` is the agent's latest run by `created_at`, so "P(safe), latest run" is accurate: it is the mean of that run's task values. `total_cost_usd` is summed over every public run. `chain_valid` is true only when all of the agent's runs are valid.

The builder's ID inventory matches mine. Its 47 entries count `tc-*` as one wildcard; my 48 also include the dynamic `s-` prefix that `#s-*` lookups build. The direction suits a judge: one plain sentence, an honest run button, the board on the first screen, evidence one click away, and less colour and motion. Removing `m0/m1/m2` threshold colouring, the spinner, count-ups and the ▼/▲ glyphs fixes tells I had flagged. Withdrawing provenance superscripts follows the lead's decision.

### Accepted thresholds (these replace my A9–A12 and tighten A3–A6)

| Id | Gate | Measured with |
|---|---|---|
| B1 | Leaderboard h2 top ≤ 400px at 1440×900 | my harness, both themes, reduced motion, after `document.fonts.ready` |
| B2 | ≥ 5 leaderboard rows fully visible at 1440×900 | six-row fixture with seeded-length names (≤ 24 characters) |
| B3 | Leaderboard h2 top ≤ 760px at 768×1024 | same |
| B4 | Leaderboard h2 top ≤ 1000px at 390×844 | same |
| B5 | Fast Eval button bottom ≤ 360px at 1440; inside the first screen at 768 and 390 | same |
| B6 | ≤ 130 visible words in the intro plus fact list | builder's counting rule, so the result compares with its baseline of 234. Labels and button text count; placeholders and closed `<details>` content do not. Header and tab words are reported separately |
| B7 | ≤ 4 fully bordered boxes wider than 120px on the first screen at 1440 | rendered borders on all four sides, including filled buttons |
| B8 | 0 `oklch(` literals, 0 violet, 0 `@keyframes`; `getAnimations()` returns 0 after load and after selecting a run | static grep plus a browser read |
| B9 | 0 monospace elements holding prose | my rule (four or more words that aren't an ID, hash, slug, path or code), which is stricter than the builder's eight words |
| B10 | Achieved Radius reads "0, no escape detected" or "1, escape detected" everywhere it appears: the defence panel, the expanded task detail (where `fmt(…,3)` must also go) and the selftest view. A missing value reads "—", never "0, no escape detected" | fixture with present, escaped and missing values |
| B11 | Contained and escaped tasks take both their word and colour from the containment level: CONTAINED in `--warn`, ESCAPED in `--bad`, even when the oracle passed. Today an escaped task whose oracle passed shows PASS | fixtures for passed+contained and passed+escaped |
| B12 | The run-view score line equals `run.scores`. When `scores` is absent (the selftest view or partial data) it shows "—", never 0 and never a quiet recomputation | fixture with and without scores |
| B13 | Evidence summary event count and head hash equal the fetched pack | fixture |

My A1, A2, A7, A8 and A13–A18 stand unchanged. A4 is unchanged, with the lead's ruling applied: system stacks only, and zero requests that leave the static origin.

### Feasibility

- **B1 is the tight one, and the builder's own numbers miss it.** Its §5 puts a 56px header, an intro of at most 300px and a sticky tab bar of about 48px above the board heading, which already adds up to 404px before any section padding. If I stack the six left-column items at the planned sizes, the h2 lands near 500px. It can work, but only if the input and both buttons share one row, `#model-scope` wraps to two lines or fewer at the 7/12 column width, and the details summary and adapter line share a row or move to the right column. The builder should budget the intro at about 270px including padding. Shrinking text below 13px, hiding `#model-scope`, or folding the mode explanation into the disclosure fails B1. Those are visible caveats that matter.
- **B2 is feasible once B1 holds.** A two-line agent cell at 14px is about 62px, so five rows end near 790px. The 80-character hostile name stays in the fixture for wrapping and overflow checks but is left out of the row count: truncating it to save a row would hide data.
- **B3 is borderline.** A stacked intro of about 420px plus a four-row fact list of about 200px, the header, tabs and padding comes to roughly 760px. Setting the fact list as two columns at 768 gives the margin.
- **B4 is probably infeasible as planned.** At 390 the stacked intro has a four-line h1, a four-line method sentence, the input, two full-width 46px buttons, about six lines of `#model-scope`, the disclosure, the adapter line and the fact list. That estimate comes to about 1,100px. Two ways to pass without hiding anything material: shorten the method and fact-list copy, or put the non-interactive fact list after the board in the DOM and place it in the right column on desktop with grid. The second changes screen-reader reading order but not keyboard order, because the list has no focus stops. I accept it as long as the desktop reading order stays sensible.
- **B6 is at its limit.** My count of the drafted copy (h1 14, method 25, scope 33, labels and buttons about 15, summary 5, adapter 12, fact list about 35) is about 139 words. Trim from the method sentence or the fact list. The scope sentence about what is not tested is a material caveat and stays.
- **B5, B7 and B8 are feasible as planned.**

### Remaining disagreements and required changes

1. **The type scale is still flat underneath.** The builder's 16, 15, 14 and 13px tiers are one pixel apart, which is kill-ai-slop tell #12, and with 32, 28 and 20 that makes seven sizes. Gate: at most six sizes outside code, smallest at least 13px, no two text sizes one pixel apart, heading steps at least 1.2×. One way to pass: 32, 28, 20, then 15 (body, table and h3 at weight 600) and 13 (meta). This replaces my A3, which asked for a 1.2× step at every size and was stricter than a data table needs.
2. **The overall weighting is shown twice.** The builder's own rule is "show the weighting once, next to the leaderboard", yet §5.2 puts it in the fact list and §5.4 repeats it in the board note. Keep it in one place. The fact list is the better one, since it sits above the board on the first screen. The note keeps the Est. USD and P(safe) caveats.
3. **"Every step is written to a hash-chained ledger" says more than the code shows.** The ledger records the events a run appends, not every step. Suggested wording: "each run's events are recorded in a hash-chained ledger". The rest of the method sentence ("gVisor where available", "deterministic oracles") checks out. Every intro sentence goes into my claim table (A7).
4. **The tab label "Run" collides with the run buttons.** A judge next to "Run Fast Eval" may read a "Run" tab as a launcher. Use "Scorecard". "Compare" is fine, since the Capability Evals and Regression Evals names stay visible inside the view.
5. **The theme switch's visible text is missing from its accessible name.** In the current page and in the plan, the visible text flips between "Light" and "Dark" while the name stays "Dark mode", which fails WCAG 2.5.3 in light mode. Keep the name and visible text constant ("Dark mode") and show the state as on or off, with `aria-checked` unchanged. Storage, OS-first behaviour and the head script stay exactly as they are, which is what the lead asked for.
6. **Two sticky bars eat a phone screen.** A sticky header plus a sticky tab bar is about 104px on desktop and about 140px at 390 with a two-line header. Gate: sticky chrome at most 15% of viewport height at every size, `scroll-padding-top` covering it, and no focused element under it (WCAG 2.4.11). On phones, letting only the tab bar stick is enough.
7. **Light `--line-strong` fails 3:1 on `--bg-2` and the selected-row tint.** Measured values: 3.15 on `--bg`, 2.93 on `--bg-2`, 2.75 on `--accent-weak`. Dark is 3.20, 3.00 and 2.69. Every text pair passes, with the lowest at 5.17 (`--warn` on the selected row in light). Inputs and secondary buttons may sit on `--bg-2` (the header) or the selected row, so darken `--line-strong` until it reaches 3:1 on the darkest surface it touches, or keep control boundaries on `--bg` only. The decorative hairline (`--line`, 1.26) is exempt as long as no control, focus state or selection depends on it.
8. **The trajectory ✓ and ✕ glyphs in tinted circles are still unaddressed.** §5.5 keeps `#trajq` but doesn't say how it renders. Use words with counts ("required steps 3/4") in ink, with status colour only on a failing count.
9. **Selection needs a state, not only a colour.** The selected row gets a tint and an inset bar. Add `aria-current="true"` on the selected `tr`, which is a presentation-level JS change. Recommended, not a gate.
10. **The regression scripts need one runner.** Builder §9 step 4 has the builder running the four scripts, and the lead's instruction says the lead runs them serially. Two runners would collide on the fixed `/tmp` databases and Docker. The builder should not run them, or should run them only after the lead confirms nothing else is running. I review the lead's log either way.
11. **The "before" needs one shared copy.** Builder §9 step 1 makes its own scratch copy. The evaluation baseline is the frozen copy at `~/.adal/engineer/tasks/attest-ui-taste/baseline/index.html` (sha256 `e340dec0…`), and the builder should confirm its copy has the same hash. The builder's baseline numbers (h2 713, first row 828, three rows) and my earlier figure (first row 876, taken from the design spec with a fixture banner) come from different harnesses. I re-measure both with mine.
12. **Scope check on additions.** The "6 agents" count (`boardRows.length`), the evidence summary list, the run-view fact line, the "Evidence" shortcut in the run heading and the empty-request text all show data the API already returns, so none is a new feature. The Evidence shortcut must only switch tabs and send no extra request, which the request log checks. Anything beyond these, such as filters, sorting, toggles, charts, chain diagrams or count badges not taken from API fields, fails.
13. **Tab order is still fixed by index.** The builder keeps `selectRun`'s `$$(".t")[1]` lookup and the tab order, so risk 1 stays mitigated as long as the scorecard tab remains second. I replay row selection and the attack corpus on the final markup.
14. **Theme check 5 changes.** Per the lead, return-to-system is deferred. I now check that no System control was added and that the stored override behaves exactly as in the baseline. Not being able to return to system is out of scope, not a finding.

Caveats that must be visible where their value appears, checked by A7 and the builder's A10:
- Est. USD: summed over all runs, from a rate table, not a charge
- P(safe): latest run, heuristic, display only
- Achieved Radius: binary, and 0 is not proof of isolation
- Tokens: reported by the API, estimated when an endpoint reports none
- Model scope: what is tested and what is not
- The visitor key goes to this server (next to the key field)
- The local adapter is planned and not available
- Chain: verified only when every run is valid

Short qualifiers in column headers ("Est. USD, all runs", "P(safe), latest run") count as visible caveats on the first screen. The full sentences may sit in the note under the table.

### Unrelated: `docs/submission/slides-outline.md`

`git diff --check` on the whole repo now exits 2 on one line: `docs/submission/slides-outline.md:3: trailing whitespace` (`Date: 2026-11-08` followed by two spaces, which is probably a deliberate Markdown line break). The file belongs to separate submission work and is outside the UI allowlist; I haven't edited it, and its hash in `baseline/SHA256SUMS` still matches. Scoped to the allowlist, `git diff --check -- attest/web/index.html docs/adal/design-spec.md` exits 0. The regression gate (A18 and contract 31) should therefore use that scoped command and report the slides line separately, so the unrelated whitespace neither blocks the UI pass nor gets "fixed" as part of it.

## Adjudicated contract (build approved 2026-11-08)

Source: the latest taste entry in `~/.adal/engineer/contracts/2026-11-contract.md` and the builder's "Response to evaluator plan". The sole implementer is `sonnet-ui-builder` (Claude Sonnet 5.5, `adal-worker-2413b30f`). The Opus builder no longer edits. I accept the builder's response in full. Where the earlier sections of this plan disagree, this section wins. Otherwise the stricter threshold applies.

### Accepted adjudications

- **Labels.** The tab is named "Scorecard". Tabs are looked up by explicit selectors (`.t[data-t=scorecard]`), never by index. Tab buttons carry `aria-controls` and `aria-current="true"` on the active one, which meets my semantics check without the full arrow-key tabs pattern.
- **Theme.** The switch's accessible name stays "Dark mode", with visible on/off state and `aria-checked`. OS-first behaviour and the stored override are unchanged. Return-to-system is deferred and not a finding. Theme check 5 now checks only that no System control was added.
- **Type.** System fonts only. The scale is 12.5, 15, 18, 22 and 28px, plus a prominent Overall number in the run view as documented. A3 is satisfied if rendered sizes outside code blocks come from that set and nothing is below 12.5px. My later "smallest at least 13px" proposal is withdrawn. There is no prose in monospace.
- **Glyphs.** An em dash is allowed only as the missing-value placeholder in data cells and metadata. Middle dots are allowed as metadata separators. Prose has no dashes. ✓, ✕, ▸, ▾, ◐, → and ▼ ▲ are gone.
- **Caveat wording (A7).** These count as meeting A7:
  - P(safe): "computed by a fixed formula from the containment classifier's result and the static capability score … for display, not a calibrated probability, and not proof of isolation". This matches `_p_safe` in `gym.py`: a base from the containment level, minus 0.3 × attempted radius, clamped.
  - Achieved Radius: "1 when the containment classifier detects an escape and 0 otherwise. 0 is not proof of isolation", with a missing value shown as unavailable.
  - Est. USD: not an invoice, summed over all runs on the leaderboard.
  - Tokens: may fall back to estimates.
  - Ledger copy says "run events", not "every step".
  - The key-to-server and not-your-own-agent disclosures stay, verbatim or tighter, never dropped.
- **Ladder and counts.** "No ladder counts" in the contract means no invented or static counts. The run view's per-run counts computed from API data are existing behaviour and stay. A count or number that is not derived from an API field fails.
- **Corrected tokens.** `--line-strong` must reach 3:1 on every surface that holds a control (`--bg`, `--bg-2` and the selected-row tint) in both themes.
- **Inline styles.** Target 0 static `style=` attributes and 1 `!important` block, for reduced motion. Runtime `style.display` toggles are existing behaviour and exempt.
- **No-JS line.** A plain `<noscript>` sentence is acceptable and is not a claim of useful no-JS data.
- **Row-count fixture.** If B2 fails only because the 80-character name wraps, I report the measurement. Rows are counted with seeded-length names. Truncating names is not allowed.

### Final numeric gates

| Gate | Value |
|---|---|
| Leaderboard h2 top | ≤ 400 (1440×900), ≤ 760 (768×1024), ≤ 1000 (390×844) |
| Full rows at 1440×900, six-row fixture | ≥ 5 |
| Primary action bottom | ≤ 360 at 1440; inside the first viewport at 768 and 390 |
| Intro plus fact-list visible words | ≤ 130 |
| Fully bordered boxes > 120px wide, first screen, 1440 | ≤ 4 |
| Sticky chrome height | ≤ 15% of viewport height on phone; no focused element under it at any size |
| Overflow and clipped controls | 0 at all six size and theme combinations |
| Contrast | ≥ 4.5 normal text, ≥ 3 large text, ≥ 3 focus and control boundaries, every visible text node, each theme |
| Tap targets at 390 | ≥ 44 × 44 px |
| External requests, assets, dependencies | 0 |
| `oklch(` literals, violet, `@keyframes`, `getAnimations()` after load | 0 |
| Monospace prose | 0 |
| Static inline styles, `!important` blocks | 0, 1 |

Unchanged: A1–A2 critique gates, A5–A8, A13–A18 and B10–B13, the section 5 mocked flow assertions, and the 35 recovery criteria.

### Concurrent submission work: attribute, don't freeze

Other files under `docs/submission/` are being edited at the same time by separate submission work, and they must be preserved. A change there is not a builder scope violation unless there is evidence the builder touched the file. My method:

- Hash snapshots of `attest/web/index.html`, `docs/adal/design-spec.md` and every file in `docs/submission/` go into `~/.adal/engineer/tasks/attest-ui-taste/hashes-HHMMSS.txt`. The first snapshot was taken at 12:06:19: the index hash still matched the baseline (`e340dec0…`), the seven baselined submission files matched, and `docs/submission/video-production-plan.md` had newly appeared, untracked.
- At final evaluation, any submission file whose hash changed is attributed by checking the builder session (`06e1ddcf-9d8d-4c97-bb3c-ed945e1af652`) transcripts and tool logs for writes to that path. A write found there is a scope violation. Otherwise it is reported as concurrent and unattributed to the builder.
- The commit must stage only the allowlisted files and role plan docs, by explicit path. A commit that includes a submission file the lead didn't name fails A18, whoever edited it.
- `git diff --check` is scoped to the allowlisted files. The `slides-outline.md:3` trailing whitespace is reported separately and left alone.

### Release checks (after my acceptance, run by the lead)

Push to GitHub and the Cloudflare update are authorized only after this evaluation and the lead's serial regression run. They are not part of implementation. For the report I will verify, read-only:

- The pushed commit contains only the staged allowlist paths, and no force push happened (`git log`, `git show --stat`)
- The served HTML on the public URL has the same sha256 as the accepted `attest/web/index.html`, fetched with a plain GET
- Public `GET /api/health` and `GET /api/leaderboard` answer, and the board renders real seeded rows. Read-only GETs only: no POST run, no `/api/selftest` (it runs attacks), no promotion against production
- One 1440×900 screenshot of the live page in each theme, compared against the accepted fixture shots for layout only

If the Quick Tunnel URL or the backend owner can't be confirmed, I mark live checks unverified rather than guess a URL.

### Sequencing

- **Allowed now (read-only):** baseline screenshots, inventory and position measurements, using the frozen copy served from my own temporary directory, in my own window and browser contexts, with every API call answered by my fixtures. Only the baseline is measured now.
- **Done 12:09–12:14:** the baseline record is `~/.adal/engineer/tasks/attest-ui-taste/baseline-measurements.md`, with 8 screenshots in `shots/before/`. At 1440 the board h2 was at 713px with 1 full row, intro words 200, 8 bordered boxes, 7 text sizes, 4 mono-prose elements; contrast had 0 failures (minimum 5.09 light, 5.94 dark). Baseline critique: Philosophy 5, Hierarchy 5, Detail 6, Functionality 7, Innovation 5.
- **Not before the lead requests it:** no measurement of the live working-tree `index.html` while Sonnet is editing, and no final scores.
