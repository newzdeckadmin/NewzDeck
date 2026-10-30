const fs=require('fs'),vm=require('vm');
function fail(m){console.error('validate-v3712-gallery-lifecycle.js: '+m);process.exit(1)}
const js=fs.readFileSync('src/app/static/app.js','utf8');
const start=js.indexOf('// v3.7.12: never use a stale numeric card index');
const end=js.indexOf('function wireGalleryCards(',start);
if(start<0||end<start)fail('Stable-id resolver block not found.');
const source=js.slice(start,end);
const ctx={state:{articles:[{message_id:'a1',media:{kind:'image'}},{message_id:'b2',media:{kind:'image'}}]},articleKey:a=>a?.message_id||''};
vm.createContext(ctx);vm.runInContext(source,ctx);
function card(key,index){const btn={dataset:{index:String(index)}},img={dataset:{thumbImageIndex:String(index)}},loader={dataset:{thumbIndex:String(index)}};return {dataset:{articleKey:key,index:String(index)},querySelector:s=>s==='.card-download-btn'?btn:null,querySelectorAll:s=>s==='[data-thumb-image-index]'?[img]:s==='[data-thumb-index]'?[loader]:[],_btn:btn,_img:img,_loader:loader}}
let old=card('b2',0);
if(ctx.stableGalleryCardIndex(old)!==1)fail('Stale numeric index was not resolved by article key.');
if(old.dataset.index!=='1'||old._btn.dataset.index!=='1'||old._img.dataset.thumbImageIndex!=='1'||old._loader.dataset.thumbIndex!=='1')fail('Stable resolution did not repair card/thumb/button indices.');
if(ctx.stableGalleryCardArticle(old)!==ctx.state.articles[1])fail('Stable action did not resolve correct article.');
if(ctx.stableGalleryCardIndex(card('missing',0))!==-1)fail('Missing article was allowed to open the wrong post.');
ctx.state.articles.reverse();if(ctx.stableGalleryCardIndex(old)!==0)fail('Index repair failed after reorder.');
for(const marker of [
  'function armGalleryImageLoadWatchdog(img)',
  'function sweepEmptyGalleryImageStages()',
  'function scheduleEmptyGalleryImageSweep()',
  'if(Date.now()-since<5000){needsRescan=true;continue}',
  '},15000);',
  'recoverBrokenThumbnail(img);',
  'const a=stableGalleryCardArticle(card);if(!a)return;',
  "const a=stableGalleryCardArticle(card);if(['image','video'].includes(a?.media?.kind)&&a.complete)",
  "const index=stableGalleryCardIndex(card);if(index>=0)handleMediaSelectionClick(index,e)",
  'scheduleEmptyGalleryImageSweep();',
  "code:'viewer_image_decode_failed'",
  "img.addEventListener('error',()=>{",
])if(!js.includes(marker))fail('Gallery lifecycle wiring marker missing: '+marker);
const viewer=js.slice(js.indexOf('async function renderMediaViewer('),js.indexOf('function navigateViewer('));
const setSrc=viewer.indexOf('img.src=data.url'),attachError=viewer.indexOf("img.addEventListener('error',()=>{");
if(attachError<0||setSrc<attachError)fail('Viewer error handler must be registered before img.src.');
if(js.includes("img.draggable=false;img.src=data.url;els.viewerStage.replaceChildren(img)"))fail('Viewer retains original unguarded src assignment.');
// Execute the actual empty-stage sweep with a simulated visible card.
const sweepStart=js.indexOf('function sweepEmptyGalleryImageStages(){');
const sweepEnd=js.indexOf('function scheduleEmptyGalleryImageSweep(){',sweepStart);
if(sweepStart<0||sweepEnd<sweepStart)fail('Empty-stage sweep not isolated.');
let fakeNow=100000,hides=[],rescanCount=0;
const item={message_id:'img1',complete:true,media:{kind:'image'}};
const emptyStage={querySelector:()=>null};
const cardNode={dataset:{articleKey:'img1',index:'0'},getBoundingClientRect:()=>({top:20,bottom:80}),querySelector:sel=>sel==='.thumb-stage'?emptyStage:null};
const list={getBoundingClientRect:()=>({top:0,bottom:200}),querySelectorAll:()=>[cardNode]};
const sweepContext={state:{activeView:'browse',articles:[item],unpreviewableMediaKeys:new Set()},els:{articlesList:list},Date:{now:()=>fakeNow},
articleKey:a=>a?.message_id||'',previewKey:a=>a.message_id,isAllPostsMode:()=>false,
rememberPreviewUnavailable:(a,info)=>{hides.push({event:'remember',a,info})},
queueUnavailableMediaHide:(a,i,role)=>{hides.push({event:'hide',a,i,role})},
armGalleryImageLoadWatchdog:()=>fail('No image exists to watch'),handleThumbnailImageLoaded:()=>fail('No image exists to inspect'),
scheduleEmptyGalleryImageSweep:()=>{rescanCount++}};
vm.createContext(sweepContext);
vm.runInContext(source,sweepContext);
sweepContext.scheduleEmptyGalleryImageSweep=()=>{rescanCount++};
sweepContext.sweepEmptyGalleryImageStages();
if(hides.length||rescanCount!==1)fail('Missing-stage first sighting must wait and reschedule.');
fakeNow+=4000;sweepContext.sweepEmptyGalleryImageStages();
if(hides.length||rescanCount!==2)fail('Missing-stage grace period was skipped.');
fakeNow+=1100;sweepContext.sweepEmptyGalleryImageStages();
if(hides.length!==2||hides[0].event!=='remember'||hides[1].event!=='hide'||hides[1].i!==0)fail('Expired missing-stage card was not suppressed and hidden.');
// A genuine pending loader must never be mistaken for a missing preview.
hides=[];emptyStage.querySelector=sel=>sel.includes('thumb-loader')?{dataset:{}}:null;
cardNode.dataset.emptyImageStageSince='100000';fakeNow+=30000;
sweepContext.sweepEmptyGalleryImageStages();
if(hides.length)fail('Active loader was incorrectly classified as missing image.');
console.log('validate-v3712-gallery-lifecycle.js: PASS');
