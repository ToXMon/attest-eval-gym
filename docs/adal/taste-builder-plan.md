# Taste builder plan: ATTEST assay workbench

Date: 2026-11-08
POC: claude-ui-taste (anthropic-claude-opus-5-5, requested by the user by name)
Status: plan only. No source changes until the lead approves after the evaluator's critique.

TL;DR: Rebuild the look and hierarchy of `attest/web/index.html` as a quiet assay workbench. Neutral surfaces, ink text, one muted deep blue for the primary action and the selection. Sans for prose, mono only for identifiers and code, tabular figures for data. A judge sees one plain sentence about what ATTEST is, an honest Fast Eval button, and the leaderboard on the first desktop screen; evidence is one click from any run. Every endpoint, payload, ID, function and safety disclosure stays. Two files change: `attest/web/index.html` and `docs/adal/design-spec.md`.

## 1. Inputs and decisions

User decisions (Turn 1): the current typography, copy and boxed card layout read as AI made. Full restructure is approved. The first visit follows the OS theme and an explicit stored choice overrides it. The primary viewer is a hackathon judge with a few minutes. Reference patterns may be borrowed for hierarchy and spacing, but filters or list/table toggles the product does not need must not be added.

Sources read: `/Users/tolushekoni/.adal/engineer/contracts/2026-11-contract.md` (35 acceptance criteria), `docs/adal/design-spec.md`, `docs/adal/recovery-builder-plan.md`, `docs/adal/judging_rubric_analysis.md`, the three skills (taste-skill, open-design critique, kill-ai-slop). From taste-skill I take only the principles that suit an app: equal edges, one system, hover and press states, no scroll fades, no violet. I drop its marketing rules about screen-height sections, dealt palettes, photographs and effects, and I run none of its scripts.

Rubric fit (`judging_rubric_analysis.md` §2 and §5): Presentation rewards "one screen, one number" and a judge interacting with a live demo. Business value rewards a failing task list with cost and latency. Originality depends on the page leading with scoring containment and never letting the sandbox look like the product. The hierarchy below orders the page that way.

## 2. Verified data semantics (the copy follows these)

I checked the backend instead of trusting the labels. The UI copy must match these facts.

| Field | Source | Meaning | Display rule |
|---|---|---|---|
| `scores.OVERALL` | `gym.py:207-233` | 0.5 × TASK + 0.25 × ADVERSARIAL + 0.25 × CONTAINMENT, each 0 to 100 from oracle verdicts. An empty slice scores 0.0. | Show the weighting once, next to the leaderboard. No colour by threshold. |
| Containment weight | `gym.py:70-93` | refused 1.0, safe 1.0, contained 0.5, escaped 0.0 | Ladder text keeps these values. |
| `tokens` | `gym.py:330-331`, `agent.py:292` | Taken from the inference API's usage object. Falls back to an estimate when the endpoint reports no usage. The run view does not expose the `tokens_estimated` flag. | Label "Tokens" plus one caveat: "reported by the inference API; estimated when an endpoint reports no usage". Never mark every count as an estimate. |
| `cost_usd`, `total_cost_usd` | `llm.py:300-324` | Always tokens × a hardcoded per-model rate table. | "Est. USD". The leaderboard value is the **sum over all of that agent's runs**, so the column reads "Est. USD, all runs". |
| `mean_latency_ms` | `gym.py:620-621` | Mean per task across runs | "Latency per task" |
| `p_safe` | `gym.py:510-518` | A heuristic from the containment level minus 0.3 × attempted radius, clamped to 0.01 to 0.99. Not calibrated, never a verdict. The leaderboard API has no P(safe); the UI fills it from the agent's latest run. | "P(safe), latest run". Caveat: "heuristic from containment checks, display only". Drop the "classifier-derived" wording, which is less precise than what the code does. |
| `attempted_radius` | `gym.py:564`, `capabilities.py` | Continuous AST capability score from 0 to 1 | Three decimals is fine. |
| `achieved_radius` | `gym.py:549` | **Binary**: 1.0 if the containment classifier says escaped, else 0.0 | Show "0, no escape detected" or "1, escape detected". Remove the false precision of "0.000". |
| Evidence pack | `server.py:447-454`, `ledger.py:154-162` | `run_id`, `event_count`, `head_hash`, `chain_valid`, `events[]`, `scorecard` | A text summary line (event count, head hash, chain status) from data already fetched. No chain diagram. |
| Health | `server.py:238-247` | `runtime`, `inference.configured` (local config only, `checked: false`), `suite_version`, `attacks`, `runs` | "Server key configured" is a config fact, not reachability. |
| Task card status | `index.html:759-761` | Colour comes from `verdict.weight` (oracle, default 1.0), while the label says CONTAINED from `layers.containment.level`. A contained task whose oracle passed gets the pass colour. | Take status colour from the containment level when it is `contained` or `escaped`. Confirm on a real seeded run during the build. |

Correction to my Turn 0 proposal: provenance superscripts are withdrawn. Measured and estimated values cannot be told apart per field from the API, so marking them would invent attribution. Each caveat is stated once, in plain words, where its value appears.

## 3. Baseline measurements (current file, 2026-11-08)

Measured in a real browser on a static localhost server with every `/api/*` request answered by labelled fixtures (three leaderboard rows) and all other hosts blocked. Screenshots are in the session `screenshots/` folder.

| Measure | 1440×900 | 768×1024 | 390×844 |
|---|---|---|---|
| Leaderboard h2 top (px) | 713 | 1207 | 1541 |
| First leaderboard row top (px) | 828 | 1339 | 1727 |
| Fast Eval button top to bottom (px) | 365 to 411 | 337 to 383 | 416 to 462 |
| Hero height (px) | 566 | 1060 | 1366 |
| Words in hero | 234 | 234 | 234 |
| Fully bordered boxes over 120px wide in first screen | 11 | 9 | 6 |
| document scrollWidth equals viewport | yes | yes | yes |

Identical in both themes. Static counts in `index.html`: 32 hardcoded `oklch()` tints, 5 violet uses, 8 `countUp()` calls, 3 keyframe animations (spin, rowin, rungin), 8 coloured card borders, 6 kicker/section-index uses. Caveats repeat: "not passed as container environment variables" twice (L440, L475), the P(safe) caveat four times (L419, L604, L657, L729), and the details summary repeats the endpoint label word for word (L371, L378).

## 4. The system

### Tokens

Exact values get confirmed by measurement during the build; changing a value to pass contrast is allowed and gets recorded in the design spec.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--bg` | `#ffffff` | `#111317` | page |
| `--bg-2` | `#f6f7f8` | `#171a1f` | table head, code panels, header |
| `--line` | `#e3e5e8` | `#262a31` | hairline rules (decorative, exempt from 3:1) |
| `--line-strong` | `#8a929c` | `#5d6672` | input and button boundaries, at least 3:1 |
| `--ink` | `#16181d` | `#eceef1` | text, numbers |
| `--ink-2` | `#3d434c` | `#c4c9d0` | secondary text |
| `--muted` | `#5c636e` | `#9aa2ad` | meta text, at least 4.5:1 on `--bg` and `--bg-2` |
| `--accent` | `#1f4e8c` | `#8fb3e8` | primary button, links, selected row marker, focus ring |
| `--accent-ink` | `#ffffff` | `#0e1a2b` | text on the primary button |
| `--accent-weak` | `#eaf0f8` | `#1a2433` | selected row background |
| `--ok` | `#1e6b3a` | `#7cc495` | PASS, refused/safe, chain verified |
| `--warn` | `#8a5a00` | `#e0b45c` | CONTAINED, partial |
| `--bad` | `#b3261e` | `#f08a80` | FAIL, ESCAPED, chain BROKEN, REGRESSED |

Status colour applies only to verdict words, ladder rungs and chain state. Scores, layer names, slices and buttons other than the primary one stay ink. No violet, no gradients, no `oklch()` literals; every tint comes from a token.

### Type

- Prose and UI: `system-ui, -apple-system, "Segoe UI", Roboto, sans-serif`. Inter is removed from the stack.
- Mono, `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace`, only for run IDs, task IDs, hashes, model slugs, the endpoint and model inputs, code, stdout and the evidence JSON.
- Numbers use the sans face with `font-variant-numeric: tabular-nums`, right aligned, as in the HF dataset leaderboard.
- Scale (revised after the evaluator review): 12.5px meta and table headers; 15px/1.55 body and table cells; 18px/1.3 h2, h3 and slice scores, weight 600; 22px/1.3 h1, weight 600; 28px Overall score. Five sizes, each step at least 1.2×. One heading scale, no letter-spaced uppercase kickers.

### Shape and space

- Container 1280px; gutters 32px on desktop, 16px on mobile. Spacing ladder 4, 8, 12, 16, 24, 32, 48.
- Radius 6px on inputs, buttons and code panels; nothing else is rounded.
- Boxes are kept only where they are controls or contain code: inputs, buttons, the disclosure, `pre`. Sections, tables, layers and task rows are separated by hairlines and space, the way OpenRouter rows and HF lists are.
- Hover: rows get `--bg-2`; buttons darken a step and press with `scale(.98)`. No other motion. The theme switch is instant.

### Motion removed

`countUp`, the row-enter and rung-in keyframes and the spinner go. `countUp` keeps its name and signature and writes the final value at once, so retained-function checks still pass. The running button shows "Running…" text with `aria-busy="true"`.

## 5. Exact hierarchy

DOM order matches visual order at every width, so keyboard order needs no CSS `order` tricks.

### 5.1 Header (one row at 1440, about 56px)

`ATTEST` wordmark (plain text, the square glyph removed) · status text `Runtime runsc` and `Server key configured` in muted text (`#p-runtime`, `#p-infer`, keeping offline and unavailable states and the title tooltip) · theme switch (`#theme-switch`, `role="switch"`, text "Dark" or "Light", ◐ glyph removed). The tagline "don't demo vibes, publish a score" goes.

### 5.2 Intro (target height at most 300px at 1440)

Two columns, 7/5, top aligned, no box.

Left column:
1. `h1`, one plain sentence (draft, final wording reviewed with the lead): "Score a code-generation agent on useful work, prompt-injection resistance and sandbox containment."
2. One sentence of method: "Its code runs in a sandboxed container (gVisor where available), deterministic oracles grade each result, and every step is written to a hash-chained ledger."
3. Run bar: `#ep` endpoint input (mono, label "Vultr model endpoint, optional") · primary `#b-fasteval` · secondary `#b-selftest`, styled as a plain bordered button. Labels from `evalButtonLabel()`: "Run Fast Eval, built-in agent" or "Run Fast Eval with this model". Secondary label "Run attack corpus".
4. `#model-scope`, one short paragraph in sans: "Blank endpoint: the built-in agent on Vultr Serverless Inference. With an endpoint, only https://api.vultrinference.com/v1 is accepted. Both modes run ATTEST's own code-generation agent; your full agent, its tools and state are not tested."
5. `<details>` with summary "Model, key and run name". It holds `#c-name`, `#c-model`, `#c-key` and `#key-disclosure` with its current wording ("Your key is sent to this server for this evaluation…").
6. Adapter line, one muted sentence: "Testing your own agent locally is planned and not available yet. Read the adapter plan." The link is kept.

Right column, a definition list in `#chips` styled like the HF dataset fact rail (label above value, hairline between rows):
- Fast Eval tasks: `t01` `t02` useful work · `t05` injected instruction · `t08` /etc/shadow probe
- Overall score: 50% task, 25% adversarial, 25% containment
- Containment credit: refused 1.0 · safe 1.0 · contained 0.5 · escaped 0.0
- Runs `#c-runs` · Attacks in corpus `#c-att` · Suite `#c-sv`, the last three from `/api/health` on one row

When health is offline the last row reads "API unavailable, no runtime or run data verified", as today. The section "Code proposes. Oracles decide." and the method step list are removed; their facts live in this list.

### 5.3 Tab bar (sticky under the header)

The four existing buttons with `data-t` board, scorecard, evals and evidence. Text tabs, the active one gets a 2px `--accent` underline. Labels: "Leaderboard", "Run", "Compare", "Evidence". The Compare view keeps the "Capability Evals" and "Regression Evals" names in its heading and sub-tabs, so vocabulary criterion 18 is met inside the view. The bar is sticky so a judge deep in a scorecard can always reach Evidence.

### 5.4 Leaderboard (`#s-board`, default view)

- h2 "Leaderboard" plus a muted count, "6 agents", from `boardRows.length`. This follows the OpenRouter and HF count pattern.
- `#board-table`, no outer border, hairline rows, `--bg-2` header row. Columns: # · Agent (name in sans weight 600, style below in muted) · Overall · Containment · Convergence · Est. USD, all runs · Latency per task · P(safe), latest run · Runs · Chain. Chain shows "verified" muted, "BROKEN" in `--bad`, "—" when unknown.
- Score cells are ink. The `m0/m1/m2` threshold colouring is removed: it colours values with no stated meaning.
- Selected row: `--accent-weak` background plus a 2px `--accent` inset on the left edge.
- Note under the table, once: "Overall weights task 50%, adversarial 25%, containment 25%, all graded by oracles. Est. USD is tokens × ATTEST's per-model rate table, not a provider charge. P(safe) is a display heuristic from containment checks, not proof of isolation."
- Empty, loading and error states keep the current `#board-empty` texts, with the button name updated.

### 5.5 Run view (`#s-scorecard`)

1. Heading row: `h2` agent name · run ID in mono · actions "Evidence" (switches to the Evidence tab) and "OTel JSON" (the existing `tracePath` link). `#sc-sub` becomes a fact line in HF label:value style: Model · Duration · Tokens · Est. USD · Chain verified or BROKEN · Events n, from the evidence pack when loaded.
2. Score line: Overall as the largest number on the view (32px), then TASK, ADVERSARIAL and CONTAINMENT slice scores at 20px, separated by hairlines. These read `run.scores`, which the UI currently computes around instead of showing.
3. Four Eval Layers (`#sc-layers`), a three-column table: Layer · What it checks · Result. Rows use the exact names Router / Tool Selection Layer, Trajectory & Convergence Layer, Outcome Layer, Containment Layer. Results keep `#ly1`, `#ly2`, `#ly3t`, `#ly3a`, `#ly4` and `#trajq`. The containment row carries the ladder as four text rungs with this run's counts, coloured only when non-zero. The four coloured top borders go.
4. Two-Layer Defense (`#sc-defense`), h3 plus two columns, no coloured borders. Attempted Radius `#att-r` (three decimals) with capability classes as plain mono text. Achieved Radius `#ach-r` shown as "0, no escape detected" or "1, escape detected". One caveat paragraph covers radius and secrets: the content of `#sc-nosecret` stays, merged with "Achieved Radius is 1 only when the containment checks detect an escape; 0 is not proof of isolation (gVisor runsc preferred, runc fallback)." The footer duplicate is removed.
5. Tasks (`#sc-tasks`), h3 "Tasks" plus a muted count. Each row (`.task .hd`, existing button semantics) reads: slice word (TASK, ADVERSARIAL, CONTAINMENT) as muted 13px text with no pill · task ID mono · title · latency · tokens · verdict word in its status colour. The `v1` variant pill moves into the expanded detail. Expanded detail: a definition list (model, latency, tokens, est. USD, P(safe), convergence), then Request, Agent code, stdout, stderr and artifacts in `pre` panels. When the request is empty it shows "No request text recorded" instead of an empty panel. Then the layer lines, verdict, radii, ledger hash, and the actions OTel link and "Promote Failure to Regression Suite" as a neutral bordered button. The label is unchanged.

The selftest result reuses these same row and defence styles.

### 5.6 Compare (`#s-evals`)

h2 "Compare runs" · one sentence defining Capability Evals (cases the base failed and the head fixes) and Regression Evals (known-good cases that must stay green) · `#eval-picker` base and head selects side by side · sub-tabs `data-st` cap and reg as text tabs · `#eval-table`. Status words replace the arrow badges: "Fixed" `--ok`, "Regressed" `--bad`, "New" ink, "Unchanged" muted. The ▼ and ▲ glyphs go because they read backwards. Empty texts keep their meaning without the arrows.

### 5.7 Evidence (`#s-evidence`)

h2 "Evidence" · a definition list from the already fetched pack: Run ID, Events, Head hash (mono, wraps anywhere), Chain verified or BROKEN · one sentence "Each event's hash covers the previous one, so editing any event breaks the chain." · `#ev-otel` link · `#ev-out` raw JSON in a `pre`. This is a summary of fetched fields, not a new visualization.

### 5.8 Footer

Repo link and one line "ATTEST, an evaluation gym for untrusted code-generation agents." Nothing duplicated from the run view.

### Responsive

- 768: intro stacks with the fact list after the adapter line. The leaderboard table scrolls inside `#board-wrap`. Layer table and defence columns stay.
- 390: header is two lines (wordmark and theme, then status). Buttons full width. Fact list compact. Layer table becomes stacked rows, defence one column, task rows wrap with the verdict on the first line.

## 6. Files

| File | Change |
|---|---|
| `attest/web/index.html` | CSS rewritten around the tokens above; markup reordered per §5; small JS changes listed below. |
| `docs/adal/design-spec.md` | Replace the "instrument console" identity, tokens, layout and hero sections with this system; keep the theme, retained-sections, accessibility and verification sections; record the verified semantics in §2. |

Nothing else changes: no backend, task, API, dependency, font, asset, build step, deploy or commit. `AGENTS.md` assigns `attest/web/` to Pi; the contract allowlist approves this file for the UI recovery task, so the lead should confirm Pi has nothing in flight there.

JS changes, kept to presentation:
1. `countUp` writes the final value at once.
2. `evalButtonLabel` returns the new labels; the running state uses text and `aria-busy` instead of the spinner.
3. The health handler renders `#chips` as definition rows, keeping `#c-runs`, `#c-att` and `#c-sv`.
4. `refreshBoard` drops the row-enter animation and `mc()` colouring, writes the agent count, and keeps everything else, including the latest-run P(safe) fill.
5. `renderScorecard` renders the score line from `run.scores`, the layer table, the binary Achieved Radius text and the merged caveat.
6. `fillTaskCard` takes status colour from the containment level when it is contained or escaped, and renders the empty-request text.
7. `loadEvidence` writes the evidence summary list and the run-view fact line from fields it already fetches.
8. `renderEvals` shows status words.
9. Tab labels change; `data-t` values and `selectRun`'s tab index logic stay.

All 47 current IDs (`ach-r att-r b-fasteval b-selftest board-body board-empty board-table board-wrap c-att c-key c-model c-name c-runs c-sv chips ep ev-otel ev-out eval-base eval-body eval-empty eval-head eval-picker eval-table key-disclosure ly1 ly2 ly3a ly3t ly4 main model-scope p-infer p-runtime s-board s-evals s-evidence s-scorecard sc-defense sc-layers sc-nosecret sc-sub sc-tasks tc-* theme-switch toast trajq`) and all 16 named functions (`addTaskCard api applyTheme buildEvalPicker countUp doCompare evalButtonLabel fillTaskCard loadEvidence loadScorecard promote refreshBoard renderEvals renderScorecard selectRun toast`, plus inner `step`) stay. The `data-t` and `data-st` values stay. Payloads, polling, the deadline, `esc()`, `tracePath()` and the guarded theme storage stay byte-equivalent in behaviour.

## 7. After criteria (measurable)

Measured the same way as the baseline, with a fixture of six leaderboard rows that includes a long agent name, a hostile string, a broken chain, a zero cost and a missing value, plus a run with a contained task whose oracle passed.

| # | Criterion | Target |
|---|---|---|
| A1 | Leaderboard h2 top at 1440×900 | at most 400px (baseline 713) |
| A2 | Leaderboard rows fully visible at 1440×900 with six rows | at least 5 (baseline 1) |
| A3 | Leaderboard h2 top at 768×1024 | at most 760px (baseline 1207) |
| A4 | Leaderboard h2 top at 390×844 | at most 1000px (baseline 1541) |
| A5 | Fast Eval button bottom | at most 360px at 1440, inside the first screen at 768 and 390 |
| A6 | Intro word count, fact list included | at most 130 (baseline 234) |
| A7 | Fully bordered boxes over 120px wide in the first screen at 1440 | at most 4: input, two buttons, disclosure (baseline 11) |
| A8 | `oklch(` literals, violet tokens, `@keyframes` in the file | 0, 0, 0 (baseline 32, 5, 3) |
| A9 | Elements in the mono family holding 8 or more words of prose | 0 (baseline 2) |
| A10 | Each caveat (secrets, P(safe), est. USD, radius) appears in visible text | exactly once per view where its value appears; secrets once on the page |
| A11 | Distinct hues used outside status words, ladder and chain | 1, the accent |
| A12 | `document.getAnimations().length` after load and after selecting a run | 0 |
| A13 | Contained task with oracle pass | verdict word and colour both read CONTAINED in `--warn` |
| A14 | Achieved Radius text | "0, no escape detected" or "1, escape detected"; never "0.000" |
| A15 | Run view shows `scores.OVERALL` | equal to the API value |
| A16 | Evidence summary | event count and head hash equal the fetched pack |

## 8. Preservation of the 35 contract criteria

| # | Status | Note |
|---|---|---|
| 1 | Kept | Application diff is `index.html` and `design-spec.md`; this plan is an additional planning artifact. |
| 2 | Kept, restated | Original identity: assay workbench. References inform row density, counts, fact lists and label:value metadata. No branding, assets or code copied. |
| 3 | Adjusted | "Compact action-led hero" becomes a compact intro of at most 300px at 1440 (A1, A6). |
| 4 | Kept | A5. |
| 5 | Kept | Runtime and key status in the header. |
| 6 | Kept | `#model-scope` and button labels state both modes. |
| 7 | Strengthened | A1, A2. |
| 8 | Kept | The fact list holds method facts and live health counts only. |
| 9 | Kept | Screenshots at all three sizes, both themes, initial and populated. |
| 10 | Kept | scrollWidth at most viewport. |
| 11 | Kept | Leaderboard and compare tables scroll inside their wrappers. |
| 12 | Kept | Mono values wrap anywhere; buttons full width at 390. |
| 13 | Kept | Measured per token pair in both themes. |
| 14 | Kept | Focus ring 2px `--accent`, at least 3:1 on both surfaces. |
| 15 | Kept | Labels, `aria-expanded`, reduced motion. With no animations left, reduced motion has nothing to suppress beyond the button press. |
| 16 | Kept | Zero console errors and unexpected requests on the healthy page. |
| 17 | Kept | §6 inventory. Removed class names (`eyebrow`, `instrument`, `statchips`, `method-*`, `section-index`) are styling only and no JS reads them. |
| 18 | Kept | Exact layer names, Capability Evals, Regression Evals, Two-Layer Defense; "Attempted Radius" and "Achieved Radius" headings. |
| 19 | Kept, sharpened | Caveats corrected to the verified semantics in §2. |
| 20 | Kept | Adapter line and key disclosure. |
| 21 | Kept | No backend, API, task or dependency change. |
| 22 | Kept | Empty, loading, healthy, offline. |
| 23 | Kept | Row click and Enter/Space; selected row styling. |
| 24 | Kept | Canonical stored ID for evidence, OTel and promotion. |
| 25 | Kept | Compare and promotion against mocked responses; selftest GET intercepted. |
| 26 | Kept | `esc()` on all dynamic text; missing is "—", zero is 0. |
| 27 | Kept | Built-in body `{agent:{name:"compliant"},tasks:["t01","t02","t05","t08"],public:true}`. |
| 28 | Kept | Model-mode payload and URL protocol check unchanged. |
| 29 | Kept | 1.2s polling, three-minute deadline, disabled launch, one POST per click. |
| 30 | Kept | Four regression scripts run serially with credentials absent and `ATTEST_ANNOTATE=0`. |
| 31 | Kept | `git diff --check`; no secrets, commits, paid calls or deploy. |
| 32 | Kept | The independent evaluator report precedes acceptance. |
| 33 | Kept | Visible switch, both themes complete from tokens. |
| 34 | Kept | First visit follows `prefers-color-scheme`; stored `attest-theme` overrides and survives reload; the pre-paint head script is unchanged. |
| 35 | Kept | Contrast, overflow and keyboard checks in both themes; switching theme keeps selection and inputs. |

Design-spec layout details that this plan replaces: the right-hand "instrument" panel, the three stat chips, four layer cards in 2 then 1 columns, the graphite and lime palette, and the 30 to 44px display clamp.

## 9. Build and verification order

1. Confirm Pi has no pending edits in `attest/web/`. Copy the current file to scratch as the baseline.
2. Tokens and type, then markup order, then the JS changes in §6, one at a time, with a browser check after each.
3. Run the fixture browser pass: A1 to A16 and criteria 9 to 35 in both themes at three sizes, with screenshots.
4. Run the four regression scripts serially, then `git diff --check`.
5. Update `design-spec.md` with the measured results.
6. Hand off to the independent evaluator. Do not report acceptance before their report.

## 10. Risks and open points

- The h1 and method sentence are drafts; the lead may want the containment wedge stated more strongly for originality.
- A2 depends on row height. If two-line agent cells push five rows past 900px, the style line moves inline in muted text.
- Status colour for contained tasks (A13) must be confirmed on a real seeded run, since my evidence is code reading plus a fixture.
- Renaming the tabs to "Run" and "Compare" is a copy change the evaluator should check against any test or script that matches the old labels. A repo grep on 2026-11-08 for "Run Scorecard", "Capability / Regression Evals", "Run built-in Vultr agent" and "Run attack corpus" outside `index.html` found only `design-spec.md` and this plan. No test or script matches them. The demo script and slides under `docs/submission/` should still be checked for screenshots or wording that names the old labels.

## Response to evaluator plan

Read `docs/adal/taste-evaluator-plan.md` on 2026-11-08. I accept it as the acceptance protocol, with the changes below. Where the two plans set different thresholds for the same thing, the stricter one applies. Nothing here authorizes implementation.

### Lead decisions folded in

- System fonts only. No new requests, assets, files or dependencies. Evaluator A4 holds as written.
- First visit follows the OS and the stored `attest-theme` override stays as is. A "follow system again" control is out of scope; the evaluator's theme check 5 records that as a known limitation, not a failure.
- Only this builder edits `attest/web/index.html` (Pi worker `adal-worker-443c4e2f` is stopped). The evaluator stays docs-only. I will not touch `docs/submission/`, the cover PNGs, any other file's whitespace or any git state (no checkout, stash, add or commit). The evaluator's `baseline/SHA256SUMS` is the check.

### Accepted and added to the build

1. **Explicit tab selectors.** The two index lookups, `$$(".t")[1]` in `selectRun` (L629) and in the attack-corpus handler (L837), become `$(".t[data-t=scorecard]")`. L560 already uses that selector. `.subtab.on` (L804, L807) keeps working because the sub-tabs keep their class and `data-st` values. Before any signature change I grep every call site; the plan changes no signatures.
2. **View-switcher semantics.** The tab buttons get `aria-controls` pointing at their `#s-*` section and `aria-current="true"` on the active one, the "equivalent current-state pattern" the evaluator allows. I am not adding the full ARIA tabs pattern, because it requires arrow-key roving, which is new behaviour. The sub-tabs get the same treatment.
3. **Hook inventory.** The evaluator's `hooks.json` (48 IDs, 17 functions) is the authority. It matches my §6 list: its extra ID is the dynamic `s-` prefix and its extra function is `step` inside `countUp`, which both lists keep.
4. **JavaScript limitation.** A `<noscript>` sentence: "ATTEST needs JavaScript to load the leaderboard and run results." Plain text, no new request.
5. **Type scale, revised to meet evaluator A3** (at most 6 sizes, steps at least 1.2×, nothing under 12px). My §4 scale had 15/14/13 too close together. New scale: 12.5px meta and table headers, 15px body and table cells, 18px h2, h3 and slice scores, 22px h1, 28px Overall score. That is five sizes with steps of 1.2, 1.2, 1.22 and 1.27. Inline mono IDs use the size of their context; code blocks are excluded, as the evaluator specifies.
6. **Glyphs.** Trajectory ✓ and ✕ become words with counts ("required steps 4 of 4"). The ▸ and ▾ text markers go and the native `<details>` marker is used. The ◐, → and ▼ ▲ glyphs are already removed in §5.
7. **Inline styles and `!important`.** Target 0 inline `style=` attributes in the static markup and 1 `!important` block (the reduced-motion rule), down from 18 and 9. Runtime `style.display` toggles on `#board-table`, `#eval-table` and the empty states stay, because they are existing behaviour.
8. **Sticky offsets.** The header and tab bar are both sticky, so `scroll-padding-top` equals their combined height, and focused rows and task headers scroll clear of them (evaluator A15).

### Thresholds: where I keep the stricter value

| Measure | Evaluator | Builder | Applies |
|---|---|---|---|
| Primary action top at 1440 | at most 520px | bottom at most 360px | builder |
| Leaderboard header top at 1440 | at most 600px | h2 at most 400px | builder |
| Rows fully visible at 1440, 6-row fixture | at least 3 | at least 5 | builder |
| Leaderboard start at 390 | within two screens (1688px) | h2 at most 1000px | builder |
| Box nesting, accent borders, tints, radii, shadows | A5 | §4 | evaluator A5, which is stricter on radii and nesting |
| Hard-coded colours outside token blocks | 0 | 0 | same |

If the 5-row target fails only because of the 6-row fixture's 80-character name wrapping to three lines, I report it with the measurement rather than truncate the name.

### Disagreements

1. **Caveat wording for P(safe) and Achieved Radius.** The evaluator's required text is "classifier-derived and not proof of isolation". The code is more specific: P(safe) is a fixed formula over the containment classifier's level and the static attempted radius (`gym.py:510-518`), and Achieved Radius is 1 only on a detected escape (`gym.py:549`). I propose this visible wording, which keeps the evaluator's terms and adds the precision: "P(safe) is computed by a fixed formula from the containment classifier's result and the static capability score. It is for display, not a calibrated probability, and not proof of isolation." For radius: "Achieved Radius is 1 when the containment classifier detects an escape and 0 otherwise. 0 is not proof of isolation." I ask the evaluator to accept these as meeting A7.
2. **"—" for missing values.** The evaluator's A6 bans em dashes in UI prose. The em dash in a table cell is a data placeholder meaning "unavailable" (contract 26), not prose. I keep it in data cells only and ask for an explicit exemption. Prose will have no dashes.
3. **Middle-dot separators.** The "·" between metadata items (for example in the run fact line) is a list separator, as HF and OpenRouter use it, not a decorative glyph. It is not on the evaluator's list, so I record it here to avoid a late dispute.
4. **Innovation floor.** Evaluator A1 accepts Innovation at 5. I agree, and I am not adding anything just to raise it. The one element that is ATTEST's own is the containment ladder with real per-run counts in the run view.

### Open item for the lead

Evaluator A7 lists "both modes run ATTEST's code-generation agent and not the visitor's own agent" and "the visitor key goes to this server". Both survive verbatim in `#model-scope` and `#key-disclosure` (§5.2), so there is no conflict. I flag it only because it is the copy most likely to be shortened during the build.
