# Judging Analysis — Mapping Every Idea to the Official Rubric

**Date:** 2026-11-07 · **Team:** `tolu`

The official rubric is four criteria Judging criteria are application of technology, presentation clarity and effectiveness, business value and practical impact, and originality [1]. Everything else in the brief — GitHub repo, Vultr VM deployment, public demo URL, demo video, README, and for Track 1 a containment moment — is a **gate**, not a score. Failing a gate disqualifies you; scoring badly on a criterion only loses points. Conflating the two is how a brilliant idea gets zero because it never shipped.

---

## 1. The gates first (pass/fail, applied before any judging happens)

### Track 1 — Blast Radius Zero gates
| Gate | Requirement |
|---|---|
| G1 | Public GitHub repository with setup and documentation |
| G2 | Backend deployed on a Vultr Cloud Compute VM; the web app runs on Vultr |
| G3 | Public demo URL |
| G4 | Recorded demo video **containing at least one containment moment** |
| G5 | README explains the Vultr services used, the deployment architecture, the use case, and how the agent executes real tasks |
| G6 | **All agent LLM calls through Vultr Serverless Inference** |
| G7 | Isolated sandbox execution (containers on Vultr, never in the app process) |
| G8 | Submission completed on LabLab; original, MIT-compliant |

### Track 2 — Powering the Future of Work gates
G1, G2, G3, G5, G8. **G4, G6 and G7 do not apply** — no containment moment required, Serverless Inference optional, no sandbox required Challenge 2 requires a Vultr VM backend and web deployment, with Serverless Inference optional and no containment-moment requirement [1].

### The two facts that fall out of this

**Fact 1 — the podium is not per-track.** The prizes are 1st/2nd/3rd place overall: $5,000 + $3,000 credits, $3,000 + $1,000, $1,000 + $1,000 The three placement awards total $9,000 in cash and $5,000 in Vultr credits [1]. Both tracks feed the same three places. So Track 2 is a legitimate route to the podium.

**Fact 2 — Track 2 is nearly empty.** Of the submissions read in full, roughly a dozen carried the C2 tag against well over a hundred carrying C1. Entering Track 2 means competing against a much smaller field for the same prize.

**But:** Track 1 is the brief's named main challenge, Vultr's own judges will read the containment mandate more fluently, and the security lead on the panel has more to react to in a Track 1 demo. **Recommendation: enter Track 1 with the winner** — it fits the gates by construction — and treat "Track 2 is emptier" as the reason to hedge the *product* (enterprise-friendly framing), not as a reason to change track.

### Gate triage across all 31 ideas

| Gate outcome | Ideas |
|---|---|
| **Fails G4/G6/G7 — needs Track 2 to compete at all** | Generative UI, System-One router, Temporal state machine, raw MCP server, grammar-constrained decoding, cost kill-switch, KV-cache prefix sharing, speculative decoding, shadow-routing, DPO flywheel, voice loop, WebGPU shim, secret rot scanner, AI invoice, co-founder match, vibecode→paying users |
| **Passes Track 1 gates** | computer-use agent, trajectory grader in CI, inter-agent sanitization proxy, PII unmasking proxy, API-to-browser fallback, fuzz-your-own-swarm, publish-one-benchmark, **eval gym (as stated)**, marketplace trust score, **eval gym + containment scoring (winner)**, ATTEST/trust attestation, cost router + benchmark *(only if a containment moment is added)* |

---

## 2. The four criteria, as this specific panel will apply them

### ① Application of Technology
*"How effectively the chosen model(s) are integrated into the solution."* Note the plural and the word *integrated*. The panel is 4 Meta engineers, 4 Amazon engineers, an Amazon applied scientist, an AI engineer from a model lab, a RAG architect, an LLMOps engineer, a Cohere-class AI/ML engineer, the NativelyAI CTO and lablab.ai's own staff. These people know what a thin `response = llm(prompt)` integration looks like.

They will reward: **models doing genuinely different jobs**; a *visible reason* for each choice; inference cost awareness; and serious use of the sponsor's stack.

They will punish: one chat call wearing an agent costume; a demo that never touches Serverless Inference; and stack name-dropping that isn't load-bearing (Jia Chen's warning applies directly to this criterion).

### ② Presentation
*"The clarity and effectiveness of the project presentation."* Not visual design — **clarity of a working system**. There is exactly one Principal PM and one McKinsey consultant on this panel. So: one screen, one number, a working demo, and a pitch that doesn't recite the stack. Plus Jia Chen's hard-won rule: connect front and back end **within the first few hours**, and let the judges *interact* with the demo rather than hear about it Chen recommends connecting the front end and back end within the first few hours and focusing on a demo judges can interact with rather than bragging about the tech stack [2]. The submitted video must also carry the containment moment Challenge 1 must show at least one containment moment in the demo video [1].

### ③ Business Value
*"The impact and practical value, considering how well it fits into business areas."* With JPMorgan's VP of SWE, Prudential's Director of Technology, American Express, Hims & Hers, Walmart's Principal PM, Amazon Ads' TPM, and McKinsey in the room — and **zero investors** — this criterion means *operational* value: hours returned, incidents avoided, artefacts a risk committee can accept.

Note the correction this forces on the pitch. "Investors ask 'show me evals'" is a true and sharp user insight, but **no judge here is an investor**. It has to be translated before it scores: *the agent team's lead needs a number they can put in front of their risk committee and their CTO.* Same pain, different mouth.

### ④ Originality
*"The uniqueness and creativity of the solution, highlighting approaches and ability to demonstrate behaviors."* **This is where the field kills you.** With 121 submissions and a saturated sandbox lane — Blast Radius Zero, ContainBench, Tool Quarantine, Neora AI, RedHanded, ShipGate, Burner, MiniLocker, Tripwire, ProofBox (×2), VibeAudit, Mantis Ring, JARVIS ProofOps, Receipts, Due Process The live feed shows 121 submissions, including Burner, MiniLocker, Detonation Chamber, Vultr Chaos Sweeper and YAI Guard among the most popular [3] — a fifteenth "Blast Radius Zero" gets a 1 or 2 out of 4 on originality from most judges, and originality is 25% of the rubric.

**The critical asymmetry: in practice this rubric behaves multiplicatively, not additively.** A judge who reacts to "another sandbox project" scores 1/4 on originality, and that reaction contaminates the other three. **Being in an empty lane is not one quarter of the win — it is the precondition for the other three quarters landing.**

---

## 3. Scores on the four official criteria

Gated to ideas that pass the gates, then scored 0–10 on each official criterion. **Equal weights** (each is 25%).

| Idea | Track | ① Technology | ② Presentation | ③ Business | ④ Originality | **Mean** |
|---|---|---|---|---|---|---|
| **Eval gym + CONTAINMENT as a score** | C1 | **9** | **9** | **8** | **9** | **8.75** |
| Eval gym as stated (no containment dimension) | C1 | 8 | 8 | 8 | 8 | 8.00 |
| Cost router + reproducible benchmark | C2 | 8 | 7 | 9 | 8 | 8.00 |
| Inter-agent sanitization proxy | C1 | 9 | 8 | 7 | 7 | 7.75 |
| PII unmasking proxy | C1/C2 | 7 | 8 | 9 | 7 | 7.75 |
| Trajectory grader in CI | C1/C2 | 8 | 7 | 9 | 3 | 6.75 |
| Computer-use agent (DOM + screenshot diff) | C1 | 9 | 8 | 6 | 4 | 6.75 |
| Voice loop (VAD) | C2 | 7 | 9 | 7 | 5 | 7.00 |
| Marketplace trust score for extensions | C1 | 8 | 8 | 8 | 3 | 6.75 |
| ATTEST — trust attestation | C1 | 8 | 7 | 8 | 3 | 6.50 |
| API-to-browser fallback | C1 | 7 | 8 | 7 | 7 | 7.25 |
| Fuzz your own agent swarm | C1 | 8 | 7 | 7 | 5 | 6.75 |
| Publish one benchmark | C1/C2 | 7 | 7 | 8 | 6 | 7.00 |
| Generative UI | C2 | 6 | 9 | 5 | 4 | 6.00 |
| Temporal state machine | C2 | 8 | 5 | 8 | 6 | 6.75 |
| Cost kill-switch | C2 | 7 | 7 | 9 | 4 | 6.75 |
| AI invoice that explains itself | C2 | 7 | 7 | 9 | 4 | 6.75 |
| Secret rot scanner | C2 | 6 | 7 | 9 | 7 | 7.25 |
| Raw MCP server in JSON-RPC | C2 | 6 | 5 | 6 | 7 | 6.00 |

**Excluded entirely — cannot be built in this event:** speculative decoding, DPO flywheel, KV-cache prefix sharing (no GPUs; no control of a managed API's serving layer) · grammar-constrained decoding (no serving-layer control) · shadow-routing (no production traffic) · WebGPU shim, co-founder match, vibecode→paying users (no Vultr story / no autonomous build).

### Reading the leaderboard honestly

The winner leads on **three of four criteria**, and the criterion where it gives ground is the one where it doesn't have to compete: Business Value. **Cost router + benchmark matches the raw eval gym at 8.00** and beats the winner on ③ (9 vs 8). That is the real threat, and it is why the cost/latency columns must ship inside the winner rather than being treated as a nice-to-have — the moment the winner carries a cost column, it absorbs the router's entire advantage.

The reason the winner still wins is **④ Originality at 9 with nothing else in the field above 8**. Nothing else in the 121 is an eval product. And it holds ① and ② at 9 because a panel of model engineers will recognise five distinct open-weight model roles and deterministic graders as genuine engineering, not a costume.

---

## 4. What the judge actually writes — and the three pushbacks it will produce

### The scorecard for the winner
> **① Application of Technology — 9/10**
> *"Five distinct open-weight models from Vultr Serverless Inference doing five genuinely different jobs, and the graders are deterministic code rather than a model vote. Real cgroup and gVisor isolation with actual caps. I wanted more of the inference cost story but it is there."*
>
> **② Presentation — 9/10**
> *"We dropped our own agent in during judging and had a score in about two minutes. The demo is one screen and one number. That is exactly how it should feel."*
>
> **③ Business Value — 8/10**
> *"It gives an agent team a regression board and an artefact a risk reviewer can sign off. Narrow — it serves agent teams, not every enterprise — but it is a real, recurring need."*
>
> **④ Originality — 9/10**
> *"Nobody else in this room is scoring agents, and scoring the containment rather than just containing it is the actual idea."*

### Pushback 1 — "Isn't this just Arize Phoenix / LangSmith?"
**Answer:** "Phoenix needs your traces — you have to instrument your agent and it scores what you already ran, on your own machine, unsandboxed. We need only your endpoint. We run the agent inside a sandbox, which is the only way to score containment, and containment is a score here, not a feature." If they push further: "We consume OpenTelemetry if the agent offers it. We are complementary, not a rival."

### Pushback 2 — "Your leaderboard has three entries."
**Answer:** "Three seeded baselines ship with it — naive, compliant, careful — so the board is never empty and the profiles are legible. And any judge can add a fourth in two minutes; that is the interaction." **Mitigation:** ship 6–8 baselines spanning the range, and a fast-suite path.

### Pushback 3 — "What is the business model?"
**Answer:** the operational one: *"An agent team ships a change. Our board says whether it regressed. That is CI, for agents, and the scorecard is the artefact you attach to the ticket."* Do **not** lead with investors — there isn't one in the room.

---

## 5. How to maximise each criterion (concrete, buildable)

| Criterion | What to build that moves it |
|---|---|
| **① Technology** | **Make model routing visible in the UI.** A per-task panel showing *which* model ran, *why*, and what it cost. This is the single highest-leverage addition: it converts "we used five models" into evidence of deliberate integration, and it hands the cost story to ③ at the same time. Use Vultr's decision models (`pplx-decider-v1.2`, `clef`) for the risk tier so the routing is principled rather than a lookup table. |
| **② Presentation** | One screen, one number. Video ≤ 2 min, first 15 seconds must show a score appearing. Front end and back end connected and live **within the first few hours**, per Jia Chen. The containment moment lands at 0:45, after the product has already shown what it is. |
| **③ Business** | Put the *failing task list* front and centre — "your agent fails these 4 of 10, here is how to reproduce each". Add cost and latency per run. Frame the buyer as an agent-team lead, never as an investor. |
| **④ Originality** | Title and demo lead with the wedge: **"We score your agent. Including whether it stays contained."** Never lead with "an eval platform" — that's the crowded category. Never let the sandbox look like the product; it is the instrument. |

---

## 6. The one-sentence pitch, stress-tested

> **"Drop your agent in. Get a score — can it do the work, does it resist injection, and did the sandbox have to save it. Deterministic graders, hash-chained evidence, public scorecard."**

Against the rubric: ① five open-weight model roles + deterministic graders + gVisor · ② one screen, judge is the subject of the demo · ③ a regression board and a signed artefact for an agent team · ④ the only eval product in a field of 121, and the only one that scores containment.

---

### Sources
Judging criteria, prize structure, both tracks' requirements, and the containment-moment requirement [1] · 121 submissions and the most popular entries [3] · Jia Chen on connecting front and back early and letting judges interact with the demo [2] · Phoenix sandboxes code evaluators rather than the agent under test, and produces no public scores or containment testing [4]

## References

- [1] Vultr: Agent Rush Hackathon AI Hackathon | lablab.build | https://lablab.build/ai-hackathons/vultr-hackathon
- [2] 21x Hackathon Winner Turned College Dropout | Jia Chen Interview | https://podscripts.co/podcasts/the-peterman-pod/21x-hackathon-winner-turned-college-dropout-jia-chen-interview
- [3] Vultr: Agent Rush Hackathon | https://lablab.ai/ai-hackathons/vultr-hackathon/live
- [4] Arize Phoenix | https://raw.githubusercontent.com/Arize-ai/phoenix/main/README.md