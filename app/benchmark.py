"""Manifest validation and offline evidence summaries; never creates model results."""
from __future__ import annotations
import csv
import hashlib
import math
from collections import defaultdict
from pathlib import Path
import numpy as np
from .audio import decode_wav
from .metrics import normalize

FIELDS = ['sample_id','audio_path','speaker_id','language','code_mixed','recording_environment','audio_condition','actual_or_synthetic_condition','recording_device_category','original_sample_rate','processed_sample_rate','duration_seconds','consent_status','reference_transcript','transcript_script_convention','critical_terms','dataset_split','file_sha256','noise_profile','configured_snr_db','telephone_simulation','processing_seed','source_utterance_id','reference_review_status']
LANGUAGES = {'hi-IN','en-IN','ta-IN','te-IN','kn-IN','ml-IN','mr-IN','bn-IN','gu-IN','pa-IN','indic-auto'}
PROFILES = {'none','broadband','crowd_synthetic','traffic_synthetic','hum_synthetic','uploaded_ambience'}

def boolean(value):
    if str(value).lower() in {'true','1','yes'}: return True
    if str(value).lower() in {'false','0','no'}: return False
    raise ValueError('Expected true/false')

def validate_manifest(manifest: Path) -> tuple[list[dict], dict]:
    """Validate every row before any paid call. Returns rows with resolved local paths."""
    manifest = Path(manifest).resolve()
    with manifest.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError('Manifest missing required fields: '+', '.join(sorted(set(FIELDS)-set(reader.fieldnames or []))))
        rows=list(reader)
    if not rows: raise ValueError('Manifest has zero samples; collect consented recordings first')
    if len(rows)>500: raise ValueError('Manifest exceeds 500 rows; evaluate in bounded cohorts')
    total_decoded_bytes=0
    seen_ids=set(); hash_splits={}; utterance_splits={}; speaker_splits=defaultdict(set)
    for index,row in enumerate(rows,2):
        try:
            if not row['sample_id'] or row['sample_id'] in seen_ids: raise ValueError('Missing or duplicate sample_id')
            seen_ids.add(row['sample_id'])
            if row['consent_status'] != 'consented': raise ValueError('Explicit consent_status=consented required')
            if row['reference_review_status'] != 'reviewed': raise ValueError('Reference must be manually reviewed before evaluation')
            if not normalize(row['reference_transcript']): raise ValueError('Reference is empty after normalization')
            for field in ['speaker_id','recording_environment','audio_condition','recording_device_category','transcript_script_convention','source_utterance_id']:
                if not row[field].strip(): raise ValueError(f'{field} required')
            if row['language'] not in LANGUAGES: raise ValueError('Unsupported language')
            if row['dataset_split'] not in {'development','validation','heldout'}: raise ValueError('Invalid dataset_split')
            if row['actual_or_synthetic_condition'] not in {'actual','synthetic'}: raise ValueError('Condition must be actual or synthetic')
            boolean(row['code_mixed']); row['_telephony']=boolean(row['telephone_simulation'])
            if row['noise_profile'] not in PROFILES: raise ValueError('Unsupported noise profile')
            if row['actual_or_synthetic_condition']=='actual' and (row['noise_profile'] != 'none' or row['_telephony']):
                raise ValueError('Synthetic noise or telephone simulation cannot be labeled actual')
            row['_snr']=float(row['configured_snr_db']); row['_seed']=int(row['processing_seed'])
            if not math.isfinite(row['_snr']) or not -5<=row['_snr']<=30: raise ValueError('SNR must be finite and -5..30')
            if not 0<=row['_seed']<=10000000: raise ValueError('Seed outside bounds')
            path=(manifest.parent/row['audio_path']).resolve()
            if path.suffix.lower()!='.wav' or not path.is_file(): raise ValueError('Missing WAV file')
            if path.stat().st_size>8_000_000: raise ValueError('WAV exceeds 8 MB')
            raw=path.read_bytes(); digest=hashlib.sha256(raw).hexdigest()
            if row['file_sha256'].lower()!=digest: raise ValueError('Audio hash mismatch')
            audio=decode_wav(raw)
            total_decoded_bytes+=audio.nbytes
            if total_decoded_bytes>128_000_000: raise ValueError('Decoded manifest audio exceeds 128 MB; use smaller cohorts')
            import io,wave
            with wave.open(io.BytesIO(raw),'rb') as w: original_rate=w.getframerate()
            if int(row['original_sample_rate'])!=original_rate: raise ValueError('Original sample rate mismatch')
            if int(row['processed_sample_rate'])!=16000: raise ValueError('Processed sample rate must be 16000')
            duration=float(row['duration_seconds'])
            if not math.isfinite(duration) or abs(duration-len(audio)/16000)>.02: raise ValueError('Duration mismatch')
            split=row['dataset_split']
            for mapping,key,label in [(hash_splits,digest,'Identical audio'),(utterance_splits,row['source_utterance_id'],'Source utterance')]:
                if key in mapping and mapping[key]!=split: raise ValueError(f'{label} crosses dataset splits')
                mapping[key]=split
            speaker_splits[row['speaker_id']].add(split)
            row['_path']=path; row['_audio']=audio; row['_raw']=raw
            if row['noise_profile']=='uploaded_ambience':
                ambience=(manifest.parent/row.get('ambience_path','')).resolve()
                if not ambience.is_file() or ambience.stat().st_size>8_000_000: raise ValueError('Valid ambience_path WAV required')
                ambient_raw=ambience.read_bytes()
                if row.get('ambience_sha256')!=hashlib.sha256(ambient_raw).hexdigest(): raise ValueError('Ambience hash mismatch')
                row['_ambience']=decode_wav(ambient_raw)
        except (ValueError,TypeError,KeyError,OSError) as exc:
            raise ValueError(f'Manifest row {index}: {exc}') from exc
    return rows, {'samples':len(rows),'speakers':len(speaker_splits),'split_counts':{s:sum(r['dataset_split']==s for r in rows) for s in ['development','validation','heldout']},'speaker_disjoint':all(len(s)==1 for s in speaker_splits.values()),'limitation':'Near-duplicate acoustic leakage requires human review; exact hashes and source utterance IDs are checked.'}

def _aggregate(rows):
    valid=[r for r in rows if r.get('status')=='real' and r.get('metrics')]
    words=sum(r['metrics']['reference_words'] for r in valid)
    edits=sum(r['metrics']['word_edits'] for r in valid)
    chars=sum(r['metrics'].get('reference_characters',0) for r in valid)
    char_edits=sum(r['metrics'].get('character_edits',0) for r in valid)
    checks=[c for r in valid for c in r['metrics'].get('critical_checks',[]) if c.get('in_reference')]
    durations=[r['wall_time_seconds'] for r in rows if r.get('status')=='real' and isinstance(r.get('wall_time_seconds'),(float,int)) and math.isfinite(r['wall_time_seconds']) and r['wall_time_seconds']>=0]
    return {'requests':len(rows),'scored_requests':len(valid),'errors':sum(r.get('status')=='error' for r in rows),'scoring_errors':sum(bool(r.get('metrics_error')) for r in rows),'reference_words':words,'word_edits':edits,'micro_wer':round(100*edits/words,4) if words else None,'macro_wer':round(sum(r['metrics']['wer'] for r in valid)/len(valid),4) if valid else None,'micro_cer':round(100*char_edits/chars,4) if chars else None,'critical_eligible':len(checks),'critical_preserved':sum(bool(c.get('preserved')) for c in checks),'critical_recall':round(100*sum(bool(c.get('preserved')) for c in checks)/len(checks),4) if checks else None,'timing_samples':len(durations),'p50_seconds':float(np.percentile(durations,50)) if len(durations)>=5 else None,'p95_seconds':float(np.percentile(durations,95)) if len(durations)>=20 else None}

def summarize_records(records: list[dict]) -> dict:
    """Summarize recorded results only. Empty metrics stay null, never zero accuracy."""
    for r in records:
        m=r.get('metrics')
        if m:
            for field in ['word_edits','reference_words','character_edits','reference_characters']:
                value=m.get(field)
                if not isinstance(value,int) or isinstance(value,bool) or value<0:
                    raise ValueError(f'Invalid integer metric count: {field}')
            if m['reference_words']<1 or m['reference_characters']<1:
                raise ValueError('Metric denominators must be positive')
            if not isinstance(m.get('wer'),(int,float)) or not math.isfinite(m['wer']):
                raise ValueError('WER must be finite')
    groups={}
    for field in ['model','language','condition','speaker_id','variant','dataset_split','scoring_mode']:
        group=defaultdict(list)
        for r in records:
            value=(r.get('metrics') or {}).get('scoring_mode','unicode') if field=='scoring_mode' else r.get(field,'unknown')
            group[str(value)].append(r)
        groups[field]={k:_aggregate(v) for k,v in sorted(group.items())}
    pairs=defaultdict(dict)
    for r in records:
        if r.get('status')=='real' and r.get('metrics'):
            key=(r.get('experiment_id'),r.get('sample_id'),r.get('model'))
            if r.get('variant') in pairs[key]: raise ValueError('Duplicate result for same experiment/sample/model/variant')
            pairs[key][r.get('variant')]=r
    comparisons={}
    rejected_pairs=[]
    candidate_variants=sorted({r.get('variant') for r in records if r.get('variant') not in {None,'clean','degraded'}})
    for variant in candidate_variants:
        matched=[]
        for key,v in pairs.items():
            if 'degraded' not in v or variant not in v: continue
            baseline,recovered=v['degraded'],v[variant]
            required=['source_sha256','reference']
            if any(not baseline.get(f) or not recovered.get(f) for f in required):
                rejected_pairs.append({'sample_id':key[1],'variant':variant,'reason':'missing_source_or_reference_provenance'})
                continue
            consistent=all(baseline.get(f)==recovered.get(f) for f in ['source_sha256','reference','language','condition'])
            consistent=consistent and all(baseline['metrics'].get(f)==recovered['metrics'].get(f) for f in ['reference_words','reference_characters','scoring_mode'])
            if not consistent:
                rejected_pairs.append({'sample_id':key[1],'variant':variant,'reason':'mismatched_source_reference_condition_or_scoring'})
                continue
            matched.append((baseline,recovered))
        if not matched: continue
        baseline=_aggregate([a for a,b in matched]); recovered=_aggregate([b for a,b in matched])
        changes=[a['metrics']['word_edits']/a['metrics']['reference_words']-b['metrics']['word_edits']/b['metrics']['reference_words'] for a,b in matched]
        delta=baseline['micro_wer']-recovered['micro_wer']
        comparisons[variant]={'paired_samples':len(matched),'improved':sum(x>0 for x in changes),'unchanged':sum(x==0 for x in changes),'worsened':sum(x<0 for x in changes),'baseline_micro_wer':baseline['micro_wer'],'recovered_micro_wer':recovered['micro_wer'],'improvement_percentage_points':round(delta,4),'relative_improvement_percent':round(100*delta/baseline['micro_wer'],4) if baseline['micro_wer'] else None}
    real=[r for r in records if r.get('status')=='real']
    return {'schema_version':1,'record_count':len(records),'real_samples':len({r.get('sample_id') for r in real if r.get('sample_id')}),'speakers':len({r.get('speaker_id') for r in real if r.get('speaker_id')}),'overall':_aggregate(records),'groups':groups,'paired_recovery':comparisons,'rejected_pairs':rejected_pairs,'limitations':['Software test doubles are not live evidence.','Overall counts pool variants/models/scoring modes; use grouped and paired metrics for scientific comparisons.','p50 requires 5 observations; p95 requires 20.','No confidence intervals or statistical significance claimed.']}

def summarize_runs(runs):
    records=[]
    for run in runs:
        for variant,result in run.get('results',{}).items():
            if variant=='recovered':
                variant='recovered:'+run.get('recovery',{}).get('mode','legacy_fixed')
            condition=f"{run.get('audio_condition','unspecified')} | noise={run.get('noise_profile','unknown')} | telephone_simulation={run.get('telephony','unknown')}"
            records.append({**result,'experiment_id':run['id'],'sample_id':run.get('source_sha256') or run.get('sample_id',run['id']),'speaker_id':run.get('speaker_id'),'language':run.get('language'),'model':run.get('model'),'condition':condition,'dataset_split':run.get('dataset_split','unassigned'),'variant':variant,'source_sha256':run.get('source_sha256'),'reference':run.get('reference')})
    return summarize_records(records)
