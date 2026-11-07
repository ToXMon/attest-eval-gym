# Vultr: Agent Rush Hackathon — Research Brief

**Date researched:** 2026-11-07 (UTC)
**Sources:** lablab.build hackathon page, Vultr Community event post, `api.vultrinference.com/v1/models`, `api.vultr.com/v2/plans`, lablab live feed, Vultr Community project showcase.

---

## 1. The event

| Item | Detail |
|---|---|
| Name | Vultr: Agent Rush Hackathon (lablab.ai × Vultr) |
| Online build | **3–8 November 2026** |
| On-site phase | 8 November 2026, Pierpont Place, Salt Lake City, UT (travel not covered) |
| **Submissions close** | **8 Nov 2026, 23:00 UTC** (live feed showed ~1d 02h 50m remaining at 19:51 UTC on 7 Nov) |
| Teams | 1–6 people |
| Platform | lablab.ai (submission required) + lablab Discord (required) |
| Participants | 2,666 (+47 today) |
| Teams registered | 785 (+29 today) |
| Submissions so far | **121** (+60 today) |
| Drafts in progress | 39 |
| Tools in use this round | 20 |

**Every participant gets $200 in free Vultr credits.** Account must use an email not previously associated with a Vultr account. Redeem via Console → Billing → promo `HACKATHON`.

### Prizes (total ~$15,000)

| Place | Cash | Vultr credits |
|---|---|---|
| 1st | $5,000 | $3,000 |
| 2nd | $3,000 | $1,000 |
| 3rd | $1,000 | $1,000 |
| On-site raffle (3 winners) | PlayStation 5 · AirPods 5 · Razer DeathAdder V3 | — |

Cash total $9,000 + $5,000 credits. Prizes appear to be awarded **overall**, not per track. Prize distribution may take up to 90 days.

### Judging criteria

1. **Application of Technology** — how effectively the chosen model(s) are integrated.
2. **Presentation** — clarity and effectiveness of the project presentation.
3. **Business Value** — impact and practical value, and fit with business areas.
4. **Originality** — uniqueness, creativity, demonstrated behaviours.

---

## 2. The two challenge tracks

### Track 01 — "Blast Radius Zero" (main challenge)
Web-based agent that performs real work (writes/runs code **or** operates a real browser) with every action contained in a sandbox on Vultr.

**Required stack**
- **Vultr VM** as backend / central control + orchestration layer
- **Vultr Serverless Inference** for **all** agent LLM calls — OpenAI-compatible, `https://api.vultrinference.com/v1`, vision-capable models available
- **Sandbox boundary**: containers or throwaway instances on Vultr, never inside the app process. Docker strongly recommended; OpenSandbox, gVisor, E2B listed as good starting points
- **Vultr API** (optional): spin up / destroy a throwaway instance per task

**Two execution patterns**
- *A — Sandboxed code execution:* user asks → model writes code → runs in container → real output returns → model explains result; errors fed back for retries
- *B — Sandboxed browser use:* user gives goal → model plans → Playwright runs in a container → screenshots return → a **vision model verifies** → **human approval before final actions**

**Vultr's own example directions (strong hints at what they want to see)**
- Pattern A: CSV Analyst · Prove-It Code Reviewer · Chart Anything · File Fixer · Self-Healing Runner
- Pattern B: Comparison Shopper · Form Filler · Site QA Sweep · Research with Receipts · Page Watcher

**Containment focus areas**
- Process isolation — execution never touches the host or app runtime
- Secret hygiene — no API keys or credentials inside the sandbox
- Resource limits — time and memory caps on every run
- Lifecycle discipline — reset or destroy the environment after each task

**Deliverables**
- Public GitHub repo with setup + docs
- Backend deployed on a Vultr VM, LLM calls through Vultr Serverless Inference
- **Public demo URL** with a real product-style experience
- **Recorded demo video including one containment moment** (e.g. sandbox absorbing an `rm -rf`, an infinite loop, or a hostile web page)
- Clear architecture + use-case explanation

### Track 02 — "Powering the Future of Work" (enterprise)
Enterprise AI solution coordinating realistic multi-step workflows. Vultr VM backend + web app required; **Serverless Inference optional**; Vultr GPUs **not available for this event**.

Focus areas: Sales Ops · Finance & Accounting · HR & Recruitment · Customer Support · Procurement.
Product expectations: public browser access, real product-style UX with clear user flows, Vultr as central backend, platform thinking not a one-off demo.

### Submission checklist (LabLab)
Title, short description, long description, tech/category tags, cover image, **video presentation**, **slide presentation**, public GitHub repo, demo platform, application URL. README must document Vultr services/infrastructure, deployment architecture, and the agent's use case + how it executes real tasks. Track 1 must show ≥1 containment moment in the video. Must submit on LabLab for judging; Vultr Community showcase is optional extra visibility.

---

## 3. Vultr Serverless Inference — live model catalogue

Fetched live from `https://api.vultrinference.com/v1/models` (public, no key needed). Prices are USD per token; table shows per **million** tokens. **Every chat model listed is open-weight** (DeepSeek, GLM/Z.ai, Xiaomi MiMo, MiniMax, Qwen, NVIDIA Nemotron/Muse, KRAFTON Raon) — no proprietary models, and no GPUs offered for the event.

### Chat / reasoning / vision (+ tool calling)

| Model ID | In $/M | Out $/M | Context | Notes |
|---|---|---|---|---|
| `qwen3.8-flash-next` | 0.10 | 0.20 | 262K | Fast multimodal MoE, reasoning + tool calling, vision/video/file. **Best cost/quality default** |
| `glm-5.3-flash` | 0.10 | 0.35 | 1M | Z.ai natively multimodal MoE, vision + video + files. Strong agentic coding |
| `mimo-v2.6-flash` | 0.10 | 0.25 | 1M | Xiaomi MoE, reasoning + tools, vision/**audio**/**video**/file |
| `nemotron-3-nano-omni-30b-a3b-reasoning` | 0.10 | 0.25 | 262K | NVIDIA, unified video+audio+image+text understanding, tools |
| `raon-1-mini-preview` | 0.10 | 0.30 | 262K | KRAFTON hybrid-attention MoE, reasoning + tools, vision |
| `deepseek-v4.1-flash-1017` | 0.15 | 0.60 | 1M | MoE, reasoning + tools, vision + file (PDF/CSV/JSON) |
| `qwen3.8-27b` | 0.15 | 1.00 | 262K | Compact dense vision-language, reasoning + tools |
| `minimax-m3.1-flash` | 0.20 | 0.90 | 1M | Sparse attention, agentic coding, **computer use**, long docs, vision + video |
| `muse-glimmer-30b` | 0.25 | 1.00 | 131K | NVIDIA, reasoning + coding + tool use, multimodal |
| `mimo-v2.6-pro` | 0.40 | 0.80 | 1M | Xiaomi flagship MoE, reasoning + tools, multimodal |
| `glm-5.2` | 0.75 | 3.00 | 1M | Z.ai flagship, long-horizon agentic, vision + file |
| `glm-5.3` | 0.75 | 3.00 | 1M | Z.ai, strongest complex coding + long-horizon agentic, vision + file |

### Decision models — return **calibrated answer probabilities** (unusual, rarely used by competitors)
| Model ID | $/M | Context | Notes |
|---|---|---|---|
| `clef-flash` | 0.05 | 262K | Cloudflare joint decision model, vision capable |
| `clef` | 0.10 | 262K | Cloudflare joint decision, vision |
| `d3` | 0.10 | 262K | vllm-sr multimodal decision model |
| `pplx-decider-v1.2` | 0.10 | 262K | Perplexity calibrated decision model, vision |

### Safety / retrieval
| Model ID | $/M | Notes |
|---|---|---|
| `nemotron-3.5-content-safety` | 0.05 in / 0.15 out | NVIDIA multimodal **moderation** model, 131K, classifies prompts/images/responses |
| `qwen3-embedding-4b` | 0.05 | Embeddings, 32K, truncatable dims, RAG |
| `bge-reranker-v2-m3` | 0.05 | Multilingual reranker, 8K |

### Media
Images: `moss-image` (0.02/MP), `z-image-turbo` (0.02/MP), `qwen-image-2.1` (eval) · Video: `minimax-h3` (0.06–0.90/s) · Music: `minimax-music3` (0.001/s), `ace-step-1.5` · TTS: `chatterbox` (0.00028/s), `qwen3-tts-12hz-1.7b`, `auk` · ASR: `whisper-large-v3-turbo` (0.00001111/s), `qwen3-asr-1.7b`, `granite-speech-5.0-2b`, `voxtral-mini-4b-realtime`

**Base URL:** `https://api.vultrinference.com/v1` (OpenAI-compatible). API key from Vultr Console → Serverless Inference. Model prices are per model; the marketing figure "$0.55/M in, $2.75/M out" is a headline average, not a flat rate.

---

## 4. Vultr Cloud Compute pricing (from `api.vultr.com/v2/plans?type=vc2`)

| Plan | vCPU | RAM | Disk | Bandwidth/mo | Monthly | Hourly |
|---|---|---|---|---|---|---|
| `vc2-1c-0.5gb-free` | 1 | 512MB | 10GB | 0 | **$0** | $0 |
| `vc2-1c-1gb` | 1 | 1GB | 25GB | 1TB | $5 | $0.007 |
| `vc2-1c-2gb` | 1 | 2GB | 55GB | 2TB | $10 | $0.014 |
| `vc2-2c-2gb` | 2 | 2GB | 65GB | 3TB | $15 | $0.021 |
| `vc2-2c-4gb` | 2 | 4GB | 80GB | 3TB | **$20** | $0.027 |
| `vc2-4c-8gb` | 4 | 8GB | 160GB | 4TB | $40 | $0.055 |
| `vc2-6c-16gb` | 6 | 16GB | 320GB | 5TB | $80 | $0.11 |
| `vc2-8c-32gb` | 8 | 32GB | 640GB | 6TB | $160 | $0.219 |

32 regions. São Paulo is +50% on most plans.

### $200 budget plan (competition runs 5 days)
| Item | Spec | Cost |
|---|---|---|
| Control-plane VM (app + Docker daemon) | `vc2-2c-4gb` | ~$3.30 for 5 days |
| Sandbox workers (burst) | `vc2-4c-8gb` × 1 | ~$6.60 for 5 days |
| Per-task throwaway instances via Vultr API | `vc2-1c-1gb` | ~$0.85 each, on demand |
| Inference (worst case, generous) | 5M in + 5M out on `qwen3.8-flash-next` | ~$1.50 |
| Inference (heavy GLM-5.3 run) | 2M in + 1M out | ~$4.50 |
| **Total** | | **≈ $20 of $200 — huge headroom** |

**Strategic read:** credits are not the constraint. *Time* is. Budget for the highest-quality single instance rather than many small ones.

---

## 5. Competitive landscape

### Top LabLab submissions by community vote (of 121)
1. SAAS Fashion Garment Marketing – Batik to Global (8 votes)
2. Neora AI (7)
3. MiniLocker (3)
4. **Burner: Test Job Code in a Safe Throwaway VM** (3)
5. **Preflight: know what you built before you ship it** (2)
6. **Detonation Chamber** (2)
7. QuantGate (1)
8. ARC — Your Company Workspace (1)
9. **Vultr Chaos Sweeper: Blast Radius Zero QA Agent** (1)
10. **YAI Guard — Prove-It Code Runner** (1)

### Vultr Community showcase projects (likely competitors)
| Project | What it does |
|---|---|
| **Blast Radius Zero — sandboxed agent runtime** | Plans tasks, fetches pages, runs generated code. Fresh disposable **network-less** Docker container per step; read-only rootfs, tmpfs workdir, dropped caps, non-root uid, empty env, caps on memory/CPU/PIDs/wall clock/output/disk. **gVisor (runsc)** with runc fallback. **7 static attack probes in CI, build fails if any escapes.** Per-step verification via a second model call (GLM-5.3). SQLite ledger with per-step commands + SHA-256 artifact hashes. Single `vc2-1c-1gb` (Seoul). Honest boundaries documented. **This is the benchmark-beater to beat.** |
| **ProofRun** | AI agent + Docker-based verifier to assess software changes (Serverless Inference) |
| **Team JC** | Browser use without vision |
| **Tripwire Sandbox** | Sandbox |
| **Tasklexa Agentic OS** | Agent orchestration + governed execution |
| **Agent Foundry** | Local-first agent reliability & provenance debugger |
| **RLForge** | Turns academic papers/specs into RL environments |
| Cascade AI | Four Gemini agents onboarding B2B clients |
| sentinel | Full-stack self-healing DevOps & security copilot |
| Dreamneti | AI operations team for shops |
| Buttery | Agent-first household food ledger |
| Accountpulse | AI customer-churn early warning |
| Agency Compiler | Spins up agents for creative projects |
| oneshot-video | Automates short product demo video creation |
| SAAS Fashion Garment Digital Control Tower | Supply-chain ops |

### The gap
**The sandbox-execution space is saturated.** At least 8 of the 121 submissions are variations on "agent runs code inside a container that contains it": Blast Radius Zero, Burner, MiniLocker, Detonation Chamber, Tripwire Sandbox, YAI Guard, Vultr Chaos Sweeper, ProofRun.

Containment-as-a-binary is table stakes. Static probe lists are table stakes. Every one of these projects sandboxes **its own** agent's code.

**Nothing in the top-10 or the showcase sandboxes *someone else's* agent and certifies it.**
