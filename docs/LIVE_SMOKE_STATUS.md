# One-call smoke execution status

The uploaded WAV passed PCM and duration checks. The user supplied an exact reviewed English transcript before submission. Speech language was therefore set to en-IN; no Hindi/Hinglish language performance is inferred.

Official documentation was reverified from https://docs.gnani.ai/api/STT/speech-to-text (HTTP200). It documents omitting `model` to use Prisma v2.5, rather than sending v2.5 as an explicit enum. The adapter now follows that rule and preserves actual successful HTTP status/request parameters. The smoke runner retains HTTP failure status, safe error code and elapsed timing, creates owner-only evidence files, and performs no retry.

An initial output-opening compatibility error was caught before any request and fixed. It consumed no API budget. The corrected software suite passed193 tests with one existing Starlette/httpx deprecation warning. New tests are explicitly software mocks, not live evidence.

The genuine POST was made exactly once at2026-11-05T16:31:48.936328+00:00. It returned HTTP403 in0.175417s. No successful transcript, returned model or scored metrics were obtained. Error response headers/body were not retained by the privacy-safe adapter, so any upstream request ID is unknown rather than proven absent. No additional probe/retry or paid benchmark was made.

Private evidence lives in `/workspace/private-evidence/gnani-smoke-001/`, files0600/directory0700, outside Git. Only this sanitized status is committed. Billing impact and precise403 origin remain unknown. Resolve account/key/model authorization and obtain a new explicit request budget before repeating. Once a smoke test succeeds, collect/review Hindi/Hinglish development/validation/held-out samples and approve a bounded benchmark separately.
