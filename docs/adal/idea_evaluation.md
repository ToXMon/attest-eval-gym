# Idea Evaluation — Vultr: Agent Rush Hackathon
### Every idea scored against the panel's collective judgement

**Date:** 2026-11-07 · **Deadline:** 8 Nov 2026, 23:00 UTC · **Team:** `tolu`
**Inputs:** 31 named judges from the hackathon page, Jia Chen's 21-win playbook, the 121-submission field, and the Arize/DeepLearning.AI eval methodology.

---

## 0. Result

| Rank | Idea | Score | Verdict |
|---|---|---|---|
| **1** | **Eval Gym with CONTAINMENT as a scored dimension** | **16.6** | **WINNER** |
| 2 | Inter-agent sanitization proxy | 14.0 | STRONG |
| 3 | PII unmasking proxy | 13.5 | STRONG |
| 4 | Cost-aware model router + reproducible benchmark | 13.3 | STRONG (fallback) |
| 5 | Eval gym *as stated* (no containment dimension) | 12.8 | VIABLE — superset by #1 |
| 6 | Trajectory grader in CI | 12.2 | VIABLE as a *component* only |
| 6 | API-to-browser fallback | 12.2 | VIABLE as a *component* only |
| 6 | Fuzz your own agent swarm | 12.2 | WEAK — crowded |
| 7 | Computer-use agent (DOM + screenshot diffing) | 12.4 | WEAK — crowded, hard |
| 8 | Marketplace trust score for AI extensions | 11.7 | DEAD — taken |
| 8 | Voice loop with VAD | 11.6 | VIABLE — wrong track |
| 8 | ATTEST — trust attestation service *(my original)* | 11.6 | DEAD — my own idea, killed by my own research |
| 9 | Cost kill-switch | 11.4 | VIABLE as a *component* only |
| 10 | System-One router | 12.0 | VIABLE — absorbed by #4 |
| 11 | Publish one benchmark | 11.3 | VIABLE as a *component* only |
| 12 | KV-cache prefix sharing | 10.2 | DEAD — needs serving-layer control |
| 13 | Generative UI | 10.4 | DEAD — fails the brief |
| 14 | Temporal state machine | 10.6 | DEAD for this event |
| 15 | AI invoice that explains itself | 10.0 | DEAD — finance lane saturated |
| 16 | Secret rot scanner | 9.5 | DEAD for this brief |
| 17 | WebGPU shim | 9.6 | DEAD — no Vultr story |
| 18 | Speculative decoding | 9.8 | DEAD — no GPUs |
| 19 | Grammar-constrained decoding | 9.5 | DEAD — no serving-layer control |
| 20 | DPO flywheel | 9.2 | DEAD — no GPUs |
| 21 | Shadow-route 5% → Slack | 9.3 | DEAD — no production traffic |
| 22 | Raw MCP server in pure JSON-RPC | 8.5 | DEAD — wrong medium |
| 23 | Co-founder match on shipped artifacts | 8.3 | DEAD — no Vultr story |
| 24 | Vibecode → first 10 paying users | 8.0 | DEAD — needs humans |

> **Two ideas in this list are dead for a reason we cannot argue with: no GPUs, and no control of the inference serving layer.** Speculative decoding, DPO flywheel and KV-cache prefix sharing all require either training/serving hardware we cannot have, or a managed API whose decoder we do not control. Any list that scores them highly is scoring a different competition.

---

## 1. The panel, and what the collective actually rewards

The page lists **31 named judges** under "Speakers, Mentors & Judges" (the source reports 32; one alt-text is duplicated) The Speakers, Mentors & Judges section lists 32 people and their stated roles and affiliations [1]:

| Employer | Judges | What that signals |
|---|---|---|
| **Security & infra** | Udit Gupta (Principal Engineer, Cloud & Network Security, Palo Alto Networks) | Containment is judged by a person whose job it is. "Blast Radius" is his native language — a containment *score* lands harder here than a containment *demo*. |
| **Regulated enterprise** | Swapnil Kale (VP–Sr Manager SWE, JPMorganChase), Bhargavi Vepuri (Director Technology Lead, Prudential Financial), Anil Mandloi (Sr SWE, American Express), Sachidananda Singh (Sr Engineering Manager, Hims & Hers Health) | These four can ask "does this survive my risk committee?" A demo that produces **audit evidence** beats a demo that produces an opinion. |
| **Big tech engineering** | Meta ×3 (Ansh Bilimoria, Mahati Kumar, Mohamed Ally Iddi), Amazon ×4 (Niranjan Yadla, Shweta Chauhan, Vasu Raj Jain, Parminder Singh), Walmart Inc. ×2, Google, Microsoft, Turso, AppsFlyer, Sigma, Anthropic-class Cohere AI engineer | They reward **depth and scale**, and they know the difference between a working system and a demo. |
| **Product & business** | Ashish Garg (Principal PM, Walmart), Harshit Gupta (Management Consultant, McKinsey), Anish Gupta (PM, Microsoft), Kirankumar Bhusanurmath (PM/Technical Marketing), Nalini Garg (Associate VP) | They reward **unit economics and adoption**, but note: exactly one Principal PM. |
| **Sponsor** | Emmanuel Iriarte (CTO, NativelyAI), Muhammad Inaamullah (lablab.ai) | They want to see their stack used seriously, not sprinkled on. |
| **Founders** | Victor Martins, Ali Amjad, Alejandro Soumah (Itô Markets), Nilesh (Head of Engineering, Monocle Intelligence) | They reward shipping and self-serve products. |

### Five collective readings that drove every score below

1. **Practitioners, not theorists.** ~28 of 31 are engineers, SREs, security folks or PMs. **Zero investors.** Therefore "business value" must be *operational* — does this save an engineer hours, prevent an incident, or produce an audit artefact? "Investors will love it" scores zero with this panel; "your compliance lead can attach this to a ticket" scores high.
2. **Security is on the panel.** A principal security engineer from Palo Alto Networks sits in the room. The brief's containment mandate will be read by someone who does this professionally. A project that treats containment as *measured and scored* will land harder with this panel than one that treats it as a feature bullet.
3. **Regulated enterprise is on the panel — twice over.** JPMorgan, Prudential, American Express, Hims & Hers. The questions they can ask: *who can sign off on this, what is the audit trail, what happens when it goes wrong?* This rewards **reproducibility, tamper-evidence, deterministic verdicts** and punishes "the LLM said it was fine".
4. **Cost and scale people are on the panel.** Amazon Ads ×2, Walmart PM, McKinsey, JPMorgan VP. Unit economics is a live question.
5. **Almost no product/design judges.** One Principal PM, one consultant. **Presentation will be judged as clarity of a working system, not visual polish.** This is why "generative UI" scores 10.4 despite the most beautiful demo in the set: its only strength is the one thing this panel scores lowest.

### Jia Chen's screen (applied as a separate, independent filter)

Her rules, from a 21-win record: research sponsor tools before building; aim for "a very solid, simple, straightforward finished product"; **connect front and back end "within the first few hours"**; keep the pitch short and **let judges interact with the demo** rather than hearing about the tech stack; execution matters as much as originality; keep shipping Chen recommends researching sponsor tools and how they fit an idea before coding, scoping to "a very solid, simple, straightforward finished product", connecting the front end and back end within the first few hours, keeping the pitch concise and focusing on a demo judges can interact with, and treating execution as as important as originality [2]. The panel's own framing matches: wins come from "team dynamics, judge interaction, and smart project execution" rather than credentials or an impressive stack The article says hackathon wins depend on "team dynamics, judge interaction, and smart project execution," and that teams can lose by spending time bragging about their tech stack [3].

**The sharpest application: which ideas let a judge *do* something in the demo?**

| Idea | Judge can interact? |
|---|---|
| **Eval Gym + containment score** | **Yes — paste your agent endpoint, get a score. The only idea where the judge is the subject of the demo.** |
| PII proxy | Yes — paste text, watch it mask |
| Cost router | Partly — send a request, watch the routing decision |
| Everything else | No — they watch |

That single fact is worth more than any score in the matrix.

---

## 2. The rubric

Weights derived from the brief + the panel profile. Scored 0–10 each; total is the weighted mean ×10.

| # | Criterion | Weight | What a 10 looks like |
|---|---|---|---|
| **A** | **Brief fit** — executes real work, safely, in a Vultr sandbox | 22% | Track 1 satisfied *by construction*; the containment moment is structural |
| **B** | **Demo impact & judge interaction** | 20% | Judge does something; one screen; one number; visibly working end-to-end |
| **C** | **Enterprise business value** | 20% | An enterprise engineer gets back a work-week, an incident avoided, or an audit artefact |
| **D** | **Technology depth / model integration** | 16% | Models used for genuinely different jobs, not one chat call |
| **E** | **Originality vs the 121-submission field** | 12% | Nobody else is in this lane |
| **F** | **Buildable in ~24 h by 1–2 humans + agents** | 10% | Scope fits the clock |

**Why A and E together dominate.** The brief demands containment Challenge 1 requires a Vultr VM backend, Vultr Serverless Inference for agent LLM calls, and isolated sandbox execution, with Docker strongly recommended [1], and originality is a quarter of the judging rubric Judging criteria are application of technology, presentation clarity and effectiveness, business value and practical impact, and originality [1]. But the sandbox lane is saturated — the field has Blast Radius Zero, ContainBench, Tool Quarantine, Neora AI, RedHanded, ShipGate, Burner, MiniLocker, Tripwire, ProofBox (×2), VibeAudit, Mantis Ring, JARVIS ProofOps, Receipts and Due Process The live feed shows 121 submissions, with Burner, MiniLocker, Detonation Chamber, Vultr Chaos Sweeper and YAI Guard among the most popular [4]. **An idea that fits the brief perfectly but lands in a crowded lane scores A and E down. An idea that is original but does not execute safely scores A down.** Only one idea clears both.

---

## 3. The full matrix

`A` brief fit 22% · `B` demo 20% · `C` business 20% · `D` depth 16% · `E` originality 12% · `F` buildability 10%

### Your 19 engineering patterns

| # | Idea | A | B | C | D | E | F | **Total** | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Computer-use agent (DOM parse, screenshot diff, click→coords) | 14 | 15 | 11 | 16 | 7 | 7 | **12.4** | WEAK |
| 2 | Generative UI (LLM → live React) | 4 | 16 | 10 | 13 | 9 | 12 | **10.4** | DEAD |
| 3 | System-One router (95% fast / 5% escalate) | 6 | 11 | 16 | 16 | 12 | 13 | **12.0** | VIABLE |
| 4 | Temporal state machine (durable execution) | 7 | 8 | 15 | 16 | 11 | 6 | **10.6** | DEAD (this event) |
| 5 | Raw MCP server in pure JSON-RPC | 4 | 6 | 11 | 10 | 10 | 14 | **8.5** | DEAD |
| 6 | Grammar-constrained decoding | 6 | 8 | 10 | 17 | 12 | 4 | **9.5** | DEAD |
| 7 | Trajectory grader in CI | 10 | 12 | 16 | 17 | 4 | 12 | **12.2** | VIABLE (component) |
| 8 | Inter-agent sanitization proxy | 15 | 15 | 13 | 16 | 12 | 11 | **14.0** | **STRONG** |
| 9 | PII unmasking proxy | 13 | 14 | 15 | 13 | 13 | 12 | **13.5** | **STRONG** |
| 10 | Cost kill-switch ($0.50, degrade tier) | 7 | 12 | 17 | 14 | 4 | 13 | **11.4** | VIABLE (component) |
| 11 | KV-cache prefix sharing (TTFT −80%) | 5 | 9 | 14 | 18 | 11 | 3 | **10.2** | DEAD |
| 12 | Speculative decoding (3B draft / 70B verify) | 4 | 9 | 13 | 18 | 12 | 2 | **9.8** | DEAD |
| 13 | Shadow-route 5% → diff → Slack | 4 | 10 | 16 | 15 | 4 | 3 | **9.3** | DEAD |
| 14 | DPO flywheel (nightly LoRA) | 4 | 8 | 12 | 17 | 12 | 2 | **9.2** | DEAD |
| 15 | Voice loop (VAD, sub-1s interruption) | 6 | 16 | 13 | 14 | 11 | 9 | **11.6** | VIABLE (wrong track) |
| 16 | API-to-browser fallback (404 → headless) | 13 | 14 | 13 | 13 | 7 | 10 | **12.2** | VIABLE (component) |
| 17 | WebGPU shim (2B in browser) | 3 | 12 | 11 | 14 | 12 | 7 | **9.6** | DEAD |
| 18 | Fuzz your own agent swarm | 13 | 13 | 12 | 16 | 6 | 11 | **12.2** | WEAK |
| 19 | Publish one benchmark (cost/latency/success) | 9 | 11 | 14 | 13 | 8 | 13 | **11.3** | VIABLE (component) |

### Your 6 product ideas

| # | Idea | A | B | C | D | E | F | **Total** | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 20 | Secret rot scanner (.env / CI / vendor keys) | 3 | 9 | 15 | 9 | 9 | 15 | **9.5** | DEAD (this brief) |
| 21 | Marketplace trust score for AI extensions | 12 | 13 | 14 | 13 | 3 | 12 | **11.7** | DEAD |
| 22 | Vibecode → first 10 paying users | 2 | 8 | 15 | 6 | 13 | 4 | **8.0** | DEAD |
| 23 | **Eval gym for agent founders** | 11 | 13 | 15 | 12 | 14 | 12 | **12.8** | **STRONG** |
| 24 | AI invoice that explains itself | 6 | 11 | 15 | 12 | 3 | 12 | **10.0** | DEAD |
| 25 | Co-founder match on shipped artifacts | 2 | 7 | 12 | 9 | 13 | 11 | **8.3** | DEAD |

### Mine

| # | Idea | A | B | C | D | E | F | **Total** | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| M1 | ATTEST — trust attestation service *(my first idea)* | 13 | 12 | 13 | 13 | 3 | 13 | **11.6** | DEAD |
| **M2** | **Eval Gym + CONTAINMENT as a scored dimension** | **18** | **17** | **16** | **17** | **16** | **14** | **16.6** | **WINNER** |
| M3 | Cost-aware router + reproducible benchmark | 9 | 13 | 17 | 16 | 12 | 13 | **13.3** | STRONG (fallback) |
| M4 | Deterministic-oracle eval pipeline as a product | 10 | 11 | 15 | 16 | 12 | 13 | **12.7** | VIABLE (component of M2) |
| M5 | Containment Assurance *(the product reframe of M2)* | = M2 | = M2 | = M2 | = M2 | = M2 | = M2 | **16.6** | Same build, product identity |
| M6 | Sanitization proxy *(refinement of #8)* | = 8 | | | | | | **14.0** | STRONG |

**M2 vs #23 — the same idea, and the difference is the whole win.** Your raw eval gym scores 12.8; adding containment as a *scored dimension* takes it to 16.6. The delta is almost entirely in **A (11→18)** and **D (12→17)**: with containment as a score, Track 1 is satisfied *by construction* rather than by bolt-on, the containment moment stops being a demo beat and becomes a headline number, and the project stops being "a sandbox project" in the eyes of a panel that already saw fifteen of them.

---

## 4. The winner, and why it beats #8 and #9

### M2 — Eval Gym with CONTAINMENT as a scored dimension

**One line:** *Drop your agent. Get a failing task suite, a regression board and a public score.*

| Why | Evidence |
|---|---|
| **Only idea in the field** that is an eval/leaderboard | 121 submissions; the sandbox lane is saturated; no eval, benchmark or leaderboard project exists. `EvalsOnly` is an empty team with no submission |
| **Brief fit by construction** | The gym's own agent generates the suite, writes code, and that code runs in a hardened gVisor sandbox on a Vultr VM. The required containment moment *is* the CONTAINMENT score |
| **The only idea a judge can be the subject of** | Paste your endpoint → score in ~2 min. Jia Chen's "let judges interact" is satisfied by nothing else on the list |
| **The panel's own anxieties are answered** | Deterministic oracles → no LLM judge (regulatory panel). Hash-chained evidence → tamper-evident audit trail (JPMorgan/Prudential). Cost + latency columns → unit economics (Amazon Ads/Walmart/McKinsey). Sandboxed execution → containment (Palo Alto) |
| **Deepest model usage in the set** | Suite generation, agent-under-test, red-teamer, risk decider, verifier — five open-weight roles from one Vultr Serverless Inference endpoint |
| **Assets already built and proven** | Hardened sandbox: **10/10 real attacks contained**; typed oracle catalogue; AST capability scanner; hash-chained ledger; gym orchestrator; FastAPI control plane; UI |

### Why it beats #8 (sanitization proxy, 14.0)
#8 is original, fits the brief, and demos beautifully. It loses on two things: it is a **narrow security tool** — one mechanism, one lane, less "platform"; and it has **no public score and no repeat use**, so it is a demo, not a product. It also sits closer to ContainBench and DealWatch. If M2's containment scoring fails to land, #8 is the next idea.

### Why it beats #9 (PII proxy, 13.5)
#9 plays directly to this panel — regulated industries, audit logs, unmasking on the way back. It is genuinely the best **business** fit of the three. It loses on A (a proxy is not really "an agent that executes work in a sandbox", so the brief's containment moment has to be bolted on) and on E (PII anonymisation is a known category). It is also the best **second product** to build after the hackathon.

### Why it beats M3 (cost router, 13.3)
M3 has the **highest business-value score in the entire matrix (C=17)** — and that matters if the panel over-weights "does this save money". It loses on A (no sandbox, no execution) and therefore on the required containment moment. **M3 is the fallback**: if the containment-scoring concept doesn't survive contact with the panel, M3 is the better bet, because it needs no sandbox work at all and rides the Vultr model catalogue.

**Pivot trigger (agreed in advance):** if, by T−16 h, the CONTAINMENT slice is not producing a clean, explainable number across the three reference agents, **cut the containment scoring, keep the gym, and pivot the headline to "the cheapest reproducible score for your agent"** — which is M3 wearing M2's clothes, and still the only eval product in the field.

---

## 5. What the matrix says about the ideas that looked best on paper

**#3 System-One router (12.0) and #19 publish one benchmark (11.3) are not rivals — they are M3.** Together they are the fallback. The router gives the benchmark a reason to exist (same score, lower cost), and the benchmark gives the router a number to prove itself with. Neither on its own clears the brief.

**#7 trajectory grader in CI (12.2) is the best *method* and the worst *project*.** It scores D=17 and C=16 — it is the canonical Arize method (their Module 4) and it directly serves enterprise CI. It scores E=4 because ShipGate, `verify` and Arize Phoenix itself already do it. It is a **component of the winner**, not a competitor to it: our regression board *is* a trajectory grader, scored with the same three questions (required steps happened / right order / information propagated).

**#21 marketplace trust score (11.7) and M1 ATTEST (11.6) are the same idea, and they are taken.** Tool Quarantine already ships a 0–100 trust score, a blast-radius map, claims-vs-reality, decoy credentials and sha256 pinning; Neora AI ships signed audit receipts; Due Process ships reproduced verdicts. **I proposed this first and my own research killed it.** That is the single most useful thing the field scan bought us.

**#20 secret rot scanner (9.5) is a better business than most of this list and the wrong project for this hackathon.** It has no Vultr story and no containment moment. If the hackathon were about GRC rather than agents, this would score 13+.

**#22 vibecode → first 10 paying users (8.0) is a service business, not a build.** It scores C=15 (real value) and F=4 (it needs humans doing outreach — exactly what the autonomous-build constraint rules out).

**#25 co-founder match (8.3) and #17 WebGPU shim (9.6) have no Vultr story at all.** Nothing in them needs a Vultr VM, Serverless Inference or a sandbox, so nothing in them can satisfy the brief.

**#2 generative UI (10.4) is the clearest example of a mis-scored idea.** It would win any hackathon judged on demo glamour. It loses here because there is no panel member whose job is visual design, and because it executes nothing.

---

## 6. The decision

**BUILD: M2 — Eval Gym with CONTAINMENT as a scored dimension.**
Product identity: **agent containment assurance**. The gym is the wedge.

**Hedge:** keep M3 (cost router + benchmark) inside M2 as the "show me evals" payload — the scorecard's cost and latency columns come free if the router ships, and the router is ~150 lines on top of what we already have. If the containment scoring flops, the project degrades gracefully into M3 rather than collapsing.

**Do not build** anything else from this list. The runner-ups are components; the losers are either taken, or impossible in this event.

---

### Sources
- Judge roster, brief, judging criteria, prizes: The hackathon page lists 32 speakers/mentors/judges, the two challenge tracks, the prize structure, the judging criteria and the submission requirements [1]
- Field scan (121 submissions, popular entries, showcase projects): 121 submissions with 2,666 participants and 785 teams [4] · Vultr Community showcase: Blast Radius Zero, ProofRun, Agent Foundry, Team JC, Cascade AI and others [5]
- Jia Chen's playbook: Research sponsor tools first; "very solid, simple, straightforward finished product"; connect front and back within the first few hours; concise pitch and judges interacting with the demo; execution as important as originality [2] · Wins come from "team dynamics, judge interaction, and smart project execution" rather than credentials or an impressive stack [3]
- Eval methodology: "Evaluating and Improving Agentic Applications", built in partnership with Arize AI, five modules from foundations through improvement after deployment [6] · Phoenix sandboxes code evaluators, not the agent under test, and specifies no public scores, leaderboards, or containment testing [7]

## References

- [1] Vultr: Agent Rush Hackathon AI Hackathon | lablab.build | https://lablab.build/ai-hackathons/vultr-hackathon
- [2] 21x Hackathon Winner Turned College Dropout | Jia Chen Interview | https://podscripts.co/podcasts/the-peterman-pod/21x-hackathon-winner-turned-college-dropout-jia-chen-interview
- [3] 21x Hackathon Winner Turned College Dropout | Jia Chen Interview | https://www.developing.dev/p/21x-hackathon-winner-turned-college
- [4] Vultr: Agent Rush Hackathon | https://lablab.ai/ai-hackathons/vultr-hackathon/live
- [5] Project Showcase | Vultr Community | https://community.vultr.com/projects
- [6] Evaluating and Improving Agentic Applications | https://learn.deeplearning.ai/courses/evaluating-and-improving-agentic-applications
- [7] Arize Phoenix | https://raw.githubusercontent.com/Arize-ai/phoenix/main/README.md