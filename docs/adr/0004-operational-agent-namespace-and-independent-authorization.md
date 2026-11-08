# Operational agent namespace and independent authorization

Date: 2026-11-08 · POC: Tolu / AdaL (lead adjudication for the live procurement agent slice)

TL;DR: The operational procurement agent lives in a new `/api/ops` namespace with its own auth, a broker-owned effect database, and a server-controlled approval authority. The frozen `/api` shapes and `attest/tasks.py` schema are unchanged. `agent.endpoint` remains a Vultr MODEL endpoint.

## Context

The 2026-11-08 submission brief (`docs/submission/implement-live-agent-prompt.md`) requires an authenticated task-service API, separately authorized purchase approval, and a live operational run visible in the finished UI. `docs/adal/spec.md` declares auth a non-goal for the read-only demo, and the existing `agent.endpoint` field is a model endpoint under the strict provider allowlist enforced by `scripts/apitest.py`. Both cannot hold without a documented boundary.

## Decision

1. **New namespace, frozen shapes intact.** All operational-agent routes are additive under a distinct prefix (e.g. `/api/ops/...`) in new router/module files. No existing `/api` route changes request or response shape; `attest/tasks.py` schema is unchanged. Anything that would alter a frozen shape requires a further ADR before implementation.
2. **`agent.endpoint` is not an agent-service field.** It stays a Vultr MODEL endpoint with the existing provider allowlist and behavior. The demo agent is integrated via an operator-configured internal adapter and an explicit new evaluation mode, never by overloading the model-endpoint field or accepting caller-supplied URLs.
3. **Separate trust boundaries, separate databases.** Merchant/action-broker effects and idempotency records live in a broker-owned database file, not in the `attest.db` scorecard hash-chain. The agent service persists its run state and completed events in its own on-disk store. Model-generated code cannot reach either store.
4. **Independent authorization.** The model may request approval but can never grant it. Approval binds exact SKU, quantity, seller, total, currency, destination reference, quote version, and expiry; any material change invalidates it. Hands-off demo runs use a server-controlled `demo_fixture` authority that is not selectable or forgeable by an ordinary agent/caller, and UI/event logs label it `Test-harness approval`.
5. **Boundary honesty.** Trusted orchestration, model transport, and the broker run outside gVisor; only model-generated analysis code executes inside it. No claim that the whole agent service is sandboxed. Per-execution runtime proof (`runsc`) is recorded, not inferred from a health string. The merchant is a test service: `Test merchant · no real charge`.
6. **Rankings stay comparable.** Operational-agent results are labeled with their own mode/suite and are not folded into returned-code baseline scores. Missing usage/cost/trajectory metrics are reported as unavailable, never as zeros or estimates of a different scope.
7. **UI integration is additive.** The finished redesign (cc77c13) is preserved: Leaderboard, Scorecard, Compare, Evidence, theme switching, Fast Eval, and the existing model-testing path remain functionally and visually intact. The operational-agent section is clearly labeled and uses the canonical run-to-scorecard/evidence navigation.

## Consequences

Existing evaluation behavior, pinned corpus counts (10/10 attacks contained, 15/15 oracles, 6 seeded agents, 9 gadget checks), and all five regression suites must stay green unchanged. New agent tests live in new test files so pinned counts do not drift. Public arbitrary-agent URL registration, local connectors, hosted framework uploads, and x402 payment remain future work and are explicitly unavailable in the UI, not silently absent.

Note: an empty `attest/sandbox/` directory exists beside the proven `attest/sandbox.py` module. New modules must not be placed inside it, to avoid shadowing the vetted sandbox on import.
