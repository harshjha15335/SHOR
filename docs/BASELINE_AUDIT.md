# SHOR baseline engineering audit

Audited 5 November 2026. Starting commit b82591f11c1522ce356bd33a526dc0411e6a02aa. Baseline: 22 software tests pass; mocked inference is not live evidence.

## Existing functionality
FastAPI upload, preview, synthetic noise / uploaded ambience, simulated telephone channel, fixed spectral recovery, model selectors, Unicode WER/CER, critical recall, SQLite history and CSV export. Static desktop/mobile interface and batch script. Endpoints: /, /static, /api/health, /api/runs, /api/runs/{id}, /api/runs/{id}/audio/{variant}, /api/export.csv, POST /api/evaluate.

## Broken or misleading behavior
Health equates key presence with live availability. Adapter fabricates returned model via fallback to requested model. Partial upstream errors have minimal classification. No real API validation. Preview history and truncated-WAV bugs were fixed in baseline.

## Missing functionality
Word alignment, detailed error categories, adaptive recovery, honest live status, dataset validation/split leakage checks, weighted offline summary, full evidence provenance, retention/deletion, search/filter, authentication and request budgets.

## Security issues
All local audio endpoints unauthenticated; no retention/deletion, rate limits or storage bounds. Credentials remain server-side. Public deployment unsafe. Synchronous remote requests block async evaluate handler. CSV user-controlled cells need formula protection. Paths need explicit validation.

## Scientific validity
No genuine speech corpus, consenting participants, verified transcripts, live results, held-out evaluation or recovery gain. Synthetic tone smoke checks are not speech evidence. Exact script scoring does not imply semantic number equivalence. Recovery policy must not inspect reference text.

## Integration risks
Runtime observations current: no key binding or process GNANI_API_KEY; no local .env. Runtime restricted network lacks api.vachana.ai. Draft contains requirement and destination but is not applied. Official docs access must be checked; cannot infer credits or entitlement.

## Coverage and readiness
22 tests cover basic audio, scoring, preview, one mocked live path, history and truncation. Missing upstream response, security, retention, adaptive, benchmark and browser interaction tests. Live authenticity, real evaluation and recovery gates blocked externally by credentials/network plus consented speech. Local independent engineering continues.
