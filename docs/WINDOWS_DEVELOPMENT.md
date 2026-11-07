# SHOR local Windows development

Requires Git for Windows, Python3.12 and PowerShell. Clone the feature branch:

```powershell
git clone --branch feature/research-reliability --single-branch https://github.com/harshjha15335/SHOR.git
Set-Location SHOR
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 in your local browser. Preview requires no API key.
Stop with Ctrl+C. The explicit interpreter avoids PowerShell activation/execution
policy changes. If reusing an existing clone, preserve uncommitted files before
switching branches; never reset merely to follow these commands.

## Credentials and privacy

Optionally copy .env.example to .env only when .env does not already exist. Edit it
locally to set the existing authorized GNANI_API_KEY; do not put the key in shell
history, browser code, screenshots or Git. Windows uses the actual provider key
in its private local environment, not the opaque marker from a Codex HTTP-secret
runtime. Injected environment variables take precedence over .env. Restart after
changing local settings. Do not remove approved proxy variables or disable TLS.
No live test is authorized by setup; the web live button would make three calls
and must not be used without separate approval.

Keep data/, filled manifests, recordings and raw evidence in private storage.
Do not copy cloud private recordings into Git or shared/synced public folders.
The cloud evidence and reviewed sample are NOT included in the clone. Paths in
older operational reports beginning /workspace describe that prior cloud instance,
not a Windows location or a guarantee those private files exist on your PC.

Private evidence files use POSIX0600/0700 on Linux. Windows does not enforce those
POSIX mode bits as equivalent owner-only ACLs: choose a private user-owned folder
and review NTFS permissions. No Windows ACL hardening or native-Windows run was
performed in the cloud. Permission assertions apply only on POSIX. Symlink tests
may explicitly skip on Windows without Developer Mode/symlink privilege; these
skips must not be reported as passes. All203 tests were rerun on Linux before
publication; Windows results must be checked locally.

## Optional checks

```powershell
.\.venv\Scripts\python.exe -m ruff check --select E9,F821,F822,F823 app scripts tests
.\.venv\Scripts\python.exe -m compileall -q app scripts
```

Browser automation is optional and uses Playwright/Chromium (not part of the
core Python lock). Existing scripts default to Linux Chromium paths; adapt the
browser executable through SHOR_CHROMIUM where supported. Core web serving has
no Node build step. Local desktop UI does not establish remote HTTPS readiness.
See DEPLOYMENT.md before any remote exposure. No merge/deployment is part of this
Windows handover, and successful direct-provider access does not resolve the
historical cloud-proxy403.
