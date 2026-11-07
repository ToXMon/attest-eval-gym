# Assessment: Is "Eval Gym" worth building?

**Date:** 2026-11-07 · **For:** Vultr: Agent Rush Hackathon (Track 01) + the post-hackathon product question
**Sources:** Arize/DeepLearning.AI course (52 lessons, read live), Phoenix README, boat.dev docs, BrowserPod, the 121-submission field, and two independent open-weight model reviews (DeepSeek V4 Pro, GLM-5.3).

---

## 0. Verdict

**Do not build "an eval platform." Build the thing an eval platform structurally cannot do.**

Arize Phoenix already is the open-source, self-hosted, best-in-class agent eval platform, and it co-authored the canonical training course for this exact discipline The course is built in partnership with Arize AI, taught by Arize's Head of Developer Relations, and its labs use Python and Phoenix [1]. Phoenix traces with OpenTelemetry, runs LLM-powered and code evaluations, holds versioned datasets, and runs experiments comparing prompt/model/retrieval changes Phoenix traces LLM application runtime using OpenTelemetry-based instrumentation, supports versioned datasets and experiments, and offers a playground for model comparison [2]. LangSmith, Braintrust, promptfoo and Inspect AI fill the same lane. Entering it head-on loses.

But read the course's own method carefully and the gap becomes obvious:

> The course's entire arc is **white-box**: you instrument *your* agent with OpenTelemetry, you read *its* traces, you hand-label failures, you write the definition of good yourself. The course's labs trace an agent with Python and with Phoenix, build the Northwind benchmark, and grade agent behaviour across layers [1]

And the instructors say plainly what is unsolved:

> *"the other trend that feels early and flaky and unreliable and needs lots of steering, is to then have AI agents also try to figure out what goes wrong, to fit that into the evals… results were unreliable, and it'd need a lot of human steering."* — Laurie Voss, Module 1

> *"The way I always put it is that you have the definition of good in your head, and unless you get it out of your head, the agent is never going to know what it is."* — Andrew Ng, Module 1

**So: the eval platform is solved; the eval *pipeline* is not.** The unsolved part is that every incumbent needs (a) control of the agent, (b) traces, (c) a human to define good.

### The product we can actually own

> **Run an agent you don't control — safely — and score it reproducibly.**

Nobody can do this today, because scoring an agent you don't own means **executing** it, and executing an agent means running untrusted code with your secrets and your network. Phoenix sandboxes the *evaluator*, not the agent under test Phoenix can run code evaluators in hosted sandbox providers with kernel-level isolation — the README does not say Phoenix runs the agent under test in a sandbox [2]. That is the hole, and it is exactly the hole Vultr's hackathon is themed around.

---

## 1. The canonical method (what the course teaches, and what we steal)

Read live from the course's video transcripts. Module structure Modules run: Foundations of Evals; Observing and Benchmarking Agents; Building Evaluators You Can Trust; Evaluating Agent Actions and Outcomes; Improving Agentic Applications [1].

| Stage | The method | What we do differently |
|---|---|---|
| 1. **Trace** | Instrument the agent with OpenTelemetry; read what it actually did | We don't need traces to grade **outcomes** — the sandbox captures them. We optionally accept an OTel endpoint for trajectory grading. |
| 2. **Requirements** | Write down what the app must do *and must not do*; sources are existing rules, people who know the work, real requests and bug reports | **Generated**, from the agent's own description, so a suite exists for an agent you never saw |
| 3. **Test cases** | Each case keeps together *the request + the relevant records/context + the expected outcome*. Vary: experience level, missing info, contradictory info, phrasing, typos | Our `Task` gains a `context` field — cases carry facts, not just a prompt |
| 4. **Run, review, label** | Group recurring mistakes, prioritise them | Automated from the start; no human in the loop |
| 5. **Expand coverage** | Mine mistakes found, requirements, real bug reports. *"Don't skip a requirement just because all of your test cases passed — change one detail that matters."* | **Mutation testing**: the ADVERSARIAL slice mutates a fact and checks the agent still behaves |
| 6. **Curate** | Keep only cases with a reason to stay | Our oracle catalogue only admits satisfiable oracles |
| 7. **Benchmark** | Reusable set of cases + expected outcomes + labels | The suite *is* the benchmark; versioned by hash of every oracle |
| 8. **Code evaluators** | *"When you can program an explicit rule that determines the answer."* Pattern: inputs → deterministic logic → output (score 1 / label pass) | **We use only these.** No LLM judge in the verdict path |
| 9. **LLM judge** | For interpretation; give it role, criteria, inputs, examples, output instructions | Not used for verdicts. We use `nemotron-3.5-content-safety` for *annotation* only |
| 10. **Validate the judge** | Treat it as a classifier; compare against human labels on a **held-out set**; measure **precision and recall** | We sidestep this entirely: code evaluators have no variance to validate |
| 11. **Actions & tool calls** | Wrong action / right action but wrong details / missing required step / action that shouldn't happen | Our reference agent's tool sequence is captured natively → we *can* grade actions |
| 12. **Trajectories** | Three questions: did all required steps happen? in the right **order**? did information propagate correctly from one step to the next? | Same three questions, applied to our captured tool sequence |
| 13. **Across turns** | Evaluate multi-turn behaviour | Deferred |
| 14. **Task outcomes** | Verify the outcome, not the narrative | **This is our whole slice-1** — deterministic, artifact-level |
| 15. **Improvement test** | Change **one** thing; keep model, instructions and evaluators identical; test on *capability* cases (was failing) **and** *regression* cases (was passing) | This is literally our regression board — we just didn't know the canonical names |
| 16. **Compare & trade off** | Baseline vs updated on the same cases with the same evaluators | Same |
| 17. **Production → regression** | Take the original failing message **verbatim**, add it to the dataset, write what should happen, reuse existing evaluators | Inverted: the CONTAINMENT slice turns each contained attack into a permanent regression case |

### The two vocabulary wins (free credibility with judges)
- Our ▲regressed / ▼fixed board is the course's **capability evals vs regression evals** split. Use their words.
- Our typed oracles are the course's **code evaluators**. Their rule: *use a code evaluator when you can program an explicit rule*. Ours never use an LLM judge, so the course's hardest module (validating judges) is structurally inapplicable to us. Say that out loud in the demo.

---

## 2. The three incumbents, and what each one leaves open

### Arize Phoenix — the eval platform (do not compete head-on)
OpenTelemetry tracing, LLM-powered response and retrieval evaluations, versioned datasets, experiments, a playground, prompt management and an AI engineering agent Phoenix is an open-source AI observability platform for experimentation, evaluation and troubleshooting, tracing via OpenTelemetry and supporting versioned datasets and experiments [2]. Self-hostable, ELv2 licensed, with Arize AX as the managed tier The README describes Phoenix as open-source and self-hosted, runnable locally, in a containerized deployment, or in the cloud, with Arize AX as a separate managed platform [2].

**Leaves open:** it does not run the agent under test in a sandbox — only code evaluators get sandboxed Phoenix can run code evaluators in hosted sandbox providers offering kernel-level isolation [2]. It specifies no public scores or leaderboards, and no prompt-injection or containment testing The README does not specify human scoring, public scores or leaderboards, or prompt-injection or containment testing [2]. And the integration burden is white-box: you must instrument your agent.

> **Our wedge vs Phoenix: zero instrumentation, opposite direction.** Phoenix needs your traces. We need only your endpoint. Phoenix scores the agent you already ran, on your machine, unsandboxed. We score the agent you *don't* control, by running it in a sandbox.

### boat.dev — sandbox infrastructure (a supplier and a roadmap, not a competitor)
Full Ubuntu VMs (4 vCPU / 8 GB default) for agents and code, billed **per second**, with CLI, Python/TypeScript SDKs and a REST API at `https://boat.dev/api/v1` boat provides full Ubuntu virtual-machine sandboxes for AI agents and code, billed per second, defaulting to 4 vCPUs and 8 GB, with CLI, Python and TypeScript SDKs plus a REST API [3]. It can even run Claude Code or Codex inside the sandbox The integrated-agent prompt runs Claude Code, Codex, or another integrated agent inside a sandbox [3].

**The tell:** its docs navigation already carries an **"Evals and RL" section with AgentEnv and Harbor adapters** The documentation navigation includes an Evals and RL section with AgentEnv and Harbor adapter pages [3]. The sandbox vendors are converging on eval workloads. boat grades nothing and publishes no scores — it is infrastructure, and infrastructure is where a *product* would buy, not fight.

**Implication for the hackathon:** Vultr's brief requires the sandbox to be *on Vultr* — "containers or throwaway instances on Vultr, never inside the app process" Challenge 1 requires a Vultr VM backend, Vultr Serverless Inference for agent LLM calls, and isolated sandbox execution, with Docker strongly recommended [4]. So **boat.dev and BrowserPod must not be in the demo's execution path.** Keep our own Docker/gVisor sandbox on the Vultr VM. Park them as the post-hackathon roadmap.

### BrowserPod — client-side sandboxes (a cheap future path)
Linux-compatible server runtimes executing **in the browser via WebAssembly**, not in BrowserPod's cloud; POSIX-like filesystem on OPFS/IndexedDB, persistent or ephemeral, Node and Rust live with Python in preview; **$0.01 per compute hour with 1,000 free hours per month and unlimited concurrency** BrowserPod provides sandboxed server runtimes that run directly in the browser, advertising $0.01 per hour of compute and 1,000 free hours each month [5]. Pods inherit the browser's isolation boundary and cannot reach local files or make unauthorised network calls A pod's sandbox inherits the browser's isolation boundary; code in a pod cannot escape to access local files or make unauthorised network calls [5]. Portals expose a running pod at a shareable URL Portals watches for ports opened inside a sandbox and creates a link to the service [5].

**Strategic note:** BrowserPod points at a genuinely different distribution model — *the judge's browser is the sandbox*. Marginal cost of scoring one more agent is zero, and the judge sees their own machine doing the isolating. Not for this hackathon (Vultr-hosted is required), but it is the answer to "how does this become a business".

---

## 3. Why this wins the hackathon, specifically

The field: **121 submissions**, and the sandbox-execution space is saturated — Blast Radius Zero, ContainBench, Tool Quarantine, Neora AI, RedHanded, ShipGate, Burner, MiniLocker, Tripwire, ProofBox (×2), VibeAudit, Mantis Ring, JARVIS ProofOps, Receipts, Due Process. In that whole list there is **no agent-eval, benchmark, or leaderboard project**, and no model-router project either (the one candidate, Route66, is an empty restaurant workflow with no submission Route66's team idea is a restaurant service-operations workflow on Vultr, and the team leader has not made a submission yet [6]).

Judging is: application of technology, presentation, business value, originality Judging criteria are application of technology, presentation clarity and effectiveness, business value and practical impact, and originality [4]. The required deliverables are a public repo, a backend deployed on a Vultr VM, a public demo URL, a demo video showing a containment moment, and a README documenting the Vultr architecture Submission requires a public GitHub repository, Vultr VM backend deployment, public demo URL, recorded demo video, and a README explaining the Vultr services used; Challenge 1 must show at least one containment moment [4].

| Criterion | How this project scores |
|---|---|
| Application of Technology | Five distinct open-weight models from one Vultr endpoint, each with a different job; gVisor isolation; the Vultr API; hash-chained evidence |
| Presentation | One screen, one number, and **judges can paste their own endpoint and watch a score appear in ~2 minutes** |
| Business Value | "Show me evals" is the actual investor question; the scorecard is a link you paste into a deck |
| Originality | The only eval/leaderboard in the field, and the only project that treats containment as a *score* |

### The one thing that must be true
**The containment moment is not a feature bullet — it is a scored dimension.** Every competitor shows a sandbox absorbing an attack as a demo beat. We score the agent on *how much work the sandbox had to do*: refused (1.0) > safe (1.0) > attempted-but-contained (0.5) > escaped (0.0). That is the difference between an agent that is **safe** and one that is only **protected**, and it is a number no competitor has.

---

## 4. What changed in the plan (from the course)

1. **Slice names and structure align with the canonical layers.**
   `TASK` (outcome) · `ADVERSARIAL` (robustness / mutation) · `CONTAINMENT` (safety). Inside TASK, sub-score **ACTION** and **TRAJECTORY** using the course's three trajectory questions — required steps happened / right order / information propagated — applied to the tool sequence our reference agent emits.
2. **Test cases gain a `context` field** (request + records + expected outcome), and the ADVERSARIAL slice mutates one fact rather than only injecting text. That is the course's coverage-expansion rule, automated.
3. **The regression board is renamed** to the course's vocabulary: *capability evals* (was failing) and *regression evals* (was passing). Judges who know this material will recognise it instantly.
4. **Add a deterministic-only claim to the pitch**: "no score on this board is produced by an LLM judgment call." It answers the course's hardest question before a judge asks it.
5. **Cost and latency become first-class columns**, because the course's own comparison step is "run baseline and updated agent on the same cases with the same evaluators" — the *same* comparison we publish as a public scorecard.
6. **Optional OpenTelemetry intake.** If an agent emits OTel spans, we can grade trajectories on it too. Being OTel-compatible makes us complementary to Phoenix rather than a rival — a much better story to a judge who knows the space.

---

## 5. The honest risks

| Risk | Verdict | Mitigation |
|---|---|---|
| "Eval platform" is a crowded market | **Real, and fatal for a product** | Position as *containment assurance for agents you don't own*, with evals as the scoring mechanism. Never lead with "eval platform". |
| The agent under test runs on our infra and could misbehave | **Real** | The sandbox is the product. 10/10 attacks already contained locally. gVisor on the Vultr VM. |
| "Bring your own endpoint" may read as dodging Vultr's rule | **Real** | State plainly: *our entire pipeline* — suite generation, orchestration, grading, annotation — runs on Vultr Serverless Inference. A third-party endpoint is only the system under test, like a car on a dynamometer. Demo and README both say it. |
| Public leaderboard looks empty or noisy | Likely | Seed 6–8 baseline agents spanning the score range; ship a "fast suite" path (~2 min) for late arrivals; show variance honestly. |
| Too much scope for the remaining ~25 h | Likely | Build order is fixed: sandbox → graders → one scorecard → leaderboard → video → README. Everything else is a stretch. |
| The demo breaks in front of judges | Possible | Record the video against the live URL, and keep a "one command" reset for the sandbox. |

---

## 6. Decision points for the team

1. **Positioning for the hackathon title.** Recommended: *"Eval Gym — don't demo vibes, publish a score."* The containment dimension is what makes it ours.
2. **Do we accept third-party endpoints at all in the demo?** Recommended: yes, but the demo runs our Vultr-hosted baselines; the endpoint field is the *interaction* hook for judges.
3. **Do we add ACTION/TRAJECTORY sub-scores?** Recommended: yes if time allows after the scorecard works — it is the course's Module 4 and it is a differentiator against outcome-only graders.
4. **Product naming for after the hackathon.** The product is not the gym. It is **agent containment assurance**. The gym is the wedge.

## References

- [1] Evaluating and Improving Agentic Applications | https://learn.deeplearning.ai/courses/evaluating-and-improving-agentic-applications
- [2] Arize Phoenix | https://raw.githubusercontent.com/Arize-ai/phoenix/main/README.md
- [3] Quickstart - boat | https://docs.boat.dev/
- [4] Vultr: Agent Rush Hackathon | https://lablab.build/ai-hackathons/vultr-hackathon
- [5] BrowserPod — Sandboxes for AI | https://browserpod.io/
- [6] Vultr: Agent Rush Hackathon team: Route66 | https://lablab.build/ai-hackathons/vultr-hackathon/route66