# Official submission checklist

Date: 2026-11-07  
POC: repository owner / team `tolu`  
TL;DR: The local documentation package is prepared. Submission gates remain open until the owner verifies access, ownership, runtime/routing, license, and finished media.

Deadline: **2026-11-08, 23:00 UTC**.

## Source scope

This checklist reuses the official-event research already captured in [the research brief](../adal/vultr_agent_rush_research.md) and [the rubric analysis](../adal/judging_rubric_analysis.md), plus the supplied submission checklist. No official page, form, API, deployed service, or account was contacted during this local pass.

Official references for later confirmation:

- [Vultr: Agent Rush event brief](https://lablab.build/ai-hackathons/vultr-hackathon): Track 01 requirements, judging criteria, and containment-video requirement, as cited in the local research.
- [LabLab Agent Rush event / submission feed](https://lablab.ai/ai-hackathons/vultr-hackathon/live): event and submission context, as cited in the local research. Current form fields and attachment constraints still need owner confirmation.

Do not interpret the links as a fresh verification that every form field or deadline is unchanged.

## Form and attachment checklist

- [x] Title, short description, long description, technology/category tag suggestions: [lablab-form.md](lablab-form.md).
- [x] Cover image concept included in the form draft.
- [x] Architecture diagram: [architecture.svg](architecture.svg), embedded in the root README.
- [x] Around ten slides mapped to Technology, Presentation, Business Value, and Originality: [slides-outline.md](slides-outline.md).
- [x] Ninety-second shot list with a real containment sequence and rehearsal warnings: [demo-script.md](demo-script.md).
- [ ] Produce and attach a real cover image.
- [ ] Render and attach a slide deck/PDF; the outline is not a finished deck.
- [ ] Record and attach video showing at least one actual containment event, including executed payload and outcome.
- [ ] Confirm repository is public and demo opens while signed out.
- [ ] Complete the LabLab form and verify submission receipt before the deadline.

## Track 01 gates

| Gate | Requirement from recorded brief | Local status / remaining check |
|---|---|---|
| G1 | Public GitHub repo with setup and documentation | README prepared. Confirm public visibility of `ToXMon/attest-eval-gym`. |
| G2 | Backend and web app deployed on Vultr Cloud Compute | Deployment design documented. VM was created with old compute key; wrong-account concern unresolved. User must confirm ownership. No replacement-account claim. |
| G3 | Public demo URL | Recorded Quick Tunnel URL retained with caveat; ephemeral and not checked here. |
| G4 | Recorded demo with at least one containment moment | Script prepared; actual recording and attachment pending. |
| G5 | README explains Vultr services, architecture, use case, real task execution | Covered locally, with SVG and reproduction commands. |
| G6 | All agent LLM calls through Vultr Serverless Inference | Local code restricts built-in inference and public custom evals to canonical `https://api.vultrinference.com/v1` HTTPS. Custom evals require the visitor's own key; arbitrary destinations and redirects are rejected. Verify the deployed revision separately. P(safe) is a classifier-derived display estimate, not model judgment. |
| G7 | Isolated execution outside the app process on Vultr | Docker runner documented. Verify deployed runtime and real containment evidence. gVisor is preferred, runc fallback exists. |
| G8 | LabLab submission, originality, MIT compliance | Not submitted in this pass. No LICENSE file found; owner must confirm rights and add the appropriate license. Avoid unsupported exclusivity claims. |

Recorded demo URL: https://bases-sources-operated-counter.trycloudflare.com. **Ephemeral, current availability unverified; old-key account ownership needs user confirmation.**

## Claims requiring evidence before recording

- Fresh sandbox self-test and benign-work result, actual runtime, and execution limits. Historical reports say 10/10 attacks contained and 15/15 Oracle checks green; they were not rerun here.
- Current model availability and Vultr-only routing. No inference calls or provider-catalog checks were made in this pass.
- A real run's complete evidence chain and trusted head, rather than only a stored `chain_valid` field.
- Current task count and UI behavior. The latest inspected Fast Eval source requests four tasks (`t01`, `t02`, `t05`, `t08`); API calls without a subset select all 13. Neither the UI flow nor completion latency was verified live.
- Cost labeled as estimated. Local blended token prices are not invoices; do not reuse the old draft's exact seeding spend as verified billing.
- Phoenix import if claimed. The implemented OTLP/JSON export alone does not establish a running integration.

## Local-only completion boundary

This work edits submission documents and the SVG only. It does not upload assets, change accounts, provision infrastructure, rotate a tunnel, call inference, SSH, commit changes, or submit the project. Resolve ownership before any later infrastructure action.
