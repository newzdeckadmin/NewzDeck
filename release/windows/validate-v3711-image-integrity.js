const fs=require('fs'),vm=require('vm'),assert=require('assert');
const app=fs.readFileSync('src/app/static/app.js','utf8');
const slice=(a,b)=>{const i=app.indexOf(a),j=app.indexOf(b,i+a.length);assert(i>=0&&j>i,`missing ${a} .. ${b}`);return app.slice(i,j)};
const ctx={};vm.createContext(ctx);vm.runInContext(slice('function imagePreviewPixelDefect(','function inspectLoadedImagePreview('),ctx);
const classify=(fn,w=64,h=64)=>{const bytes=new Uint8ClampedArray(w*h*4);for(let y=0;y<h;y++)for(let x=0;x<w;x++){const v=fn(x,y),i=(y*w+x)*4;bytes[i]=v[0];bytes[i+1]=v[1];bytes[i+2]=v[2];bytes[i+3]=v[3]===undefined?255:v[3]}return ctx.imagePreviewPixelDefect(bytes,w,h)};
const textured=(x,y)=>[(x*17+y*23)%256,(x*47+y*13)%256,(x*97+y*29)%256];
const noisy=(x,y)=>{const k=(x*23+y*71)%13-6;return[127+k,127+k,127+k]};
assert.strictEqual(classify(()=>[0,0,0]),'blank','pure black');
assert.strictEqual(classify((x,y)=>x<5&&y<5?[35,40,46]:[5,9,15]),'blank','black-card example with a little noise');
assert.strictEqual(classify(noisy),'blank','noisy gray decoder blank');
assert.strictEqual(classify((x,y)=>y>=28?noisy(x,y):textured(x,y)),'partial','corrupt lower gray fill');
assert.strictEqual(classify((x,y)=>y<28?noisy(x,y):textured(x,y)),'partial','corrupt upper gray fill');
assert.strictEqual(classify((x,y)=>x<27?noisy(x,y):textured(x,y)),'partial','corrupt left gray fill');
assert.strictEqual(classify((x,y)=>x>=34?noisy(x,y):textured(x,y)),'partial','corrupt right gray fill');
assert.strictEqual(classify((x,y)=>y>=28?[3,4,6]:textured(x,y)),'partial','partially black decoded image');
assert.strictEqual(classify((x,y)=>y>=51?[0,0,0]:textured(x,y)),'','normal narrow letterbox');
assert.strictEqual(classify((x,y)=>y>=28?[40,110,200]:textured(x,y)),'','legitimate colorful graphic');
assert.strictEqual(classify((x,y)=>[x*3,y*3,(x+y)]),'','real gradient');
assert.strictEqual(classify(textured),'','detailed photo-like image');
for(const marker of [
  "const size=64,canvas=document.createElement('canvas')",
  'function queueLoadedImageQualityCheck(img)',
  "if(img.isConnected&&a?.media?.kind==='image'&&articleKey(a)===stable&&group===state.selectedGroup&&provider===state.providerId)",
  'const live=batch.filter(x=>x.group===group&&x.provider===provider&&articleKey(state.articles[x.index])===articleKey(x.a));',
  'if(!card||card.dataset.articleKey!==articleKey(a))return false;card.remove();return true;',
])assert(app.includes(marker),`missing lifecycle guard: ${marker}`);
assert(!slice('function runLoadedImageQualityChecks(', 'function handleThumbnailImageLoaded(').includes('generation===state.galleryGeneration'), 'generation changes must not drop same-article quality check');
console.log('validate-v3711-image-integrity.js: PASS (black, noisy gray, four-edge partial, normal-image protection, stale-article lifecycle)');
