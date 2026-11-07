"""Storage privacy and retention fixtures; all data is synthetic and temporary."""
from datetime import datetime,timedelta,timezone
from uuid import uuid4
import pytest
from app import storage

@pytest.fixture(autouse=True)
def temporary_storage(tmp_path,monkeypatch):
 monkeypatch.setattr(storage,'ROOT',tmp_path)
 monkeypatch.setattr(storage,'AUDIO_DIR',tmp_path/'audio')
 monkeypatch.setattr(storage,'DB',tmp_path/'runs.sqlite3')
 monkeypatch.setenv('SHOR_RETENTION_HOURS','168')
 monkeypatch.setenv('SHOR_MAX_RUNS','500')

def record(**updates):
 r={'id':str(uuid4()),'created_at':datetime.now(timezone.utc).isoformat(),'title':'synthetic fixture','status':'preview'}
 r.update(updates);return r

def test_save_get_list_and_delete_artifacts():
 r=record();storage.save(r,{'clean':b'test-only','degraded':b'test-only','recovered':b'test-only'})
 assert storage.get(r['id'])==r
 assert storage.list_runs()==[r]
 assert storage.audio_path(r['id'],'clean').read_bytes()==b'test-only'
 assert storage.delete(r['id']) is True
 assert not (storage.AUDIO_DIR/r['id']).exists()
 assert storage.get(r['id']) is None
 assert storage.list_runs()==[]
 assert storage.delete(r['id']) is False

def test_retention_removes_db_and_audio(monkeypatch):
 old=record(created_at=(datetime.now(timezone.utc)-timedelta(hours=2)).isoformat())
 storage.save(old,{'clean':b'test-only'})
 fresh=record();storage.save(fresh,{'clean':b'test-only'})
 monkeypatch.setenv('SHOR_RETENTION_HOURS','1')
 assert storage.prune()==1
 assert storage.get(old['id']) is None
 assert not (storage.AUDIO_DIR/old['id']).exists()
 assert storage.get(fresh['id'])==fresh

def test_capacity_rejects_without_erasing_existing(monkeypatch):
 monkeypatch.setenv('SHOR_MAX_RUNS','1')
 r=record();storage.save(r,{'clean':b'test-only'})
 second=record()
 with pytest.raises(ValueError,match='capacity'):storage.save(second,{'clean':b'test-only'})
 assert storage.get(r['id'])==r
 assert not (storage.AUDIO_DIR/second['id']).exists()

@pytest.mark.parametrize('identity',['../private','../../etc/passwd','not-a-uuid','',None])
def test_invalid_identity_never_accesses_artifact(identity):
 assert storage.get(identity) is None
 assert storage.delete(identity) is False
 assert storage.audio_path(identity,'clean') is None
 with pytest.raises(ValueError):storage.save(record(id=identity),{'clean':b'test-only'})

def test_invalid_variant_rejected():
 r=record()
 with pytest.raises(ValueError):storage.save(r,{'../private':b'test-only'})
 assert storage.audio_path(r['id'],'../private') is None

def test_file_symlink_not_served(tmp_path):
 r=record();storage.save(r,{'clean':b'test-only'})
 target=tmp_path/'outside';target.write_bytes(b'private')
 f=storage.AUDIO_DIR/r['id']/'clean.wav';f.unlink();_make_symlink(f,target)
 assert storage.audio_path(r['id'],'clean') is None
 assert storage.delete(r['id']);assert target.read_bytes()==b'private'

def test_run_directory_symlink_not_served_or_followed(tmp_path):
 r=record();storage.save(r,{'clean':b'test-only'})
 import shutil
 folder=storage.AUDIO_DIR/r['id'];shutil.rmtree(folder)
 target=tmp_path/'outside';target.mkdir();(target/'clean.wav').write_bytes(b'private')
 _make_symlink(folder,target,True)
 assert storage.audio_path(r['id'],'clean') is None
 assert storage.delete(r['id']);assert (target/'clean.wav').read_bytes()==b'private'

def test_failed_json_serialization_leaves_no_artifact():
 r=record(unserializable=object())
 with pytest.raises(TypeError):storage.save(r,{'clean':b'test-only'})
 assert not (storage.AUDIO_DIR/r['id']).exists()
 assert storage.list_runs()==[]

def test_nan_evidence_rejected():
 r=record(value=float('nan'))
 with pytest.raises(ValueError):storage.save(r,{'clean':b'test-only'})
 assert not (storage.AUDIO_DIR/r['id']).exists()


def _make_symlink(link, target, is_directory=False):
 try:
  link.symlink_to(target,target_is_directory=is_directory)
 except OSError as exc:
  if getattr(exc,'winerror',None)==1314:
   pytest.skip('Windows symlink test requires Developer Mode or symlink privilege')
  raise
