const fs=require('fs'),vm=require('vm'),assert=require('assert');
const app=fs.readFileSync('src/app/static/app.js','utf8');
const slice=(a,b)=>{const i=app.indexOf(a),j=app.indexOf(b,i+a.length);assert(i>=0&&j>i,`missing ${a} .. ${b}`);return app.slice(i,j)};
const source=slice('function imagePreviewPixelDefect(', 'function inspectLoadedImagePreview(');
const ctx={};vm.createContext(ctx);vm.runInContext(source,ctx);
const classify=(fn,w=48,h=48)=>{let p=new Uint8ClampedArray(w*h*4);for(let y=0;y<h;y++)for(let x=0;x<w;x++){const q=(y*w+x)*4,[r,g,b,a=255]=fn(x,y);p[q]=r;p[q+1]=g;p[q+2]=b;p[q+3]=a}return ctx.imagePreviewPixelDefect(p,w,h)};
const textured=(x,y)=>[(x*17+y*23)%256,(x*47+y*13)%256,(x*97+y*29)%256,255];
assert.strictEqual(classify(textured),'','ordinary textured image');
assert.strictEqual(classify(()=>[0,0,0]),'blank','black blank');
assert.strictEqual(classify(()=>[255,255,255]),'blank','white blank');
assert.strictEqual(classify(()=>[100,101,99]),'blank','neutral gray blank');
assert.strictEqual(classify(()=>[0,0,0,0]),'blank','transparent blank');
assert.strictEqual(classify((x,y)=>y>=20?[128,128,128]:textured(x,y)),'partial','corrupt lower-fill rectangle');
assert.strictEqual(classify((x,y)=>x>=20?[0,0,0]:textured(x,y)),'partial','corrupt right-fill rectangle');
assert.strictEqual(classify((x,y)=>y<8?[0,0,0]:textured(x,y)),'','top letterbox tolerated');
assert.strictEqual(classify((x,y)=>y>=38?[0,0,0]:textured(x,y)),'','normal bottom letterbox tolerated');
assert.strictEqual(classify((x,y)=>y>=20?[40,110,200]:textured(x,y)),'','large colored design field tolerated');
assert.strictEqual(classify((x,y)=>[(x+y)%5,(x+y)%5,(x+y)%5]),'blank','near-uniform blank');
// Live DOM guard path: a detected defect marks article unavailable and queues
// removal; clean pixels leave the preview visible. Mocks don't infer corruption.
const ds={thumbImageIndex:'0',thumbRole:'item'};
let invalidated=0, hidden=0, remembered=0;
const article={media:{kind:'image'},message_id:'a'};
const img={isConnected:true,dataset:ds,closest:()=>({dataset:{articleKey:'a'}}),getAttribute:()=>'/thumb/1234567890abcdef1234567890abcdef',src:'/thumb/1234567890abcdef1234567890abcdef'};
const state={articles:[article],imageThumbCache:new Map([['p',{}]]),previewCache:new Map([['p',{}]]),thumbImageRecovery:new Map(),unpreviewableMediaKeys:new Set(),thumbQualityQueue:[],thumbQualityTimer:null,galleryGeneration:4,selectedGroup:'alt.test',providerId:'p'};
const c={state,previewKey:()=> 'p',articleKey:a=>a.message_id,mediaSetKey:()=> 'set1',thumbnailTokenFromUrl:()=> '1234',api:()=>{invalidated++;return Promise.resolve()},rememberPreviewUnavailable:()=>{remembered++},queueUnavailableMediaHide:()=>{hidden++}, setTimeout:()=>1,inspectLoadedImagePreview:()=> 'partial'};
vm.createContext(c);vm.runInContext(slice('function suppressBrokenPreview(', 'function queueLoadedImageQualityCheck('),c);
assert.strictEqual(c.suppressBrokenPreview(img,'partial'),true);
assert.strictEqual(hidden,1);assert.strictEqual(remembered,1);assert.strictEqual(state.imageThumbCache.size,0);assert.strictEqual(state.previewCache.size,0);
img.closest=()=>({dataset:{articleKey:'another'}});
assert.strictEqual(c.suppressBrokenPreview(img,'partial'),false,'stale article protection');
assert.strictEqual(hidden,1);
img.closest=()=>null; img.dataset.thumbRole='set-cover'; img.dataset.thumbSetKey='another-set';
assert.strictEqual(c.suppressBrokenPreview(img,'partial'),false,'stale Image Set cover protection');
assert.strictEqual(hidden,1);
for(const s of [
 'if(a?.media?.kind===\'image\')queueLoadedImageQualityCheck(img);',
 'if(role===\'set-cover\'){if(kind===\'image\'&&attempt>=2){suppressBrokenPreview(img,\'decode\');return}',
  "if(role==='set-cover'&&img.dataset.thumbSetKey&&mediaSetKey(a)!==img.dataset.thumbSetKey)return false;",
 'catch(e){if(thumbnailHolder(index,role))markThumbnailError(index,e,kind,role)}',
 'if(state.thumbQualityTimer){clearTimeout(state.thumbQualityTimer);state.thumbQualityTimer=null}state.thumbQualityQueue.length=0;',
])assert(app.includes(s),`missing behavior ${s}`);
console.log('validate-v3710-image-quality.js: PASS (blank, partial-fill, valid images, stale guards, removal path)');
