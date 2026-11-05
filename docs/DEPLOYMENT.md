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
