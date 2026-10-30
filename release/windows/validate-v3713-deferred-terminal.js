const fs=require('fs'),vm=require('vm'),assert=require('assert');
const js=fs.readFileSync('src/app/static/app.js','utf8');
function source(start,end){const a=js.indexOf(start),b=js.indexOf(end,a+start.length);assert(a>=0&&b>a,`missing ${start}..${end}`);return js.slice(a,b)}
const deferred=source("function scheduleDeferredFullPreviewRecovery(index,role='item'){",'function isSelectableMedia(');
for(const marker of ['thumbDeferredRecoveryStarted','if(elapsed>=THUMB_DEFER_MAX_MS&&!active)','error.deferredRecoveryExpired=true','state.unpreviewableMediaKeys.has(pkey)','rememberPreviewUnavailable(a,terminal)','queueUnavailableMediaHide(a,index,role)'])assert(js.includes(marker),'missing '+marker);
let now=100000, id=0, timer=new Map(), hidden=[], skipped=[];
let rectangle={top:700,bottom:810};
let holder={isConnected:true,dataset:{thumbDeferredRecovery:'1',thumbDeferredSince:String(now)},getBoundingClientRect:()=>rectangle};
const item={message_id:'one',complete:true,media:{kind:'image'}};
const state={articles:[item],selectedGroup:'alt.photos',providerId:'provider1',galleryGeneration:3,thumbDeferredRecoveryTimers:new Map(),thumbDeferredRecoveryStarted:new Map(),thumbEscalations:new Map(),thumbEscalationActive:1,unpreviewableMediaKeys:new Set(),imageThumbCache:new Map(),previewCache:new Map(),thumbFailureCache:new Map(),groupRelatedMedia:false,selectedItems:new Map(),selectedArticleKey:'',viewerKey:''};
const ctx={state,Date:{now:()=>now},setTimeout:(fn,ms)=>{const n=++id;timer.set(n,{fn,at:now+ms});return n},clearTimeout:n=>timer.delete(n),previewKey:a=>a.message_id,articleKey:a=>a?.message_id||'',
 thumbnailHolder:()=>holder,els:{contentFilter:{value:'images'},articlesList:{getBoundingClientRect:()=>({top:0,bottom:550})}},
 friendlyPreviewError:e=>({code:e?.deferredRecoveryExpired?'recover-expired':'other',retryable:true,label:'Request failed',message:String(e?.message||'')}),
 rememberPreviewUnavailable:(a,info)=>{state.unpreviewableMediaKeys.add(a.message_id);state.thumbDeferredRecoveryStarted.delete(a.message_id);hidden.push(['remember',a.message_id,info])},
 queueUnavailableMediaHide:(a,index)=>{hidden.push(['hide',a.message_id,index]);return true},renderArticles:()=>skipped.push('render'),
 thumbnailDeferredRecoveryReady:()=>false,escalateVisibleImageThumbnail:()=>{throw Error('Offscreen image should not escalate')},
 scheduleThumbnailDemandScan:()=>{},registerThumbnailHolderNode:()=>{},isDefinitiveUnsupportedMedia:()=>false,escapeHtml:x=>x,
 };
vm.createContext(ctx);vm.runInContext('const THUMB_DEFER_RETRY_MS=450;const THUMB_DEFER_MAX_MS=12000;const THUMB_RECOVERY_TIMEOUT_MS=12000;',ctx);vm.runInContext(deferred,ctx);
ctx.scheduleDeferredFullPreviewRecovery(0);
assert.strictEqual(state.thumbDeferredRecoveryTimers.size,1);
function runTo(ms){let count=0;while(timer.size&&count++<100){const [tid,t]=[...timer.entries()].sort((a,b)=>a[1].at-b[1].at)[0];if(t.at>ms)break;timer.delete(tid);now=t.at;t.fn()}now=ms}
runTo(104500);assert.strictEqual(hidden.length,0,'prematurely hid deferred image');
// Rebuild the card/loader. The original 12-second clock must survive.
holder={isConnected:true,dataset:{thumbDeferredRecovery:'1',thumbDeferredSince:'104500'},getBoundingClientRect:()=>rectangle};
ctx.scheduleDeferredFullPreviewRecovery(0); // timer should not duplicate or restart.
assert.strictEqual(state.thumbDeferredRecoveryTimers.size,1,'duplicate timer across loader rebuild');
assert.strictEqual(state.thumbDeferredRecoveryStarted.get('one'),100000,'rebuild reset stable deadline');
runTo(112500);
assert.strictEqual(hidden.length,2,'offscreen expired image not suppressed and queued for removal');
assert.strictEqual(hidden[0][2].code,'deferred_preview_exhausted');
assert.strictEqual(hidden[1][0],'hide');
assert.strictEqual(state.thumbDeferredRecoveryTimers.size,0,'expired timer not cleared');
assert.strictEqual(state.thumbDeferredRecoveryStarted.has('one'),false,'expired start tracker not cleared');
assert.strictEqual(skipped.length,0,'unexpected full rerender');
// A terminal fallback error must hide the image even when it is marked retryable.
const a2={message_id:'two',complete:true,media:{kind:'image'}};state.articles.push(a2);state.thumbDeferredRecoveryStarted.set('two',now);
ctx.markThumbnailError(1,new Error('Full image unavailable'),'image','item');
assert(state.unpreviewableMediaKeys.has('two'),'fallback error did not remove broken image');
assert.strictEqual(hidden[hidden.length-1][1],'two');
// Normal successful inspection must drop the recovery deadline rather than hide the card.
const checks=source('function runLoadedImageQualityChecks(){','function handleThumbnailImageLoaded(');
ctx.state.thumbQualityQueue=[{img:{isConnected:true},index:1,stable:'two',group:'alt.photos',provider:'provider1'}];
ctx.state.thumbQualityTimer=3;ctx.state.thumbDeferredRecoveryStarted.set('two',now);
ctx.inspectLoadedImagePreview=()=>'';ctx.suppressBrokenPreview=()=>{throw Error('Valid image suppressed')};ctx.scheduleThumbnailDemandScan=()=>{};
ctx.setTimeout=(fn,ms)=>{const n=++id;timer.set(n,{fn,at:now+ms});return n};ctx.clearTimeout=n=>timer.delete(n);
ctx.state.thumbImageRecovery=new Map([['two',2]]);ctx.state.thumbQualityQueue[0].img.isConnected=true;
// Invalidated state cannot affect test of the success cleanup branch.
ctx.state.unpreviewableMediaKeys.delete('two');vm.runInContext(checks,ctx);
ctx.runLoadedImageQualityChecks();
assert.strictEqual(state.thumbDeferredRecoveryStarted.has('two'),false,'verified success failed to reset deadline');
assert.strictEqual(state.thumbImageRecovery.has('two'),false,'verified success failed to reset recovery attempts');
console.log('validate-v3713-deferred-terminal.js: PASS (offscreen expiry, re-render clock, fallback removal, success reset)');
