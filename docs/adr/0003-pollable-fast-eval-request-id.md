# Keep the Fast Eval request ID pollable

Date: 2026-11-07 · POC: ticket 7 local integration

TL;DR: Add pending/failure status responses and resolve the POST request ID to the stored Run without changing the completed Four Eval Layers scorecard.

`POST /api/run` allocates a stream/request ID, while the gym independently allocates the persisted Run ID. Previously `GET /api/run/{request_id}` returned 404 even after completion. Keep the gym and persisted ledger identities unchanged; add an in-memory request-to-Run alias after storage, and return `{run_id,status:"running",tasks:[]}` while pending or `{run_id,status:"failed",error,tasks:[]}` after worker failure. Completed responses retain the frozen shape and expose the canonical Run ID for evidence, OTel, and Promote Failure to Regression Suite. Unknown IDs still return 404.

This additive status response supports polling without depending on an SSE completion event that can arrive before storage. Request aliases are process-local; persisted canonical Run IDs remain available after restart. The UI polls every 1.2 seconds with a 3-minute deadline and uses the canonical completed ID thereafter. No task schema or frozen completed-scorecard fields change.
