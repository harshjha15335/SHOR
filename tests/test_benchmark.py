"""Software fixtures only: no real speakers, consent records or API evidence."""
import csv,hashlib,json
from pathlib import Path
import numpy as np
import pytest
from app.audio import encode_wav
from app.benchmark import FIELDS,validate_manifest,summarize_records


def manifest(tmp_path, overrides=None, extra_rows=None):
    raw=encode_wav(np.sin(np.arange(16000)*.1).astype(np.float32)*.1)
    (tmp_path/'fixture.wav').write_bytes(raw)
    row=dict.fromkeys(FIELDS,'')
    row.update(sample_id='fixture-1',audio_path='fixture.wav',speaker_id='test-double-speaker',language='hi-IN',code_mixed='false',recording_environment='software test fixture',audio_condition='fixture only',actual_or_synthetic_condition='actual',recording_device_category='test fixture',original_sample_rate='16000',processed_sample_rate='16000',duration_seconds='1',consent_status='consented',reference_transcript='नमस्ते दुनिया',transcript_script_convention='Devanagari',critical_terms='दुनिया',dataset_split='development',file_sha256=hashlib.sha256(raw).hexdigest(),noise_profile='none',configured_snr_db='8',telephone_simulation='false',processing_seed='42',source_utterance_id='fixture-source',reference_review_status='reviewed')
    row.update(overrides or {})
    p=tmp_path/'manifest.csv'
    with p.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows([row]+(extra_rows or []))
    return p,row


def test_manifest_verifies_audio_and_provenance(tmp_path):
    p,_=manifest(tmp_path);rows,result=validate_manifest(p)
    assert len(rows[0]['_audio'])==16000
    assert result['samples']==1 and result['speakers']==1

@pytest.mark.parametrize('override,match',[
    ({'consent_status':'unknown'},'consent'),
    ({'reference_review_status':'pending'},'reviewed'),
    ({'file_sha256':'0'*64},'hash'),
    ({'configured_snr_db':'nan'},'finite'),
    ({'processing_seed':'-1'},'Seed'),
    ({'reference_transcript':'!!!'},'empty'),
    ({'duration_seconds':'nan'},'Duration'),
    ({'noise_profile':'traffic_synthetic'},'labeled actual'),
    ({'telephone_simulation':'true'},'labeled actual'),
    ({'original_sample_rate':'8000'},'sample rate'),
    ({'dataset_split':'test'},'dataset_split'),
])
def test_invalid_manifest_fails_before_live(tmp_path,override,match):
    p,_=manifest(tmp_path,override)
    with pytest.raises(ValueError,match=match):validate_manifest(p)


def test_empty_manifest_rejected(tmp_path):
    p=tmp_path/'manifest.csv';p.write_text(','.join(FIELDS)+'\n')
    with pytest.raises(ValueError,match='zero'):validate_manifest(p)


def test_identical_audio_cannot_cross_splits(tmp_path):
    p,row=manifest(tmp_path)
    manifest(tmp_path,extra_rows=[row|{'sample_id':'fixture-2','dataset_split':'heldout'}])
    with pytest.raises(ValueError,match='crosses dataset splits'):validate_manifest(p)


def record(sample,variant,edits,words,**extra):
    return {'sample_id':sample,'source_sha256':'test-source-'+sample,'reference':'test reference '+sample,'experiment_id':'test-only','model':'test-double','variant':variant,'status':'real','metrics':{'wer':100*edits/words,'reference_words':words,'word_edits':edits,'reference_characters':words*4,'character_edits':edits,'critical_checks':[]},**extra}


def test_weighted_summary_and_paired_regressions():
    rows=[record('a','degraded',1,2),record('b','degraded',1,8),record('a','adaptive',0,2),record('b','adaptive',2,8)]
    summary=summarize_records(rows)
    base=summary['groups']['variant']['degraded']
    assert base['micro_wer']==20
    assert base['macro_wer']==31.25
    comparison=summary['paired_recovery']['adaptive']
    assert comparison['improved']==1 and comparison['worsened']==1
    assert comparison['improvement_percentage_points']==0


def test_unscored_preview_not_zero_accuracy():
    summary=summarize_records([{'status':'not_run','variant':'clean','metrics':None}])
    assert summary['overall']['micro_wer'] is None
    assert summary['real_samples']==0
    assert summary['overall']['p95_seconds'] is None


def test_duplicate_evidence_not_silently_double_counted():
    r=record('a','degraded',1,4)
    with pytest.raises(ValueError,match='Duplicate'):summarize_records([r,r])


def test_latency_minimum_counts():
    rows=[record(str(i),'degraded',0,4,wall_time_seconds=i+1) for i in range(5)]
    summary=summarize_records(rows)['overall']
    assert summary['p50_seconds']==3
    assert summary['p95_seconds'] is None


def load_runner(name):
    import importlib.util
    path=Path(__file__).resolve().parents[1]/'scripts'/f'{name}.py'
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def test_dry_run_processes_audio_without_live_calls(tmp_path,monkeypatch,capsys):
    path,_=manifest(tmp_path)
    runner=load_runner('batch_benchmark')
    monkeypatch.setattr(runner,'transcribe',lambda *a:pytest.fail('Dry run must not call API'))
    monkeypatch.setattr('sys.argv',['batch','--manifest',str(path),'--dry-run'])
    runner.main()
    assert 'zero API requests' in capsys.readouterr().out


def test_live_batch_budget_fails_before_any_call(tmp_path,monkeypatch):
    path,_=manifest(tmp_path)
    runner=load_runner('batch_benchmark')
    monkeypatch.setattr(runner,'transcribe',lambda *a:pytest.fail('No authorized calls'))
    monkeypatch.setattr('sys.argv',['batch','--manifest',str(path),'--allow-live','--max-api-calls','1'])
    with pytest.raises(SystemExit) as exc:runner.main()
    assert exc.value.code==2


def test_partial_failure_retained_and_nonzero(tmp_path,monkeypatch):
    path,_=manifest(tmp_path)
    runner=load_runner('batch_benchmark')
    monkeypatch.setattr(runner,'configured',lambda:True)
    calls=[]
    def fake(*args):
        calls.append(args)
        if len(calls)==2:raise runner.GnaniError('test-only failure')
        return {'status':'real','transcript':'नमस्ते दुनिया','request_id':'test-double-only','wall_time_seconds':.01}
    monkeypatch.setattr(runner,'transcribe',fake)
    output=tmp_path/'results.jsonl'
    monkeypatch.setattr('sys.argv',['batch','--manifest',str(path),'--allow-live','--max-api-calls','4','--output',str(output)])
    with pytest.raises(SystemExit) as exc:runner.main()
    assert exc.value.code==1 and len(calls)==4
    rows=[json.loads(line) for line in output.read_text().splitlines()]
    assert len(rows)==4 and sum(r['status']=='error' for r in rows)==1
    assert rows[1]['metrics'] is None
    assert all(r['audio_sha256'] for r in rows)


def test_corrupt_summary_denominators_rejected():
    r=record('a','degraded',1,4);r['metrics']['reference_words']=0
    with pytest.raises(ValueError,match='positive'):summarize_records([r])


@pytest.mark.parametrize('field,value',[('source_sha256','different'),('reference','different'),('condition','different')])
def test_pairing_rejects_mismatched_provenance(field,value):
    a=record('a','degraded',1,4); b=record('a','adaptive',0,4)
    b[field]=value
    result=summarize_records([a,b])
    assert result['paired_recovery']=={}
    assert result['rejected_pairs'][0]['reason']=='mismatched_source_reference_condition_or_scoring'


def test_pairing_rejects_different_scoring_convention():
    a=record('a','degraded',1,4); b=record('a','adaptive',0,4)
    a['metrics']['scoring_mode']='strict';b['metrics']['scoring_mode']='unicode'
    assert summarize_records([a,b])['paired_recovery']=={}


def test_web_recovery_modes_kept_separate():
    from app.benchmark import summarize_runs
    def run(i,mode):
        return {'id':i,'model':'test-double','reference':'test','source_sha256':'test-hash','recovery':{'mode':mode},'audio_condition':'noisy_real','noise_profile':'none','telephony':False,'results':{'degraded':record(i,'degraded',1,4),'recovered':record(i,'recovered',0,4)}}
    summary=summarize_runs([run('a','fixed'),run('b','adaptive')])
    assert set(summary['paired_recovery'])=={'recovered:fixed','recovered:adaptive'}


def test_scoring_failure_keeps_real_transcript(tmp_path,monkeypatch):
    path,_=manifest(tmp_path)
    runner=load_runner('batch_benchmark')
    monkeypatch.setattr(runner,'configured',lambda:True)
    monkeypatch.setattr(runner,'transcribe',lambda *a:{'status':'real','transcript':'test-double-only','request_id':'test-id','wall_time_seconds':.01})
    def bad_score(*a):raise ValueError('test-only scoring failure')
    monkeypatch.setattr(runner,'score',bad_score)
    output=tmp_path/'results.jsonl'
    monkeypatch.setattr('sys.argv',['batch','--manifest',str(path),'--allow-live','--max-api-calls','4','--output',str(output)])
    with pytest.raises(SystemExit):runner.main()
    records=[json.loads(line) for line in output.read_text().splitlines()]
    assert all(r['status']=='real' and r['transcript']=='test-double-only' and r['metrics_error'] for r in records)
    assert summarize_records(records)['overall']['scoring_errors']==4


def test_smoke_verifies_output_before_one_call(tmp_path,monkeypatch):
    path,_=manifest(tmp_path);runner=load_runner('live_smoke')
    monkeypatch.setattr(runner,'configured',lambda:True)
    destination=tmp_path/'blocked';destination.write_text('not a directory')
    monkeypatch.setattr(runner,'transcribe',lambda *a:pytest.fail('Must not spend credits without evidence output'))
    monkeypatch.setattr('sys.argv',['smoke','--manifest',str(path),'--sample-id','fixture-1','--allow-one-live-call','--output',str(destination/'out.jsonl')])
    with pytest.raises(OSError):runner.main()


def test_smoke_scoring_error_keeps_traceable_transcript(tmp_path,monkeypatch):
    path,_=manifest(tmp_path);runner=load_runner('live_smoke')
    monkeypatch.setattr(runner,'configured',lambda:True)
    calls=[]
    def fake(*a):
        calls.append(a);return {'status':'real','transcript':'test-double-only','request_id':'test-only-id'}
    monkeypatch.setattr(runner,'transcribe',fake)
    def bad_score(*a):raise ValueError('test-only scoring failure')
    monkeypatch.setattr(runner,'score',bad_score)
    output=tmp_path/'smoke.jsonl'
    monkeypatch.setattr('sys.argv',['smoke','--manifest',str(path),'--sample-id','fixture-1','--allow-one-live-call','--output',str(output)])
    with pytest.raises(SystemExit) as exc:runner.main()
    result=json.loads(output.read_text())
    assert exc.value.code==1 and len(calls)==1
    assert result['status']=='real' and result['transcript']=='test-double-only' and result['request_id']=='test-only-id'
    assert result['metrics'] is None and result['metrics_error']


def test_web_repeated_source_counts_one_audio_sample():
    from app.benchmark import summarize_runs
    def run(i):
        return {'id': i, 'source_sha256':'same-source-hash','results':{'clean':{'status':'real','metrics':None}}}
    assert summarize_runs([run('first'),run('repeat')])['real_samples']==1


def test_smoke_records_actual_failure_status_timing_and_private_file(tmp_path,monkeypatch):
    from app.gnani import GnaniError
    path,_=manifest(tmp_path);runner=load_runner('live_smoke')
    monkeypatch.setattr(runner,'configured',lambda:True)
    calls=[]
    def failed(*args):
        calls.append(args)
        raise GnaniError('Test-only access denied','access_denied',403)
    monkeypatch.setattr(runner,'transcribe',failed)
    output=tmp_path/'private-smoke.jsonl'
    monkeypatch.setattr('sys.argv',['smoke','--manifest',str(path),'--sample-id','fixture-1','--allow-one-live-call','--output',str(output)])
    with pytest.raises(SystemExit):runner.main()
    record=json.loads(output.read_text())
    assert len(calls)==1 and record['request_attempts']==1
    assert record['http_status']==403 and record['error_code']=='access_denied'
    assert record['wall_time_seconds']>=0 and record['transcript'] is None
    assert output.stat().st_mode & 0o777 == 0o600
