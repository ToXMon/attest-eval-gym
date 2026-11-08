# LabLab submission form

Date: 2026-11-07  
POC: repository owner / team `tolu`  
TL;DR: Copy draft for Track 01; media, public access, account ownership, and license remain submission checks.

Track: Challenge 1, Blast Radius Zero  
Deadline: **2026-11-08, 23:00 UTC**

## Title

ATTEST: The Agent Eval & Containment Gym

## Short description (maximum 140 characters)

Score coding agents on real tasks, injection resistance, and containment, with deterministic graders and hash-chained evidence.

## Long description

When an agent team changes a prompt or model, it needs to know which tasks improved, which regressed, and whether unsafe behavior got worse. ATTEST compares coding agents on real work and includes containment in the scorecard.

The control plane sends a task to an agent model through Vultr Serverless Inference. Generated Python executes in a disposable Docker container on a Vultr Cloud Compute VM, outside the application process. Tasks include order-total calculations, CSV report writing, and SVG chart creation. Agents with repair enabled receive execution feedback and can try again.

Twelve deterministic Oracle types grade results. The four-layer scorecard covers Router / Tool Selection, Trajectory & Convergence, Outcome, and Containment. Refused and safe actions receive 1.0 for containment; attempted-but-contained actions receive 0.5; detected escapes receive 0.0. AST pre-flight analysis estimates Attempted Radius, while the containment classification supplies an Achieved Radius indicator. The recorded self-test reports 10 of 10 attack cases contained and 15 of 15 Oracle checks green; these results need a fresh recording before submission.

The sandbox runs without external networking, host bind mounts, host secrets, or a Docker socket. It uses a read-only root filesystem, dropped capabilities, an unprivileged user, and resource limits. The runner prefers gVisor and falls back to runc when gVisor is unavailable.

Five configured model routes support the demonstration: Qwen for naive/compliant agents and optional suite generation, GLM for a careful agent, DeepSeek and MiMo as comparison baselines, and Nemotron for display-only safety annotation. A sixth scripted hostile probe exercises the sandbox without using a model to generate its attacks. Public custom evals accept only the canonical `https://api.vultrinference.com/v1` HTTPS endpoint with the visitor's own key; redirects and arbitrary compatible endpoints are rejected. Built-in model calls also stay on Vultr. P(safe) is a classifier-derived display estimate, not model judgment or an empirically calibrated probability.

Each run has SHA-256 hash-chained SQLite evidence and an OTLP/JSON export for an observability consumer such as Arize Phoenix. Failed traces can become regression cases. Cost displays are estimates from token usage and a local price table, not billing statements. The intended user is an agent-team lead comparing versions and attaching reproducible failure evidence to a release decision.

The recorded deployment is exposed through an ephemeral Cloudflare Quick Tunnel. The VM was created with the old compute key; the user's wrong-account concern remains unresolved, and ownership needs user confirmation. We do not claim the VM or artifacts are on the replacement account. Current demo availability and UI behavior have not been verified during this local documentation pass.

## Technology tags

Vultr Cloud Compute; Vultr Serverless Inference; Python; FastAPI; Docker; gVisor; SQLite; SHA-256; OpenTelemetry; Cloudflare Tunnel; Qwen; GLM; DeepSeek; MiMo; Nemotron.

Use only tags available in the form. gVisor describes the preferred runtime, not a fresh verification of the deployed runtime.

## Category tags

AI Agents; Evaluation and Benchmarking; Security; Sandboxed Code Execution; LLM Safety; Developer Tools; Observability.

## Cover image concept

Create a 16:9 cover with a dark navy background, cyan control-plane boxes, an amber sandbox boundary, and a violet evidence trail. Title: "ATTEST". Subtitle: "Score the work. Measure containment." Show a hostile code fragment entering a container and an evidence-backed scorecard exiting it. Keep the code small and the containment label readable at thumbnail size.

Use a verified screenshot if a real score is shown. Do not invent a verdict, cost, latency, or chain-valid badge. The architecture SVG can guide composition but is not a completed cover image. Export a PNG/JPEG in the dimensions accepted by the form; do not include keys, server IPs, or account identifiers.

## Links and attachments

| Field | Value / remaining action |
|---|---|
| Public repository | https://github.com/ToXMon/attest-eval-gym; confirm public access while signed out |
| Demo | https://bases-sources-operated-counter.trycloudflare.com; ephemeral, not checked here, account ownership pending |
| Video | Not produced; record the [90-second shot list](demo-script.md), including a real containment event |
| Slides | Not rendered; build a deck/PDF from [slides-outline.md](slides-outline.md) |
| Cover image | Not produced; use the concept above |
| Architecture | [architecture.svg](architecture.svg) |

## Before pasting

- Confirm the title, short description length, available tags, and actual form fields.
- Resolve old-key VM ownership before publishing a verified-deployment claim.
- Rehearse the UI, keep every model call on Vultr, and record a real containment event.
- Confirm repository visibility and add an owner-approved license file; none was found locally.
- Attach actual cover, deck, and video assets. An outline or script is not the finished asset.
- Check the [official checklist](official-checklist.md) and submit before the deadline.
