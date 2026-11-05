#!/usr/bin/env python3
"""Reproducible, real-Gnani multi-file ASR benchmark. Zero invented transcripts.

Example:
    python scripts/batch_benchmark.py --manifest docs/benchmark-manifest-template.csv --output results.csv --limit 5

Important: requests use credits (three calls per row). Only use consented audio.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv
from app.audio import create_variants, decode_wav, encode_wav
from app.gnani import transcribe, configured, GnaniError
from app.metrics import score, compare


def main():
    parser=argparse.ArgumentParser(description="Paired ASR reliability benchmark on real Gnani Prisma calls")
    parser.add_argument('--manifest',required=True,help="CSV with audio_path,reference,language,profile,snr_db,telephony,seed,critical_terms")
    parser.add_argument('--output',default='benchmark_results.csv')
    parser.add_argument('--model',choices=['prisma-v2.5','prisma-v3.0'],default='prisma-v2.5')
    parser.add_argument('--limit',type=int,default=10,help="Safety cap on number of samples (3 calls per sample)")
    parser.add_argument('--dry-run',action='store_true',help="Validate manifest and audio; no API calls")
    args=parser.parse_args()
    load_dotenv()
    manifest=Path(args.manifest).resolve()
    if not manifest.exists():parser.error('Manifest file does not exist')
    if not args.dry_run and not configured():parser.error('GNANI_API_KEY is missing. Copy .env.example to .env first.')
    with manifest.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    if not rows:parser.error('Manifest contains no data')
    if args.limit <= 0:parser.error('--limit must be positive')
    selected=rows[:args.limit]
    print(f"Rows: {len(selected)}; API calls: {0 if args.dry_run else len(selected)*3}; model: {args.model}")
    if not args.dry_run: print('These are real paid/credit-consuming transcriptions.')
    out=[]
    for idx,row in enumerate(selected,1):
        path=(manifest.parent / row['audio_path']).resolve()
        if not path.is_file() or path.suffix.lower()!='.wav':
            print(f"Skipped row {idx}: invalid/missing WAV {path}",file=sys.stderr);continue
        raw=path.read_bytes()
        try:
            audio=decode_wav(raw)
            profile=row.get('profile','traffic_synthetic')
            snr=float(row.get('snr_db') or 8)
            telephony=row.get('telephony','true').lower() in ('1','true','yes')
            seed=int(row.get('seed') or 42)
            if profile=='uploaded_ambience':
                print(f"Skipped row {idx}: uploaded_ambience is supported by web app; batch manifest uses synthetic profiles only",file=sys.stderr);continue
            waves=create_variants(audio,profile,snr,telephony,seed)
        except (ValueError, KeyError) as exc:
            print(f"Skipped row {idx}: {exc}",file=sys.stderr);continue
        ref=row.get('reference','')
        if not ref.strip():
            print(f"Skipped row {idx}: reference transcript missing",file=sys.stderr);continue
        terms=[t.strip() for t in row.get('critical_terms','').split('|') if t.strip()]
        record={'sample':idx,'source':row['audio_path'],'audio_sha256':hashlib.sha256(raw).hexdigest(),
                'language':row.get('language','hi-IN'),'model':args.model,'profile':profile,'snr_db':snr,'telephony':telephony,'seed':seed}
        if args.dry_run:
            print(f"[{idx}] VALIDATED {path.name} ({len(audio)/16000:.1f}s); variants = {','.join(waves)}")
            continue
        per={}
        for variant,wave in waves.items():
            try:
                transcript=transcribe(encode_wav(wave),record['language'],args.model)
                m=score(ref,transcript['transcript'],terms)
                per[variant]=m
                out.append(record|{'variant':variant,'status':'real','reference':ref,'transcript':transcript['transcript'],
                                   'wer':m['wer'],'cer':m['cer'],'word_edits':m['word_edits'],
                                   'reference_words':m['reference_words'],'critical_recall':m['critical_recall'],
                                   'api_request_id':transcript.get('request_id'),'elapsed_s':transcript['wall_time_seconds'],'error':''})
            except (GnaniError,ValueError) as exc:
                out.append(record|{'variant':variant,'status':'error','reference':ref,'transcript':'',
                                   'wer':'','cer':'','word_edits':'','reference_words':'','critical_recall':'',
                                   'api_request_id':'','elapsed_s':'','error':str(exc)})
        delta=compare(per.get('degraded'),per.get('recovered'))
        print(f"[{idx}] {path.name} | degraded WER={per.get('degraded',{}).get('wer','ERROR')} | recovery change={delta.get('wer_change_percentage_points','n/a') if delta else 'n/a'} pp")
        # Save progressively so partial results are retained if there is a later failure.
        output=Path(args.output)
        with output.open('w',encoding='utf-8',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(out[0]));writer.writeheader();writer.writerows(out)
    if args.dry_run: print('DRY RUN COMPLETE — zero Gnani API requests; no benchmark scores.')
    else:print('Saved',args.output,'— contains only real Gnani API results or explicit errors.')

if __name__=='__main__':main()
