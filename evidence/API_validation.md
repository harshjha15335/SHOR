# Genuine one-call Gnani validation

Updated 5 November 2026. The runtime secret binding is READY and unrestricted networking is enforced. Current official REST documentation was fetched successfully (HTTP200) before the call.

## Actual attempt

- A user-uploaded, 25.648-second human-speech WAV was used with the user's exact reviewed English transcript.
- Request: ONE POST to `https://api.vachana.ai/stt/v3`, with server-side X-API-Key-ID, `language_code=en-IN`, `format=verbatim`.
- Requested model: Prisma v2.5. Current official documentation specifies omitting the model field for this default; the adapter was corrected and tested before the call.
- UTC attempt window: 2026-11-05 16:31:48.936328 to 16:31:49.117322.
- Actual HTTP status: **403**. Safe category: `access_denied`.
- Failed request elapsed time: **0.175417 seconds**. This is not model inference latency.
- No successful transcript, returned model, WER/CER or recovery result was obtained.
- Request ID: **not captured/available**. The error path did not retain raw response body or headers, so it cannot establish whether an upstream error ID was provided.
- **No retry. The authorized one-call budget is exhausted.** Billing/credit impact is unknown.

A 403 alone does not distinguish invalid-key authorization, account/model entitlement, or an intermediary denial. Runtime policy readiness does not prove provider authorization. No credit-exhaustion conclusion is justified by this response. Runtime diagnostics exposed no additional cause. Do not describe this as a successful Gnani transcription or claim that the key is definitely invalid.

## Private evidence

Source audio, original/reviewed transcript, manifest, authorization basis and durable JSONL result are retained outside the repository at `/workspace/private-evidence/gnani-smoke-001/`. Directory permissions0700; evidence files0600. No credentials were logged. Private audio/reference/result are not published to GitHub.

The source and submitted WAV SHA-256 values are stored privately. The runner normalized/re-encoded the WAV to 16kHz mono PCM; no noise, phone simulation or recovery was applied. This English recording does not establish Hindi/Hinglish quality.

## Next gate

Resolve authorization/entitlement with the Gnani account owner or provider, then obtain a renewed explicit one-call budget before trying again. A successful response is required before any controlled Hindi/Hinglish benchmark. A larger benchmark needs its own approved request budget and reviewed consented corpus. No larger paid run was launched.
