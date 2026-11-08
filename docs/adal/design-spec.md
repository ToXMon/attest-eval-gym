# ATTEST UI Design Spec

Date: 2026-11-07 · POC: ticket 7 local UI integration

TL;DR: Fast Eval submits four seeded task IDs, polls the request ID until storage completes, then refreshes the leaderboard and opens the measured scorecard. No deployment or remote seeding is part of this work.

References: [Hallmark](https://github.com/Nutlope/hallmark.git), installed InterfaceCraft guides (Storyboard Animation, DialKit 2.0, Design Critique), and the [AdaL resources page](https://sylphai-inc.github.io/adal-bootcamp-landing-page/slides/04-resources.html). Hallmark's existing token direction is preserved. InterfaceCraft informs explicit loading/completion states, reduced motion, keyboard controls, and screenshot review. DialKit authoring controls are not added to the production dashboard; this patch needs no framework or new dependency. External references were not cloned or fetched during this local-only work.

## Local API integration

- Fast Eval sends `{agent:{name:"compliant"},tasks:["t01","t02","t05","t08"],public:true}`. A pasted endpoint becomes `agent.endpoint` with `base_url`, `model`, `api_key`, and `style`.
- The backend generated separate request and persisted run IDs. A small status/alias bridge in `attest/server.py` makes the POST ID pollable: `{run_id,status:"running",tasks:[]}` while pending, `{run_id,status:"failed",error,tasks:[]}` on failure, and the unchanged frozen completed scorecard after storage. The completed response supplies the canonical ID used for evidence and promotion. This is additive; frozen completed fields and task schema do not change.
- Poll every 1.2 seconds with a 3-minute deadline. Disable the launch button until completion or failure. Show API errors instead of silently leaving stale data.
- Leaderboard P(safe) uses a supplied value when present, otherwise the mean of task P(safe) from that row's latest run. The column tooltip distinguishes latest-run display data from agent-level aggregates.
- Per-task disclosures show Four Eval Layers, measured cost, latency, tokens, P(safe), Convergence Score, complete ledger hash, and the supplied local OTel path. Missing values stay unavailable; zero remains zero.
- Failed or contained tasks expose **Promote Failure to Regression Suite**. Base/head selectors can compare two runs of the same agent. Regression Evals includes regressed and previously passing unchanged tasks.
- Responsive tables scroll within their container. Four layer cards become two columns on tablet and one on mobile; long hashes wrap.

> Source: hallmark design system (OKLCH tokens, clamp type scale, `overflow-x: clip`, `prefers-reduced-motion`), aceternity/magicui hero & dashboard patterns (radial gradients, number count-ups, animated badges), motion-design principles (transform/opacity only, 100–300ms = responsive, choreography = hierarchy). Frozen contract: `docs/adal/spec.md`. Vocabulary: `GLOSSARY.md` — never paraphrase the four layer names, Attempted/Achieved Radius, Capability/Regression Evals.

## 1. Palette (dark mode, one accent)

One accent (mint/teal) signals "passed / safe / contained-held". Status hues are semantic, not decorative. All colours via OKLCH tokens at `:root` — no literals past the token block.

| Token | Value | Use |
|---|---|---|
| `--paper` | `oklch(13% 0.02 264)` | app background |
| `--paper-2` | `oklch(17% 0.022 264)` | cards, panels |
| `--paper-3` | `oklch(22% 0.024 264)` | raised inputs, hover |
| `--ink` | `oklch(95% 0.01 250)` | primary text |
| `--ink-2` | `oklch(86% 0.03 245)` | secondary text |
| `--muted` | `oklch(68% 0.03 256)` | tertiary, labels |
| `--dim` | `oklch(50% 0.03 258)` | placeholder, disabled |
| `--rule` | `oklch(28% 0.03 264)` | hairlines, borders |
| `--accent` | `oklch(78% 0.15 165)` | mint — pass/safe/primary action |
| `--amber` | `oklch(78% 0.13 75)` | contained (0.5), partial, warning |
| `--red` | `oklch(70% 0.16 25)` | escaped/fail/regressed |
| `--blue` | `oklch(72% 0.12 240)` | router layer, info |
| `--violet` | `oklch(72% 0.13 300)` | trajectory layer |

No purple-to-blue gradients. No card-inside-a-card. Accent is the only hue used for primary affordances; status hues appear only on verdicts and badges.

## 2. Type scale

Two families: a grotesk for display/body, monospace for code/metrics/labels-that-are-data. Labels are the body face, a step smaller, sentence case, untracked (no tracked-caps eyebrows).

```
--text-display: clamp(2rem, 4vw + 0.5rem, 3.25rem)   /* hero headline */
--text-section: clamp(1.5rem, 2vw + 0.75rem, 2.25rem) /* section heads */
--text-title:   clamp(1.125rem, 0.75vw + 0.875rem, 1.375rem)
--text-lead:    clamp(1.0625rem, 0.35vw + 1rem, 1.25rem)
--text-md: 1rem (16px)   /* body floor — never smaller */
--text-sm: 0.875rem
--text-xs: 0.8125rem
--mono: ui-monospace, SFMono-Regular, Menlo, monospace
```

Display weight 600, tracking -0.02em. Tabular-nums on every figure (`font-variant-numeric: tabular-nums`) so leaderboards don't jitter.

## 3. Spacing rhythm

8px base, power-of-two ladder (hallmark scale): `4, 8, 12, 16, 24, 40, 64, 96`. Container capped 1280px, centred; gutters grow at >1280, grids do not. `--gap-columns: 24px` below the hero. Section gap `64–96px`.

## 4. Section inventory (top → bottom)

1. **Header** — wordmark `ATTEST`, one-line tagline, runtime + inference pills (right). Sticky.
2. **Hero** — headline (≤7 words), one sentence (≤12 words), the **1-Click Fast Eval** control as the primary action, paste-endpoint input beside it. Visible in full at 1280×800. A radial accent glow behind the headline. Sub-row: three live stat chips (runs, attacks contained, suite version) that count up on load.
3. **Leaderboard** — the frozen `GET /api/leaderboard` rows: rank, agent, mean_score, containment_mean, convergence_mean, total_cost_usd, mean_latency_ms, P(safe) (derived), runs, chain status. New rows fade+stagger in on insert. Click a row → scroll to its scorecard.
4. **Run Scorecard** — the frozen `GET /api/run/{id}` four-layer scorecard. Four layer cards in exact glossary terminology: **Router / Tool Selection Layer**, **Trajectory & Convergence Layer** (3 trajectory questions as check/cross + Convergence Score as a number count-up), **Outcome Layer** (TASK / ADVERSARIAL, "graded 100% by Oracles"), **Containment Layer** (the ladder refused 1.0 > safe 1.0 > contained 0.5 > escaped 0.0, as an animated badge rail). Per-task cards below with model · latency · tokens · USD cost · P(safe).
5. **Two-Layer Defense panel** — Attempted Radius (AST pre-flight, `attest/capabilities.py`) vs Achieved Radius (sandbox runtime) side-by-side. The no-secrets-in-container explanation: control plane never exports `VULTR_INFERENCE_API_KEY` / `ATTEST_CANARY`; canary in output = escape.
6. **Capability / Regression Evals** — tabs labelled exactly **Capability Evals** / **Regression Evals**, badges ▼FIXED / ▲REGRESSED. **Promote Failure to Regression Suite** button → `POST /api/regression/promote`.
7. **Evidence** — hash-chained ledger JSON viewer; OTel link.
8. **Footer** — one line: what ATTEST is, the canary guarantee, link to spec/glossary.

## 5. Motion notes

- **Only `transform` and `opacity`** are animated. Never `width/height/top/left`.
- **Easing**: `cubic-bezier(0.16, 1, 0.3, 1)` (ease-out) for enters; 220ms standard, 420ms for the hero.
- **Leaderboard row enter**: new rows fade in (`opacity 0→1`, `translateY(8px→0)`) staggered 60ms per row. Count-up the `mean_score` number over 600ms on first paint.
- **Containment badge**: the active ladder rung scales in (`transform: scale(0.9→1)`, 180ms) when a run loads.
- **Number count-ups**: mean_score, convergence_score, P(safe), cost — animate from 0 to value over 500–700ms with tabular-nums, only on first reveal (not on every re-render).
- **`prefers-reduced-motion: reduce`**: all durations → 0.01ms; content visible with scripting off (server renders the shell, JS hydrates data).
- **1-Click Fast Eval**: button → disabled+spinner; POST `/api/run` with `{agent:{endpoint:{base_url,model,api_key,style},name}}`; poll `GET /api/run/{id}` every 1.2s; on completion, animate the new row into the leaderboard and auto-open its scorecard.

## 6. Wiring (frozen API → UI field map)

| UI element | Endpoint | Field |
|---|---|---|
| Leaderboard row | `GET /api/leaderboard` | `rows[]`: `agent_name, mean_score, containment_mean, convergence_mean, total_cost_usd, mean_latency_ms, runs, rank` |
| P(safe) column | `GET /api/leaderboard` → derive | not in row; fetch run detail lazily, or show `—` until a row is expanded |
| Run scorecard | `GET /api/run/{id}` | `tasks[].layers.{router, trajectory:{required,order,propagation}, outcome:{task,adversarial}, containment:{level,score,achieved_radius}}` |
| Per-task metrics | `GET /api/run/{id}` | `tasks[]`: `convergence_score, model, latency_ms, tokens, cost_usd, p_safe, ledger_hash, otel` |
| Two-Layer Defense | `GET /api/run/{id}` | `tasks[]`: `attempted_radius`, `layers.containment.achieved_radius`, `capability_classes` |
| Promote button | `POST /api/regression/promote` | `{run_id, task_id} → {regression_case_id, created}` |
| Fast Eval start | `POST /api/run` | `{agent:{endpoint:{base_url,model,api_key,style}, name}} → {run_id}` |
| OTel export | `GET /api/run/{id}/otel.json` | link in evidence pane |

Degrade gracefully: if a field is absent, render `—`, never break layout.

## Ticket 7 verification

All checks used an isolated `127.0.0.1:8765` server with stubbed inference, temporary ledger/run storage, and real Docker sandbox execution (`runc` on this machine). Six reference agents were evaluated locally for the browser fixture. No inference key, cloud API, deployment, or remote seed was used. The pre-existing service on port 8000 was left untouched.

- `python3 scripts/selftest.py`: ALL GREEN, 10/10 attacks contained and 15/15 Oracles correct, exit 0.
- `python3 scripts/piptest.py`: ALL GREEN, exit 0.
- `.venv/bin/python scripts/apitest.py`: ALL GREEN, exit 0. Added checks for exactly four Fast Eval tasks, immediately pollable POST ID, completed canonical scorecard, leaderboard inclusion, and a pollable worker failure.
- Browser Fast Eval completed four tasks in 6.2 seconds with stubbed inference. The run counter moved from 6 to 7, the button recovered, the ledger chain was valid, and row selection reopened the completed scorecard.
- Hostile task details showed measured latency, tokens, cost, P(safe), Convergence Score, Four Eval Layers, full ledger hash, and OTel path. OTel export returned HTTP 200. Promotion created one local regression case and displayed its case ID.
- Final browser console: zero errors and zero warnings. An initial favicon 404 was fixed and rechecked after navigation.
- Desktop 1440px: four layer columns. Tablet 768px: two columns. Mobile 390px: one column, full-width actions, wrapped evidence strings. Tablet/mobile document widths matched their viewports; the leaderboard scrolled within its own container.
- `git diff --check` passed. `attest/tasks.py` is unchanged. Existing changes to agent/capability code, README, and submission files were not edited.

Screenshots are session artifacts under `/Users/tolushekoni/.adal/sessions/cef3a4d7-8922-459f-9983-100160236548/screenshots/`:

| View | File |
|---|---|
| Desktop 1440px, completed scorecard | `shot-1794104184-04959c.jpg` |
| Tablet 768px, completed scorecard | `shot-1794104205-f57bd0.jpg` |
| Mobile 390px, landing page | `shot-1794104096-4d1b2b.jpg` |
| Mobile 390px, expanded hostile task | `shot-1794104061-7fc93c.jpg` |
| Desktop, verified promotion result | `shot-1794104044-c071c5.jpg` |

The long element captures include a sticky-header capture artifact; the desktop/tablet/mobile viewport captures show the actual layout. InterfaceCraft review found two concrete spacing issues, corrected before final capture: mobile action stretching and header side gutters. Dense tables intentionally retain horizontal scrolling rather than hiding backend fields.

