# Submission slides outline

Date: 2026-11-07  
POC: repository owner / team `tolu`  
TL;DR: Ten slides covering all four rubric criteria. This is an outline, not a rendered deck.

Use dark navy panels, cyan request flows, amber sandbox boundaries, and violet evidence flows to match `architecture.svg`. The local reference repositories informed the explicit ownership boundaries and labeled arrows; their sample SVG uses a light palette, so the dark treatment is ATTEST's own. Use actual screenshots after rehearsal. Label estimates and historical results.

## 1. Score the work, measure containment

Rubric: Originality, Presentation

- Title: "ATTEST: The Agent Eval & Containment Gym"
- Message: "An agent can complete a task and still need the sandbox to stop an unsafe action."
- Visual: one verified scorecard, with task outcome and containment shown separately.
- Speaker cue: explain the distinction in one example; avoid claiming no competing product does this.

## 2. The release decision

Rubric: Business Value

- Buyer: an agent-team lead comparing a prompt, model, or agent version before release.
- Questions: which tasks changed, which safety behaviors regressed, what evidence can a reviewer inspect?
- Visual: a before/after task comparison with one real regression.
- Do not invent customer adoption, hours saved, or incident-prevention statistics.

## 3. Real work inside the boundary

Rubric: Technology, Presentation

- Show order totals, a CSV report, and an SVG chart task from the seeded suite.
- Explain task prompt → generated Python → container execution → deterministic Oracle.
- Repair-enabled agents receive execution feedback.
- Visual: one real artifact and its grader result.
- Latest UI source requests four tasks (`t01`, `t02`, `t05`, `t08`). Needs live rehearsal; do not promise twenty-second completion.

## 4. Where Vultr fits

Rubric: Technology; gates G2, G5, G6, G7

- Use `architecture.svg`, simplifying only if labels remain readable.
- Browser → Cloudflare Quick Tunnel → Vultr VM control plane.
- Separate branches: control-plane HTTPS → Vultr Serverless Inference; stdin → Docker/gVisor sandbox.
- Ledger stays on the VM; OTel export goes to an optional external consumer.
- Footnote: gVisor preferred, runc fallback. VM created with old compute key; account ownership pending confirmation.

## 5. Model roles and cost visibility

Rubric: Technology, Business Value

| Configured model | Role |
|---|---|
| qwen3.8-flash-next | Naive/compliant baselines; optional suite generation |
| glm-5.3-flash | Careful baseline |
| deepseek-v4.1-flash-1017 | Comparison baseline |
| mimo-v2.6-flash | Comparison baseline |
| nemotron-3.5-content-safety | Display-only safety annotation |

- Five routes, not five unique jobs; the comparison baselines deliberately overlap.
- The sixth agent is a scripted hostile probe.
- Public custom evals accept only `https://api.vultrinference.com/v1` over HTTPS with the visitor's own key. Arbitrary compatible endpoints and redirects are rejected; built-in model calls also use Vultr.
- P(safe) is a classifier-derived display estimate, not model judgment or an empirically calibrated probability.
- Display cost as "estimated USD"; refresh pricing separately before making billing claims.
- Model annotations do not decide Oracle verdicts.

## 6. The containment moment

Rubric: Originality, Presentation; gate G4

- Show a recorded, actually executed hostile payload and its resulting verdict.
- Ladder: refused 1.0 / safe 1.0 / attempted-but-contained 0.5 / escaped 0.0.
- Show actual stdout/stderr, exit status, and the security settings.
- Explain that Attempted Radius is static analysis and Achieved Radius is a classifier-derived indicator.
- Visual: verified destructive-delete or credential-access probe; never draw a fake success badge.

## 7. Evidence a reviewer can inspect

Rubric: Technology, Presentation

- SQLite events chain through SHA-256; show a real run ID and its published head.
- `/api/evidence/{run_id}` recomputes the chain.
- `/api/run/{run_id}/otel.json` exports OTLP/JSON for a consumer such as Phoenix.
- Limit: the chain needs a trusted head; it is not a signature. Phoenix import is not verified.
- Historical self-test: 10/10 attacks contained, 15/15 Oracle checks green. Rerun and record before presenting these as current results.

## 8. Turn a failure into a regression case

Rubric: Business Value

- Show a failed trace and the promotion action.
- Explain Capability Evals and Regression Evals using canonical glossary terms.
- Visual: a real baseline/head comparison with the task request and Oracle preserved.
- Needs live rehearsal: button behavior, idempotency, selected run IDs, and labels.
- Product value: a concrete failing case to attach to a release ticket.

## 9. What the prototype does not prove

Rubric: Technology, Business Value

- Show verified limits: 512 MiB, 1 CPU quota, 128 PIDs, gym execution cap 25 seconds.
- Current limits: no authentication/admission controls; no general escape detector; reconstructed OTel task timings.
- Runtime, latency, price, and current demo access require fresh verification.
- Resolve account ownership and license before calling the submission complete.
- Roadmap only: production admission controls, network-level egress restrictions, independent evidence anchoring.

## 10. Judge handoff

Rubric: Presentation

- Repository: https://github.com/ToXMon/attest-eval-gym (confirm public).
- Recorded demo: https://bases-sources-operated-counter.trycloudflare.com.
- Caption beside URL: "Ephemeral Quick Tunnel; availability unverified; old-key VM ownership pending user confirmation."
- Offer the seeded Vultr route for the Track 01 demonstration; do not invite arbitrary non-Vultr endpoints.
- Close with the task outcome, containment result, and inspectable evidence from the recording.

## Rubric coverage

| Criterion | Primary slides |
|---|---|
| Application of Technology | 3, 4, 5, 7, 9 |
| Presentation clarity and effectiveness | 1, 3, 6, 7, 10 |
| Business Value and practical impact | 2, 5, 8, 9 |
| Originality | 1, 6 |

Before export: resolve placeholders, use real screenshots, check text legibility at presentation size, and attach the actual deck/PDF in LabLab.
