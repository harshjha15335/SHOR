# SHOR engineering handover — 5 November 2026

## A. Executive summary

The baseline local MVP is now a tested research workflow: detailed transcript errors, reference-free adaptive audio recovery, auditable manifests and offline summaries, robust provider handling, privacy controls, and a functional research dashboard. Existing visual design and audio/recording workflow are preserved.

**No real Gnani inference, real speech benchmark, held-out recovery gain, public deployment, video or competition submission is claimed.** External access and real consented speech remain essential blockers. Untuned acoustic thresholds are hypotheses, not learned or validated improvements.

## B. Engineering changes

| Files | Delivered behavior |
|---|---|
| `app/gnani.py` | Safe error codes, connect/read timeouts, no redirects/retries, response validation, real metadata nullable, input hash and UTC times, process-local observed integration status |
| `app/metrics.py` | Deterministic alignment and substitution/deletion/insertion counts; strict and Unicode scoring; exact critical-number/phrase retention; measured versus heuristic taxonomy; resource guards |
| `app/recovery.py` | Audio-only passthrough/fixed/adaptive policy, acoustic estimates and interpretable reason, conservative filtering, silence/clipping/unsuitable-signal fallback, output safety guard |
| `app/benchmark.py` | Reviewed-consent manifest validation, hashes/sample-rate/duration checks, split leakage checks, weighted/macro summaries and provenance-matched pairs, rejected-pair reasons, group summaries and timing thresholds |
| `app/main.py` | Explicit three-call web approval, thread-offloaded processing, evidence hashes, truthful health, private-demo Basic auth, cross-origin mutation protection, bounded uploads, rate/concurrency limits, filters, JSON/CSV export, safe spreadsheet cells, deletion and summaries |
| `app/storage.py` | Canonical UUID paths, retention on access, capacity preflight before paid requests, artifact deletion, atomic cleanup on failed save |
| `app/static/*` | Existing theme plus recovery/scoring/source controls, word diff and critical errors, raw evidence details, honest health, filters/deletion/summary, uppercase SHOR identity |
| `scripts/live_smoke.py` | Explicit one-call opt-in on reviewed actual speech; verifies writable output before requesting; durable raw evidence |
| `scripts/batch_benchmark.py` | Four variants/model/sample, paired models, explicit approved budget, complete preflight, no retries, preserved partial/scoring failures |
| `scripts/summarize_evidence.py` | Rebuild summaries from local JSONL without network inference |
| `scripts/browser_smoke.py` | Real Chromium UI interactions with synthetic fixtures; mobile/tablet/desktop and microphone grant/denial |
| `.github/workflows/tests.yml`, `requirements-lock.txt` | Exact development dependency pins; software tests, dependency checks, compilation, limited static analysis and repository hygiene gate |
| `evidence/*`, `docs/*` | Honest empty evidence template, collection/research/deployment protocols, submission drafts and audit |

New API routes: `GET /api/summary`, `GET /api/evidence.json`, `DELETE /api/runs/{id}`. Existing routes remain. Compatibility: legacy `SHORLAB_DATA_DIR` still works; new `SHOR_DATA_DIR` takes priority. Data paths are not silently moved. Old history remains readable; unavailable historical provenance is not invented.

## C. Git status

- Branch: `feature/research-reliability`.
- Starting commit: `b82591f11c1522ce356bd33a526dc0411e6a02aa`.
- Baseline audit milestone: `d9bdc4a`.
- Tested engineering milestone: `7a9bd9d` (later handover/documentation commit follows).
- Feature branch is intended for review; main is not merged or overwritten. No force-push.
- Verify exact delivered HEAD and remote state with `git log -3 --oneline` and `git ls-remote origin refs/heads/feature/research-reliability`.
- GitHub-hosted CI is configured; its remote outcome has not been independently observed. Local checks are reported separately below.

## D. Gnani integration and blocker

Successful live call: **no**. Model/language/request ID/live latency: **not measured/not available**. API calls executed in this work: **0**. Provider-account balance is unknown; no spending or extra credits were initiated.

Current runtime observations: no `GNANI_API_KEY` process value or injected secret binding; no local `.env`; runtime restricted policy lacks `api.vachana.ai`. The existing environment draft has the requirement/destination. A saved requirement is not a bound secure value or applied runtime policy. The current official docs URL returned HTTP/CONNECT 403 through the inherited proxy; no bypass was attempted and no undocumented API option was introduced.

User action: in environment settings, verify secure binding named `GNANI_API_KEY`, review/save/apply the prepared network configuration, publish the onboarding environment as prompted, then restart. Permit `docs.gnani.ai` for current documentation verification. Do not send credentials in chat. Supply a nonsensitive consented speech recording and manually reviewed transcript/manifest; none is bundled. Then use the initial one-call smoke budget. Further three-path web or four-path research comparisons need their separate explicit credit authorization.

Health distinguishes key presence, observed network response, authentication, validated requested models, recent success and safe error status. It does not spend credits or guarantee current balance/entitlement. Observations reset on process restart.

## E. Evaluation results

| Item | Actual result |
|---|---|
| Real speech samples evaluated | 0 |
| Real documented speakers evaluated | 0 |
| Genuine model requests during execution | 0 |
| WER/CER, critical recall | Not measured on real speech |
| Recovery improvements/regressions | Not measured on real speech |
| Live request latency | Not measured |
| Held-out evaluation / confidence claims | None |

Tests use synthetic WAV fixtures and clearly labeled HTTP doubles. Their numerical expectations validate algorithms only. The committed collection manifest is header-only. Empty offline summaries produce null accuracy rather than a misleading zero. A dry-run of the empty collection template intentionally fails rather than pretending to evaluate samples.

## F. Feature status

- **Implemented and software-tested:** WAV/preview/recording workflow; strict/Unicode scores, alignment and exact critical checks; audio-only recovery decisions; manifest/split/hash checks; weighted offline aggregation; history/search/export/deletion; private-demo authentication, limits and retention; browser workflows.
- **Implemented but not live-validated:** Gnani adapter and status observations, one-call runner, paired-model/four-arm benchmark workflow, any actual recognition benefit from fixed/adaptive processing.
- **Prepared:** data collection/review protocol, evidence package, private deployment guide, 60-second storyboard, narration/subtitle text, public-post drafts, submission checklist.
- **Planned/incomplete:** physical-device recording validation; human-reviewed entity/code-switch taxonomy; validated script-aware/semantic number equivalence; live conversational clarification agent; real corpus and frozen held-out policy evaluation; production-grade authentication/multi-tenancy; final video and publication.
- **Blocked externally:** credentials/runtime networking, official reference access and real recordings/reference review. Public deployment/publication/submission require separate approval.

## G. Quality assurance

Baseline: **22 passed**. Final integrated suite: **175 passed, 0 failed**, one Starlette/httpx deprecation warning, in 2.65 seconds on this instance.

Commands actually executed:

```bash
/workspace/shorlab/.venv/bin/python -m pytest -q
/workspace/shorlab/.venv/bin/python -m pip install -r requirements-lock.txt
/workspace/shorlab/.venv/bin/python -m pip check
/workspace/shorlab/.venv/bin/python -m ruff check --select E9,F821,F822,F823 app scripts tests
/workspace/shorlab/.venv/bin/python -m compileall -q app scripts
node --check app/static/app.js
python3 scripts/check_repository.py
git diff --check
python3 scripts/browser_smoke.py --base-url http://127.0.0.1:8011 --output-dir /tmp/SHOR-browser-final
/workspace/shorlab/.venv/bin/python scripts/summarize_evidence.py /dev/null --output /tmp/SHOR-empty-summary.json
```

All listed checks passed. Installing the pins into the existing environment succeeded; this is not a claim of fresh-machine restoration. Ruff selection checks syntax/undefined-name errors, not a comprehensive security audit. Repository hygiene checks only filenames/private-key markers, not a full credential-scanning service.

Browser checks: desktop/tablet/mobile upload, adaptive preview, unmeasured scores, actual WAV load/play, filters/open, CSV/JSON downloads, deletion and 404 artifacts, no horizontal overflow; malformed upload with recovered controls; synthetic-device microphone start/stop; actual browser microphone permission denial and upload fallback. **0 Gnani requests**. See `docs/validation/browser-results.json`. Physical microphone/audio intelligibility is not validated by fake-device tests.

## H. Security and deployment

Credentials remain server-side; errors omit raw private upstream bodies; redirects and automatic retries are disabled. Active data is local plaintext and should be consented/nonsensitive. Basic auth user is `shor`; password comes from `SHOR_ACCESS_PASSWORD`. `SHOR_PUBLIC_MODE=true` fails closed without it. Use a single worker, loopback by default and trusted HTTPS for any remote access.

Defaults: 8 MB/WAV, bounded 16.1 MB actual multipart body, one active upload/experiment/process, 10 evaluations/minute/process, 500 runs, 168-hour retention **on access**. Capacity is checked before paid requests. Rate and concurrency state are process-local. A singleton upload receiver prevents parallel body buffering within one process. A deployment must supply ingress timeouts, TLS, disk monitoring and a vetted access/backup policy.

Deletion removes active DB rows/WAVs, not filesystem/SQLite forensic remnants or external backups. No private recordings, filled manifests, raw results or keys were pushed. Git ignore is only an accidental-commit safeguard. This is a controlled local/private demo, not certified production security or multi-tenant isolation.

No public deployment or provider account provisioning was performed. No deployment URL is supplied.

## I. Verification gates

| Gate | Status | Evidence / limit |
|---|---|---|
| 1 Software health | PASS | 175 tests; backend/browser upload, playback, history/export/deletion across three viewport sizes |
| 2 Gnani authenticity | BLOCKED | No runtime key or endpoint access; no live transcript/request ID |
| 3 Evaluation quality | PARTIAL | Correct tested diagnostics and collection pipeline; zero reviewed real samples evaluated |
| 4 Recovery quality | PARTIAL | Reference-free policy and safety/software tests; no held-out ASR comparison or measured gains |
| 5 Security | PARTIAL | Private-demo controls/deletion/retention tested; production/remote validation and comprehensive audit not completed |
| 6 Submission | PARTIAL | Technical docs/storyboard/post drafts ready; authentic live demo/results/video/public links missing |

## J. Remaining actions

**User/external:** activate secure key and required network destinations; supply consented speech and reviewed transcripts; establish credit budget/model entitlement; verify current programme terms; authorize any remote deployment or public posting.

**Engineering/research after access:** capture one genuine success; benchmark development/validation recordings; revise and freeze policy without gold leakage; evaluate frozen held-out speakers/utterances; report wins/losses and uncertainty; decide whether recovery helps; validate remote private demo; capture genuine video and finalize submission. No thresholds were tuned using real held-out data.

## K. Demo, reproduction and submission

```bash
cd /workspace/SHOR
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The onboarding instance already has a usable interpreter at `/workspace/shorlab/.venv/bin/python`. Isolated UI test servers used temporary data on ports 8010/8011; they are not canonical datasets. Do not mistake these preview fixtures for experiments.

Reproduce collection validation and offline analysis with README commands and `evidence/evaluation_protocol.md`. Use the one-call smoke runner only after the required external prerequisites. The batch runner uses four calls/model/sample and refuses insufficient explicit budgets. Do not benchmark with an unknown remaining balance.

Repository: https://github.com/harshjha15335/SHOR. Review `feature/research-reliability`; main remains the baseline until a separately authorized merge.

The narration, timestamped shot list, subtitles, evidence requirements, submission fields and unpublished LinkedIn/X drafts are in `docs/SUBMISSION_PACKAGE.md`. They contain no fabricated results. The supplied competition deadline/award details remain unverified against current official rules. No actual video, post or final form submission exists yet.

Environment install/start instructions were updated and saved to the draft. Review/save/publish remains a product action; no publication or fresh-task restoration is claimed.
