const fs=require('fs');
const vm=require('vm');
const assert=require('assert');
const app=fs.readFileSync('src/app/static/app.js','utf8');
const slice=(start,end)=>{const a=app.indexOf(start),b=app.indexOf(end,a+start.length);assert(a>=0&&b>a,`Missing code boundaries: ${start} .. ${end}`);return app.slice(a,b)};
const must=(needle)=>assert(app.includes(needle),`Missing preview guard: ${needle}`);

// Indexed duplicate suppression stays O(n), not O(n^2), for larger Image Sets.
{
  let keyLookups=0;
  const state={mediaSetIndexBuckets:new Map(),mediaSetIndexSingles:new Map(),mediaSetIndexSeenKeys:new Map(),mediaSetIndexValid:false};
  const ctx={state,mediaSetKey:()=>"alt.test|image|album|poster@example.com",articleKey:a=>{keyLookups++;return a.id;}};
  vm.createContext(ctx);
  vm.runInContext(slice('function resetMediaSetIndex(){','function mediaSetIndexSnapshot('),ctx);
  const changed=new Set();
  ctx.resetMediaSetIndex();
  for(let n=1;n<=5000;n++)ctx.addMediaSetIndexItem({a:{id:`${n}`}},changed);
  ctx.addMediaSetIndexItem({a:{id:'5000'}},changed);
  assert.strictEqual(state.mediaSetIndexBuckets.get('alt.test|image|album|poster@example.com').length,5000);
  assert.strictEqual(keyLookups,5001,'Dedupe must use one article identity lookup per insertion, not scan every prior member');
  assert.strictEqual(changed.size,1);
  ctx.resetMediaSetIndex();
  assert.strictEqual(state.mediaSetIndexSeenKeys.size,0,'Seen index must clear along with buckets');
}

// A deferral is bounded even when thumbnails/downloads never reach strict idle.
{
  let now=0,downloadBusy=true,slot=0,visible=true,requestOK=false,failures=[];
  const timers=new Map();let seq=1;
  const state={thumbActive:7,thumbQueue:[{role:'item',priority:0}],lastBrowseScrollTs:0,browseScrollVelocity:0,thumbEscalationActive:0,thumbEscalations:new Map(),galleryGeneration:4,selectedGroup:'alt.test',providerId:'p',previewCache:new Map(),thumbDeferredRecoveryTimers:new Map(),articles:[{message_id:'id1',media:{kind:'image'},complete:true}]};
  const holder={isConnected:true,dataset:{thumbDeferredRecovery:'1',thumbDeferredSince:'1'},innerHTML:''};
  const ctx={state,Date:{now:()=>now},setTimeout:(fn,ms)=>{const id=seq++;timers.set(id,{fn,at:now+ms});return id;},clearTimeout:id=>timers.delete(id),
    activeDownloadTraffic:()=>downloadBusy,thumbnailFullRecoveryIdle:()=>false,
    thumbnailHolder:()=>holder,previewKey:()=>"p|alt.test|id1",articleKey:a=>a?.message_id,
    els:{articlesList:{getBoundingClientRect:()=>({top:0,bottom:500})}},
    fetchPrepared:()=>requestOK?Promise.resolve({url:'image-data'}):Promise.reject(new Error('Full preview could not be retrieved.')),
    replaceThumbnailHolderWithImage:()=>{requestOK=true;},markThumbnailError:(index,error)=>{failures.push(String(error.message));holder.dataset.thumbDeferredRecovery=undefined;},
    scheduleThumbnailDemandScan:()=>{},
    performance:{now:()=>now},
  };
  holder.getBoundingClientRect=()=>visible?{top:30,bottom:160}:{top:550,bottom:650};
  vm.createContext(ctx);
  vm.runInContext(slice('const THUMB_DEFER_SOFT_MS','function queueThumbnail('),ctx);
  vm.runInContext(slice("function scheduleDeferredFullPreviewRecovery(index,role='item')",'function markThumbnailError('),ctx);
  assert.strictEqual(ctx.thumbnailDeferredRecoveryReady(2000),false,'Should not start immediately');
  assert.strictEqual(ctx.thumbnailDeferredRecoveryReady(8000),true,'Full preview must become eligible after bounded wait');
  assert.strictEqual(ctx.THUMB_DEFER_MAX_MS,undefined,'Constant should remain local to VM');
  ctx.scheduleDeferredFullPreviewRecovery(0);
  assert.strictEqual(state.thumbDeferredRecoveryTimers.size,1);
  // Simulate a lane permanently occupied: it must yield a visible error by 12 seconds.
  state.thumbEscalationActive=1;
  for(let i=0;i<32&&timers.size;i++){
    const t=[...timers.entries()].sort((a,b)=>a[1].at-b[1].at)[0];timers.delete(t[0]);now=t[1].at;t[1].fn();
  }
  assert.strictEqual(failures.length,1,'Long-running fallback slot must not leave an infinite waiting card');
  assert(now<=13000,`Recovery must settle in bounded time; got ${now}ms`);
  assert.strictEqual(state.thumbDeferredRecoveryTimers.size,0,'Timer tracking must be cleaned up');
  // A free lane after 8s should initiate a real fallback even if downloads remain busy.
  now=0;timers.clear();failures=[];state.thumbEscalationActive=0;holder.dataset.thumbDeferredRecovery='1';holder.dataset.thumbDeferredSince='1';
  ctx.scheduleDeferredFullPreviewRecovery(0);
  for(let i=0;i<25&&timers.size;i++){
    const t=[...timers.entries()].sort((a,b)=>a[1].at-b[1].at)[0];timers.delete(t[0]);now=t[1].at;t[1].fn();
    if(holder.dataset.thumbDeferredRecovery==='running')break;
  }
  assert.strictEqual(holder.dataset.thumbDeferredRecovery,'running','Fallback was not initiated while other thumbnails remained active');
  assert(now<=9000,`Fallback initiation exceeded deadline: ${now}ms`);
}

for(const marker of [
  "if(role==='item'&&['1','running'].includes(holder.dataset.thumbDeferredRecovery)){",
  "if(role==='item'&&['1','running'].includes(holder?.dataset.thumbDeferredRecovery))return false;",
  "holder.dataset.thumbDeferredRecovery='1'",
  "delete holder.dataset.thumbDeferredRecovery;delete holder.dataset.thumbDeferredSince;",
  'fetchPrepared(a,{timeoutMs:THUMB_RECOVERY_TIMEOUT_MS})',
  "markThumbnailError(index,error,'image',role)",
  'withThumbnailRecoveryTimeout',
])must(marker);
console.log('validate-v379-preview.js: PASS (dedupe, bounded recovery, timeout/error path, retry-state guards)');
