# shor — Indic Speech Reliability & Recovery Lab

**Original, reproducible speech recognition stress testing for Indian-language audio, powered by real Gnani Prisma API calls.** Built as a starting point for the [Great Indian AI Internship Challenge](https://www.gnani.ai/internship), especially the Noise Canceller Award.

> **Status: working local MVP, NOT a validated competition submission.** The core audio/test/metrics stack is implemented. The local test suite passes. No Gnani API key was available during construction, so no production transcription or winning-score claim has been made.

## What it does

1. Upload or record a **consented, ≤30-second PCM WAV** (8–96kHz, mono/stereo). Browser recording saves WAV locally.
2. Supply an **exact ground-truth transcript**, ideally in the same writing system the selected model will return.
3. Configure noise (synthetic broadband/crowd-like/traffic-like/hum OR a *real, uploaded ambient noise recording*), target SNR, optional 300–3400Hz telephone-style channel, deterministic random seed.
4. Generate three audio variants: **clean** (reference), **degraded**, **recovered** (stationary spectral-gating of degraded audio). All three files are playable.
5. In **Preview** mode: generate audio without model inference. No accuracy numbers are invented.
6. In **Live** mode: run **three REAL REST transcription requests to Gnani Prisma**, measure WER/CER and exact critical term retention, and display all raw transcripts, errors and wall-clock times.
7. Browse experiment history and export a CSV with original evidence.

**IMPORTANT:** The recovery is a simple signal-processing filter. It is **not** a trained AI denoiser or an auto-corrected transcript. It can help, do nothing, or harm accuracy; the UI reports whichever outcome the real model produces. Synthetic traffic/crowd-like mixtures are **not real telephonic audio**. To pursue Gnani's Noise Canceller award, gather and evaluate **consented actual noisy recordings or real phone audio** separately.

## Quick start (Windows 11 / PowerShell)

```powershell
cd shorlab
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
Copy-Item .env.example .env
# Edit .env and set GNANI_API_KEY=YOUR_KEY (do not commit it)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open **http://127.0.0.1:8000**. Without a key, **Preview audio only** still works. Browser recording needs a localhost or HTTPS origin and microphone permission.

macOS/Linux:
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## API key and Gnani models

Get programme registration and credits from **https://www.gnani.ai/internship**; create an API key from **https://app.gnani.ai/voice**. Put it in server-side `.env` only. Never expose your key in client-side JS, GitHub, logs or demos.

Implementation verified against [Gnani's official REST transcription documentation](https://docs.gnani.ai/api/STT/speech-to-text):

- `POST https://api.vachana.ai/stt/v3`
- `X-API-Key-ID` server-side header
- `multipart/form-data`: `audio_file`, `model`, `language_code`, `format=verbatim`
- Prisma v2.5 selected by default; Prisma v3.0 optionally available
- `indic-auto` supported on v3.0, not v2.5
- **Up to 30 seconds per clip**, so split longer recordings before upload.

The app makes **three billable/credit-consuming Gnani requests per live run**. Do not mistake source WAV preview or mocked unit tests for a real model benchmark.

## Project structure

```
app/main.py            FastAPI REST endpoints and experiment orchestration
app/audio.py           WAV I/O, deterministic noise injection, telephony and recovery
app/gnani.py           Real Gnani API adapter, guarded credentials, response errors
app/metrics.py         Unicode-aware WER, CER and critical phrase checks
app/storage.py         SQLite history and local WAV artifacts
app/static/            Original responsive dark UI (no JS build step)
scripts/               Reproducible CSV batch evaluator
samples/               [not included: record consented speech yourself]
tests/                 Unit and API tests
docs/recording-script.md 20 suggested prompts across Indian languages
docs/benchmark-manifest-template.csv  Benchmark manifest example
```

## Tests

```bash
python -m pytest -q
```

Unit tests cover round-trip WAV encoding, audio length, deterministic noise profiles, recovery output, Unicode handling, WER, exact critical terms, local preview truthfulness, and API refusal without a key. These are **software tests**, not demonstrations of improved ASR.

## Batch evaluation

Record test WAV clips and write a CSV manifest beside your recordings (see `docs/benchmark-manifest-template.csv`). Then:

```bash
python scripts/batch_benchmark.py --manifest docs/my-manifest.csv --limit 4 --dry-run
python scripts/batch_benchmark.py --manifest docs/my-manifest.csv --output evidence.csv --limit 4 --model prisma-v2.5
```

Each valid row triggers three real requests, unless `--dry-run`. The CSV records a SHA-256 of source WAV, model, profile, language, SNR, seed, true API request IDs, raw transcripts, WER/CER and explicit errors. Never tune your method on the final held-out test clips.

## Critical research caveats

- **WER** = `(substitutions + deletions + insertions) / reference words × 100`; it may exceed 100%. **CER** similarly counts character edits.
- Tokenization uses NFKC casefolding and punctuation stripping while preserving Indic scripts. It is not code-mix-aware transliteration, so a Hindi native-script reference and Romanized hypothesis can appear artificially wrong. Specify a consistent annotation policy.
- Critical term checks are simple exact token/phrase matches, not semantic inference. Only terms present in the reference are eligible for recall.
- Audio SNR is set relative to the full-signal RMS; active speech SNR may differ when recordings have silence.
- A simulated phone bandpass is NOT a real PSTN codec/network or a verified phone-call test.
- This local MVP does not include authentication, multi-tenant isolation, data deletion or upload-abuse protection. **Do not deploy publicly as-is.** Local `data/` contains raw audio + reference text and is gitignored.
- The app does not store your API key and never sends it to the browser.

## Award-ready improvements (next milestones)

1. Obtain actual self-recorded/consented noisy speech and a proper blind evaluation set with at least 3 speakers.
2. Build an **adaptive recovery policy** that chooses the original or filtered audio without peeking at the ground-truth transcript. Prove change on a held-out set; include cases where recovery loses.
3. Compare v2.5 and v3.0 in a paired benchmark, consistently preserving output formatting and language.
4. Track code-switch segments, proper nouns, critical numbers and user-important failure cases.
5. Turn the results into a 60-second transparent video showing real API requests, audio, reference and side-by-side transcriptions. Post first on LinkedIn/X with `#GnaniAI` and `#GreatIndianAIInternshipChallenge`; submit the designated links before **November 10, 2026, 11:59 PM IST**.

## Inspiration and attribution

Inspired at a high level by public discussion of **Kasauti (कसौटी)**, an Indic voice-agent test platform, which was shared in Bolna's builders community. shor is a **fresh implementation** focused on audio reliability benchmarking, with independently authored code and a distinct workflow. Do not claim Kasauti's results or copy its code/assets without checking its license and attribution requirements.

## Academic honesty and safety

No synthetic performance claims; no hidden use of gold transcripts to choose best outputs; no simulated calls presented as real calls; no real customer personal data. Consent is required before collecting speech/ambient recordings. Do not upload sensitive medical, financial or identity information.

## Cloud development

From `/workspace/SHOR`, install `requirements-dev.txt` into a Python 3.12 virtual environment, run `python -m pytest -q`, then `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Configure `GNANI_API_KEY` server-side through environment settings or an ignored `.env`. Tests use local fixtures and mocked inference, and are not live Gnani evidence.
