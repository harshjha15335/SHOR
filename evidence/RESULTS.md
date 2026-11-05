# Actual validation results

As of5 November2026:

| Measure | Observed result |
|---|---|
| Genuine speech clips submitted | 1 user-provided English clip,25.648s |
| Genuine transcription POST attempts | 1 |
| Successful transcriptions | 0 |
| HTTP result |403 access_denied |
| Failed HTTP attempt elapsed |0.175417s; not ASR inference latency |
| Provider transcript / returned model | Not obtained |
| Request ID | Not captured/available on the error path |
| WER/CER / critical recall | Not measurable |
| Recovery gain or regression | Not evaluated |
| Hindi/Hinglish samples evaluated |0 |
| Automatic retries / larger benchmark |0 |
| Remaining authorized requests |0 |
| Credits charged |Unknown |

See API_validation.md. Full genuine evidence is private, outside this repository. The committed manifest remains a header-only collection template. Software tests use labeled fixtures and are not included in the above genuine-attempt count.

An unsuccessful authorization attempt is evidence of an integration failure, not a recognition result. It does not prove whether the key, entitlement or an intermediary caused403. No real ASR performance, held-out gain, confidence interval or p50/p95 latency is claimed.
