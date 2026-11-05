# SHOR — Indic Speech Reliability & Recovery Lab

SHOR measures how recognition fails on Indian-language speech and compares audio recovery without letting the recovery policy read the reference transcript. It extends the supplied FastAPI application and its dark/lime browser interface; it does not modify Gnani model weights.

**Current evidence:** the local preview workflow works; live Gnani inference, a real multi-speaker benchmark, held-out recovery gains and award readiness remain unvalidated. Software test doubles and synthetic tones are not speech-performance evidence. See [baseline audit](docs/BASELINE_AUDIT.md), [API validation](evidence/API_validation.md) and [results status](evidence/RESULTS.md).

## What works locally

- Upload or record short PCM WAV audio: 0.2–30 seconds, 8–96 kHz mono/stereo, supported 8/16/32-bit PCM, up to 8 MB per file. Browser microphone capture requires a secure origin and permission.
- Generate original, degraded and recovered signals using deterministic synthetic noise, uploaded ambience and optional **simulated** telephone filtering. Actual noisy recordings must be labeled separately.
- Choose pass-through, fixed spectral attenuation or an interpretable, reference-free acoustic recovery heuristic. It may worsen speech recognition; no improvement is guaranteed.
- Score real transcripts using strict script-preserving or Unicode-normalized WER/CER; inspect deterministic word alignments, substitution/deletion/insertion counts, exact critical-term/number/phrase recall and labeled heuristic review prompts.
- Inspect evidence hashes, real provider metadata when returned, processing decisions, request errors, history filters and a benchmark overview. Preview scores remain unmeasured.
- Export CSV/JSON and delete runs and audio. Default local retention is seven days on access, with a 500-run cap. Optional private-demo authentication and request limits are included; these do not constitute a production security certification.

## Run

Use Python 3.12 from the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements-lock.txt
python -m pytest -q
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

On Windows, use `py -3.12 -m venv .venv`, activate `.\.venv\Scripts\Activate.ps1`, then the same Python commands. Dependency ranges remain in `requirements.txt` and `requirements-dev.txt`; `requirements-lock.txt` records the resolved test environment. A CI workflow is provided, but remote CI success must be checked rather than assumed.

Preview mode needs no account. Live requests require server-side `GNANI_API_KEY`, an allowed route to `api.vachana.ai`, supported account entitlement and available credits. Set the key securely in environment settings or an ignored `.env`; never paste it into browser code or Git. Configuration saving does not automatically prove runtime activation. Health distinguishes key presence from observed successful requests.

The web live action requires explicit approval for **three requests**. First use the separate one-call smoke runner with a reviewed, consented real recording; do not start a full benchmark before access and the credit budget are understood. No automatic retry is performed; a timeout may still have consumed credits.

## Architecture and integration

Browser → FastAPI → WAV validation / noise transformations → selected audio recovery → optional Gnani REST calls → scoring → local SQLite and WAV artifacts.

| File | Responsibility |
|---|---|
| `app/main.py` | Workbench, evidence API, bounded uploads, private-demo controls |
| `app/audio.py` | PCM conversion, deterministic mixtures, simulated telephone channel |
| `app/recovery.py` | Reference-free acoustic policy and decision evidence |
| `app/metrics.py` | Script-preserving metrics, alignment and critical-term diagnostics |
| `app/gnani.py` | Server-side REST adapter and observed integration status |
| `app/storage.py` | Local history, deletion and retention |
| `app/benchmark.py` | Manifest validation and offline weighted summaries |
| `scripts/` | Budgeted live smoke/benchmark runners and offline summary regeneration |

The retained adapter uses `POST https://api.vachana.ai/stt/v3`, `X-API-Key-ID`, multipart `audio_file`, `model`, `language_code`, and `format=verbatim`. Selectors support Prisma v2.5 and v3.0, with `indic-auto` restricted to v3.0. **Current official documentation could not be reverified because the proxy returned 403.** No new undocumented parameters were added. Returned model IDs and request IDs remain null when the provider omits them; requested model is recorded separately.

## Collect and reproduce evidence

Copy the header-only [dataset template](evidence/dataset_manifest.csv) outside the repository, collect consented real recordings, and review exact transcripts before inference. See [collection protocol](evidence/evaluation_protocol.md), [data dictionary](evidence/data_dictionary.md) and [research method](docs/RESEARCH_METHOD.md). Target Hindi/Hinglish and Tamil/Tanglish first; additional selector options do not prove language-specific quality.

```bash
# Local validation and transformations; no model requests.
python scripts/batch_benchmark.py --manifest /private/manifest.csv --dry-run --limit 20

# ONE real request; requires secure credentials, access and reviewed real speech.
python scripts/live_smoke.py --manifest /private/manifest.csv --sample-id SAMPLE_ID \
  --allow-one-live-call --output evidence/raw_results/smoke.jsonl

# Optional paired comparison, only AFTER approval for its eight calls.
python scripts/batch_benchmark.py --manifest /private/manifest.csv --limit 1 \
  --models prisma-v2.5 prisma-v3.0 --allow-live --max-api-calls 8 \
  --output evidence/raw_results/paired.jsonl

# Existing evidence only; no API calls or credits.
python scripts/summarize_evidence.py evidence/raw_results/paired.jsonl \
  --output evidence/aggregate_results/paired.json
```

The research batch runner uses **four variants per model**: clean, degraded, fixed and adaptive. This differs intentionally from the web workbench's three-path experiment. Live runners preserve errors and refuse output-file overwrites. Corpus WER uses total edits / total reference words; macro WER is separately labeled. Use matched sample/model groups when comparing recovery. Empty data does not imply zero error.

## Limits and privacy

No real speech dataset, consenting speaker count, authenticated provider request, measured ASR gain, confidence claim, or live demo video is supplied. The acoustic policy is a deterministic engineering hypothesis, not a trained or tuned denoiser. Exact number recall does not equate digits and number words. Cross-script transliteration is not silently applied. Actual call audio and synthetic telephone filtering are different conditions.

Keep recordings, filled manifests, raw evidence and credentials private. `.gitignore` is an accidental-commit safeguard, not anonymization. SQLite/WAV storage is local plaintext. Deletion does not erase external backups or SQLite forensic remnants. Read [deployment guidance](docs/DEPLOYMENT.md) before any remote access. Public deployment and competition publication have not been performed.

## Competition and attribution

The supplied brief targets the Noise Canceller Award within the Great Indian AI Internship Challenge and cites 10 November 2026, 11:59 PM IST. These terms and current registration requirements were not independently reverified. Check the [official programme page](https://www.gnani.ai/internship) before submission. [Submission materials](docs/SUBMISSION_PACKAGE.md) are drafts with explicit evidence gaps.

Kasauti is credited as conceptual inspiration only. SHOR's scope is independently implemented speech reliability measurement and reference-free recovery. No Kasauti code/assets or results are claimed. No new license or ownership representation is made; resolve rights and contributor permissions before distribution under a chosen license.

## Gnani connection panel

The website shows server credential availability, a labeled startup-policy snapshot and actual observed authentication separately. **Recheck connection** reads status without Gnani calls or credit use. A saved HTTP secret may still require binding/application to the running environment. Keep credentials server-side; no browser key entry is needed. See [connection fix](docs/GNANI_CONNECTION_FIX.md).
