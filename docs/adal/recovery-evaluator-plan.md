# Recovery evaluator plan

Date: 2026-11-08  
POC: independent evaluator  
TL;DR: Evaluate the proposed ATTEST UI recovery against the two-file scope, the frozen API contract, and observable browser behavior. This is a review plan, not implementation approval or an evaluation report. Do not edit application code, start the existing service, invoke live runs, or touch original run storage.

## Scope and evidence

Review only `attest/web/index.html` and `docs/adal/design-spec.md` for the redesign. The frozen API/task contracts, Vultr endpoint policy, evaluation semantics, and sandbox are invariants. The user has also approved visible light/dark mode with complete tokenized themes, guarded persistence and OS fallback, early initialization, and preserved UI state. No local-agent adapter, backend changes, deployment, paid inference, commits, release checks, or work on other files. This evaluator plan is the requested planning artifact, not an expansion of the implementation allowlist.

Ground the review in `docs/adal/recovery-builder-plan.md`, `docs/adal/design-spec.md`, `docs/adal/spec.md`, and the current HTML. Keep prior ticket-7 browser and test results as historical evidence only; they do not verify the redesign. Do not repeat broad reference browsing. Judge whether the spec distills OpenRouter’s comparison density and policy/cost clarity and Hugging Face’s task-discovery structure into an original ATTEST instrument console without suggesting unsupported features.

## Response to builder plan

The two-file boundary, preserved API and model policy, truthful local-adapter status, and prohibition on cloud, paid inference, deployment, or unrelated cleanup are sound. Keep the compact action-led console and desktop-first-viewport leaderboard as design goals, then check them against actual screenshots and the functional hooks rather than accepting the visual description as proof.

Clarify three points before implementation:

1. The current page already has many of the older spec’s cards, tokens, interactions, and responsive rules. Treat the redesign as a deliberate visual-hierarchy and layout change, not a blank-slate rewrite. Record which existing sections and labels remain, and preserve their actual data and behavior.
2. Do not carry forward the design spec’s claim that the shell has useful content with scripting off: this is a static HTML page whose API-driven leaderboard and scorecard populate in JavaScript. Describe the real loading/offline state. Likewise, keep “six seeded agents on first paint” and any live/demo claims conditional on actual API data; never add sample rows that could read as real evidence.
3. The page has two Vultr model-mode controls: the endpoint field in the hero and model/key fields in a disclosure. Preserve and test how they work together. Blank endpoint must still run the built-in 4-task mode; an entered endpoint must still select model mode, with the approved host policy and visitor-key disclosure intact. Don’t simplify the form in a way that silently changes which credentials or mode are used.

For test safety, separate browser presentation/interaction checks from integration scripts. Existing API tests stub inference but retain real sandbox execution in paths that run the gym. Mocking a model does not make a browser-launched Fast Eval or attack corpus a harmless fixture. Use synthetic API responses and intercept every mutating route in the browser; never click a real run, selftest, or promote control against a live or default local service. If the interaction cannot be exercised safely with mocked routes, mark it untested rather than improvising a server fixture.

## Review criteria

### Scope and contract

- `git diff --name-only` contains only `attest/web/index.html` and `docs/adal/design-spec.md` for implementation review; `git diff --check` exits 0.
- Existing selectors, DOM IDs, data attributes, endpoint paths, payload fields, and named functions relied on by the current page remain available, or the builder demonstrates their equivalent behavior. In particular, inspect `refreshBoard`, `selectRun`, `loadScorecard`, `loadEvidence`, `renderScorecard`, `doCompare`, `promote`, Fast Eval, and attack-corpus controls.
- No change to API/task shapes, agent/model/provider policy, score interpretation, sandbox claims, or persistence. No false “existing agent” functionality. Evidence and all fixture rows are either API-backed or unmistakably labeled illustrative.
- Preserve the Four Eval Layer vocabulary, Capability Evals / Regression Evals, Two-Layer Defense, attempted versus achieved radius, and the limitations around estimated cost, classifier-derived P(safe), and containment detection. Do not label classifier output as proof of isolation or estimated USD as a charge.
- All data inserted into HTML remains escaped; dynamic evidence stays text-rendered. Model-mode copy makes clear that a visitor key goes to this server for the evaluation.

### Visual checks

Use the browser on a locally served static page with synthetic, clearly labeled API fixtures; do not attach to the production URL. Capture viewport screenshots at **1440×900**, **768×1024**, and **390×844**, including the initial desktop view and a populated scorecard/evidence state. Retain paths in the later evaluation report.

Pass only if:

- At 1440×900, the primary action, runtime/inference status, built-in versus Vultr model distinction, and the beginning of the real/API-backed leaderboard are visible without scrolling. The first viewport has a clear action and evidence hierarchy rather than a generic marketing hero.
- In both light and dark themes at all three sizes, `document.documentElement.scrollWidth <= window.innerWidth`, key text/actions are not clipped, and dense tables scroll inside their own containers. No hidden overflow masks inaccessible controls.
- At 768 and 390 CSS px, cards and controls reflow without overlap; scorecard, detail disclosures, model fields, action labels, and long hashes remain readable. Check 390px specifically for horizontal page drift.
- Text contrast meets WCAG AA: at least **4.5:1** for normal text and **3:1** for large text; visible focus indicators have at least **3:1** contrast against adjacent colors. Check computed colors for representative muted/body text, links, statuses, borders/focus, and disabled controls, not just the brightest token.
- In both themes, keyboard-only navigation reaches and operates all controls, including the theme switch, in a logical order; focus is visible; disclosure, nav, task cards, and table-row activation have usable names and state. Labels remain programmatically associated with endpoint/model/key inputs. Reduced-motion mode suppresses nonessential animation while leaving content/state clear.
- Browser console has **zero uncaught errors**, and there are no failed local assets or unexpected network requests.

### Light and dark themes (contract criteria 33–35)

Test both themes at **1440×900**, **768×1024**, and **390×844**. Require a visible, explicitly labeled light/dark switch that is keyboard-operable, has an accessible name and state, and is available without relying on OS settings. Verify that every surface, text role, border, focus indicator, status, control, and disabled state uses the theme tokens and has a deliberate value in both themes; no hard-coded colors should leave unreadable components in either mode.

Check persistence in isolated browser contexts with storage available and with storage access throwing:

- With no stored preference, the page follows `prefers-color-scheme` for both OS light and dark settings.
- A stored light or dark choice overrides the OS setting across reloads and when the OS preference changes.
- Storage access failures do not break rendering or switch operation; use an in-memory fallback for the current page if that is the implemented behavior.
- Initialization applies the resolved theme before first paint. Capture reloads under conflicting stored/OS preferences and check for an incorrect-theme flash; verify the initial document/root theme attribute or class before content paint where observable.
- Switching themes preserves the selected run, expanded disclosures/task details, current comparison selections/tab, input values, and any in-progress/polling state; theme control must not reset or duplicate actions.

Repeat the numeric contrast, overflow, component reflow, focus visibility, keyboard operation, and no-clipping checks from Visual checks in both themes, including muted text, links, badges/status colors, input states, disabled controls, and focus rings. Record contrast results separately by theme; passing one theme does not imply the other passes. Use mocked/synthetic API data only and do not submit or promote runs to test theme preservation.

### Behavior with synthetic fixtures

Intercept reads for health, leaderboard, run detail, evidence, comparison, and OTel. Give them deterministic, visibly fixture-only values with missing/zero values and hostile HTML strings. Intercept and record POSTs for run, promotion, and selftest; return controlled responses without executing them.

Verify: healthy/offline loading states; empty/populated board; row keyboard and click opens the matching scorecard; evidence and OTel target the canonical run ID; compare controls render fixed/regressed/unchanged rows; promotion reports its mocked response; hostile strings render as text; missing values remain unavailable and zero remains zero. For Fast Eval, test blank and nonblank endpoint selection, exactly `t01,t02,t05,t08` and `public:true` for the built-in request, the visitor-key model payload when the approved endpoint is selected, disabled-during-request/recovery states, and synthetic running/completed/failed polling. The fixture must assert one POST per deliberate click and no duplicate launch. Do not call the real selftest endpoint.

A browser route mock verifies UI behavior, not server enforcement. Use the existing local regression scripts separately for code regressions; explicitly state that they are not a live inference or production-runtime check.

## Regression commands and caveats

Run the builder plan’s complete discovered suite only in the implementation/review phase, with Vultr credentials absent and annotation disabled:

```text
python3 scripts/selftest.py
python3 scripts/piptest.py
.venv/bin/python scripts/apitest.py
.venv/bin/python scripts/hardeningtest.py
git diff --check
```

Confirm the expected result from the scripts: selftest contains 10/10 attacks and passes 15/15 oracle cases; every script exits zero. These scripts execute real Docker/runc sandbox paths even where inference is stubbed. They are local regression tests, not disposable browser fixtures, and they do not verify gVisor or deployment. `piptest.py` uses fixed `/tmp/attest-piptest.db`; run it serially. `apitest.py` uses fixed `/tmp/attest-apitest.db` by default, a temporary startup runs directory, and also has test code that writes `/tmp/attest-apitest-ledger.db`; inspect/clean only those test-owned artifacts if needed, never repository evidence. Do not import `attest.server` with default storage: startup can quarantine files under its configured runs directory. No tests have been run as part of this planning pass.

## Later report

Write the evaluation report separately under `/Users/tolushekoni/.adal/engineer/tasks/attest-ui-recovery/`. Include the actual diff paths, commands and exit results, screenshots, viewport/contrast/keyboard findings, fixture POST log, console/network findings, and limitations. Mark any skipped check as unverified. This plan does not authorize implementation or release work.