#!/usr/bin/env python3
"""Behavioral regression: FFmpeg and FFprobe never open Windows console windows."""
from __future__ import annotations
import ast, json, sys, tempfile, subprocess
from pathlib import Path
from types import SimpleNamespace
P=Path(__file__).resolve().parents[2]/'src/app/server.py'
source=P.read_text(encoding='utf-8')
tree=ast.parse(source)
find=lambda name:next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
functions=ast.Module(body=[find('_try_ffmpeg_frame'),find('video_metadata')],type_ignores=[])
code=compile(ast.fix_missing_locations(functions),str(P),'exec')
with tempfile.TemporaryDirectory() as t:
 root=Path(t)
 for win in [True,False]:
  calls=[]
  def run(args,**kwargs):
   calls.append((args,kwargs))
   if '-frames:v' in args:
    Path(args[-1]).write_bytes(b'fake frame')
    return SimpleNamespace(returncode=0)
   return SimpleNamespace(stdout=json.dumps({'streams':[{'width':1920,'height':1080,'codec_name':'h264','avg_frame_rate':'30/1'}],'format':{'duration':'12.5'}}),returncode=0)
  mock_subprocess=SimpleNamespace(run=run,DEVNULL=subprocess.DEVNULL,PIPE=subprocess.PIPE,CREATE_NO_WINDOW=0x08000000)
  mock_sys=SimpleNamespace(platform='win32' if win else 'linux')
  ctx={'Path':Path,'subprocess':mock_subprocess,'sys':mock_sys,'json':json,
       'cached_thumbnail_result':lambda token:None,'_ffmpeg_path':lambda:'ffmpeg.exe',
       'thumbnail_cache_path':lambda token:root/(('win-' if win else 'posix-')+token+'.jpg'),
       'thumbnail_cache_url':lambda token,p:'url/'+token,
       '_mark_thumbnail_stats_dirty':lambda:None,'cleanup_thumbnail_cache':lambda:None,
       'shutil':SimpleNamespace(which=lambda name:'ffprobe.exe')}
  exec(code,ctx)
  assert ctx['_try_ffmpeg_frame'](root/'sample.mp4','sample')=='url/sample'
  info=ctx['video_metadata'](root/'sample.mp4')
  assert info['width']==1920 and info['height']==1080 and info['duration']==12.5 and info['frame_rate']==30
  assert len(calls)==2
  assert calls[0][0][0]=='ffmpeg.exe' and calls[0][1]['timeout']==15
  assert calls[1][0][0]=='ffprobe.exe' and calls[1][1]['timeout']==12
  assert calls[0][1]['creationflags']==(0x08000000 if win else 0)
  assert calls[1][1]['creationflags']==(0x08000000 if win else 0)
  assert calls[0][1]['check'] is False and calls[1][1]['check'] is False
  # No installed FFmpeg: preserve the browser fallback without launching a process.
  ctx['_ffmpeg_path']=lambda:None
  assert ctx['_try_ffmpeg_frame'](root/'sample.mp4','none') is None and len(calls)==2
  # FFmpeg failure must return fallback instead of throwing or exposing a terminal.
  def fail(args,**kwargs):
   if '-frames:v' in args: raise OSError('simulated decoder launch failure')
   return run(args,**kwargs)
  mock_subprocess.run=fail
  ctx['_ffmpeg_path']=lambda:'ffmpeg.exe'
  assert ctx['_try_ffmpeg_frame'](root/'sample.mp4','fail') is None
assert source.count('creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if sys.platform == "win32" else 0')==2
assert source.count('_try_ffmpeg_frame(')>=3, 'Both cached/full and sampled video preview paths must keep using the guarded process'
print('validate-v3716-video-console.py: PASS (Win32 hidden FFmpeg/FFprobe, non-Windows, fallbacks, timeouts)')
