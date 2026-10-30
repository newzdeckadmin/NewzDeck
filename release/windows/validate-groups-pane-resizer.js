const fs = require('fs');
const vm = require('vm');
function fail(m){console.error('validate-groups-pane-resizer.js: '+m);process.exit(1)}
const app=fs.readFileSync('src/app/static/app.js','utf8');
const html=fs.readFileSync('src/app/static/index.html','utf8');
const css=fs.readFileSync('src/app/static/styles.css','utf8');
const start=app.indexOf("const GROUPS_PANE_WIDTH_KEY");
const end=app.indexOf("const THEME_IDS",start);
if(start<0||end<0||end<=start)fail('Could not isolate pure Newsgroups-pane sizing helpers.');
const helperSource=app.slice(start,end);
if(/\bdocument\b|\bwindow\b|applyTheme\s*\(/.test(helperSource))fail('Pure sizing-helper slice contains browser initialization.');
const context={};vm.createContext(context);vm.runInContext(helperSource,context);
const bounds=context.groupsPaneWidthBounds,clamp=context.clampGroupsPaneWidth;
if(typeof bounds!=='function'||typeof clamp!=='function')fail('Sizing helpers missing.');
let b=bounds(1250,1440);if(b.min!==240||b.max!==460)fail('Desktop bounds changed.');
if(clamp(999,1250,1440)!==460||clamp(200,1250,1440)!==240)fail('Desktop clamp failed.');
b=bounds(980,1100);if(b.max!==560||clamp(500,980,1100)!==500)fail('Compact clamp failed.');
b=bounds(736,800);if(b.max!==376||clamp(600,736,800)!==376)fail('Narrow clamp failed.');
b=bounds(2000,1920);if(b.max!==640)fail('Hard maximum changed.');
for(const m of ['id="groupsPaneResizer"','role="separator"','aria-orientation="vertical"','tabindex="0"'])if(!html.includes(m))fail('HTML marker missing: '+m);
for(const m of ['function initGroupsPaneResizer()',"localStorage.setItem(GROUPS_PANE_WIDTH_KEY","handle.addEventListener('pointerdown'","handle.addEventListener('pointermove'","handle.addEventListener('dblclick'","e.key==='ArrowLeft'||e.key==='ArrowRight'","initGroupsPaneResizer();"])if(!app.includes(m))fail('JS marker missing: '+m);
const hotfixMarker='/* v3.7.7 - Newsgroups splitter cascade hotfix */';
const hotfix=css.lastIndexOf(hotfixMarker);if(hotfix<0)fail('Final hotfix block missing.');
if(css.lastIndexOf('.panel>*')>hotfix)fail('A later .panel>* rule can override splitter positioning.');
const tail=css.slice(hotfix);
for(const m of [
'.workspace{grid-template-columns:var(--groups-pane-width) minmax(540px,1fr) minmax(300px,380px)}',
'.panel>.groups-pane-resizer{position:absolute;top:0;right:0;bottom:0;left:auto;width:10px;height:auto;z-index:40;display:block;flex:none;cursor:col-resize;touch-action:none;pointer-events:auto}',
'@media(max-width:1280px){.workspace{grid-template-columns:var(--groups-pane-width) minmax(500px,1fr) minmax(275px,330px)}}',
'@media(max-width:1150px){.workspace{grid-template-columns:var(--groups-pane-width) minmax(0,1fr)}.preview-pane{display:none}}',
'@media(max-width:760px){.workspace{grid-template-columns:1fr}.groups-pane{display:none}.panel>.groups-pane-resizer{display:none}}'
])if(!tail.includes(m))fail('Final-cascade marker missing: '+m);
const lastFixed=Math.max(css.lastIndexOf('grid-template-columns:minmax(265px,310px)'),css.lastIndexOf('grid-template-columns:minmax(248px,300px)'),css.lastIndexOf('grid-template-columns:minmax(252px,306px)'));
if(lastFixed>hotfix)fail('A later fixed desktop grid overrides --groups-pane-width.');
console.log('validate-groups-pane-resizer.js: PASS');
