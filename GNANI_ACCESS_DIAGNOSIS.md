# SHOR — public-safe Gnani integration status

The application uses the documented Prisma REST endpoint with server-side
GNANI_API_KEY and X-API-Key-ID, multipart audio_file, language_code and verbatim
format. Prisma v2.5 selects the provider default by omitting model. TLS verification
and the configured HTTPS proxy are preserved; redirects/retries are disabled.

## Evidence boundary

The user reported a successful direct Windows request returning HTTP200 and
prisma-v2.5. This is distinct from the Codex application/proxy path, where
authorized attempts returned403. No successful SHOR application inference or
ASR/recovery improvement is claimed. One later failure returned an HTML response
and a sanitized edge correlation identifier; these do not establish denial origin.

Opaque destination-bound secret markers cannot identify the underlying stored key.
Key identity, historical substitution and provider/account association are not
proved locally. There is no confirmed SCOPE_NOT_ALLOWED or proxy defect.

## Diagnostics and privacy

Sanitized structured error codes and selected diagnostic headers are retained only
in private CLI evidence. Raw messages, transcripts, authorization and cookies are
excluded from diagnostics; diagnostics are excluded from public web responses.
Account metadata, credential suffixes, support correlation IDs, personal speech,
references and raw evidence are intentionally excluded from this published report.
The detailed local report was preserved outside this checkout before sanitization.

## Next gate

Privately compare the existing bound credential with the known working local key;
request provider/platform correlation as needed. Do not rotate keys or bypass TLS/
proxy controls speculatively. Any new live call requires explicit approval; the
previous approved budgets are exhausted. No live call is part of Windows setup.

See docs/WINDOWS_DEVELOPMENT.md, docs/FINAL_DEMO_READINESS.md and
docs/LIVE_STT_TEST_PLAN.md. Remote deployment remains separately gated.
