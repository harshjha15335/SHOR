# SHOR — final private-demo readiness, 7 November2026

## 1. Executive summary

**PASSED LOCALLY:** existing application, private diagnostics patch,203 software
tests and local lifecycle/browser/security controls. **READY BUT UNTESTED:**
reviewable HTTPS ingress candidate and one-call plan. **BLOCKED:** genuine SHOR
inference success and identification of the historical403 origin.
**REQUIRES USER APPROVAL:** any live call, commit/push/merge or remote deployment.

No claim of full integration, deployed HTTPS, production readiness, or measured
speech recovery improvement is made. Existing work and private evidence survived.

## 2. Verified application functionality

Uvicorn started on127.0.0.1:8000 with real provider Requests calls disabled.
Desktop1440px, tablet820px and mobile390px browser workflows passed: synthetic
WAV upload, adaptive preview, unmeasured metrics, real WAV playback, filters,
open-history, CSV/JSON download, deletion/artifact404 and no horizontal overflow.
Malformed WAV feedback recovered controls. Browser microphone grant/start/stop
used Chromium's fake media device; real permission denial yielded upload fallback.
Physical microphone fidelity is not verified.

A separate synthetic preview persisted after orderly server shutdown/restart,
including retrievable WAV bytes. It was then deleted. With public mode and a
generated test password, pages/history/evidence/CSV/connection reject anonymous
access401 and accept authenticated access200. Health remains nonsecret/public.
Public mode without password rejects health/home503. Test data is isolated under
/tmp, not mixed with the user's genuine recording/archive.

Result visualization, raw transcript/error handling and private-diagnostic
exclusion are covered by mocked backend tests; they are not provider performance
evidence. Browser tests use preview and never present mock transcripts as real.
See validation/final-readiness-results.json.

## 3. Local validation results

- Python3.12.14; all30 requirements-lock.txt versions matched.
- `pip install --no-index --no-deps -r requirements-lock.txt`: all already satisfied;
  no unnecessary package download or rebuild. `pip check`: no broken requirements.
  This is consistency validation, not a new artifact-signature or vulnerability audit.
- Full pytest with actual Requests Session.request blocked: **203 passed**, one
  existing Starlette/httpx deprecation warning, **3.84seconds**.
- Scoped Ruff `E9,F821,F822,F823`, compileall, Node JS syntax and whitespace: pass.
  No full formatter policy is configured; source was not reformatted gratuitously.
- Existing repository hygiene plus tracked/untracked candidate scan: no full
  current credential/marker, full private reviewed transcript, WAV, SQLite,
  real.env or private-key marker findings. Staging index is empty. The scan is
  limited; gitleaks is not installed, and no comprehensive external scan is claimed.
- Local lifecycle/browser/auth/persistence run: PASS. The first harness assumed
  a zero exit code after SIGTERM and failed. It was corrected to accept the
  expected signal exit only with “Application shutdown complete” in the log;
  corrected run passed. No application defect was inferred or speculative fix applied.

No Gnani requests were made during these checks. Logs/results are local software
validation, not live inference evidence. No test count was substituted for a real
provider success.

## 4. Credential and network configuration

The prior local audit verified GNANI_API_KEY presence, X-API-Key-ID assignment,
correct endpoint/multipart/default-v2.5 selection, inherited HTTPS proxy and
TLS verification. Deployment injection is supported already via the same
server-side variable; dotenv is optional and injected values take precedence.
No underlying credential was decoded or printed. Codex exposes an opaque secret
marker; underlying key identity remains **UNVERIFIED**. Privately compare the
existing HTTP-secret's underlying value to the successful Windows key, without
changing or posting the credential. Confirm destination api.vachana.ai and
published binding metadata. Do not treat marker suffix mismatch as wrong-key proof.
No additional configuration probe or speculative access change was needed here.

## 5. Direct API evidence

**VERIFIED as user-provided successful direct-test evidence:** Windows PowerShell,
7 November2026, POST api.vachana.ai/stt/v3, HTTP200, returned prisma-v2.5,
en-IN/verbatim,1.3s and reported ID
[private correlation ID omitted].
The original successful response/audio/script were not independently inspected
in this session. This supports the direct credential/path at that time, not a
successful SHOR application request. Raw returned transcript was not supplied;
no WER/CER is computed from the direct report.

## 6. Codex proxy uncertainty

Historical Codex POST:5 November2026 16:31:48.936UTC, HTTP403,0.175417s.
No raw body/headers, upstream ID or historical key fingerprint survive. Provider
scope, account association, stored binding/substitution and transport remain
unresolved. No proxy defect or SCOPE_NOT_ALLOWED is proven. Original private
files under /workspace/private-evidence/gnani-smoke-001 are untouched.

## 7. Security findings and limitations

Private diagnostics preserve allowlisted structured error codes/headers only;
known visible credentials and unsafe/free-text fields are redacted. Private CLI
files0600, new directories0700. Public responses/health/exports omit diagnostics;
regression tests pass. Proxy-hidden key material cannot be inspected directly;
review sanitized files privately before support sharing.

Loopback/private Basic auth, fail-closed public mode, cross-origin mutation
protection, bounded upload16.1MB/8MB per WAV, rate limit, singleton processing,
capacity preflight, retention-on-access and artifact deletion exist and are
locally tested. Rate/concurrency state is per process; use one worker. Slow
uploads need ingress timeouts. SQLite/WAV storage is plaintext; no per-user
isolation, distributed quota, encryption-at-rest or forensic erasure guarantee.
Retention runs on access, not an idle scheduler; backups need a separate policy.
A private demo needs TLS and trusted operators; local tests are not a penetration
test or production certification. No working code was changed just to produce work.

## 8. Remaining blockers

Underlying HTTP-secret identity and real SHOR authentication remain unverified.
No secure remote host, DNS/certificate, ingress executable or remote persistent
volume was approved/provided. Nginx/Caddy are unavailable for validation here.
Physical-device microphone use, restart after machine reboot, remote HTTPS,
remote audio privacy and live credit usage remain untested.

## 9. Exact live-test approval gate

Plan: LIVE_STT_TEST_PLAN.md. Existing reviewed English sample; one request,
Prisma v2.5 default, en-IN,verbatim; unique local UUID and genuine provider ID
only if returned; private output; no retries. Expected credit charge unknown.
No credit-balance query API is authorized. Current authorized budget is zero.

Required approval: “Authorize exactly ONE SHOR Prisma v2.5 transcription
request using the existing reviewed English sample and current approved
credential/proxy configuration, with private sanitized evidence, no retries
and no additional API calls.”

This report does not grant that approval. No live invocation was run.

## 10. Deployment candidate

`deploy/private-demo.nginx.conf.example` plus DEPLOYMENT.md specifies TLS ingress
to one loopback Uvicorn worker, server-side secrets and private storage.
**READY BUT UNTESTED:** candidate only; no Nginx syntax/certificate or public
reachability validation. Minimum publication steps: approve host/access/data
policy; supply existing secure credentials and certificate; validate ingress
syntax/TLS/auth/storage/restart on approved host; separately approve publication.
Do not expose Uvicorn directly or serve private files statically. No infrastructure
purchase, remote listener, public endpoint or paid subscription was created.

## 11. Files changed / preserved

Existing diagnostics work preserved: app/gnani.py, new app/http_diagnostics.py,
scripts/live_smoke.py, scripts/batch_benchmark.py and diagnostic/privacy tests.
Reports updated: GNANI_ACCESS_DIAGNOSIS.md, docs/DEPLOYMENT.md.
New deliverables: this report, docs/LIVE_STT_TEST_PLAN.md,
deploy/private-demo.nginx.conf.example and docs/validation/final-readiness-results.json.
Original recordings, reviewed text, genuine403 evidence, existing tests and data
were not deleted or reset. Test fixtures remained in isolated temporary storage.

## 12. Git status and proposed commit

Branch feature/research-reliability, HEAD13e3f3d. Existing modified/untracked files
are retained. No files staged, committed, pushed or merged. Hosted CI was not
run/observed by this work.

Proposed commit title, only after explicit approval:
“Preserve private Gnani error diagnostics and document validated demo readiness”.
Proposed scope: existing diagnostic module/adapter/CLI/tests and reviewed
readiness/deployment/diagnosis files. Exclude all private evidence, secrets,
recordings, personal transcripts, databases, venvs and temporary artifacts.
Review full diff and repeat the limited private-data scan immediately before
any separately approved commit. A commit approval does not authorize a push,
merge, deployment or API request.

## 13. Recommended next action

Privately verify that the stored HTTP-secret is the same key that succeeded on
Windows. If confirmed, request explicit approval for the prepared one-call SHOR
smoke test; do not use the three-request web action. If denied, use private
sanitized diagnostics for provider/platform correlation and stop. Deployment
publication is a separate gate after approved-host HTTPS checks. No more
speculative integration changes are indicated by the current local evidence.

## Windows handover publication update

The user subsequently authorized committing and pushing reviewed non-sensitive
changes to the existing feature branch only. The earlier Git/approval statements
above describe the readiness checkpoint before that authorization. A new local
run verified203 tests (one warning,3.05s), pip/static/JS/whitespace checks, and a
64-file known-value/private-artifact scan. The scanner's initial empty-env-example
false positive was corrected by restricting assignment matching to one line;
no secret was present in that example. The full account-specific forensic report
was preserved privately; the repository diagnosis is sanitized. Native Windows
execution remains unverified; see WINDOWS_DEVELOPMENT.md for platform limits.
No merge, deployment or live-provider test was authorized by this publication.
