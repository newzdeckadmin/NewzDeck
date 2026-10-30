#!/usr/bin/env python3
from pathlib import Path
import json
R=Path(__file__).resolve().parents[2]
A=R/'src/app'
def rd(p):return p.read_text(encoding='utf-8')
def check(x,msg):
  if not x:raise SystemExit('v3.7.11 REGRESSION FAILED: '+msg)
js=rd(A/'static/app.js'); html=rd(A/'static/index.html'); css=rd(A/'static/styles.css'); m=json.loads(rd(A/'build-manifest.json'))
server=rd(A/'server.py');sab=rd(A/'sab_engine.py');automation=rd(A/'automation_engine.py');tray=rd(R/'src/windows/NewzDeckTray.go');workflow=rd(R/'.github/workflows/publish-release-trigger.yml')
check(rd(A/'version.txt').strip()=='3.7.11','version')
check('APP_VERSION = "3.7.11"' in server,'server version')
check('ADAPTER_VERSION = "3.7.11"' in sab and 'SAB_VERSION = "5.1.2"' in sab,'SAB adapter baseline')
check("const UI_VERSION = '3.7.11';" in js,'JS version')
check("version='3.7.11'" in automation,'Automation fallback')
check('argValue("--version", "3.7.11")' in tray,'tray fallback')
check(m.get('version')=='3.7.11' and m.get('base_version')=='3.7.10' and m.get('adapter_version')=='3.7.11','manifest version')
check(m.get('sab_version')=='5.1.2' and m.get('sabctools_version')=='9.6.3' and m.get('sabctools_upstream_commit')=='54d7663b9e8f527b5ab196d43f0d5c561a87c1ac','bundle provenance')
check(html.count('3.7.11-image-integrity')==3 and '<span>v3.7.11</span>' in html,'app HTML version')
# Original v3.7.8 functionality and update path remain.
for marker in ('function mediaSetSubjectSequence(','function mediaSetSequenceBase(','function mediaSetKey(','function initGroupsPaneResizer()','liveCards.get(memberKey)',"if(state.groupRelatedMedia){renderGroupedGallery(items);return}","state.groupRelatedMedia?appendContinuousGroupedGallery(previousKeys):appendContinuousGallery(previousKeys)","group_related_media:state.groupRelatedMedia","if(state.groupRelatedMedia){renderGroupedGallery(items);return}"):
  check(marker in js, 'v3.7.8 feature regressed: '+marker)
check('/* v3.7.7 - Newsgroups splitter cascade hotfix */' in css,'splitter CSS changed')
check('args = ["/update", "/SILENT", "/SP-", "/NORESTART", "/CLOSEAPPLICATIONS", "/FORCECLOSEAPPLICATIONS"]' in server,'managed Setup handoff changed')
# The specific regression fixes.
for marker in ('mediaSetIndexSeenKeys:new Map()', 'state.mediaSetIndexSeenKeys.clear()', 'seen.has(itemKey)', 'THUMB_DEFER_FORCE_MS=8000','THUMB_DEFER_MAX_MS=12000','THUMB_RECOVERY_TIMEOUT_MS=12000','function thumbnailDeferredRecoveryReady(','function withThumbnailRecoveryTimeout(',"holder.dataset.thumbDeferredRecovery='1'", "if(role==='item'&&['1','running'].includes(holder?.dataset.thumbDeferredRecovery))return false;", 'delete holder.dataset.thumbDeferredRecovery;delete holder.dataset.thumbDeferredSince;',"markThumbnailError(index,error,'image',role)"):
  check(marker in js,'missing preview fix: '+marker)
check('Waiting for idle preview recovery' not in js,'old unbounded recovery label returned')
check('members.some(x=>articleKey(x.a)===itemKey)' not in js,'old quadratic set lookup returned')
check('Validate NewzDeck source and v3.7.11 regression guard' in workflow and "if ($env:VERSION -cne '3.7.11')" in workflow,'workflow version')
for t in ('validate-v3711-regressions.py','validate-v379-preview.js','validate-v3710-image-quality.js','validate-v3711-image-integrity.js','validate-image-sets-v378.js','validate-media-set-key.js','validate-groups-pane-resizer.js'):
  check(t in workflow,'workflow missing test '+t)
check('NewzDeck-v3711-smoke' in workflow,'workflow smoke dir')
check('current stable release is **NewzDeck v3.7.11**' in rd(R/'README.md'),'README version')
check('NewzDeck_v3.7.11_Setup.exe' in rd(R/'README.md'),'README installer')
check('## Current release: v3.7.11' in rd(R/'docs/SOURCE_RELEASES.md'),'history')
# New visual and invalid-removal checks cannot be bypassed by a successful img.onload.
for marker in ('function imagePreviewPixelDefect(', 'function inspectLoadedImagePreview(', 'function queueLoadedImageQualityCheck(', 'function suppressBrokenPreview(', 'function runLoadedImageQualityChecks(', 'queueUnavailableMediaHide(a,index,role)', "if(a?.media?.kind==='image')queueLoadedImageQualityCheck(img)"):
  check(marker in js,'missing broken-image suppression: '+marker)
check('img.onload=null' not in js[:100], 'unexpected JavaScript header')
for marker in ('const size=64,canvas=document.createElement(\'canvas\')',
               'if(!card||card.dataset.articleKey!==articleKey(a))return false;card.remove();return true;',
               'const live=batch.filter(x=>x.group===group&&x.provider===provider&&articleKey(state.articles[x.index])===articleKey(x.a));'):
  check(marker in js, 'v3.7.11 visual integrity gate missing: '+marker)
check(rd(R/'index.html').count('v3.7.11')>=4,'website')
print('validate-v3711-regressions.py: PASS')
