"""Small repository hygiene gate; not a substitute for a secret-scanning service."""
import subprocess
from pathlib import Path

files = subprocess.check_output(['git','ls-files'],text=True).splitlines()
errors=[]
for name in files:
    p=Path(name)
    if p.name == '.env' or p.suffix.lower() in {'.wav','.sqlite3'} or '.venv' in p.parts:
        errors.append(name)
    if p.suffix in {'.py','.js','.html','.md','.txt','.yml'} and p.exists():
        text=p.read_text()
        if '-----BEGIN PRIVATE KEY-----' in text and p.name != 'check_repository.py':
            errors.append(name)
if errors:
    raise SystemExit('Disallowed private artifacts or key material: '+', '.join(errors))
print('Repository hygiene checks passed (limited filename/key marker checks).')
