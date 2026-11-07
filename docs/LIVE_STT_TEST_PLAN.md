# SHOR one-call approval gate — prepared, NOT executed

Status: **REQUIRES USER APPROVAL**. Existing Codex transcription budget is zero.
The successful Windows request does not authorize a new Codex/application call.

## Proposed test

Use the existing private reviewed manifest:
`/workspace/private-evidence/gnani-smoke-001/manifest.csv`, sample
`uploaded-smoke-001`, actual25.648s human English speech, en-IN/verbatim,
Prisma v2.5 (model omitted). Do not modify the recording or infer Hindi quality.
The prior consent/review basis is retained privately. Confirm approval covers
reuse of that sample in the intended environment before execution.

The existing smoke runner generates a unique UUID `experiment_id` before the
request: a **local correlation ID**, distinct from any genuine provider request
ID. Do not invent an upstream ID or send undocumented provider parameters.

## Exact future invocation — do NOT run until explicit approval

Run from `/workspace/SHOR` with the tested venv. Set `RUN_ID` to a fresh UUID
using Python locally, then:

```bash
RUN_ID=$(python3 -c 'from uuid import uuid4; print(uuid4())')
/workspace/shorlab/.venv/bin/python scripts/live_smoke.py \
  --manifest /workspace/private-evidence/gnani-smoke-001/manifest.csv \
  --sample-id uploaded-smoke-001 \
  --model prisma-v2.5 \
  --allow-one-live-call \
  --output "/workspace/private-evidence/gnani-live-approved-${RUN_ID}.jsonl"
```

This command is prepared only. `--allow-one-live-call` must not be interpreted
as pre-existing user authorization. Before execution confirm the intended
runtime binding privately; an opaque Codex marker cannot identify the underlying
key. Preserve the approved HTTPS proxy and CA/TLS settings. Do not substitute a
raw key to evade the proxy. Verify one actual manifest row and writable private
output; the runner refuses overwrites and writes0600. Use one process, no retries
and no web three-call evaluation. Check the working diff before execution.

## Evidence and cost

Expected: local UUID, source/submitted hashes, requested language/model/format,
UTC timestamps, actual HTTP status, total wall time, actual returned model and
provider request ID only if supplied, raw transcript and scored reference when
successful; on failure, safe category plus private sanitized body/header IDs.
Artifacts remain private; do not print the personal reference/transcript in
public logs or reports. Error codes remain observed data, not automatic proof
of which intermediary generated them.

One provider request may consume programme credits; exact charge is unknown.
An error or timeout may still be charged. There is no refund assumption.
Record balance before/after manually if available in the dashboard; no extra
credit-query API call is authorized or required. Do not claim observed usage
from HTTP status alone. A successful result validates only this key/model/path
and sample. Stop after one attempt, regardless of outcome.

## Approval wording

“Authorize exactly ONE SHOR Prisma v2.5 transcription request using the existing
reviewed English sample and current approved credential/proxy configuration,
with private sanitized evidence, no retries and no additional API calls.”

After approval: execute once, verify the durable evidence, report success/failure
and stop. Any benchmark, other model, retry, three-path web run or publication
requires separate approval. No successful SHOR inference is claimed yet.

Publication note: this is a future approval template, not current permission.
A later explicitly approved single request was already spent and returned403.
Any next live invocation needs renewed explicit approval. Private recordings,
filled manifests, correlation details and results are not shipped in a clone.
Windows users should follow WINDOWS_DEVELOPMENT.md for preview-only setup.
