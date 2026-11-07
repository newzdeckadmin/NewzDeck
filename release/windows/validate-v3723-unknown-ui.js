// Offline v3.7.23 browser eligibility and user-driven controls regression.
const fs=require('fs'),path=require('path'),vm=require('vm');
const code=fs.readFileSync(path.join(__dirname,'../../src/app/static/app.js'),'utf8');
function check(value,msg){if(!value)throw new Error('v3.7.23 browser: '+msg)}
for(const marker of [
  "'/api/articles/inspect-unknown'","'/api/articles/save-fragment'",
  'function inspectUnknownArticle(', 'function saveUnknownFragment(',
  'article-row-inspect','article-row-save-fragment',
  'inspectUnknownBtn','saveUnknownFragmentBtn',
  'a.unknown_inspection.can_queue','renderPreviewDetails(a,false)',
  'Save decoded article (.part)',
])check(code.includes(marker),'missing UI/manual action '+marker);
check(!/setInterval\([^)]*(inspectUnknownArticle|saveUnknownFragment)/.test(code),'no automatic bulk BODY scans');
function fn(name){const match=code.match(new RegExp(`function ${name}\\([^]*?\\n\\}`));check(match,'missing function '+name);return match[0]}
const context={articleNeedsNameResolution:()=>false,isUnresolvedMultipartFragment:()=>false};
vm.createContext(context);vm.runInContext(fn('isUnresolvedDownloadCandidate')+'\n'+fn('isSelectableMedia'),context);
const bare={complete:true,media:null,subject:'9fa1fead73d4c808999',segments:[{message_id:'a@b'}],segment_count:1,segment_total:1};
check(!context.isSelectableMedia(bare),'unprobed opaque article must not enter normal queue');
check(context.isSelectableMedia({...bare,unknown_inspection:{can_queue:true,status:'possible_complete'}}),'explicit complete inspection must allow queue');
check(!context.isSelectableMedia({...bare,unknown_inspection:{can_queue:false,status:'fragment'}}),'identified fragment must not enter queue');
check(!context.isSelectableMedia({...bare,complete:false,unknown_inspection:{can_queue:true}}),'incomplete header group cannot enter queue');
check(context.isSelectableMedia({...bare,media:{kind:'image',filename:'known.jpg'}}),'ordinary media queue retained');
check(code.includes('function nameResolutionCandidates(')&&code.includes('function scheduleObfuscatedNameResolution('),'old name discovery preserved');
console.log('validate-v3723-unknown-ui.js: PASS (manual inspection controls, guarded download eligibility, existing resolver retained)');
