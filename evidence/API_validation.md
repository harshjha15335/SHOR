# Live API validation

Status: BLOCKED; no live inference performed by the evidence pipeline.

At audit, the current runtime had no GNANI_API_KEY binding, no local .env, and restricted destination policy did not include api.vachana.ai. The saved draft requirement/destination is not runtime activation. Securely apply the existing environment settings; never paste a key into chat. Confirm network and credential state, then authorize a one-call test using reviewed consented speech. No recording satisfying that requirement is bundled.

Use `scripts/live_smoke.py` with explicit `--allow-one-live-call`; a manifest and fresh output path are mandatory. Record genuine transcript, request ID only if provided, returned model only if provided, requested model, language, formatting, submitted audio hash and timings. A successful request establishes only that sample/model/account operation. Additional tests require a known approved credit budget.

Neither mocked unit tests nor synthetic-tone previews validate API authentication, language recognition, credits, model entitlements or recovery quality.
