# Gnani website connection fix

The website previously checked credentials once when the page loaded and told users to set a local `.env`, even when they had already saved an HTTP secret. It had no visible setup/recheck flow. This confused a saved secret with a credential actually available to the server.

## Delivered

- Visible connection panel on desktop and mobile with actionable server-binding guidance.
- Separate credential, startup network-policy, and observed live-authentication states.
- Recheck button that only reads `/api/connection`: zero provider calls and no credit consumption.
- Live control disabled when credentials/status are unavailable; audio preview stays enabled.
- Recheck on browser focus and before/after live experiments so stale page state does not govern access.
- Safe error guidance for auth, credits, rate limits, and connectivity; no credential-entry field, no secret values exposed.
- Existing three-request approval remains required. Recheck is not an authentication test.

A network-policy result is labeled as a server-startup snapshot and may be stale. It is not a new external connectivity probe. Key presence permits an explicitly approved attempt; it does not prove authentication. The UI does not retrieve secrets from environment settings or activate the cloud configuration.

## Validation

- Full suite: **190 passed**, one Starlette/httpx deprecation warning, 2.71 seconds.
- New connection tests: 15, covering absent/available credentials, policy variants, failed/previously successful observations, no provider requests, auth protection and no key disclosure.
- Desktop/mobile connection browser checks: PASS (actual missing-key screenshots; labeled UI doubles only for state transition/outage checks).
- Full desktop/tablet/mobile regression browser workflow: PASS, including preview/playback/history/exports/deletion and microphone grant/denial simulations.
- Ruff scoped static checks, JavaScript syntax and whitespace checks: PASS.
- Live Gnani calls: **0**. Actual ASR quality remains unmeasured.

## Current external blocker

Latest runtime observation: revision1, no injected GNANI_API_KEY and api.vachana.ai not permitted. Saved draft revision4 contains the secret requirement and destination. The user's screenshot confirms a masked HTTP-secret value is saved. That does not prove runtime application or key validity.

Keep the key in HTTP secrets. Verify the secret targets application variable GNANI_API_KEY for api.vachana.ai, apply the environment configuration and reconnect/restart. No ordinary plaintext environment-variable entry or browser key field is required. The agent cannot activate or publish the environment with the tools available here.
