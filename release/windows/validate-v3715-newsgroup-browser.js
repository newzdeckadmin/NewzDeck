'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const src=fs.readFileSync(path.join(__dirname,'../../src/app/static/app.js'),'utf8');
function fn(name){let pos=src.indexOf(`function ${name}(`);if(pos<0)throw Error('missing '+name);let i=src.indexOf('){',pos)+1,depth=0,string='',comment='';for(;i<src.length;i++){const c=src[i],n=src[i+1];if(comment==='line'){if(c==='\n')comment='';continue}if(comment==='block'){if(c==='*'&&n==='/'){comment='';i++}continue}if(string){if(c==='\\'){i++;continue}if(c===string)string='';continue}if(c==='/'&&n==='/'){comment='line';i++;continue}if(c==='/'&&n==='*'){comment='block';i++;continue}if(c==='\''||c==='"'||c==='`'){string=c;continue}if(c==='{')depth++;if(c==='}'&&!--depth)return src.slice(pos,i+1)}throw Error('unbalanced '+name)}
// The endpoint must not reconstruct fewer multipart headers in Images than in All Posts.
assert.match(fn('articlePageRequest'),/smart_binaries:true/);assert.match(src,/articlePageRequest\(targetPage,\{refresh,progressive:!append\}\)/);
const ctx={state:{providerId:'p',selectedGroup:'alt.test',articles:[],selectedItems:new Map(),selectionAnchorKey:'',selectedArticleKey:'',activeMediaSetKey:'',articleStatusFilter:'all',articleSearchTerm:'',unsupportedMediaKeys:new Set(),unpreviewableMediaKeys:new Set(),showBlockedPosters:true,groupRelatedMedia:false,nameResolutionAutoRemaining:24, nameResolutionAttempted:new Set(),nameResolutionDeferred:new Map(),nameResolutionFailures:new Map(),nameResolutionClassifications:new Map(),nameResolutionInFlight:false,smartBinaryPending:false},els:{contentFilter:{value:'all'},articleLimit:{value:'300'}},document:{querySelector:()=>({classList:{add(){}}})},isPosterBlocked:()=>false,isArticleNew:()=>false,isArticleSeen:()=>false,previewKey:a=>a.id,articleKey:a=>a.id,nameResolutionKey:a=>a.id,isAllPostsMode:()=>ctx.els.contentFilter.value==='all',isSelectableMedia:a=>!!a.complete,updateSelectionBar(){},updateSelectionDomInPlace(){},updateActiveArticleDomInPlace(){},renderPreviewDetails(){},browsePayload:x=>x,browserPerfMode:()=>ctx.els.contentFilter.value,parseQuickQuery:()=>({include:[],exclude:[],poster:[],ext:[],filename:[],subject:[],messageId:[]})};
vm.createContext(ctx);vm.runInContext(['filteredArticles','selectRangeTo','handleMediaSelectionClick','articlePageRequest','applyNameResolutionResultToArticle'].map(fn).join('\n'),ctx);
const a=[{id:'a',article:10,complete:true,media:{kind:'image',filename:'one.jpg',extension:'jpg'}},{id:'b',article:11,complete:true,media:{kind:'video',filename:'two.mp4',extension:'mp4'}},{id:'c',article:12,complete:true,media:{kind:'file',filename:'other.rar',extension:'rar'}}];ctx.state.articles=a;
assert.equal(ctx.articlePageRequest(1).smart_binaries,true);
ctx.els.contentFilter.value='images';assert.deepEqual(Array.from(ctx.filteredArticles(),x=>x.a.id),['a']);assert.equal(ctx.articlePageRequest(1).smart_binaries,true);
ctx.els.contentFilter.value='videos';assert.deepEqual(Array.from(ctx.filteredArticles(),x=>x.a.id),['b']);assert.equal(ctx.articlePageRequest(1).smart_binaries,true);
ctx.els.contentFilter.value='media';assert.deepEqual(Array.from(ctx.filteredArticles(),x=>x.a.id),['a','b']);
ctx.els.contentFilter.value='all';ctx.handleMediaSelectionClick(0,{});ctx.handleMediaSelectionClick(1,{});assert.equal(ctx.state.selectedItems.size,2,'two ordinary clicks must preserve both');ctx.handleMediaSelectionClick(0,{});assert.equal(ctx.state.selectedItems.size,1,'ordinary click toggles selection');ctx.handleMediaSelectionClick(2,{shiftKey:true});assert.equal(ctx.state.selectedItems.size,3,'range adds previously selected rows');
ctx.els.contentFilter.value='images';ctx.handleMediaSelectionClick(0,{});assert.equal(ctx.state.selectedItems.size,1,'media single click retains normal semantics');
// The same recovered yEnc filename should become visible in Images without
// losing the prior v3.7.13 prohibition on re-showing known broken previews.
const recovered={id:'recovered',article:13,complete:true,media:null,subject:'opaque yEnc'};ctx.state.articles.push(recovered);
assert.deepEqual(Array.from(ctx.filteredArticles(),x=>x.a.id),['a']);
assert(ctx.applyNameResolutionResultToArticle(recovered,{resolved:true,media:{filename:'recovered.jpg',extension:'jpg',kind:'image'}}));
assert.deepEqual(Array.from(ctx.filteredArticles(),x=>x.a.id),['a','recovered']);
ctx.state.unpreviewableMediaKeys.add('recovered');assert.deepEqual(Array.from(ctx.filteredArticles(),x=>x.a.id),['a']);
ctx.state.unpreviewableMediaKeys.clear();
assert.match(fn('scheduleObfuscatedNameResolution'),/nameResolutionInFlight/);assert.doesNotMatch(fn('scheduleObfuscatedNameResolution'),/!isAllPostsMode\(\)/);assert.match(fn('automaticNameResolutionCandidates'),/if\(!isAllPostsMode\(\)\)/);assert.doesNotMatch(fn('flushNameResolutionResultRender'),/!isAllPostsMode\(\)/);
assert.match(src,/scheduleObfuscatedNameResolution\(\);updateSelectionBar\(\)/,'auto-probing when media view has zero visible matches');
assert.match(src,/client_key:articleKey\(a\),segments:/,'source IDs retained for partial queue confirmations');
console.log('validate-v3715-newsgroup-browser.js: PASS (shared header scan, filter classification, additive All Posts selection, bounded filename recovery)');
