# SHOR private-demo deployment

## Delivery status

Local development and controlled-demo configuration are prepared. No public host,
TLS endpoint, cloud provider, production release or deployment acceptance is
claimed. No external paid infrastructure was initiated. Publication requires the
user's explicit approval and a concrete reviewed deployment.

## Default: local only

Run from the checkout with Python 3.12 and the tested dependency lock:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pip check
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Use the existing isolated checkout; no Git worktree is required. Preserve
historical data. `SHOR_DATA_DIR` overrides legacy `SHORLAB_DATA_DIR`; otherwise
storage defaults to `./data` relative to the working directory. Set the desired
storage directory before importing the app. Restart processes after environment
restoration or configuration changes.

## Controlled remote demo

1. Keep Uvicorn bound to loopback behind an authenticated HTTPS reverse proxy or
   an approved private tunnel. Use one worker: in-process rate and concurrency
   controls are not distributed locks.
2. Set `SHOR_ACCESS_PASSWORD` securely. HTTP Basic username is **`shor`**. The
   password must never be checked into `.env.example`, scripts, a URL or Git.
3. Set `SHOR_PUBLIC_MODE=true`. Requests fail closed with 503 when this flag is
   true and no password is set. With a password, application pages, static assets,
   history, exports and recordings require authentication; `/api/health` remains
   a nonsecret public diagnostic.
4. Terminate **HTTPS** before any remote Basic authentication or microphone use.
   Basic authentication is only encoding; HTTP does not protect the password.
   Test the actual browser origin and microphone permissions on the approved host.
5. Configure proxy upload/body limits and timeouts consistently. Do not log
   Authorization headers, transcripts, form bodies, keys or audio. Keep databases,
   source manifests, raw evidence and backup locations outside public static roots.
6. Test unauthenticated access denial, authenticated upload/preview/download,
   export, deletion, restart and configured retention before promotion.

This is a single-operator demo design, not a multi-tenant product. There is no
claim of per-user data isolation, distributed quota accounting, audited identity
management, encrypted-at-rest storage or penetration-test certification. Do not
expose private audio merely because authentication was added.

## Configuration and limits

| Variable | Default / use |
|---|---|
| `GNANI_API_KEY` | Secure server-side provider credential; required only for real inference |
| `SHOR_ACCESS_PASSWORD` | Optional locally; required by public-mode guard; Basic user `shor` |
| `SHOR_PUBLIC_MODE` | `false`; `true` refuses requests without access password |
| `SHOR_DATA_DIR` | Overrides legacy data directory; default fallback `./data` |
| `SHOR_RETENTION_HOURS` | `168` (seven days); positive retention window |
| `SHOR_MAX_RUNS` | `500`; refuse new runs at capacity, delete old runs to resume |
| `SHOR_REQUESTS_PER_MINUTE` | `10`; aggregate local experiment cap, bounded to 1–100 |

The application accepts at most 8 MB per WAV and bounds multipart experiment
requests to 16.1 MB. One experiment is allowed at a time per process. Retention is
performed **on storage access**, not by a background scheduler; it is not a
promised deletion deadline when the process is idle. Capacity is a run count,
not an independent disk-byte quota. Provision storage for the configured cohort
and monitor free space. Deletion removes the active database record and audio
artifacts; SQLite pages, filesystem remnants and external backups require a
separate secure-erasure/backup policy.

## Gnani runtime activation

The last verified runtime had no `GNANI_API_KEY` binding, no local `.env` and no
allowed runtime destination for `api.vachana.ai`. The saved configuration draft
contains both requirements; it does not prove application. Confirm secure entry,
save/apply settings and publish the onboarding snapshot when prompted, then
restart and verify runtime state. No credential value should be shared in chat.
`docs.gnani.ai` also needs permitted access to reverify current official docs.

Health reports key presence separately from actual observed authentication,
network response, available requested model observations, last successful request
and sanitized errors. It never initiates a billable probe. The status is scoped
to the current process and resets on restart. It does not prove current credits.

A real smoke test requires a reviewed, consented speech sample and explicit
one-call authorization. Three-path web runs require three-call approval; the
four-path research runner requires four per model/sample. Timeouts may still be
billed; no automatic retries or refund guarantees are provided.


## Direct API evidence and deployment credential choice (7 November2026)

The user reports a successful direct Windows Prisma v2.5 request (HTTP200,
request ID [private correlation ID omitted]). This validates that
reported direct credential/account path, not Codex HTTP-secret substitution
or this deployment. See GNANI_ACCESS_DIAGNOSIS.md at the repository root.

SHOR already reads server-side GNANI_API_KEY from the deployment environment.
Use the intended environment's secret manager to provide the existing authorized
provider key, or its supported HTTPS-destination-bound secret integration.
An ignored checkout .env is an optional local-development fallback; injected
variables take precedence. Never export an opaque Codex secret marker as a key
for another deployment. Keep the key out of client-side code, logs and Git.

No endpoint/provider change or proxy/TLS bypass is required or justified.
Keep approved inherited network/trust configuration; restart the app after any
intentional credential configuration update. A direct PowerShell success is
not a successful SHOR application request and does not establish web-worker
health. Do not execute a new transcription without an explicit request budget.

## Final local demo candidate — 7 November2026

Latest independent local run:203 tests pass; all30 locked versions match;
no-index/no-deps installation confirms requirements already satisfied; pip check,
scoped Ruff, compileall, JavaScript syntax and whitespace checks pass. Real
provider HTTP is blocked during ordinary validation. Local Uvicorn startup,
health, synthetic browser workflows, orderly shutdown, restart persistence,
protected routes and public-mode missing-password rejection were exercised.
See FINAL_DEMO_READINESS.md for evidence and qualifications.

Candidate HTTPS ingress: `deploy/private-demo.nginx.conf.example`. Nginx/Caddy
are not installed here, so configuration syntax, certificates, DNS, external
HTTPS and remote access have NOT been validated. This file is a review candidate,
not an active deployment. Do not load it or expose a port without approval.

Before an approved private demo, provision the already approved host, a valid
certificate and private persistent volume; supply GNANI_API_KEY and a strong
SHOR_ACCESS_PASSWORD via server-side secrets; set SHOR_PUBLIC_MODE=true and
SHOR_DATA_DIR to that volume. Run exactly one Uvicorn worker on127.0.0.1:8000,
with access logs disabled and proxy headers trusted only from the local ingress:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 \
  --workers 1 --no-access-log --proxy-headers --forwarded-allow-ips 127.0.0.1
```

Validate Nginx configuration, TLS, Basic auth, unauthenticated audio/export
rejection, upload/time limits, deletion/retention and reboot persistence before
promotion. Preserve proxy variables and TLS CA trust for outbound Gnani access.
Never copy a Codex opaque marker into another deployment. Do not serve the
private SQLite/WAV/evidence directories as static paths. Keep free-text upstream
diagnostics out of access logs, website errors and public reports.

A controlled deployment still needs provider/application live verification,
ingress validation, disk/backup policy and explicit publication authorization.
Local authentication is not multi-tenant production certification. No remote
service, TLS listener, paid infrastructure or published endpoint was created.
