// Real production JS functions extracted without requiring a browser or network.
const fs=require('fs'),path=require('path'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(path.resolve(__dirname,'../../src/app/static/app.js'),'utf8');
function extract(start,end){const a=source.indexOf(start),b=source.indexOf(end,a+start.length);assert(a>=0&&b>a,`Production function missing: ${start}`);return source.slice(a,b)}
const funcs=[extract('function articlePageRequest(','function headerPrefetchMatches('),extract('function filteredArticles(','function renderArticleSearchHistory('),extract('function rememberPreviewUnavailable(','function rememberUnsupportedMedia('),extract('function queueUnavailableMediaHide(','function hideUnavailableArticleByKey(')].join('\n');
const liveVideo={media:{kind:'video',filename:'clip.mkv',extension:'mkv'},complete:true,article:99};
const liveImage={media:{kind:'image',filename:'pic.jpg',extension:'jpg'},complete:true,article:98};
const state={providerId:'test',selectedGroup:'fake',articleSearchTerm:'',articles:[liveVideo,liveImage],articleStatusFilter:'all',showBlockedPosters:true,unsupportedMediaKeys:new Set(['preview:99','preview:98']),unpreviewableMediaKeys:new Set(['preview:99','preview:98']),thumbDeferredRecoveryStarted:new Map(),groupRelatedMedia:false,thumbFailureCache:new Map(),selectedItems:new Set(['article:99']),selectedArticleKey:'article:99',viewerKey:'',unavailableHideQueue:new Map(),unavailableHideTimer:null,thumbQueued:new Set(),thumbQueue:[]};
const els={contentFilter:{value:'videos'},articleLimit:{value:'300'}};
const sandbox={state,els,previewKey:a=>'preview:'+a.article,articleKey:a=>'article:'+a.article,
 browserPerfMode:()=>els.contentFilter.value,browsePayload:x=>x,parseQuickQuery:()=>({poster:[],ext:[],filename:[],subject:[],messageId:[],include:[],exclude:[]}),
 isPosterBlocked:()=>false,isArticleSeen:()=>false,isArticleNew:()=>true,isDefinitiveUnsupportedMedia:()=>true,resetPreview:()=>{throw Error('video selection removed')},closeMediaViewer:()=>{},flushUnavailableMediaHides:()=>{},setTimeout:()=>1};
vm.createContext(sandbox);vm.runInContext(funcs,sandbox);
const payload=vm.runInContext('articlePageRequest(1)',sandbox);
assert.equal(payload.smart_binaries,false,'video browse must not start All Posts deep binary scan');
assert.equal(payload.video_discovery,true,'video mode should request progressive discovery');
assert.equal(payload.progressive,true,'first page should not wait for background scan');
assert.equal(vm.runInContext('filteredArticles().length',sandbox),1,'Video should remain even with failed previews');
vm.runInContext('rememberPreviewUnavailable(state.articles[0],{retryable:false,code:"decode_failed"})',sandbox);
assert(state.selectedItems.has('article:99'),'Thumbnail errors must not change video selection');
assert(!state.unpreviewableMediaKeys.has('preview:99')===false,'Preexisting flags do not bypass visibility safety');
assert(state.thumbFailureCache.has('preview:99'),'Thumbnail error must provide placeholder');
assert.equal(vm.runInContext('queueUnavailableMediaHide(state.articles[0],0)',sandbox),false);
assert.equal(state.unavailableHideQueue.size,0,'Video must never be scheduled for deletion from gallery');
assert.equal(vm.runInContext('filteredArticles().length',sandbox),1,'Video visible after failure');
els.contentFilter.value='images';assert.equal(vm.runInContext('filteredArticles().length',sandbox),0,'Image failure behavior preserved');
assert(source.includes('const isAppend=state.loadedPages.size>1'),'Progressive older-page completion must merge data');
assert(source.includes('if(state.smartBinaryPending)scheduleProgressiveBinaryCompletion(targetPage,generation)'),'Both initial and appended pages must poll');
assert(source.includes('if(state.selectedGroup){state.loadedPages.clear();state.articlePage=1'),'Switching filters must not retain stale discovery results');
console.log('PASS: real video-only request; video preview failure visibility/selection; image safety unchanged; append polling; filter switching');
