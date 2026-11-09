#!/usr/bin/env python3
"""Offline SABnzbd v5.1.3 URL/hash, safe upgrade ordering, and bad-binary rejection."""
from __future__ import annotations
from pathlib import Path
from unittest.mock import patch
import importlib.util, io, tempfile, threading
R=Path(__file__).resolve().parents[2]
A=R/'src/app'
SHA='62733e427534a1afec6a64b89dd06253f1a3cf51cb189d980f4e759c04f8d7eb'
URL='https://github.com/sabnzbd/sabnzbd/releases/download/5.1.3/SABnzbd-5.1.3-win64-bin.zip'
def check(value,why):
    if not value: raise AssertionError('v3.7.30 SAB regression: '+why)
src=(A/'sab_engine.py').read_text(encoding='utf-8')
for marker in ('SAB_VERSION = "5.1.3"','ADAPTER_VERSION = "3.7.30"',f'SAB_WINDOWS_X64_URL = "{URL}"',f'SAB_WINDOWS_X64_SHA256 = "{SHA}"',
               'self.engine_dir = self.root / SAB_VERSION','self.admin_dir = self.root / "admin"',
               'self.incomplete_dir = self.root / "incomplete"','self.state_file = self.root / "newzdeck-jobs.json"',
               'if digest != SAB_WINDOWS_X64_SHA256:', 'if rel.is_absolute() or ".." in rel.parts:',
               'self._api("shutdown", timeout=3.0)', 'self._provision_engine()',
               'if not version or not key or self._auth_kind(port, key, timeout=0.8) != "apikey":'):
    check(marker in src,'missing safeguard '+marker)
spec=importlib.util.spec_from_file_location('newzdeck_sab_test',A/'sab_engine.py');check(spec is not None and spec.loader is not None,'module load')
sab=importlib.util.module_from_spec(spec);spec.loader.exec_module(sab)
check(sab.SAB_VERSION=='5.1.3' and sab.SAB_WINDOWS_X64_SHA256==SHA,'runtime pin')
class Fake:
 def __init__(self,version='5.1.2',auth=True,download_ok=True,release=True):
    self.version=version;self.auth=auth;self.download_ok=download_ok;self.release=release
    self.port_free=False;self.calls=[];self.shutdown_event=threading.Event()
    self._sab_version_upgrade_next_ts=0;self._sab_version_probe_cooldown_skips=0
    self._sab_version_upgrade_attempts=0;self._sab_version_upgrade_successes=0;self._sab_version_upgrade_deferred=0
    self._sab_version_upgrade_last_from='';self._sab_version_current_recheck_seconds=300
    self._running_sab_version='';self._last_api_success_ts=20;self._last_ready_ts=20;self._last_error=''
 def _load_engine_identity(self):return {'port':50011,'api_key':'valid'}
 def _port_available(self,port):check(port==50011,'wrong port');return self.port_free
 def _probe_version(self,port,timeout):return self.version
 def _auth_kind(self,port,key,timeout):return 'apikey' if self.auth else 'invalid'
 def _provision_engine(self):
    self.calls.append('provision')
    if not self.download_ok:raise OSError('offline')
    return 'verified-target'
 def _api(self,mode,timeout):
    check(mode=='shutdown','unexpected api mutation');self.calls.append('shutdown');self.port_free=self.release
 def _close_sab_http_connection(self):self.calls.append('close')
 def _event(self,*args,**kwargs):pass
upgrade=sab.SabDownloadManager._upgrade_running_sab_if_needed
up_to_date=Fake(version='5.1.3');check(not upgrade(up_to_date) and 'shutdown' not in up_to_date.calls,'no-op existing target')
unauthorized=Fake(auth=False);check(not upgrade(unauthorized) and not unauthorized.calls,'no unauthorized process takeover')
offline=Fake(download_ok=False);check(not upgrade(offline) and 'shutdown' not in offline.calls and offline._sab_version_upgrade_deferred==1,'download failure must preserve queue')
old=Fake();check(upgrade(old) and old.calls.index('provision')<old.calls.index('shutdown'),'provision must precede graceful stop')
check(old._sab_version_upgrade_successes==1 and old._running_sab_version=='','new binary needs new runtime proof')
class FakeClock:
    n=0
    def monotonic(self):self.n+=10;return self.n
    def time(self):return 1000.0
    def sleep(self,*_):pass
clock=FakeClock();stuck=Fake(release=False)
with patch.object(sab.time,'monotonic',clock.monotonic),patch.object(sab.time,'time',clock.time),patch.object(sab.time,'sleep',clock.sleep):
    check(not upgrade(stuck) and stuck._sab_version_upgrade_deferred==1,'no force-kill on failed shutdown')
class Response(io.BytesIO):
    headers={'Content-Length':'14'}
    def __enter__(self):return self
    def __exit__(self,*_):self.close()
with tempfile.TemporaryDirectory() as td:
    target=Path(td)/'SABnzbd-5.1.3-win64-bin.zip'
    dummy=type('TestSelf',(),{'_download_progress':{}})()
    with patch.object(sab.urllib.request,'urlopen',side_effect=lambda *a,**kw:Response(b'wrong-byte-data')):
        try:sab.SabDownloadManager._download_official_engine(dummy,target)
        except RuntimeError as e:check('checksum verification failed' in str(e),'wrong failure')
        else:raise AssertionError('unverified official ZIP accepted')
    check(not target.exists() and not target.with_suffix('.download').exists(),'bad asset left behind')
print('PASS: v3.7.30 SAB 5.1.3 pin, authenticated provision-first upgrade, safe deferral, checksum rejection')
