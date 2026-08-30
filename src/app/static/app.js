const state = {
  providers: [], providerId: '', groups: [], groupsTotal: 0, groupPageSize: 1000,
  selectedGroup: '', articles: [], selectedArticleKey: '', selectedItems: new Map(), selectionAnchorKey: '', articlePage: 1, articlePaging: null, articleSearchTerm: '',
  loadedPages: new Set(), continuousMode: true, continuousLoading: false, thumbnailSize: 'medium', browseScrollTop: 0, browseSessionToken:'', browseAbortController:null, headerPrefetch:null, progressiveBinaryTimer:null, smartBinaryPending:false, browseScrollVelocity:0, browseScrollDirection:1, lastBrowseScrollTop:0, lastBrowseScrollTs:0, thumbReleaseTimer:null, thumbCacheTrimTimer:null, continuousJumpHoldUntil:0, continuousJumpTimer:null, thumbGeometry:new Map(), thumbGeometryTs:0, thumbHolderRegistry:new Map(), thumbHolderRegistryStats:{hits:0,fallbacks:0}, speculativeThumbStats:{started:0,completed:0,cancelled:0},
  viewMode: 'gallery', previewCache: new Map(), previewPromises: new Map(), imageThumbCache: new Map(), imageThumbPromises: new Map(), videoThumbCache: new Map(), videoThumbPromises: new Map(), thumbQueued: new Set(), thumbQueue: [],
  thumbActive: 0, thumbVideoActive: 0, thumbSetActive: 0, thumbConcurrency: 7, videoThumbConcurrency: 1, setCoverConcurrency: 3, galleryGeneration: 0, previewConcurrencyMode:'idle', previewRamp:null, thumbFailureCache: new Map(), thumbImageRecovery: new Map(), thumbActiveTasks: new Map(), thumbEscalations: new Map(), thumbEscalationActive: 0, unsupportedMediaKeys: new Set(), unpreviewableMediaKeys: new Set(),
  downloadSnapshot: {paused:false,jobs:[],collections:[],counts:{},folder:''}, downloadedIndex: new Set(), queuedIndex: new Set(), downloadIndexSignature:'', downloadFilter:'active', downloadSearchTerm:'', selectedDownloads:new Set(), downloadSelectionAnchor:'', expandedDownloads:new Set(), expandedCollections:new Set(), postProgressMemory:new Map(), activeView:'browse', downloadOrganization:'flat',
  groupSearchJob:null, searchMode:false, browsePageBeforeSearch:1, groupSearchPollTimer:null, favorites:new Set(), bookmarkFolders:[], recentGroups:[], groupStates:{}, groupSessions:new Map(), groupMode:'all', nameResolutionInFlight:false, nameResolutionAttempted:new Set(), nameResolutionTimer:null, nameResolutionAutoRemaining:24,
  viewerOpen:false, viewerKey:'', viewerFit:true, viewerMode:'fit', viewerZoom:1, viewerRotation:0, viewerSetOnly:false, viewerReturnState:null, viewerPreloadTimer:null, viewerDrag:null, viewerInfoOpen:false, articleSearchReturn:null, articleSearchHistory:[], articleSearchTimer:null, perfMetrics:{}, uiSaveTimer:null, groupStateSaveTimer:null, groupRelatedMedia:false, groupBinarySets:true, binaryPackageFilter:'downloadable', binaryPackageSort:'newest', binaryMinSizeValue:0, binaryMinSizeUnit:'MB', smartBinaryHeaders:0, expandedBinarySets:new Set(), binarySetGroups:new Map(), settingsData:{}, activeMediaSetKey:'', savedSearches:[], activeSavedSearchId:'', blockedPosters:new Set(), showBlockedPosters:false, groupSeenHigh:{}, groupReadStates:{}, currentSeenArticles:new Set(), currentUnseenArticles:new Set(), currentReadStateKey:'', groupVisitBaseline:{}, articleStatusFilter:'all', trackedGroupStatus:{}, groupStatusRefreshTimer:null, browserTabs:[], activeBrowserTabId:'', diagnosticsSnapshot:null, onlineUpdate:null, pendingNzbFiles:[], currentNzbPreview:null, archivePasswordJobId:'', dragDownloadId:'', onboardingActive:false, serviceStatus:null, serviceTransition:'', automation:null, automationTab:'tv', automationLoadError:'', automationCalendarView:localStorage.getItem('newzdeckAutomationCalendarView')==='month'?'month':'guide', automationCalendarKind:localStorage.getItem('newzdeckAutomationCalendarKind')||'all', automationCalendarStatus:localStorage.getItem('newzdeckAutomationCalendarStatus')||'all', automationCalendarRange:Number(localStorage.getItem('newzdeckAutomationCalendarRange')||30), automationCalendarMonth:'', automationCalendarSelectedDate:'', discover:null, discoverTab:'home', discoverItems:[], discoverCurrentDetail:null, discoverLoadToken:0, discoverDetailToken:0, discoverDetailCache:{}, discoverDetailCacheTs:{}, discoverDetailInflight:{}, discoverDetailPrefetchTimers:{}, discoverGenres:{tv:[],movie:[]}, discoverPersonReturn:null, discoverPage:1, discoverPayloadCache:{home:null,for_you:null}, discoverPayloadCacheTs:{home:0,for_you:0}
};
const UI_VERSION = '3.6.15';
const $ = (id) => document.getElementById(id);
const els = {
  providerSelect:$('providerSelect'), providerDot:$('providerDot'), groupsList:$('groupsList'), groupHint:$('groupHint'),
  groupSearch:$('groupSearch'), groupSort:$('groupSort'), browserTabs:$('browserTabs'), mutedPostersBtn:$('mutedPostersBtn'), groupsMoreWrap:$('groupsMoreWrap'), loadMoreGroupsBtn:$('loadMoreGroupsBtn'), groupAllBtn:$('groupAllBtn'), groupFavoritesBtn:$('groupFavoritesBtn'), groupRecentBtn:$('groupRecentBtn'), favoriteCount:$('favoriteCount'), recentCount:$('recentCount'), bookmarkTools:$('bookmarkTools'), newBookmarkFolderBtn:$('newBookmarkFolderBtn'), recentTools:$('recentTools'), clearRecentBtn:$('clearRecentBtn'),
  articlesList:$('articlesList'), articleTitle:$('articleTitle'), articleEyebrow:$('articleEyebrow'), articleSummary:$('articleSummary'),
  articleLimit:$('articleLimit'), articleSort:$('articleSort'), contentFilter:$('contentFilter'), articleStatusFilter:$('articleStatusFilter'), jumpFirstUnseenBtn:$('jumpFirstUnseenBtn'), markAllSeenBtn:$('markAllSeenBtn'), galleryViewBtn:$('galleryViewBtn'), listViewBtn:$('listViewBtn'), articleViewToggle:$('articleViewToggle'), binaryViewToggle:$('binaryViewToggle'), binaryPackagesBtn:$('binaryPackagesBtn'), rawPostsBtn:$('rawPostsBtn'), binaryMinSizeToolbar:$('binaryMinSizeToolbar'), binaryMinSizeInput:$('binaryMinSizeInput'), binaryMinSizeUnit:$('binaryMinSizeUnit'), thumbnailSize:$('thumbnailSize'), continuousBrowseBtn:$('continuousBrowseBtn'), groupRelatedBtn:$('groupRelatedBtn'),
  articleSearch:$('articleSearch'), articleSearchInfo:$('articleSearchInfo'), articleSearchHistory:$('articleSearchHistory'), clearArticleSearchBtn:$('clearArticleSearchBtn'), entireGroupSearchBtn:$('entireGroupSearchBtn'),
  articlePagingBar:$('articlePagingBar'), olderArticlesBtn:$('olderArticlesBtn'), newerArticlesBtn:$('newerArticlesBtn'), latestArticlesBtn:$('latestArticlesBtn'), exitGroupSearchBtn:$('exitGroupSearchBtn'), articlePageInput:$('articlePageInput'), articlePageTotal:$('articlePageTotal'), articleRangeLabel:$('articleRangeLabel'),
  selectionBar:$('selectionBar'), selectionCount:$('selectionCount'), downloadSelectedBtn:$('downloadSelectedBtn'), clearSelectionBtn:$('clearSelectionBtn'), selectVisibleBtn:$('selectVisibleBtn'), selectLoadedBtn:$('selectLoadedBtn'), invertSelectionBtn:$('invertSelectionBtn'), markSelectedSeenBtn:$('markSelectedSeenBtn'), markSelectedUnseenBtn:$('markSelectedUnseenBtn'),
  previewContent:$('previewContent'), previewBadge:$('previewBadge'), providerModal:$('providerModal'), providerList:$('providerList'),
  mediaViewer:$('mediaViewer'), viewerStage:$('viewerStage'), viewerTitle:$('viewerTitle'), viewerMeta:$('viewerMeta'), viewerPosition:$('viewerPosition'), viewerPrevBtn:$('viewerPrevBtn'), viewerNextBtn:$('viewerNextBtn'), viewerFitBtn:$('viewerFitBtn'), viewerFillBtn:$('viewerFillBtn'), viewerActualBtn:$('viewerActualBtn'), viewerZoomOutBtn:$('viewerZoomOutBtn'), viewerZoomInBtn:$('viewerZoomInBtn'), viewerRotateBtn:$('viewerRotateBtn'), viewerZoomLabel:$('viewerZoomLabel'), viewerSetBtn:$('viewerSetBtn'), viewerInfoBtn:$('viewerInfoBtn'), viewerInfo:$('viewerInfo'), viewerSelectBtn:$('viewerSelectBtn'), viewerQueueBtn:$('viewerQueueBtn'), viewerCloseBtn:$('viewerCloseBtn'),
  providerForm:$('providerForm'), providerTestResult:$('providerTestResult'), settingsModal:$('settingsModal'), settingsCloseBtn:$('settingsCloseBtn'), settingsSaveBtn:$('settingsSaveBtn'), settingsCancelBtn:$('settingsCancelBtn'),
  browseView:$('browseView'), downloadsView:$('downloadsView'), diagnosticsView:$('diagnosticsView'), automationView:$('automationView'), discoverView:$('discoverView'), downloadsList:$('downloadsList'), downloadNavBadge:$('downloadNavBadge'),
  pauseDownloadsBtn:$('pauseDownloadsBtn'), hardStopDownloadsBtn:$('hardStopDownloadsBtn'), clearCompletedBtn:$('clearCompletedBtn'), importNzbBtn:$('importNzbBtn'), nzbFileInput:$('nzbFileInput'), chooseDownloadsFolderBtn:$('chooseDownloadsFolderBtn'), openDownloadsFolderBtn:$('openDownloadsFolderBtn'), downloadOrganization:$('downloadOrganization'),
  downloadSelectionBar:$('downloadSelectionBar'), downloadSelectionCount:$('downloadSelectionCount'), downloadPrioritySelect:$('downloadPrioritySelect'), downloadMoveTopBtn:$('downloadMoveTopBtn'), downloadMoveBottomBtn:$('downloadMoveBottomBtn'), downloadPauseSelectedBtn:$('downloadPauseSelectedBtn'), downloadResumeSelectedBtn:$('downloadResumeSelectedBtn'), downloadRetrySelectedBtn:$('downloadRetrySelectedBtn'), downloadCancelSelectedBtn:$('downloadCancelSelectedBtn'), downloadRemoveSelectedBtn:$('downloadRemoveSelectedBtn'), downloadClearSelectionBtn:$('downloadClearSelectionBtn'),
  nzbImportModal:$('nzbImportModal'), nzbImportCloseBtn:$('nzbImportCloseBtn'), nzbImportCancelBtn:$('nzbImportCancelBtn'), nzbCollectionName:$('nzbCollectionName'), nzbImportSummary:$('nzbImportSummary'), nzbImportFiles:$('nzbImportFiles'), nzbImportSelectionSummary:$('nzbImportSelectionSummary'), nzbImportQueueBtn:$('nzbImportQueueBtn'), nzbSelectAllBtn:$('nzbSelectAllBtn'), nzbSelectRecommendedBtn:$('nzbSelectRecommendedBtn'), nzbSelectNoneBtn:$('nzbSelectNoneBtn'),
  archivePasswordModal:$('archivePasswordModal'), archivePasswordInput:$('archivePasswordInput'), archivePasswordCloseBtn:$('archivePasswordCloseBtn'), archivePasswordCancelBtn:$('archivePasswordCancelBtn'), archivePasswordSubmitBtn:$('archivePasswordSubmitBtn'),
  aboutModal:$('aboutModal'), aboutInstallStatus:$('aboutInstallStatus'), aboutRuntimeStatus:$('aboutRuntimeStatus'), aboutInstallPath:$('aboutInstallPath'), aboutDataPath:$('aboutDataPath'), onlineUpdateStatus:$('onlineUpdateStatus'), onlineUpdateDetail:$('onlineUpdateDetail'), onlineReleaseNotes:$('onlineReleaseNotes'), onlineUpdateResult:$('onlineUpdateResult'), checkUpdatesBtn:$('checkUpdatesBtn'), installOnlineUpdateBtn:$('installOnlineUpdateBtn'), updatePackageInput:$('updatePackageInput'), updatePackageName:$('updatePackageName'), installUpdateBtn:$('installUpdateBtn'), updateResult:$('updateResult'), openDataFolderBtn:$('openDataFolderBtn'), aboutCloseBtn:$('aboutCloseBtn'),
  groupSearchModal:$('groupSearchModal'), entireGroupSearchInput:$('entireGroupSearchInput'), entireGroupSearchGroup:$('entireGroupSearchGroup'),
  entireGroupSearchProgress:$('entireGroupSearchProgress'), entireGroupSearchStatus:$('entireGroupSearchStatus'), entireGroupSearchPercent:$('entireGroupSearchPercent'), entireGroupSearchProgressFill:$('entireGroupSearchProgressFill'), entireGroupSearchStats:$('entireGroupSearchStats'), entireGroupSearchError:$('entireGroupSearchError'),
  startEntireGroupSearchBtn:$('startEntireGroupSearchBtn'), cancelEntireGroupSearchBtn:$('cancelEntireGroupSearchBtn'), viewEntireGroupSearchResultsBtn:$('viewEntireGroupSearchResultsBtn'), closeGroupSearchModalBtn:$('closeGroupSearchModalBtn'), entireSearchKind:$('entireSearchKind'), entireSearchPoster:$('entireSearchPoster'), entireSearchMinMb:$('entireSearchMinMb'), entireSearchMaxMb:$('entireSearchMaxMb'), entireSearchAge:$('entireSearchAge'), entireSearchExtensions:$('entireSearchExtensions'), savedSearchSelect:$('savedSearchSelect'), saveCurrentSearchBtn:$('saveCurrentSearchBtn'), deleteSavedSearchBtn:$('deleteSavedSearchBtn'),
};
let thumbObserver = null;
let continuousObserver = null;
let downloadSnapshotRequestId = 0;
let downloadSnapshotAppliedId = 0;
let downloadSnapshotAppliedSeq = 0;
let downloadDomSignature = '';
let downloadPollTimer = null;
let downloadPollInFlight = false;
let thumbDemandRaf = 0;
let thumbWatchdogTimer = null;

function friendlyTransportErrorMessage(message,path=''){
  const text=String(message||'').trim(),low=text.toLocaleLowerCase();
  const reset=/(?:winerror|errno)\s*10054|forcibly closed|connection reset|connection aborted|broken pipe|remote end closed/.test(low);
  const unavailable=/(?:winerror|errno)\s*10061|connection refused|actively refused|timed out|timeout/.test(low);
  const grab=String(path||'').includes('/api/automation/releases/grab');
  if(reset)return grab?'The built-in download engine briefly reset its local connection while queueing this release. Check Downloads; if the release is not listed, try Grab again in a moment.':'NewzDeck briefly lost a local connection. Try the operation again.';
  if(unavailable)return grab?'The built-in download engine was temporarily unavailable while queueing this release. Check Downloads; if it is not listed, try Grab again in a moment.':'A required local service was temporarily unavailable. Try again in a moment.';
  return text||'The request could not be completed.';
}

async function api(path, body=null, options={}){
  const timeoutMs=Math.max(0,Number(options?.timeoutMs||0)),externalSignal=options?.signal||null;
  const controller=(timeoutMs||externalSignal)?new AbortController():null;
  let timer=null,abortListener=null;
  if(controller&&timeoutMs)timer=setTimeout(()=>controller.abort('timeout'),timeoutMs);
  if(controller&&externalSignal){abortListener=()=>controller.abort('superseded');if(externalSignal.aborted)abortListener();else externalSignal.addEventListener('abort',abortListener,{once:true})}
  const opts = body ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : {};
  if(controller)opts.signal=controller.signal;
  try{
    const r = await fetch(path, opts); let data={}; try{data=await r.json()}catch{}
    if(!r.ok){let msg=data.error || `Request failed (${r.status})`;if(data.detail&&String(data.detail)!==String(data.error||''))msg+=` — ${data.detail}`;msg=friendlyTransportErrorMessage(msg,path);const err=new Error(msg);err.data=data;err.status=r.status;throw err} return data;
  }catch(e){
    if(e?.name==='AbortError'){if(externalSignal?.aborted){const err=new Error('Browsing request superseded.');err.code='browse-cancelled';throw err}const err=new Error(options?.timeoutMessage||'Request timed out. NewzDeck stopped waiting so the interface can recover.');err.code='ui-timeout';throw err}
    if(e instanceof Error)e.message=friendlyTransportErrorMessage(e.message,path);
    throw e;
  }finally{if(timer)clearTimeout(timer);if(externalSignal&&abortListener)externalSignal.removeEventListener('abort',abortListener)}
}

function makeBrowseSessionToken(){try{return crypto.randomUUID()}catch{return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`}}
function browseRequestOptions(extra={}){return {...extra,...(state.browseAbortController?{signal:state.browseAbortController.signal}:{})}}
function browsePayload(payload={}){return {...payload,...(state.browseSessionToken?{browse_session:state.browseSessionToken}:{})}}
async function beginBrowseSession(group=state.selectedGroup,{preserveProgressive=false}={}){
  if(state.browseAbortController)state.browseAbortController.abort();
  if(state.progressiveBinaryTimer){clearTimeout(state.progressiveBinaryTimer);state.progressiveBinaryTimer=null}
  state.headerPrefetch=null;if(!preserveProgressive)state.smartBinaryPending=false;state.browseAbortController=new AbortController();state.browseSessionToken=makeBrowseSessionToken();
  state.thumbQueue=[];state.thumbQueued.clear();state.thumbGeometry.clear();state.thumbGeometryTs=0;state.thumbHolderRegistry.clear();state.previewPromises.clear();state.imageThumbPromises.clear();state.videoThumbPromises.clear();
  try{await api('/api/browse/session',{provider_id:state.providerId,group,browse_session:state.browseSessionToken},{timeoutMs:4000})}
  catch(e){if(e?.code!=='browse-cancelled'){state.browseSessionToken='';console.warn('Could not register browsing session',e)}}
}
function rotateBrowsePreviewSession(){
  if(!state.selectedGroup)return Promise.resolve();const pending=!!state.smartBinaryPending,page=state.articlePage,generation=++state.galleryGeneration;
  const promise=beginBrowseSession(state.selectedGroup,{preserveProgressive:pending}).then(()=>{if(generation!==state.galleryGeneration)return;if(pending){state.smartBinaryPending=true;scheduleProgressiveBinaryCompletion(page,generation)}scheduleThumbnailDemandScan()});
  promise.catch(e=>console.warn('Could not rotate browsing preview session',e));return promise;
}
async function metadataApi(path,body=null){return api(path,body,{timeoutMs:40000,timeoutMessage:'Metadata request timed out. NewzDeck stopped waiting; try again in a moment or check Automation → Health.'})}

function perfRecord(name,ms){
  const value=Number(ms);if(!Number.isFinite(value)||value<0)return;const key=String(name||'other');const list=state.perfMetrics[key]||(state.perfMetrics[key]=[]);list.push(value);if(list.length>40)list.splice(0,list.length-40);
}
function perfAverage(name){const list=state.perfMetrics[name]||[];return list.length?list.reduce((a,b)=>a+b,0)/list.length:0}
function browseCacheLimits(){
  const ram=Number(navigator.deviceMemory||8);
  if(ram<=4)return{thumb:320,preview:64,failure:240,recovery:160};
  if(ram<=8)return{thumb:640,preview:128,failure:360,recovery:240};
  if(ram<=16)return{thumb:1100,preview:220,failure:520,recovery:360};
  return{thumb:1800,preview:360,failure:800,recovery:520};
}
function boundedCacheSet(map,key,value,limit){if(map.has(key))map.delete(key);map.set(key,value);while(map.size>limit){const oldest=map.keys().next().value;if(oldest==null)break;map.delete(oldest)}return value}
function trimBrowsingMemoryCaches(){
  const lim=browseCacheLimits(),keep=new Set();
  if(state.selectedGroup){const prefix=`${state.providerId}|${state.selectedGroup}|`;for(const a of state.articles){const key=previewKey(a);if(key.startsWith(prefix))keep.add(key)}}
  const trim=(map,limit)=>{if(map.size<=limit)return;for(const key of [...map.keys()]){if(map.size<=limit)break;if(!keep.has(key))map.delete(key)}while(map.size>limit){const key=map.keys().next().value;if(key==null)break;map.delete(key)}};
  trim(state.imageThumbCache,lim.thumb);trim(state.videoThumbCache,Math.max(96,Math.floor(lim.thumb*.28)));trim(state.previewCache,lim.preview);trim(state.thumbFailureCache,lim.failure);trim(state.thumbImageRecovery,lim.recovery);
}
function scheduleBrowsingMemoryTrim(){if(state.thumbCacheTrimTimer)return;state.thumbCacheTrimTimer=setTimeout(()=>{state.thumbCacheTrimTimer=null;trimBrowsingMemoryCaches()},1800)}
function perfSummaryText(){const labels=[['headers','Headers'],['render','Render'],['search','Local search'],['thumbnail','Thumbnail'],['preview','Full preview'],['viewer_preload','Viewer preload']];return labels.map(([k,l])=>{const v=perfAverage(k);return v?`${l} ${Math.round(v)} ms`:''}).filter(Boolean).join(' • ')||'No browser timing samples yet'}
function toast(msg,type=''){ if(state.serviceTransition&&/failed to fetch|networkerror|load failed/i.test(String(msg||'')))return;const n=document.createElement('div'); n.className=`toast ${type}`;n.textContent=msg;$('toastStack').appendChild(n);setTimeout(()=>n.remove(),4200); }
async function copyText(text){try{await navigator.clipboard.writeText(String(text||''));toast('Copied to clipboard.','success')}catch{const t=document.createElement('textarea');t.value=String(text||'');document.body.appendChild(t);t.select();document.execCommand('copy');t.remove();toast('Copied to clipboard.','success')}}
function closeContextMenu(){document.querySelector('.desktop-context-menu')?.remove()}
function showContextMenu(x,y,items){closeContextMenu();const menu=document.createElement('div');menu.className='desktop-context-menu';for(const item of items){if(item.separator){menu.appendChild(document.createElement('hr'));continue}const b=document.createElement('button');b.type='button';b.textContent=item.label;b.disabled=!!item.disabled;b.onclick=()=>{closeContextMenu();if(item.action)item.action()};menu.appendChild(b)}document.body.appendChild(menu);const r=menu.getBoundingClientRect();menu.style.left=`${Math.max(8,Math.min(x,window.innerWidth-r.width-8))}px`;menu.style.top=`${Math.max(8,Math.min(y,window.innerHeight-r.height-8))}px`;setTimeout(()=>document.addEventListener('pointerdown',closeContextMenu,{once:true}),0)}
function formatCount(n){ n=Number(n||0); return n>=1e6?(n/1e6).toFixed(1)+'m':n>=1e3?(n/1e3).toFixed(n>=1e5?0:1)+'k':n.toLocaleString(); }
function formatBytes(n){ n=Number(n||0); if(!n)return '—'; const units=['B','KB','MB','GB'];let i=0;while(n>=1024&&i<units.length-1){n/=1024;i++}return `${n.toFixed(i>1?1:0)} ${units[i]}`; }
function escapeHtml(s=''){ return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }
function shortDate(s){ const d=new Date(s); return Number.isNaN(d.getTime())?String(s||'').slice(0,16):d.toLocaleDateString(undefined,{month:'short',day:'numeric',year:d.getFullYear()!==new Date().getFullYear()?'numeric':undefined}); }
function articleKey(a){ return a?.message_id || `${a?.article||''}|${a?.subject||''}`; }
function articleGroup(a){return a?.group||state.selectedGroup||''}
function previewKey(a){ return `${state.providerId}|${articleGroup(a)}|${articleKey(a)}`; }
function segmentPayload(a){ return (a.segments||[]).map(s=>({...s,bytes:Number(s.bytes||0)||Math.ceil((a.bytes||0)/Math.max(1,a.segment_count||1))})); }
function hydrateServerThumbnailHints(items){
  const lim=browseCacheLimits();for(const a of items||[]){if(a?.small_image_suppressed&&a?.media?.kind==='image'){a.media_meta={...(a.media_meta||{}),width:Number(a.media_meta?.width||0),height:Number(a.media_meta?.height||0)};continue}const url=String(a?.cached_thumbnail_url||'');if(!url||!a?.media)continue;const key=previewKey(a),result={url,thumbnail_url:url,thumbnail_token:a.cached_thumbnail_token||'',cached:true,method:'header-cache-hint'};if(a.media.kind==='image')boundedCacheSet(state.imageThumbCache,key,result,lim.thumb);else if(a.media.kind==='video')boundedCacheSet(state.videoThumbCache,key,result,Math.max(96,Math.floor(lim.thumb*.28)));}
}
function thumbnailLaneHint(a,task=null){
  if(a?.media?.kind!=='image'||Number(a.segment_count||0)<4)return 1;const bytes=Number(a.bytes||0);const foreground=task?.priority===0||((task&&liveThumbnailTaskScore(task)<1e9));if(!foreground)return 1;if(bytes>=24*1024*1024)return 3;if(bytes>=8*1024*1024)return 2;return 1;
}

function downloadLookupKey(providerId,group,filename){return `${providerId||''}|${group||''}|${String(filename||'').toLocaleLowerCase()}`}
function itemDownloadKey(a){return downloadLookupKey(state.providerId,articleGroup(a),a?.media?.filename||'')}
function formatDuration(seconds){seconds=Number(seconds);if(!Number.isFinite(seconds)||seconds<=0)return '';const s=Math.floor(seconds%60),m=Math.floor((seconds/60)%60),h=Math.floor(seconds/3600);return h?`${h}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`:`${m}:${String(s).padStart(2,'0')}`}
function daysBackFromLoaded(){let oldest=Infinity;for(const a of state.articles){const t=Date.parse(a.date||'');if(Number.isFinite(t)&&t<oldest)oldest=t}if(!Number.isFinite(oldest))return 0;return Math.max(0,Math.floor((Date.now()-oldest)/86400000))}
function applyThumbnailSize(){
  if(!els.articlesList)return;for(const size of ['small','medium','large','xlarge'])els.articlesList.classList.toggle(`thumb-${size}`,state.thumbnailSize===size);
  if(els.thumbnailSize)els.thumbnailSize.value=state.thumbnailSize;
}
function updateContinuousButton(){
  if(!els.continuousBrowseBtn)return;els.continuousBrowseBtn.classList.toggle('active',state.continuousMode);els.continuousBrowseBtn.setAttribute('aria-pressed',state.continuousMode?'true':'false');els.continuousBrowseBtn.title=state.continuousMode?'Continuous browsing is on — older headers load as you scroll':'Continuous browsing is off — use the page controls';
}
function isAllPostsMode(){return els.contentFilter?.value==='all'}
function effectiveViewMode(){return isAllPostsMode()?'list':state.viewMode}
function syncBinaryMinSizeToolbar(){
  if(els.binaryMinSizeInput)els.binaryMinSizeInput.value=String(Math.max(0,Number(state.binaryMinSizeValue||0)));
  if(els.binaryMinSizeUnit)els.binaryMinSizeUnit.value=['MB','GB'].includes(state.binaryMinSizeUnit)?state.binaryMinSizeUnit:'MB';
}
function updateBrowseModeControls(){
  const all=isAllPostsMode(),mode=effectiveViewMode(),packages=all&&state.groupBinarySets;
  const browseView=$('browseView'),previewPane=browseView?.querySelector('.preview-pane');
  browseView?.classList.toggle('all-posts-wide',all);
  if(previewPane){previewPane.setAttribute('aria-hidden',all?'true':'false');if(all)previewPane.classList.remove('open')}
  els.articleViewToggle?.classList.toggle('hidden',all);els.binaryViewToggle?.classList.toggle('hidden',!all);
  els.binaryPackagesBtn?.classList.toggle('active',packages);els.rawPostsBtn?.classList.toggle('active',all&&!state.groupBinarySets);
  syncBinaryMinSizeToolbar();
  document.querySelector('.thumbnail-size-label')?.classList.toggle('hidden',all);
  els.galleryViewBtn?.classList.toggle('active',mode==='gallery');els.listViewBtn?.classList.toggle('active',mode==='list');
  if(els.galleryViewBtn)els.galleryViewBtn.disabled=all;if(els.listViewBtn)els.listViewBtn.disabled=all;
  updateGroupRelatedButton();
}
function updateGroupRelatedButton(){
  if(!els.groupRelatedBtn)return;const all=isAllPostsMode(),active=state.groupRelatedMedia;
  els.groupRelatedBtn.classList.toggle('hidden',all);els.groupRelatedBtn.classList.toggle('active',!all&&active);els.groupRelatedBtn.setAttribute('aria-pressed',!all&&active?'true':'false');
  els.groupRelatedBtn.textContent=active?'▦ Media grouped':'▦ Group related';
  els.groupRelatedBtn.title='Group numbered image/video filename sequences into visual media sets';
}
function compactReadStates(){
  const now=Date.now(),maxAge=180*24*60*60*1000;const protectedKeys=new Set([seenKey(state.selectedGroup),...state.browserTabs.map(t=>seenKey(t.group,t.provider_id)),...state.recentGroups,...[...state.favorites].map(g=>seenKey(g))].filter(Boolean));
  const entries=Object.entries(state.groupReadStates||{}).filter(([key,raw])=>protectedKeys.has(key)||now-Number(raw?.updated_ts||0)<=maxAge).sort((a,b)=>Number(b[1]?.updated_ts||0)-Number(a[1]?.updated_ts||0)).slice(0,100);const out={};
  for(const [key,raw] of entries){const through=Math.max(0,Number(raw?.seen_through||0));const seen=[...new Set((Array.isArray(raw?.seen_articles)?raw.seen_articles:[]).map(Number).filter(n=>Number.isFinite(n)&&n>through))].sort((a,b)=>a-b).slice(-1500);const unseen=[...new Set((Array.isArray(raw?.unseen_articles)?raw.unseen_articles:[]).map(Number).filter(n=>Number.isFinite(n)&&n>0&&n<=through))].sort((a,b)=>a-b).slice(-750);out[key]={seen_through:through,seen_articles:seen,unseen_articles:unseen,acknowledged_high:Math.max(0,Number(raw?.acknowledged_high||0)),updated_ts:Number(raw?.updated_ts||now)}}
  state.groupReadStates=out;return out
}
function saveUiSettings(){
  clearTimeout(state.uiSaveTimer);state.uiSaveTimer=setTimeout(()=>api('/api/settings/save',{article_limit:Number(els.articleLimit?.value||300),thumbnail_size:state.thumbnailSize,continuous_browse:state.continuousMode,view_mode:state.viewMode,content_filter:els.contentFilter?.value||'images',download_organization:state.downloadOrganization||'flat',group_related_media:state.groupRelatedMedia,group_binary_sets:state.groupBinarySets,binary_min_size_value:Number(state.binaryMinSizeValue||0),binary_min_size_unit:state.binaryMinSizeUnit||'MB',favorites:[...state.favorites],bookmark_folders:state.bookmarkFolders.map(f=>({id:f.id,name:f.name,groups:[...(f.groups||[])],collapsed:!!f.collapsed})),recent_groups:state.recentGroups,group_states:state.groupStates,blocked_posters:[...state.blockedPosters],group_seen_high:state.groupSeenHigh,group_read_states:compactReadStates(),browser_tabs:state.browserTabs.map(t=>({id:t.id,provider_id:t.provider_id,group:t.group,title:t.title||t.group})),active_browser_tab:state.activeBrowserTabId}).catch(()=>{}),250);
}
async function loadUiSettings(){
  try{
    const settings=await api('/api/settings');state.settingsData=settings;
    if(els.articleLimit&&[...els.articleLimit.options].some(o=>o.value===String(settings.article_limit)))els.articleLimit.value=String(settings.article_limit);
    state.thumbnailSize=['small','medium','large','xlarge'].includes(settings.thumbnail_size)?settings.thumbnail_size:'medium';
    state.continuousMode=settings.continuous_browse!==false;
    state.viewMode=settings.view_mode==='list'?'list':'gallery';
    if(els.contentFilter&&['images','videos','media','all'].includes(settings.content_filter))els.contentFilter.value=settings.content_filter;
    state.downloadOrganization=['flat','newsgroup','kind','newsgroup_kind'].includes(settings.download_organization)?settings.download_organization:'flat';if(els.downloadOrganization)els.downloadOrganization.value=state.downloadOrganization;state.groupRelatedMedia=!!settings.group_related_media;state.groupBinarySets=settings.group_binary_sets!==false;const savedBinaryMin=Number(settings.binary_min_size_value||0);state.binaryMinSizeValue=Number.isFinite(savedBinaryMin)?Math.max(0,Math.min(1000000,savedBinaryMin)):0;const savedBinaryUnit=String(settings.binary_min_size_unit||'MB').toUpperCase();state.binaryMinSizeUnit=['MB','GB'].includes(savedBinaryUnit)?savedBinaryUnit:'MB';state.favorites=new Set(Array.isArray(settings.favorites)?settings.favorites:[]);state.bookmarkFolders=normalizeBookmarkFolders(settings.bookmark_folders);for(const f of state.bookmarkFolders)for(const g of f.groups)state.favorites.add(g);state.recentGroups=Array.isArray(settings.recent_groups)?settings.recent_groups.slice(0,20):[];state.groupStates=settings.group_states&&typeof settings.group_states==='object'?settings.group_states:{};state.blockedPosters=new Set(Array.isArray(settings.blocked_posters)?settings.blocked_posters:[]);state.groupSeenHigh=settings.group_seen_high&&typeof settings.group_seen_high==='object'?settings.group_seen_high:{};state.groupReadStates=settings.group_read_states&&typeof settings.group_read_states==='object'?settings.group_read_states:{};for(const [key,high] of Object.entries(state.groupSeenHigh)){if(!state.groupReadStates[key])state.groupReadStates[key]={seen_through:0,seen_articles:[],unseen_articles:[],acknowledged_high:Number(high||0),updated_ts:0}}state.browserTabs=Array.isArray(settings.browser_tabs)?settings.browser_tabs.filter(t=>t&&t.group).slice(0,20):[];state.activeBrowserTabId=String(settings.active_browser_tab||'');
  }catch(_e){
    state.viewMode=localStorage.getItem('usenetViewMode')==='list'?'list':'gallery';
    state.thumbnailSize='medium';state.continuousMode=true;state.downloadOrganization='flat';state.groupRelatedMedia=false;state.groupBinarySets=true;state.binaryMinSizeValue=0;state.binaryMinSizeUnit='MB';state.favorites=new Set();state.bookmarkFolders=[];state.recentGroups=[];state.groupStates={};state.blockedPosters=new Set();state.groupSeenHigh={};state.groupReadStates={};state.currentSeenArticles=new Set();state.currentUnseenArticles=new Set();state.currentReadStateKey='';state.groupVisitBaseline={};state.trackedGroupStatus={};state.browserTabs=[];state.activeBrowserTabId='';
  }
  applyThumbnailSize();updateContinuousButton();updateBrowseModeControls();updateFavoriteUi();updateMutedPostersButton();renderBrowserTabs();
}
function switchSettingsTab(name){
  document.querySelectorAll('[data-settings-tab]').forEach(b=>b.classList.toggle('active',b.dataset.settingsTab===name));
  document.querySelectorAll('[data-settings-section]').forEach(x=>x.classList.toggle('active',x.dataset.settingsSection===name));
}
function populateSettingsForm(settings,health={}){
  state.settingsData=settings||{};
  const set=(id,value)=>{const el=$(id);if(el)el.value=String(value??'')};
  const check=(id,value)=>{const el=$(id);if(el)el.checked=!!value};
  set('settingsViewMode',settings.view_mode||state.viewMode||'gallery');set('settingsContentFilter',settings.content_filter||els.contentFilter?.value||'images');set('settingsThumbnailSize',settings.thumbnail_size||state.thumbnailSize||'medium');
  check('settingsContinuousBrowse',settings.continuous_browse!==false);set('settingsArticleLimit',settings.article_limit||300);set('settingsPreviewLimit',settings.preview_limit_mb||512);check('settingsGroupRelated',!!settings.group_related_media);
  $('settingsDownloadFolder').textContent=settings.download_folder||state.downloadSnapshot?.folder||'—';$('settingsDownloadFolder').title=$('settingsDownloadFolder').textContent;set('settingsDownloadOrganization',settings.download_organization||state.downloadOrganization||'flat');set('settingsDiskReserve',settings.disk_reserve_gb||1);
  check('settingsWatchEnabled',!!settings.watch_folder_enabled);$('settingsWatchFolder').textContent=settings.watch_folder||'—';$('settingsWatchFolder').title=settings.watch_folder||'';check('settingsWatchArchive',settings.watch_archive_processed!==false);check('settingsSmartCategories',!!settings.smart_categories_enabled);set('settingsMoviesKeywords',settings.category_movies_keywords||'');set('settingsMoviesFolder',settings.category_movies_folder||'Movies');set('settingsTvKeywords',settings.category_tv_keywords||'');set('settingsTvFolder',settings.category_tv_folder||'TV');set('settingsImagesKeywords',settings.category_images_keywords||'');set('settingsImagesFolder',settings.category_images_folder||'Images');set('settingsOtherFolder',settings.category_other_folder||'Other');check('settingsBandwidthSchedule',!!settings.bandwidth_schedule_enabled);set('settingsBandwidthStart',settings.bandwidth_schedule_start||'18:00');set('settingsBandwidthEnd',settings.bandwidth_schedule_end||'23:00');set('settingsBandwidthLimit',settings.bandwidth_schedule_limit_mb_s||25);check('settingsCompletionNotification',!!settings.completion_notification);check('settingsCompletionOpenFolder',!!settings.completion_open_folder);const watchSel=$('settingsWatchProvider');if(watchSel){watchSel.innerHTML='<option value="">Automatic (first download provider)</option>'+state.providers.filter(p=>p.use_downloads!==false).map(p=>`<option value="${escapeHtml(p.id)}">${escapeHtml(p.name||p.host||'Provider')}</option>`).join('');watchSel.value=settings.watch_provider_id||'';}
  check('settingsPostProcessing',settings.post_processing!==false);check('settingsAutoRepair',settings.auto_repair!==false);check('settingsAutoFetchPar2',settings.auto_fetch_par2!==false);check('settingsAutoExtract',settings.auto_extract!==false);set('settingsDirectUnpackMode',settings.direct_unpack_mode||'auto');check('settingsExtractSubfolder',settings.extract_subfolder!==false);check('settingsCleanupArchives',!!settings.cleanup_archives);check('settingsAutomationMediaCleanup',settings.automation_media_cleanup!==false);set('settingsThumbCache',settings.thumbnail_cache_gb||2);
  const tools=[];if(health.par2)tools.push(health.par2_managed?'PAR2 repair ready (managed)':'PAR2 repair ready');else if(health.par2_auto_install)tools.push(health.par2_install_error?'PAR2 auto-install will retry when needed':'PAR2 tool will install automatically when needed');else tools.push('PAR2 tool not found');if(health.sevenzip)tools.push('7-Zip ready');else tools.push('7-Zip not found (ZIP extraction still works)');if(health.unrar)tools.push(health.unrar_managed?`Direct Unpack ready (managed UnRAR ${health.unrar_managed_version||'7.23'})`:'Direct Unpack ready (external UnRAR)');else if(health.unrar_auto_install)tools.push(health.unrar_install_error?'Managed UnRAR setup will retry automatically':`Managed UnRAR ${health.unrar_managed_version||'7.23'} installs automatically`);else tools.push('Direct Unpack unavailable');
  const status=$('postToolStatus');status.textContent=tools.join(' • ');status.className=`post-tool-status ${(health.par2&&health.sevenzip)?'good':'warning'}`;
}
function renderServiceSettings(info={}){
  state.serviceStatus=info||{};
  const title=$('serviceStatusTitle'),detail=$('serviceStatusDetail'),badge=$('serviceStatusBadge'),install=$('installServiceBtn'),startBtn=$('startServiceBtn'),stopBtn=$('stopServiceBtn'),restart=$('restartServiceBtn'),repair=$('repairServiceBtn'),tray=$('settingsTrayAutostart');
  if(tray)tray.checked=!!info.tray_autostart;
  const status=String(info.status||'unknown');
  if(info.service_mode&&status==='running'){
    if(title)title.textContent='Background service is running';
    if(detail)detail.textContent='Downloads continue when the NewzDeck window is closed. The service owns the active queue.';
    if(badge){badge.textContent='RUNNING';badge.className='service-status-badge running'}
  }else if(status==='running'){
    if(title)title.textContent='Background service is running';
    if(detail)detail.textContent='NewzDeck is switching to the service-owned background engine.';
    if(badge){badge.textContent='RUNNING';badge.className='service-status-badge running'}
  }else if(info.installed){
    if(title)title.textContent=`Background service: ${status}`;
    if(detail)detail.textContent=info.worker_detail||'The service is installed but is not currently serving NewzDeck.';
    if(badge){badge.textContent=status.toUpperCase();badge.className='service-status-badge warning'}
  }else{
    if(title)title.textContent='Background service is not installed';
    if(detail)detail.textContent='Install it once so downloads and future TV/movie monitoring can run 24/7 without the main window.';
    if(badge){badge.textContent='OFF';badge.className='service-status-badge off'}
  }
  if(install){install.textContent=info.installed?'Service Installed':'Install Background Service';install.disabled=!!info.installed}
  const running=status==='running'||status==='starting';
  if(startBtn)startBtn.disabled=!info.installed||running||status==='stopping';
  if(stopBtn)stopBtn.disabled=!info.installed||!running||status==='stopping';
  if(restart)restart.disabled=!info.installed||status==='starting'||status==='stopping';
  if(repair)repair.disabled=!info.installed||status==='starting'||status==='stopping';
}
async function refreshServiceSettings(){try{const info=await api('/api/service/status');renderServiceSettings(info);return info}catch(e){renderServiceSettings({status:'unavailable'});return null}}
async function installBackgroundService(){
  const btn=$('installServiceBtn');if(btn){btn.disabled=true;btn.textContent='Waiting for Windows…'}
  try{
    const r=await api('/api/service/install',{});renderServiceSettings(r);toast('Background service installed. NewzDeck is switching to service mode.','success');
    if(r.switch_required&&r.service_url){setTimeout(()=>{window.location.href=r.service_url},700)}
  }catch(e){toast(e.message,'error');await refreshServiceSettings()}finally{if(btn&&!state.serviceStatus?.installed){btn.disabled=false;btn.textContent='Install Background Service'}}
}
async function waitForServiceSwitch(){
  for(let i=0;i<60;i++){
    await new Promise(r=>setTimeout(r,750));
    try{const info=await api('/api/service/status');renderServiceSettings(info);if(info.service_ready&&!info.service_mode&&info.service_url){window.location.href=info.service_url;return true}}catch(e){}
  }
  return false;
}
function showServiceTransitionOverlay(mode='stop'){
  let box=$('serviceTransitionOverlay');if(!box){box=document.createElement('div');box.id='serviceTransitionOverlay';box.className='service-transition-overlay';document.body.appendChild(box)}
  const restarting=mode==='restart';
  box.innerHTML=`<div class="service-transition-card"><div class="service-transition-mark">N<span>↓</span></div><h2>${restarting?'Restarting NewzDeck Service…':'NewzDeck Background Service stopped'}</h2><p>${restarting?'The background engine is restarting. This window will reconnect automatically.':'The background engine has been stopped intentionally. The tray icon remains available so you can start it again without reopening this window.'}</p><button id="serviceReconnectBtn" type="button">${restarting?'Reconnect now':'Check for service'}</button></div>`;
  const check=async()=>{try{const r=await fetch('/api/health',{cache:'no-store'});if(r.ok){location.reload();return true}}catch(_e){}return false};
  $('serviceReconnectBtn').onclick=check;
  if(restarting){const timer=setInterval(async()=>{if(await check())clearInterval(timer)},700)}
}
async function serviceSettingsControl(action){
  const disruptive=action==='stop'||action==='restart';if(disruptive)state.serviceTransition=action;
  try{
    const r=await api('/api/service/control',{action});renderServiceSettings(r);
    if(action==='launch_tray')toast('NewzDeck tray icon started.','success');
    else if(action==='start'){toast('Windows is starting the NewzDeck service.','success');if(!r.service_mode)waitForServiceSwitch()}
    else if(action==='stop'){toast('Windows is stopping the NewzDeck service.','success');closeSettingsModal();showServiceTransitionOverlay('stop')}
    else if(action==='restart'){toast('Windows is restarting the NewzDeck service.','success');closeSettingsModal();showServiceTransitionOverlay('restart')}
    else if(action==='repair')toast('Windows is repairing the NewzDeck service.','success');
  }catch(e){if(disruptive&&/Failed to fetch|NetworkError|fetch/i.test(String(e.message||''))){showServiceTransitionOverlay(action);return}state.serviceTransition='';toast(e.message,'error')}
}
async function openSettingsModal(tab='general'){
  els.settingsModal.classList.remove('hidden');switchSettingsTab(tab);
  try{const [settings,health,service]=await Promise.all([api('/api/settings'),api('/api/health'),api('/api/service/status')]);populateSettingsForm(settings,health);renderServiceSettings(service)}catch(e){toast(e.message,'error')}
}
function closeSettingsModal(){els.settingsModal.classList.add('hidden')}
async function saveSettingsModal(){
  const payload={
    view_mode:$('settingsViewMode').value,content_filter:$('settingsContentFilter').value,thumbnail_size:$('settingsThumbnailSize').value,continuous_browse:$('settingsContinuousBrowse').checked,
    article_limit:Number($('settingsArticleLimit').value||300),preview_limit_mb:Number($('settingsPreviewLimit').value||512),group_related_media:$('settingsGroupRelated').checked,
    download_organization:$('settingsDownloadOrganization').value,concurrent_downloads:1,disk_reserve_gb:Number($('settingsDiskReserve').value||1),
    watch_folder_enabled:$('settingsWatchEnabled').checked,watch_folder:$('settingsWatchFolder').textContent==='—'?'':$('settingsWatchFolder').textContent,watch_provider_id:$('settingsWatchProvider').value,watch_archive_processed:$('settingsWatchArchive').checked,
    smart_categories_enabled:$('settingsSmartCategories').checked,category_movies_keywords:$('settingsMoviesKeywords').value,category_movies_folder:$('settingsMoviesFolder').value,category_tv_keywords:$('settingsTvKeywords').value,category_tv_folder:$('settingsTvFolder').value,category_images_keywords:$('settingsImagesKeywords').value,category_images_folder:$('settingsImagesFolder').value,category_other_folder:$('settingsOtherFolder').value,
    bandwidth_schedule_enabled:$('settingsBandwidthSchedule').checked,bandwidth_schedule_start:$('settingsBandwidthStart').value||'18:00',bandwidth_schedule_end:$('settingsBandwidthEnd').value||'23:00',bandwidth_schedule_limit_mb_s:Number($('settingsBandwidthLimit').value||25),completion_notification:$('settingsCompletionNotification').checked,completion_open_folder:$('settingsCompletionOpenFolder').checked,
    post_processing:$('settingsPostProcessing').checked,auto_repair:$('settingsAutoRepair').checked,auto_fetch_par2:$('settingsAutoFetchPar2').checked,auto_extract:$('settingsAutoExtract').checked,direct_unpack_mode:$('settingsDirectUnpackMode').value,extract_subfolder:$('settingsExtractSubfolder').checked,cleanup_archives:$('settingsCleanupArchives').checked,automation_media_cleanup:$('settingsAutomationMediaCleanup').checked,
    thumbnail_cache_gb:Number($('settingsThumbCache').value||2)
  };
  try{
    const saved=await api('/api/settings/save',payload);state.settingsData=saved;state.thumbnailSize=saved.thumbnail_size;state.continuousMode=saved.continuous_browse!==false;state.viewMode=saved.view_mode==='list'?'list':'gallery';state.groupRelatedMedia=!!saved.group_related_media;state.downloadOrganization=saved.download_organization||'flat';
    if(els.articleLimit)els.articleLimit.value=String(saved.article_limit);if(els.contentFilter)els.contentFilter.value=saved.content_filter;if(els.downloadOrganization)els.downloadOrganization.value=state.downloadOrganization;
    applyThumbnailSize();updateContinuousButton();updateGroupRelatedButton();renderArticles();closeSettingsModal();toast('Settings saved.','success');
  }catch(e){toast(e.message,'error')}
}
async function settingsChooseDownloadFolder(){
  try{const r=await api('/api/settings/choose-download-folder',{});if(!r.cancelled){state.settingsData=r;$('settingsDownloadFolder').textContent=r.download_folder||'—';$('settingsDownloadFolder').title=r.download_folder||'';toast('Download folder updated.','success');await loadDownloads()}}catch(e){toast(e.message,'error')}
}
async function settingsChooseWatchFolder(){
  try{const r=await api('/api/settings/choose-watch-folder',{});if(!r.cancelled){state.settingsData=r;$('settingsWatchFolder').textContent=r.watch_folder||'—';$('settingsWatchFolder').title=r.watch_folder||'';toast('NZB watch folder updated.','success')}}catch(e){toast(e.message,'error')}
}
function exportConfigBackup(){window.location.href='/api/config/backup'}
async function restoreConfigBackup(file){if(!file)return;try{const text=await file.text();const payload=JSON.parse(text);const saved=await api('/api/config/restore',payload);await loadProviders();populateSettingsForm(saved,await api('/api/health'));toast('Configuration restored. Existing download queue was left unchanged.','success')}catch(e){toast(`Restore failed: ${e.message}`,'error')}finally{$('settingsRestoreInput').value=''}}
function formatNzbGroups(groups=[]){if(!groups.length)return 'No group listed';return groups.length===1?groups[0]:`${groups.length} newsgroups`}
function updateNzbSelectionSummary(){if(!state.currentNzbPreview)return;const checked=[...els.nzbImportFiles.querySelectorAll('input[type="checkbox"]:checked')];let bytes=0,segs=0;for(const c of checked){bytes+=Number(c.dataset.bytes||0);segs+=Number(c.dataset.segments||0)}els.nzbImportSelectionSummary.textContent=`${checked.length.toLocaleString()} selected • ${formatBytes(bytes)} • ${segs.toLocaleString()} segments`;els.nzbImportQueueBtn.disabled=!checked.length;}
function renderNzbPreview(d){state.currentNzbPreview=d;els.nzbCollectionName.value=d.name||'Imported NZB';els.nzbImportSummary.textContent=`${Number(d.file_count||0).toLocaleString()} files • ${formatBytes(d.total_bytes||0)} • ${Number(d.total_segments||0).toLocaleString()} segments • ${formatNzbGroups(d.groups||[])}`;els.nzbImportFiles.innerHTML=(d.files||[]).map(f=>{const blocks=Number(f.recovery_blocks||0);const role=f.role==='recovery_par2'?` • Recovery PAR2 (deferred${blocks?` • ${blocks} blocks`:''})`:f.role==='par2'?' • PAR2 index':'';return `<label class="nzb-file-row"><input type="checkbox" data-index="${Number(f.index)}" data-bytes="${Number(f.bytes||0)}" data-segments="${Number(f.segments||0)}" ${f.default_selected?'checked':''}><span class="nzb-file-main"><b title="${escapeHtml(f.filename)}">${escapeHtml(f.filename)}</b><small>${escapeHtml(f.group||'No group')} • ${Number(f.segments||0).toLocaleString()} segments${role}</small></span><span class="nzb-file-size">${formatBytes(f.bytes||0)}</span></label>`}).join('');els.nzbImportFiles.querySelectorAll('input[type="checkbox"]').forEach(c=>c.onchange=updateNzbSelectionSummary);updateNzbSelectionSummary();els.nzbImportModal.classList.remove('hidden');}
async function inspectNzbFile(file){if(!file)return;if(!state.providerId){toast('Choose a browsing/download provider first.','error');state.pendingNzbFiles=[];return}const button=els.importNzbBtn,old=button.textContent;button.disabled=true;button.textContent='Inspecting…';try{const r=await fetch('/api/nzb/inspect',{method:'POST',headers:{'Content-Type':'application/x-nzb','X-Filename':encodeURIComponent(file.name),'X-Provider-ID':encodeURIComponent(state.providerId)},body:file});let d={};try{d=await r.json()}catch{}if(!r.ok)throw new Error(d.error||`NZB inspection failed (${r.status})`);renderNzbPreview(d)}catch(e){toast(`${file.name}: ${e.message}`,'error');state.currentNzbPreview=null;state.pendingNzbFiles.shift();setTimeout(openNextNzbPreview,0)}finally{button.disabled=false;button.textContent=old}}
function startNzbImport(files){state.pendingNzbFiles=[...(files||[])].filter(f=>f&&f.name?.toLowerCase().endsWith('.nzb'));els.nzbFileInput.value='';if(!state.pendingNzbFiles.length)return;openNextNzbPreview()}
function openNextNzbPreview(){if(state.currentNzbPreview||!state.pendingNzbFiles.length)return;inspectNzbFile(state.pendingNzbFiles[0])}
function closeNzbPreview(skipCurrent=true){els.nzbImportModal.classList.add('hidden');state.currentNzbPreview=null;if(skipCurrent&&state.pendingNzbFiles.length)state.pendingNzbFiles.shift();setTimeout(openNextNzbPreview,0)}
async function queueCurrentNzb(){const d=state.currentNzbPreview;if(!d)return;const selected=[...els.nzbImportFiles.querySelectorAll('input[type="checkbox"]:checked')].map(c=>Number(c.dataset.index));if(!selected.length)return;els.nzbImportQueueBtn.disabled=true;const old=els.nzbImportQueueBtn.textContent;els.nzbImportQueueBtn.textContent='Queueing…';try{const result=await api('/api/nzb/import-selection',{provider_id:state.providerId,token:d.token,selected,collection_name:els.nzbCollectionName.value.trim()||d.name});await loadDownloads();setMainView('downloads');const skipped=Number(result.skipped?.length||0),dupes=Number(result.duplicates?.length||0);toast(`NZB queued: ${Number(result.added?.length||0)} files${skipped?` • ${skipped} skipped`:''}${dupes?` • ${dupes} duplicates`:''}.`,'success');if(result.warnings?.length)toast(result.warnings[0],'error');closeNzbPreview(true)}catch(e){toast(e.message,'error')}finally{els.nzbImportQueueBtn.disabled=false;els.nzbImportQueueBtn.textContent=old}}


function rebuildDownloadIndexes(){
  const completed=new Set(),queued=new Set();
  for(const job of state.downloadSnapshot?.jobs||[]){
    const key=downloadLookupKey(job.origin_provider_id||job.provider_id,job.group,job.filename);if(!job.filename)continue;
    if(job.status==='completed')completed.add(key);else if(['queued','downloading','retry_wait','cancelling'].includes(job.status))queued.add(key);
  }
  const signature=[...completed].sort().join('\n')+'\n--\n'+[...queued].sort().join('\n');
  const changed=signature!==state.downloadIndexSignature;state.downloadIndexSignature=signature;state.downloadedIndex=completed;state.queuedIndex=queued;return changed;
}

function updateDownloadBadgesInPlace(){
  if(!state.selectedGroup)return;
  els.articlesList.querySelectorAll('[data-download-key]').forEach(node=>{
    const key=node.dataset.downloadKey;node.classList.toggle('downloaded',state.downloadedIndex.has(key));node.classList.toggle('queued',state.queuedIndex.has(key));
    const stage=node.querySelector('.thumb-stage');if(!stage)return;
    stage.querySelectorAll('.downloaded-badge,.queued-badge').forEach(x=>x.remove());
    if(state.downloadedIndex.has(key))stage.insertAdjacentHTML('beforeend','<span class="downloaded-badge">✓ DOWNLOADED</span>');
    else if(state.queuedIndex.has(key))stage.insertAdjacentHTML('beforeend','<span class="queued-badge">⇣ QUEUED</span>');
  });
}


function showWelcomeStep(step){
  const modal=$('welcomeModal'); if(!modal)return;
  modal.classList.remove('hidden');
  $('welcomeStepIntro').classList.toggle('hidden',step!=='intro');
  $('welcomeStepFolder').classList.toggle('hidden',step!=='folder');
  $('welcomeStepReady').classList.toggle('hidden',step!=='ready');
  if($('welcomeFolderCurrent'))$('welcomeFolderCurrent').textContent=state.downloadSnapshot?.folder||'Downloads\\NewzDeck';
}
function closeWelcome(){const m=$('welcomeModal');if(m)m.classList.add('hidden')}
async function loadProviders(){
  const data=await api('/api/providers'); state.providers=data.providers; renderProviderSelect(); renderProviderList();
  const browseProviders=state.providers.filter(p=>p.enabled!==false&&p.use_browsing!==false);
  if(!state.providerId || !browseProviders.some(p=>p.id===state.providerId)){ const remembered=localStorage.getItem('providerId');state.providerId=browseProviders.some(p=>p.id===remembered)?remembered:(browseProviders[0]?.id||''); }
  els.providerSelect.value=state.providerId; updateProviderState();
  if(!state.providers.length&&els.providerModal.classList.contains('hidden')){ showWelcomeStep('intro'); }
}
function renderProviderSelect(){ const items=state.providers.filter(p=>p.enabled!==false&&p.use_browsing!==false);els.providerSelect.innerHTML=items.length?items.map(p=>`<option value="${p.id}">${escapeHtml(p.name)}${p.role&&p.role!=='primary'?` (${escapeHtml(p.role)})`:''}</option>`).join(''):'<option value="">No browsing provider</option>'; }
function activeDownloadTraffic(){
  return (state.downloadSnapshot?.jobs||[]).some(j=>['downloading','retry_wait','cancelling'].includes(String(j.status||'')));
}
function previewStartingConcurrency(connections){return connections<=2?1:connections<=5?2:connections<=10?5:connections<=20?9:connections<=40?13:connections<=60?16:20}
function previewDownloadConcurrency(connections){const reserve=connections<=2?1:Math.max(1,Math.min(4,Math.ceil(connections*.04)));return Math.max(1,reserve-(reserve>1?1:0))}
function previewIdleCeiling(connections,floor){const reserve=connections<=4?1:Math.max(2,Math.ceil(connections*.12));return Math.max(floor,Math.min(80,Math.max(1,connections-reserve)))}
function applyPreviewConcurrency(connections,value,mode){
  state.thumbConcurrency=Math.max(1,Math.min(80,Math.round(value||1)));
  state.videoThumbConcurrency=Math.max(1,Math.min(4,connections>=48?4:connections>=24?3:connections>=12?2:1,state.thumbConcurrency));
  state.setCoverConcurrency=state.groupRelatedMedia&&!state.activeMediaSetKey?Math.max(1,state.thumbConcurrency-Math.min(4,state.thumbConcurrency-1)):Math.min(6,state.thumbConcurrency);
  state.previewConcurrencyMode=mode;
}
function resetPreviewRamp(connections,downloadsBusy){
  const floor=Math.max(1,Math.min(80,previewStartingConcurrency(connections))),ceiling=previewIdleCeiling(connections,floor),step=Math.max(1,Math.min(8,Math.ceil(connections*.10))),mode=downloadsBusy?'download-reserve':'browse-adaptive';
  const current=downloadsBusy?previewDownloadConcurrency(connections):floor;
  state.previewRamp={providerId:state.providerId,connections,floor,ceiling,step,current,mode,windowStarted:performance.now(),completed:0,failed:0,lastRate:0,cooldownUntil:0};
  applyPreviewConcurrency(connections,current,mode);
}
function recordPreviewSample(elapsedMs,ok){
  const r=state.previewRamp;if(!r||r.mode!=='browse-adaptive'||activeDownloadTraffic())return;
  const now=performance.now(),priorSamples=r.completed+r.failed;if(!priorSamples)r.windowStarted=Math.max(r.windowStarted,now-Math.max(0,Number(elapsedMs)||0));
  if(ok)r.completed++;else r.failed++;
  const sampleCount=r.completed+r.failed,elapsed=Math.max(.25,(now-r.windowStarted)/1000);
  if(elapsed<1.6||sampleCount<6)return;
  const rate=r.completed/elapsed,failureRate=r.failed/Math.max(1,sampleCount),backlog=state.thumbQueue.length+state.thumbActive;let next=r.current;
  if(failureRate>=.18){next=Math.max(r.floor,r.current-r.step);r.cooldownUntil=now+5000}
  else if(now>=r.cooldownUntil&&backlog>Math.max(r.current+2,Math.ceil(r.current*1.15))&&r.current<r.ceiling){
    if(!r.lastRate||rate>=r.lastRate*.88)next=Math.min(r.ceiling,r.current+r.step);
    else if(rate<r.lastRate*.70&&r.current>r.floor){next=Math.max(r.floor,r.current-r.step);r.cooldownUntil=now+3500}
  }else if(r.lastRate&&rate<r.lastRate*.55&&r.current>r.floor&&backlog>r.floor){next=Math.max(r.floor,r.current-r.step);r.cooldownUntil=now+3500}
  r.lastRate=rate;r.windowStarted=now;r.completed=0;r.failed=0;
  if(next!==r.current){r.current=next;applyPreviewConcurrency(r.connections,next,'browse-adaptive');pumpThumbQueue()}
}
function recalculatePreviewConcurrency(){
  const p=state.providers.find(p=>p.id===state.providerId);if(!p)return;
  const connections=Math.max(1,Number(p.connections||20)),downloadsBusy=activeDownloadTraffic(),mode=downloadsBusy?'download-reserve':'browse-adaptive',r=state.previewRamp;
  if(!r||r.providerId!==state.providerId||r.connections!==connections||r.mode!==mode)resetPreviewRamp(connections,downloadsBusy);
  else if(downloadsBusy){r.current=previewDownloadConcurrency(connections);applyPreviewConcurrency(connections,r.current,mode)}
  else applyPreviewConcurrency(connections,r.current,mode);
  pumpThumbQueue();
}
function updateProviderState(){
  const p=state.providers.find(p=>p.id===state.providerId); els.providerDot.classList.toggle('online',!!p); els.groupHint.textContent=p?'Search or refresh to load newsgroups.':(state.providers.length?'Enable “Browsing & headers” on a provider to browse newsgroups.':'Add a provider to start browsing.');
  if(p){localStorage.setItem('providerId',p.id);recalculatePreviewConcurrency();}
}
function renderProviderList(){
  els.providerList.innerHTML=state.providers.map(p=>`<button class="provider-list-item ${p.id===$('providerId').value?'active':''}" data-provider-id="${p.id}"><b>${escapeHtml(p.name)} <em class="provider-role ${escapeHtml(p.role||'primary')}">${escapeHtml((p.role||'primary').toUpperCase())}</em></b><span>P${Number(p.priority||10)} • ${escapeHtml(p.host)}:${p.port} • ${p.ssl?'SSL':'Plain'} • ${p.use_recovery!==false?'Recovery on':'Recovery off'}</span></button>`).join('');
  els.providerList.querySelectorAll('[data-provider-id]').forEach(b=>b.onclick=()=>editProvider(b.dataset.providerId));
}
function openProviderModal(){ els.providerModal.classList.remove('hidden'); loadProviders().catch(e=>toast(`Could not refresh providers: ${e.message}`,'error')); }
function closeProviderModal(){ els.providerModal.classList.add('hidden'); }
function newProvider(){
  $('providerId').value='';$('providerName').value='';$('providerHost').value='';$('providerPort').value='563';$('providerSsl').checked=true;$('providerUsername').value='';$('providerPassword').value='';$('providerConnections').value='20';$('providerPipelineDepth').value='0';$('providerRole').value='primary';$('providerPriority').value='10';$('providerUseBrowsing').checked=true;$('providerUsePreviews').checked=true;$('providerUseDownloads').checked=true;$('providerUseRecovery').checked=true;$('deleteProviderBtn').classList.add('hidden');els.providerTestResult.classList.add('hidden');renderProviderList();
}
function editProvider(id){ const p=state.providers.find(x=>x.id===id);if(!p)return;$('providerId').value=p.id;$('providerName').value=p.name;$('providerHost').value=p.host;$('providerPort').value=p.port;$('providerSsl').checked=p.ssl;$('providerUsername').value=p.username;$('providerPassword').value='';$('providerConnections').value=p.connections;$('providerPipelineDepth').value=String(p.pipeline_depth||0);$('providerRole').value=p.role||'primary';$('providerPriority').value=String(p.priority||10);$('providerUseBrowsing').checked=p.use_browsing!==false;$('providerUsePreviews').checked=p.use_previews!==false;$('providerUseDownloads').checked=p.use_downloads!==false;$('providerUseRecovery').checked=p.use_recovery!==false;$('deleteProviderBtn').classList.remove('hidden');els.providerTestResult.classList.add('hidden');renderProviderList(); }
function providerFormData(){ return {id:$('providerId').value||undefined,name:$('providerName').value,host:$('providerHost').value,port:Number($('providerPort').value),ssl:$('providerSsl').checked,username:$('providerUsername').value,password:$('providerPassword').value||undefined,connections:Number($('providerConnections').value||20),pipeline_depth:Number($('providerPipelineDepth').value||0),role:$('providerRole').value,priority:Number($('providerPriority').value||10),use_browsing:$('providerUseBrowsing').checked,use_previews:$('providerUsePreviews').checked,use_downloads:$('providerUseDownloads').checked,use_recovery:$('providerUseRecovery').checked}; }

function normalizedPoster(v){return String(v||'').trim().toLocaleLowerCase()}
function isPosterBlocked(a){return state.blockedPosters.has(normalizedPoster(a?.from))}
function updateMutedPostersButton(){if(!els.mutedPostersBtn)return;const n=state.blockedPosters.size;els.mutedPostersBtn.textContent=`⊘ Muted ${n}`;els.mutedPostersBtn.classList.toggle('active',state.showBlockedPosters);els.mutedPostersBtn.disabled=n===0;els.mutedPostersBtn.title=n?`${n} muted poster${n===1?'':'s'} • ${state.showBlockedPosters?'currently visible':'currently hidden'} • click to ${state.showBlockedPosters?'hide':'show'}`:'No muted posters';}
function mutePoster(poster,force=null){const raw=String(poster||'').trim();if(!raw)return;const key=normalizedPoster(raw),add=force==null?!state.blockedPosters.has(key):!!force;if(add)state.blockedPosters.add(key);else state.blockedPosters.delete(key);updateMutedPostersButton();saveUiSettings();renderArticles();toast(add?`Muted poster: ${raw}`:`Unmuted poster: ${raw}`,'success')}
function seenKey(group,provider=state.providerId){return `${provider||''}::${group||''}`}
function readStateFor(group=state.selectedGroup,provider=state.providerId){const key=seenKey(group,provider);let rec=state.groupReadStates[key];if(!rec||typeof rec!=='object')rec={seen_through:0,seen_articles:[],unseen_articles:[],acknowledged_high:Number(state.groupSeenHigh[key]||0),updated_ts:Date.now()};rec.seen_through=Math.max(0,Number(rec.seen_through||0));rec.acknowledged_high=Math.max(0,Number(rec.acknowledged_high||state.groupSeenHigh[key]||0));if(!Array.isArray(rec.seen_articles))rec.seen_articles=[];if(!Array.isArray(rec.unseen_articles))rec.unseen_articles=[];state.groupReadStates[key]=rec;return rec}
function beginGroupVisit(group){const key=seenKey(group);const rec=readStateFor(group);state.groupVisitBaseline[key]=Number(rec.acknowledged_high||0);state.currentReadStateKey=key;state.currentSeenArticles=new Set(rec.seen_articles.map(Number).filter(Number.isFinite));state.currentUnseenArticles=new Set(rec.unseen_articles.map(Number).filter(Number.isFinite));state.articleStatusFilter='all';if(els.articleStatusFilter)els.articleStatusFilter.value='all'}
function endGroupVisit(group,provider=state.providerId){const key=seenKey(group,provider);delete state.groupVisitBaseline[key];if(state.currentReadStateKey===key){state.currentReadStateKey='';state.currentSeenArticles=new Set();state.currentUnseenArticles=new Set()}}
function trackedStatusFor(group,provider=state.providerId){return state.trackedGroupStatus[seenKey(group,provider)]||null}
function groupNewCount(g){const name=g?.name;if(!name)return 0;const high=Number(g?.high||trackedStatusFor(name)?.high||0),key=seenKey(name),existing=state.groupReadStates[key];const acknowledged=Number(existing?.acknowledged_high??state.groupSeenHigh[key]??0);return high>acknowledged&&acknowledged>0?Math.max(0,high-acknowledged):0}
function groupUnseenCount(g){const name=g?.name;if(!name)return 0;const key=seenKey(name),rec=state.groupReadStates[key];if(!rec)return 0;const status=trackedStatusFor(name)||g||{};const low=Math.max(0,Number(status.low||0)),high=Math.max(0,Number(status.high||0)),total=Math.max(0,Number(status.articles||0));if(!low||!high||!total)return name===state.selectedGroup&&state.articles.length?state.articles.filter(a=>!isArticleSeen(a)).length:0;const through=Math.max(0,Number(rec.seen_through||0));let seen=Math.max(0,Math.min(total,Math.min(high,through)-low+1));const explicit=(Array.isArray(rec.seen_articles)?rec.seen_articles:[]).map(Number).filter(n=>n>Math.max(through,low-1)&&n<=high).length;const exceptions=(Array.isArray(rec.unseen_articles)?rec.unseen_articles:[]).map(Number).filter(n=>n>=low&&n<=Math.min(high,through)).length;seen=Math.max(0,Math.min(total,seen+explicit-exceptions));return Math.max(0,total-seen)}
function groupCurrentHigh(group=state.selectedGroup){const g=state.groups.find(x=>x.name===group)||trackedStatusFor(group);return Math.max(0,Number(g?.high||state.articlePaging?.high||0))}
function markGroupSeen(group){const high=groupCurrentHigh(group);if(high>0){const rec=readStateFor(group);rec.acknowledged_high=Math.max(high,Number(rec.acknowledged_high||0));rec.updated_ts=Date.now();state.groupSeenHigh[seenKey(group)]=rec.acknowledged_high;saveUiSettings();renderGroups()}}
function articleNumber(a){return Math.max(0,Number(a?.article||0))}
function isArticleSeen(a){const n=articleNumber(a),rec=readStateFor();if(!n)return false;if(state.currentUnseenArticles.has(n))return false;return n<=Number(rec.seen_through||0)||state.currentSeenArticles.has(n)}
function isArticleNew(a){const n=articleNumber(a),baseline=Number(state.groupVisitBaseline[seenKey(state.selectedGroup)]||0);return !!(n&&baseline>0&&n>baseline)}
function articleStatusClass(a){return `${isArticleSeen(a)?'seen':'unseen'}${isArticleNew(a)?' is-new':''}`}
function articleStatusBadge(a){return isArticleNew(a)?'<span class="article-status-badge new">NEW</span>':(!isArticleSeen(a)?'<span class="article-status-badge unseen">UNSEEN</span>':'')}
function updateArticleStatusDomInPlace(a){const index=state.articles.findIndex(x=>articleKey(x)===articleKey(a));if(index<0)return;els.articlesList.querySelectorAll(`[data-index="${index}"]`).forEach(node=>{node.classList.toggle('seen',isArticleSeen(a));node.classList.toggle('unseen',!isArticleSeen(a));node.classList.toggle('is-new',isArticleNew(a));node.querySelectorAll('.article-status-badge').forEach(x=>x.remove());const stage=node.querySelector('.thumb-stage');if(stage){stage.insertAdjacentHTML('beforeend',articleStatusBadge(a))}else{const top=node.querySelector('.article-top');if(top)top.insertAdjacentHTML('beforeend',articleStatusBadge(a))}})}
function syncCurrentReadState(){const rec=readStateFor();rec.seen_articles=[...state.currentSeenArticles].filter(n=>n>Number(rec.seen_through||0)).sort((a,b)=>a-b).slice(-1500);rec.unseen_articles=[...state.currentUnseenArticles].filter(n=>n<=Number(rec.seen_through||0)).sort((a,b)=>a-b).slice(-750);rec.updated_ts=Date.now()}
function setArticlesSeen(items,seen=true,{toastResult=false}={}){if(!state.selectedGroup)return;const rec=readStateFor(),changedItems=[];for(const a of items||[]){const n=articleNumber(a);if(!n)continue;const before=isArticleSeen(a);if(seen){state.currentUnseenArticles.delete(n);if(n>Number(rec.seen_through||0))state.currentSeenArticles.add(n)}else{state.currentSeenArticles.delete(n);if(n<=Number(rec.seen_through||0))state.currentUnseenArticles.add(n)}if(before!==seen)changedItems.push(a)}if(!changedItems.length)return;syncCurrentReadState();saveUiSettings();const status=state.articleStatusFilter||'all';if(status==='seen'||status==='unseen')renderArticles({preserveScroll:true});else{for(const a of changedItems)updateArticleStatusDomInPlace(a);updateNewContentBoundaryDom();renderArticleSummary();updateSelectionBar()}renderGroups();if(toastResult)toast(`${changedItems.length} post${changedItems.length===1?'':'s'} marked ${seen?'seen':'unseen'}.`,'success')}
function markArticleSeen(a){setArticlesSeen([a],true)}
function markArticleUnseen(a){setArticlesSeen([a],false,{toastResult:true})}
function markSelectedSeen(seen=true){const items=[...state.selectedItems.values()];if(!items.length){toast('Select one or more posts first.','error');return}setArticlesSeen(items,seen,{toastResult:true})}
function markAllCurrentGroupSeen(){if(!state.selectedGroup)return;const high=groupCurrentHigh();if(!high){toast('Load the newsgroup first.','error');return}const rec=readStateFor();rec.seen_through=Math.max(Number(rec.seen_through||0),high);rec.seen_articles=[];rec.unseen_articles=[];rec.acknowledged_high=Math.max(Number(rec.acknowledged_high||0),high);rec.updated_ts=Date.now();state.currentSeenArticles=new Set();state.currentUnseenArticles=new Set();state.groupSeenHigh[seenKey(state.selectedGroup)]=rec.acknowledged_high;saveUiSettings();renderArticles({preserveScroll:true});renderGroups();toast('All current posts marked as seen.','success')}
function jumpToFirstUnseen(){if(!state.selectedGroup||!state.articles.length){toast('Load a newsgroup first.','error');return}const matches=filteredArticles({ignoreStatus:true});const target=matches.find(({a})=>!isArticleSeen(a));if(!target){toast('No unseen posts are loaded for the current filters.','success');return}if(state.articleStatusFilter==='seen'){state.articleStatusFilter='all';if(els.articleStatusFilter)els.articleStatusFilter.value='all';renderArticles({preserveScroll:true})}requestAnimationFrame(()=>{const node=els.articlesList.querySelector(`[data-index="${target.index}"]`);if(!node){state.articleStatusFilter='unseen';if(els.articleStatusFilter)els.articleStatusFilter.value='unseen';renderArticles({preserveScroll:true});requestAnimationFrame(()=>scrollUnseenNode(target.index));return}scrollUnseenNode(target.index)});captureCurrentGroupState()}
function scrollUnseenNode(index){const node=els.articlesList.querySelector(`[data-index="${index}"]`);if(!node)return;node.scrollIntoView({block:'center',behavior:'smooth'});node.classList.add('jump-highlight');setTimeout(()=>node.classList.remove('jump-highlight'),1400)}
function mergeTrackedGroupStatus(groups=[]){for(const g of groups){if(!g?.name)continue;state.trackedGroupStatus[seenKey(g.name)]=g;const existing=state.groups.find(x=>x.name===g.name);if(existing)Object.assign(existing,g)}renderGroups()}
async function refreshTrackedGroupStatus({quiet=true}={}){if(!state.providerId||activeDownloadTraffic())return;const names=[...new Set([...state.favorites,...currentProviderRecentNames(),...(state.selectedGroup?[state.selectedGroup]:[])])].filter(Boolean).slice(0,50);if(!names.length)return;try{const data=await api('/api/groups/status',{provider_id:state.providerId,groups:names});mergeTrackedGroupStatus(data.groups||[])}catch(e){if(!quiet)toast(e.message,'error')}}
function startTrackedGroupRefresh(){if(state.groupStatusRefreshTimer)clearInterval(state.groupStatusRefreshTimer);state.groupStatusRefreshTimer=setInterval(()=>refreshTrackedGroupStatus({quiet:true}),180000);setTimeout(()=>refreshTrackedGroupStatus({quiet:true}),3500)}
function newBrowserTab(group,provider=state.providerId){return{id:`tab_${Date.now().toString(36)}_${Math.random().toString(36).slice(2,7)}`,provider_id:provider,group,title:group}}
function ensureBrowserTab(group,{newTab=false,tabId=''}={}){if(!group)return null;let tab=tabId?state.browserTabs.find(t=>t.id===tabId):null;if(!tab&&!newTab)tab=state.browserTabs.find(t=>t.provider_id===state.providerId&&t.group===group);if(!tab){tab=newBrowserTab(group);state.browserTabs.push(tab);if(state.browserTabs.length>12)state.browserTabs.splice(0,state.browserTabs.length-12)}state.activeBrowserTabId=tab.id;renderBrowserTabs();saveUiSettings();return tab}
function renderBrowserTabs(){if(!els.browserTabs)return;const tabs=state.browserTabs.filter(t=>t&&t.group);const add='<button id="newTabHint" class="browser-tab-new" type="button" title="Duplicate current group in a new tab">＋</button>';els.browserTabs.innerHTML=tabs.map(t=>`<div class="browser-tab ${t.id===state.activeBrowserTabId?'active':''}" data-tab-id="${escapeHtml(t.id)}" role="tab" aria-selected="${t.id===state.activeBrowserTabId?'true':'false'}"><button class="browser-tab-main" type="button" title="${escapeHtml(t.group)}"><span class="browser-tab-dot"></span><span>${escapeHtml(t.title||t.group)}</span></button><button class="browser-tab-close" type="button" title="Close tab">×</button></div>`).join('')+add;els.browserTabs.querySelectorAll('.browser-tab').forEach(node=>{node.querySelector('.browser-tab-main').onclick=()=>activateBrowserTab(node.dataset.tabId);node.querySelector('.browser-tab-close').onclick=e=>{e.stopPropagation();closeBrowserTab(node.dataset.tabId)}});$('newTabHint')?.addEventListener('click',()=>{if(state.selectedGroup)openGroupInNewTab(state.selectedGroup)})}
async function activateBrowserTab(id){const tab=state.browserTabs.find(t=>t.id===id);if(!tab)return;captureCurrentGroupState();state.activeBrowserTabId=id;if(tab.provider_id&&tab.provider_id!==state.providerId&&state.providers.some(p=>p.id===tab.provider_id)){state.providerId=tab.provider_id;els.providerSelect.value=tab.provider_id;updateProviderState();state.groups=[];state.groupsTotal=0;await loadGroups()}renderBrowserTabs();await selectGroup(tab.group,{tabId:id,fromTab:true})}
async function openGroupInNewTab(group){const tab=ensureBrowserTab(group,{newTab:true});await selectGroup(group,{tabId:tab.id,fromTab:true})}
async function closeBrowserTab(id){const i=state.browserTabs.findIndex(t=>t.id===id);if(i<0)return;const was=id===state.activeBrowserTabId;state.browserTabs.splice(i,1);if(was){const next=state.browserTabs[Math.min(i,state.browserTabs.length-1)]||null;state.activeBrowserTabId=next?.id||'';renderBrowserTabs();saveUiSettings();if(next){await activateBrowserTab(next.id);return}captureCurrentGroupState();state.selectedGroup='';state.articles=[];state.articlePaging=null;state.selectedArticleKey='';els.articleTitle.textContent='Articles';els.articleEyebrow.textContent='NO GROUP SELECTED';els.entireGroupSearchBtn.disabled=true;renderArticles();resetPreview()}renderBrowserTabs();saveUiSettings()}
function groupStateKey(group=state.selectedGroup,provider=state.providerId){return `${provider||''}::${group||''}`}
function currentProviderRecentNames(){const prefix=`${state.providerId}::`;return state.recentGroups.filter(x=>String(x).startsWith(prefix)).map(x=>String(x).slice(prefix.length)).filter(Boolean)}
function normalizeBookmarkFolders(raw){const out=[],seen=new Set();for(const item of Array.isArray(raw)?raw:[]){if(!item||typeof item!=='object')continue;const name=String(item.name||'').trim().slice(0,80);if(!name)continue;let id=String(item.id||'').replace(/[^A-Za-z0-9_-]+/g,'-').slice(0,80);if(!id||seen.has(id))id=`folder-${Date.now().toString(36)}-${out.length+1}`;seen.add(id);const groups=[...new Set((Array.isArray(item.groups)?item.groups:[]).map(x=>String(x||'').trim()).filter(Boolean))].slice(0,500);out.push({id,name,groups,collapsed:!!item.collapsed});if(out.length>=50)break}return out}
function bookmarkFolderFor(group){return state.bookmarkFolders.find(f=>(f.groups||[]).includes(group))||null}
function bookmarkUnfiledNames(){const filed=new Set(state.bookmarkFolders.flatMap(f=>f.groups||[]));return [...state.favorites].filter(g=>!filed.has(g)).sort((a,b)=>a.localeCompare(b))}
function updateFavoriteUi(){if(els.favoriteCount)els.favoriteCount.textContent=String(state.favorites.size);const recentCount=currentProviderRecentNames().length;if(els.recentCount)els.recentCount.textContent=String(recentCount);if(els.groupAllBtn)els.groupAllBtn.classList.toggle('active',state.groupMode==='all');if(els.groupFavoritesBtn)els.groupFavoritesBtn.classList.toggle('active',state.groupMode==='favorites');if(els.groupRecentBtn)els.groupRecentBtn.classList.toggle('active',state.groupMode==='recent');if(els.bookmarkTools)els.bookmarkTools.classList.toggle('hidden',state.groupMode!=='favorites');if(els.recentTools)els.recentTools.classList.toggle('hidden',state.groupMode!=='recent');if(els.clearRecentBtn)els.clearRecentBtn.disabled=recentCount===0;}
function toggleFavorite(group,force=null){if(!group)return;const add=force==null?!state.favorites.has(group):!!force;if(add)state.favorites.add(group);else{state.favorites.delete(group);for(const f of state.bookmarkFolders)f.groups=(f.groups||[]).filter(g=>g!==group)}saveUiSettings();updateFavoriteUi();renderGroups();toast(add?`Bookmarked ${group}.`:`Removed bookmark for ${group}.`,'success');}
function favoriteGroupObjects(){const map=new Map(state.groups.map(g=>[g.name,g]));return [...state.favorites].sort((a,b)=>a.localeCompare(b)).map(name=>map.get(name)||{name,articles:0,favorite_only:true});}
function removeRecentGroup(group){if(!group||!state.providerId)return;const token=groupStateKey(group);const before=state.recentGroups.length;state.recentGroups=state.recentGroups.filter(x=>x!==token);if(state.recentGroups.length===before)return;saveUiSettings();renderGroups();toast(`Removed ${group} from Recent.`,'success')}
function clearCurrentProviderRecentGroups(){if(!state.providerId)return;const names=currentProviderRecentNames();if(!names.length)return;if(!confirm(`Clear all ${names.length} recent newsgroup${names.length===1?'':'s'} for this provider?\n\nBookmarks, open tabs, and saved browsing state will not be changed.`))return;const prefix=`${state.providerId}::`;state.recentGroups=state.recentGroups.filter(x=>!String(x).startsWith(prefix));saveUiSettings();renderGroups();toast('Recent newsgroups cleared.','success')}
function createBookmarkFolder(){const raw=prompt('Folder name:','');if(raw==null)return;const name=String(raw).trim().slice(0,80);if(!name)return;if(state.bookmarkFolders.some(f=>f.name.toLocaleLowerCase()===name.toLocaleLowerCase())){toast('A bookmark folder with that name already exists.','error');return}state.bookmarkFolders.push({id:`folder-${Date.now().toString(36)}-${Math.random().toString(36).slice(2,7)}`,name,groups:[],collapsed:false});saveUiSettings();renderGroups();toast(`Created bookmark folder “${name}”.`,'success')}
function renameBookmarkFolder(id){const f=state.bookmarkFolders.find(x=>x.id===id);if(!f)return;const raw=prompt('Rename bookmark folder:',f.name);if(raw==null)return;const name=String(raw).trim().slice(0,80);if(!name)return;if(state.bookmarkFolders.some(x=>x.id!==id&&x.name.toLocaleLowerCase()===name.toLocaleLowerCase())){toast('A bookmark folder with that name already exists.','error');return}f.name=name;saveUiSettings();renderGroups()}
function deleteBookmarkFolder(id){const f=state.bookmarkFolders.find(x=>x.id===id);if(!f)return;if(!confirm(`Delete the folder “${f.name}”?\n\nIts ${Number((f.groups||[]).length)} bookmark(s) will be kept and moved to Unfiled.`))return;state.bookmarkFolders=state.bookmarkFolders.filter(x=>x.id!==id);saveUiSettings();renderGroups();toast(`Deleted “${f.name}”. Bookmarks were moved to Unfiled.`,'success')}
function moveBookmarkToFolder(group,folderId=''){if(!group)return;state.favorites.add(group);for(const f of state.bookmarkFolders)f.groups=(f.groups||[]).filter(g=>g!==group);const target=state.bookmarkFolders.find(f=>f.id===folderId);if(target){target.groups=[...(target.groups||[]),group].filter((x,i,a)=>a.indexOf(x)===i);toast(`Moved ${group} to ${target.name}.`,'success')}else toast(`Moved ${group} to Unfiled.`,'success');saveUiSettings();renderGroups()}
function showBookmarkFolderChooser(x,y,group){const current=bookmarkFolderFor(group);const items=[{label:`${current?'':'✓ '}Unfiled`,action:()=>moveBookmarkToFolder(group,'')}];for(const f of state.bookmarkFolders)items.push({label:`${current?.id===f.id?'✓ ':''}${f.name}`,action:()=>moveBookmarkToFolder(group,f.id)});if(!state.bookmarkFolders.length)items.push({separator:true},{label:'＋ Create folder…',action:()=>{createBookmarkFolder();if(state.bookmarkFolders.length)moveBookmarkToFolder(group,state.bookmarkFolders[state.bookmarkFolders.length-1].id)}});showContextMenu(x,y,items)}
function bookmarkGroupObject(name){const g=state.groups.find(x=>x.name===name)||trackedStatusFor(name);return g||{name,articles:0,favorite_only:true}}
function groupRowMarkup(g,{bookmarkTree=false,recentHistory=false}={}){const fresh=groupNewCount(g),showUnseen=bookmarkTree||recentHistory,unseen=showUnseen?groupUnseenCount(g):0;return `<div class="group-row-wrap ${g.name===state.selectedGroup?'active':''}" data-group="${escapeHtml(g.name)}" ${bookmarkTree?'draggable="true"':''}><button class="group-row ${g.name===state.selectedGroup?'active':''}" data-group="${escapeHtml(g.name)}"><span class="group-name">${escapeHtml(g.name)}</span><span class="group-status-counts">${fresh?`<span class="group-new-count">+${formatCount(fresh)} new</span>`:''}${unseen?`<span class="group-unseen-count">${formatCount(unseen)} unseen</span>`:''}</span><span class="group-count">${g.favorite_only||g.recent_only?'':formatCount(g.articles)}</span></button><button class="favorite-star ${state.favorites.has(g.name)?'active':''}" type="button" title="${state.favorites.has(g.name)?'Remove bookmark':'Bookmark newsgroup'}">${state.favorites.has(g.name)?'★':'☆'}</button>${recentHistory?'<button class="recent-remove" type="button" title="Remove from Recent" aria-label="Remove from Recent">×</button>':''}</div>`}
function bindGroupRows(){els.groupsList.querySelectorAll('.group-row').forEach(row=>row.onclick=()=>selectGroup(row.dataset.group));els.groupsList.querySelectorAll('.favorite-star').forEach(btn=>btn.onclick=e=>{e.stopPropagation();toggleFavorite(btn.closest('.group-row-wrap').dataset.group)});els.groupsList.querySelectorAll('.recent-remove').forEach(btn=>btn.onclick=e=>{e.stopPropagation();removeRecentGroup(btn.closest('.group-row-wrap').dataset.group)});els.groupsList.querySelectorAll('.group-row-wrap').forEach(row=>{row.addEventListener('contextmenu',e=>{e.preventDefault();const group=row.dataset.group,bookmarked=state.favorites.has(group);const items=[{label:group===state.selectedGroup?'Refresh group':'Open newsgroup',action:()=>selectGroup(group)},{label:'Open in new tab',action:()=>openGroupInNewTab(group)},{separator:true},{label:bookmarked?'Remove bookmark':'Bookmark newsgroup',action:()=>toggleFavorite(group)}];if(bookmarked)items.push({label:'Move bookmark to folder…',action:()=>showBookmarkFolderChooser(e.clientX,e.clientY,group)});if(state.groupMode==='recent')items.push({separator:true},{label:'Remove from Recent',action:()=>removeRecentGroup(group)});items.push({separator:true},{label:'Mark all current posts seen',action:async()=>{if(state.selectedGroup!==group)await selectGroup(group);markAllCurrentGroupSeen()}},{separator:true},{label:'Search entire newsgroup',action:async()=>{if(state.selectedGroup!==group)await selectGroup(group);openEntireGroupSearch()}},{label:'Copy group name',action:()=>copyText(group)});showContextMenu(e.clientX,e.clientY,items)});if(row.draggable){row.addEventListener('dragstart',e=>{e.dataTransfer.setData('text/newzdeck-bookmark',row.dataset.group);e.dataTransfer.effectAllowed='move';row.classList.add('dragging')});row.addEventListener('dragend',()=>row.classList.remove('dragging'))}})}
function renderBookmarkTree(){const folders=state.bookmarkFolders,unfiled=bookmarkUnfiledNames();if(!folders.length&&!state.favorites.size){els.groupsList.innerHTML='<div class="empty-state"><h3>No bookmarks yet</h3><p>Click the ☆ beside a newsgroup to bookmark it, then create folders to organize your bookmarks.</p></div>';return}const sections=[];for(const f of folders){const names=(f.groups||[]).filter(g=>state.favorites.has(g)).sort((a,b)=>a.localeCompare(b));sections.push(`<section class="bookmark-folder-section ${f.collapsed?'collapsed':''}" data-folder-id="${escapeHtml(f.id)}"><div class="bookmark-folder-head" data-folder-id="${escapeHtml(f.id)}"><button class="bookmark-folder-toggle" type="button" title="${f.collapsed?'Expand folder':'Collapse folder'}">${f.collapsed?'▸':'▾'}</button><span class="bookmark-folder-icon">▰</span><b>${escapeHtml(f.name)}</b><span class="bookmark-folder-count">${names.length}</span><button class="bookmark-folder-menu" type="button" title="Folder options">•••</button></div><div class="bookmark-folder-items">${names.length?names.map(n=>groupRowMarkup(bookmarkGroupObject(n),{bookmarkTree:true})).join(''):'<div class="bookmark-folder-empty">Drag bookmarks here</div>'}</div></section>`)}if(unfiled.length||!folders.length)sections.push(`<section class="bookmark-folder-section unfiled" data-folder-id=""><div class="bookmark-folder-head" data-folder-id=""><span class="bookmark-folder-toggle placeholder">•</span><span class="bookmark-folder-icon">☆</span><b>Unfiled</b><span class="bookmark-folder-count">${unfiled.length}</span></div><div class="bookmark-folder-items">${unfiled.length?unfiled.map(n=>groupRowMarkup(bookmarkGroupObject(n),{bookmarkTree:true})).join(''):'<div class="bookmark-folder-empty">Bookmarks not assigned to a folder appear here</div>'}</div></section>`);els.groupsList.innerHTML=sections.join('');bindGroupRows();els.groupsList.querySelectorAll('.bookmark-folder-head').forEach(head=>{head.addEventListener('dragover',e=>{if(e.dataTransfer.types.includes('text/newzdeck-bookmark')){e.preventDefault();e.dataTransfer.dropEffect='move';head.classList.add('drop-target')}});head.addEventListener('dragleave',()=>head.classList.remove('drop-target'));head.addEventListener('drop',e=>{e.preventDefault();head.classList.remove('drop-target');const group=e.dataTransfer.getData('text/newzdeck-bookmark');if(group)moveBookmarkToFolder(group,head.dataset.folderId||'')})});els.groupsList.querySelectorAll('.bookmark-folder-toggle:not(.placeholder)').forEach(btn=>btn.onclick=()=>{const sec=btn.closest('.bookmark-folder-section'),f=state.bookmarkFolders.find(x=>x.id===sec.dataset.folderId);if(!f)return;f.collapsed=!f.collapsed;saveUiSettings();renderGroups()});els.groupsList.querySelectorAll('.bookmark-folder-menu').forEach(btn=>btn.onclick=e=>{e.stopPropagation();const id=btn.closest('.bookmark-folder-section').dataset.folderId;showContextMenu(e.clientX,e.clientY,[{label:'Rename folder',action:()=>renameBookmarkFolder(id)},{label:'Delete folder',action:()=>deleteBookmarkFolder(id)}])})}
function recentGroupObjects(){const map=new Map(state.groups.map(g=>[g.name,g]));return currentProviderRecentNames().map(name=>map.get(name)||trackedStatusFor(name)||{name,articles:0,recent_only:true});}
function markRecentGroup(group){if(!group||!state.providerId)return;const token=groupStateKey(group);state.recentGroups=[token,...state.recentGroups.filter(x=>x!==token)].slice(0,20);saveUiSettings();}
function captureCurrentGroupState(){if(!state.selectedGroup)return;const key=groupStateKey();const persisted={content_filter:els.contentFilter?.value||'images',status_filter:state.articleStatusFilter||'all',article_sort:els.articleSort?.value||'newest',binary_package_filter:state.binaryPackageFilter||'downloadable',binary_package_sort:state.binaryPackageSort||'newest',thumbnail_size:state.thumbnailSize,view_mode:state.viewMode,article_limit:Number(els.articleLimit?.value||300),continuous_browse:state.continuousMode,recent_searches:(state.articleSearchHistory||[]).slice(0,8),updated_ts:Date.now()};state.groupStates[key]=persisted;state.groupSessions.delete(key);const entries=Object.entries(state.groupStates).sort((a,b)=>Number(b[1]?.updated_ts||0)-Number(a[1]?.updated_ts||0)).slice(0,100);state.groupStates=Object.fromEntries(entries);saveUiSettings();}
function applyStoredGroupControls(stored={}){const recentSearches=stored.recent_searches||stored.recentSearches;state.articleSearchHistory=Array.isArray(recentSearches)?recentSearches.map(x=>String(x||'').trim()).filter(Boolean).slice(0,8):[];renderArticleSearchHistory();const filter=stored.content_filter||stored.contentFilter;if(els.contentFilter&&['images','videos','media','all'].includes(filter))els.contentFilter.value=filter;const status=stored.status_filter||stored.statusFilter||'all';state.articleStatusFilter=['all','new','unseen','seen'].includes(status)?status:'all';if(els.articleStatusFilter)els.articleStatusFilter.value=state.articleStatusFilter;const sort=stored.article_sort||stored.articleSort;if(els.articleSort&&sort)els.articleSort.value=sort;const binaryFilter=stored.binary_package_filter||stored.binaryPackageFilter||'downloadable';state.binaryPackageFilter=['downloadable','all','incomplete'].includes(binaryFilter)?binaryFilter:'downloadable';const binarySort=stored.binary_package_sort||stored.binaryPackageSort||'newest';state.binaryPackageSort=['newest','oldest','largest','smallest','name','files','health'].includes(binarySort)?binarySort:'newest';const limit=stored.article_limit||stored.articleLimit;if(els.articleLimit&&limit){const v=String(limit);if([...els.articleLimit.options].some(o=>o.value===v))els.articleLimit.value=v}state.thumbnailSize=['small','medium','large','xlarge'].includes(stored.thumbnail_size||stored.thumbnailSize)?(stored.thumbnail_size||stored.thumbnailSize):state.thumbnailSize;state.viewMode=(stored.view_mode||stored.viewMode)==='list'?'list':'gallery';state.continuousMode=(stored.continuous_browse??stored.continuousMode)===false?false:true;applyThumbnailSize();updateContinuousButton();}

async function loadGroups({refresh=false,append=false}={}){
  if(!state.providerId){openProviderModal();return}
  const offset=append?state.groups.length:0; setGroupLoading(true,append);
  try{
    const data=await api('/api/groups',{provider_id:state.providerId,query:els.groupSearch.value.trim(),sort:els.groupSort.value,offset,page_size:state.groupPageSize,refresh});
    state.groups=append?[...state.groups,...data.groups]:data.groups;state.groupsTotal=data.total;renderGroups();
    const source=data.cache_source==='disk'?'disk cache':data.cache_source==='memory'?'memory cache':'provider';
    els.groupHint.textContent=`Showing ${state.groups.length.toLocaleString()} of ${data.total.toLocaleString()} groups • ${data.elapsed_ms} ms • ${source}`;
    els.groupsMoreWrap.classList.toggle('hidden',!data.has_more);
    if(data.has_more) els.loadMoreGroupsBtn.textContent=`Load more groups (${(data.total-state.groups.length).toLocaleString()} remaining)`;
  }catch(e){ toast(e.message,'error');els.groupHint.textContent='Could not load groups.';if(!append){state.groups=[];state.groupsTotal=0;renderGroups();} }
  finally{setGroupLoading(false,append)}
}
function setGroupLoading(on,append=false){
  $('refreshGroupsBtn').disabled=on;$('groupSearchBtn').disabled=on;els.groupSort.disabled=on;els.loadMoreGroupsBtn.disabled=on;
  if(on&&!append){els.groupsList.innerHTML='<div class="loading-line"></div>'.repeat(7);els.groupsMoreWrap.classList.add('hidden')}
  if(!on) els.loadMoreGroupsBtn.disabled=false;
}
function renderGroups(){
  updateFavoriteUi();els.groupsMoreWrap.classList.toggle('hidden',state.groupMode!=='all'||state.groups.length>=state.groupsTotal);
  if(state.groupMode==='favorites'){renderBookmarkTree();return}
  const list=state.groupMode==='recent'?recentGroupObjects():state.groups;if(!list.length){els.groupsList.innerHTML=state.groupMode==='recent'?'<div class="empty-state"><h3>No recently viewed groups</h3><p>Groups you open will appear here automatically.</p></div>':'<div class="empty-state"><h3>No groups found</h3><p>Try another search term or refresh the provider.</p></div>';return}
  els.groupsList.innerHTML=list.map(g=>groupRowMarkup(g,{recentHistory:state.groupMode==='recent'})).join('');bindGroupRows();
}
async function selectGroup(group,opts={}){if(!group)return;if(state.browseAbortController)state.browseAbortController.abort();const previousGroup=state.selectedGroup,previousProvider=state.providerId;const tab=ensureBrowserTab(group,{newTab:false,tabId:opts.tabId||''});if(tab)state.activeBrowserTabId=tab.id;if(group===state.selectedGroup&&state.articles.length&&!opts.fromTab){state.loadedPages.clear();state.articlePage=1;state.articlePaging=null;state.galleryGeneration++;state.thumbQueue=[];state.thumbQueued.clear();els.articlesList.scrollTop=0;await loadArticles({page:1,append:false,refresh:true});return}captureCurrentGroupState();if(previousGroup&&previousGroup!==group)endGroupVisit(previousGroup,previousProvider);if(state.groupSearchJob&&['queued','scanning','cancelling'].includes(state.groupSearchJob.status)&&state.groupSearchJob.group!==group){api('/api/group-search/cancel',{id:state.groupSearchJob.id}).catch(()=>{});}if(state.groupSearchPollTimer){clearInterval(state.groupSearchPollTimer);state.groupSearchPollTimer=null}closeMediaViewer();state.selectedGroup=group;state.nameResolutionAttempted.clear();state.nameResolutionAutoRemaining=24;clearTimeout(state.nameResolutionTimer);state.nameResolutionTimer=null;beginGroupVisit(group);markRecentGroup(group);renderBrowserTabs();state.selectedItems.clear();state.selectionAnchorKey='';state.articleSearchTerm='';state.activeMediaSetKey='';state.searchMode=false;state.groupSearchJob=null;state.continuousLoading=false;els.articleSearch.value='';state.galleryGeneration++;state.thumbQueue=[];state.thumbQueued.clear();renderGroups();updateSelectionBar();updateArticleSearchUi();els.entireGroupSearchBtn.disabled=false;els.articleTitle.textContent=group;els.articleEyebrow.textContent='VISUAL NEWSGROUP BROWSER';resetPreview();const key=groupStateKey(group),persisted=state.groupStates[key]||{};applyStoredGroupControls(persisted);state.groupSessions.delete(key);state.articles=[];state.selectedArticleKey='';state.articlePage=1;state.articlePaging=null;state.loadedPages.clear();state.browseScrollTop=0;state.browsePageBeforeSearch=1;els.articlesList.scrollTop=0;await loadArticles({page:1,append:false,refresh:true});requestAnimationFrame(()=>{els.articlesList.scrollTop=0;markGroupSeen(group)});}

function mergeArticlePages(existing,incoming){
  const map=new Map(existing.map(a=>[articleKey(a),a]));for(const a of incoming||[])map.set(articleKey(a),a);return [...map.values()];
}
function renderArticleSummary(elapsedMs=0){
  if(state.searchMode){renderSearchModeSummary();return}
  const images=state.articles.filter(a=>a.media?.kind==='image').length;
  const videos=state.articles.filter(a=>a.media?.kind==='video').length;
  const previewable=state.articles.filter(a=>a.media&&a.complete).length;const unseen=state.articles.filter(a=>!isArticleSeen(a)).length;const fresh=state.articles.filter(isArticleNew).length;
  const pages=[...state.loadedPages].sort((a,b)=>a-b),smart=!!state.articlePaging?.smart_binary_scan;const pageText=pages.length>1?`<span><b>Header pages ${pages[0].toLocaleString()}–${pages[pages.length-1].toLocaleString()}</b> ${smart?'scanned':'loaded'}</span>`:(pages.length?`<span><b>Page ${pages[0].toLocaleString()}</b></span>`:'');
  const depth=daysBackFromLoaded(),itemWord=isAllPostsMode()?'binary items':'posts';const depthText=state.articles.length?`<span class="browse-depth"><b>${state.articles.length.toLocaleString()}</b> ${itemWord} loaded • ${depth?`${depth.toLocaleString()} day${depth===1?'':'s'} back`:'latest'}</span>`:'';
  const retained=state.articlePaging?Math.max(0,Number(state.articlePaging.high||0)-Number(state.articlePaging.low||0)+1):0;
  els.articleSummary.classList.remove('hidden');els.articlesList.classList.add('has-summary');
  els.articleSummary.innerHTML=`<span><b>${images.toLocaleString()}</b> images</span><span><b>${videos.toLocaleString()}</b> videos</span><span><b>${unseen.toLocaleString()}</b> unseen</span>${fresh?`<span class="new-summary"><b>${fresh.toLocaleString()}</b> new this visit</span>`:''}<span><b>${previewable.toLocaleString()}</b> previewable</span>${pageText}${depthText}${retained?`<span><b>${formatCount(retained)}</b> retained range</span>`:''}${elapsedMs?`<span>${elapsedMs} ms</span>`:''}`;
}
function clearPreviewUnavailableForGroup(group){
  const prefix=`${state.providerId}|${group}|`;
  for(const key of [...state.unpreviewableMediaKeys]){if(key.startsWith(prefix))state.unpreviewableMediaKeys.delete(key)}
  for(const [key,failure] of [...state.thumbFailureCache]){if(key.startsWith(prefix)&&!state.unsupportedMediaKeys.has(key))state.thumbFailureCache.delete(key)}
}
function canIncrementallyAppendContinuous(previousKeys,incoming){
  if(!state.continuousMode||state.searchMode||state.viewMode!=='gallery'||state.groupRelatedMedia||state.activeMediaSetKey)return false;
  if((els.articleSort?.value||'newest')!=='newest')return false;
  if(!els.articlesList?.querySelector('.media-grid')||els.articlesList.classList.contains('empty-state'))return false;
  return !(incoming||[]).some(a=>previousKeys.has(articleKey(a)));
}
function appendContinuousGallery(previousKeys){
  const grid=els.articlesList?.querySelector('.media-grid');if(!grid)return false;
  const additions=filteredArticles().filter(({a})=>!previousKeys.has(articleKey(a)));
  if(additions.length){
    const template=document.createElement('template');template.innerHTML=additions.map(({a,index})=>galleryCard(a,index)).join('');const added=[...template.content.children];
    const sentinel=$('continuousSentinel');if(sentinel&&sentinel.parentElement===grid)grid.insertBefore(template.content,sentinel);else grid.appendChild(template.content);
    for(const card of added){rebuildThumbnailHolderRegistry(card,{clear:false});wireGalleryCards(card);wireThumbnailImages(card);observeThumbnails({reuse:true,root:card})}
    updateNewContentBoundaryDom();scheduleBrowsingMemoryTrim();
  }
  updateArticleSearchUi(filteredArticles().length);updateSelectionBar();return true;
}
function articlePageRequest(page,{refresh=false,progressive=false}={}){return browsePayload({provider_id:state.providerId,group:state.selectedGroup,limit:Number(els.articleLimit.value),page,media_only:false,smart_binaries:isAllPostsMode(),progressive,refresh})}
function headerPrefetchMatches(page){const p=state.headerPrefetch;return !!(p&&p.page===page&&p.group===state.selectedGroup&&p.provider===state.providerId&&p.session===state.browseSessionToken)}
async function warmPrefetchedPageThumbnails(data,page,group,provider,session){
  if(!data?.articles?.length||group!==state.selectedGroup||provider!==state.providerId||session!==state.browseSessionToken||activeDownloadTraffic())return;
  // Lowest-priority speculation: warm only a handful of the next page's first
  // complete images, sequentially, and stop the instant foreground demand returns.
  const candidates=data.articles.filter(a=>a?.media?.kind==='image'&&a.complete&&!a.small_image_suppressed&&!a.cached_thumbnail_url).slice(0,4);
  if(!candidates.length)return;
  await new Promise(r=>setTimeout(r,350));
  for(const a of candidates){
    if(group!==state.selectedGroup||provider!==state.providerId||session!==state.browseSessionToken||activeDownloadTraffic()||state.thumbActive>0||state.thumbQueue.length){state.speculativeThumbStats.cancelled++;break}
    state.speculativeThumbStats.started++;
    try{
      const result=await api('/api/thumbnail/image',browsePayload({provider_id:provider,group:articleGroup(a),segments:segmentPayload(a),media:a.media,thumbnail_lanes:1}),browseRequestOptions());
      if(result?.suppressed_small){a.small_image_suppressed=true;a.media_meta={...(a.media_meta||{}),width:Number(result.width||0),height:Number(result.height||0)}}
      else if(result?.thumbnail_url){a.cached_thumbnail_token=result.thumbnail_token||'';a.cached_thumbnail_url=result.thumbnail_url}
      state.speculativeThumbStats.completed++;
    }catch(e){if(e?.code==='browse-cancelled')break}
  }
}
function prefetchOlderArticles(){
  if(continuousJumpHeld()||!state.selectedGroup||state.searchMode||!state.continuousMode||state.continuousLoading||state.smartBinaryPending||!state.articlePaging?.has_older)return;
  const page=Number(state.articlePaging?.next_older_page||state.articlePage+1);if(!page||headerPrefetchMatches(page))return;
  const group=state.selectedGroup,provider=state.providerId,session=state.browseSessionToken;
  const promise=api('/api/articles',articlePageRequest(page,{progressive:false}),browseRequestOptions()).then(data=>{warmPrefetchedPageThumbnails(data,page,group,provider,session);return data}).catch(e=>{if(e?.code!=='browse-cancelled')console.warn('Header prefetch failed',e);throw e});
  state.headerPrefetch={page,group,provider,session,promise,started:performance.now()};
}
function schedulePredictiveHeaderPrefetch(){
  if(continuousJumpHeld()||!els.articlesList||!state.selectedGroup||state.browseScrollDirection<0)return;
  const el=els.articlesList,remaining=Math.max(0,el.scrollHeight-(el.scrollTop+el.clientHeight)),velocity=Math.abs(Number(state.browseScrollVelocity||0));
  const lead=Math.max(4200,el.clientHeight*(3.5+Math.min(4,velocity*2.2)));if(remaining<=lead)prefetchOlderArticles();
}
function scheduleProgressiveBinaryCompletion(page,generation,attempt=0){
  if(state.progressiveBinaryTimer)clearTimeout(state.progressiveBinaryTimer);const group=state.selectedGroup,provider=state.providerId,session=state.browseSessionToken;
  state.progressiveBinaryTimer=setTimeout(async()=>{
    state.progressiveBinaryTimer=null;if(generation!==state.galleryGeneration||group!==state.selectedGroup||provider!==state.providerId||session!==state.browseSessionToken)return;
    try{const data=await api('/api/articles',articlePageRequest(page,{progressive:true}),browseRequestOptions());
      if(generation!==state.galleryGeneration||group!==state.selectedGroup||provider!==state.providerId||session!==state.browseSessionToken)return;
      if(data.smart_binary_pending&&attempt<12){scheduleProgressiveBinaryCompletion(page,generation,attempt+1);return}
      state.smartBinaryPending=false;if(data.smart_binary_pending)return;
      if(state.loadedPages.size!==1||state.articlePage!==page)return;
      const anchors=captureBrowseAnchors(),scroll=els.articlesList.scrollTop;state.articles=data.articles||[];state.articlePaging=data.paging||state.articlePaging;state.smartBinaryHeaders=Number(data.smart_binary_headers||state.smartBinaryHeaders||0);sortArticles(false);renderArticles({preserveScroll:true,scrollTop:scroll,anchor:anchors});updateArticlePaging();renderArticleSummary(data.elapsed_ms||0);updateContinuousSentinelInPlace();schedulePredictiveHeaderPrefetch();
    }catch(e){if(e?.code!=='browse-cancelled'){state.smartBinaryPending=false;updateContinuousSentinelInPlace()}}
  },Math.min(900,220+attempt*70));
}
async function loadArticles({page=null,append=false,refresh=false,pageJump=false}={}){
  if(!state.selectedGroup)return;
  if(refresh)clearPreviewUnavailableForGroup(state.selectedGroup);
  const targetPage=Math.max(1,Number(page??state.articlePage??1)||1);
  if(append&&state.continuousLoading)return;
  let generation=state.galleryGeneration;
  if(!append){
    generation=++state.galleryGeneration;state.thumbQueue=[];state.thumbQueued.clear();
    if(pageJump){state.headerPrefetch=null;armContinuousAfterJump(30000);if(els.articlesList)els.articlesList.scrollTop=0;state.browseScrollTop=0;state.lastBrowseScrollTop=0;state.browseScrollVelocity=0;state.browseScrollDirection=1;}
    await beginBrowseSession(state.selectedGroup)
  }
  if(append)state.continuousLoading=true;
  setArticleLoading(true,append);
  if(pageJump&&els.articlesList)els.articlesList.scrollTop=0;
  try{
    let data;if(append&&headerPrefetchMatches(targetPage)){const prefetched=state.headerPrefetch;state.headerPrefetch=null;data=await prefetched.promise}else data=await api('/api/articles',articlePageRequest(targetPage,{refresh,progressive:!append&&isAllPostsMode()}),browseRequestOptions());
    if(generation!==state.galleryGeneration)return;
    const incoming=data.articles||[];hydrateServerThumbnailHints(incoming);state.smartBinaryHeaders=Number(data.smart_binary_headers||0);state.smartBinaryPending=!!data.smart_binary_pending;
    const previousKeys=append?new Set(state.articles.map(a=>articleKey(a))):null;
    const liveAnchors=append?captureBrowseAnchors():null;
    const liveScroll=append?els.articlesList.scrollTop:0;
    const incremental=append&&canIncrementallyAppendContinuous(previousKeys,incoming);
    state.articles=append?mergeArticlePages(state.articles,incoming):incoming;
    const loadedStart=Number(data.paging?.page||targetPage),loadedEnd=Math.max(loadedStart,Number(data.paging?.scanned_page_end||loadedStart));if(append){for(let pg=loadedStart;pg<=loadedEnd;pg++)state.loadedPages.add(pg)}else{state.loadedPages=new Set();for(let pg=loadedStart;pg<=loadedEnd;pg++)state.loadedPages.add(pg)};
    state.articlePaging=data.paging||null;state.articlePage=Number(data.paging?.page||1);if(data.group?.name)mergeTrackedGroupStatus([data.group]);if(!append)state.selectedArticleKey='';sortArticles(false);
    if(incremental){
      appendContinuousGallery(previousKeys);
    }else{
      if(append){generation=++state.galleryGeneration;state.thumbQueue=[];state.thumbQueued.clear();}
      renderArticles({preserveScroll:append&&!pageJump,scrollTop:pageJump?0:liveScroll,anchor:pageJump?null:liveAnchors});
    }
    perfRecord('headers',Number(data.elapsed_ms||0));updateArticlePaging();renderArticleSummary(data.elapsed_ms||0);if(data.cache_source&&data.cache_source!=='provider')els.articleSummary.insertAdjacentHTML('beforeend',`<span class="header-cache-chip">⚡ ${escapeHtml(data.cache_source)}${Number(data.cache_age_seconds||0)?` • ${Number(data.cache_age_seconds)}s`:''}</span>`);if(pageJump){armContinuousAfterJump(1350);requestAnimationFrame(()=>{if(generation===state.galleryGeneration){els.articlesList.scrollTop=0;scheduleThumbnailDemandScan()}})}if(!append&&state.smartBinaryPending)scheduleProgressiveBinaryCompletion(targetPage,generation);else if(!pageJump)schedulePredictiveHeaderPrefetch();
  }catch(e){
    if(generation===state.galleryGeneration&&e?.code!=='browse-cancelled'){if(pageJump)armContinuousAfterJump(350);toast(e.message,'error');if(!append){state.articles=[];state.loadedPages.clear();renderArticles({preserveScroll:false});}}
  }finally{
    if(generation===state.galleryGeneration){state.continuousLoading=false;setArticleLoading(false,append);updateContinuousSentinelInPlace();}
  }
}
async function loadOlderArticles(){
  if(state.searchMode){goToArticlePage(state.articlePage+1);return}
  if(!state.articlePaging?.has_older||state.continuousLoading)return;
  await loadArticles({page:Number(state.articlePaging?.next_older_page||state.articlePage+1),append:true});
}
function updateArticlePaging(){
  const p=state.articlePaging;
  const visible=!!(state.selectedGroup&&p);
  els.articlePagingBar.classList.toggle('hidden',!visible);
  if(!visible)return;
  const pages=Math.max(0,Number(p.page_count||0));
  const current=Math.max(1,Number(p.page||1));
  const searchPaging=p.mode==='search'||state.searchMode;
  els.olderArticlesBtn.disabled=!p.has_older||state.continuousLoading;
  els.newerArticlesBtn.disabled=!p.has_newer;
  els.latestArticlesBtn.disabled=!p.has_newer;
  els.articlePageInput.disabled=pages===0;
  els.articlePageInput.min='1';els.articlePageInput.max=String(Math.max(1,pages));els.articlePageInput.value=String(current);
  els.articlePageTotal.textContent=pages?`of ${pages.toLocaleString()}`:'of 0';
  els.exitGroupSearchBtn.classList.toggle('hidden',!searchPaging);
  els.latestArticlesBtn.textContent=searchPaging?'First':'Latest';
  els.latestArticlesBtn.title=searchPaging?'Return to the first page of search matches':'Return to the newest retained headers';
  els.olderArticlesBtn.textContent=!searchPaging&&state.continuousMode?'← Load older':'← Older';
  if(searchPaging){
    const count=Number(p.result_count||0),from=Number(p.start||0),to=Number(p.end||0);const q=state.groupSearchJob?.query||'';
    els.articleRangeLabel.textContent=count?`Matches ${from.toLocaleString()}–${to.toLocaleString()} of ${count.toLocaleString()} • “${q}”`:`No matches yet • “${q}”`;
  }else{
    const loaded=[...state.loadedPages].sort((a,b)=>a-b),scanWord=p.smart_binary_scan?'scanned':'loaded';const loadedText=loaded.length>1?`Header pages ${loaded[0].toLocaleString()}–${loaded[loaded.length-1].toLocaleString()} ${scanWord} • `:'';
    els.articleRangeLabel.textContent=pages?`${loadedText}headers through ${Number(p.start).toLocaleString()} • retained ${Number(p.low).toLocaleString()}–${Number(p.high).toLocaleString()}`:'No retained headers';
  }
}
function goToArticlePage(page){
  const max=Math.max(1,Number(state.articlePaging?.page_count||1));
  const target=Math.max(1,Math.min(max,Number(page)||1));
  if(target===state.articlePage&&state.articles.length&&state.loadedPages.size===1)return;
  if(state.searchMode)loadEntireGroupSearchResults(target);else loadArticles({page:target,append:false,pageJump:true});
}
function setArticleLoading(on,append=false){
  if(append){els.olderArticlesBtn.disabled=on||!state.articlePaging?.has_older;updateContinuousSentinelInPlace();return}
  $('refreshArticlesBtn').disabled=on;els.articleLimit.disabled=on;els.articleSort.disabled=on;els.contentFilter.disabled=on;els.galleryViewBtn.disabled=on;els.listViewBtn.disabled=on;els.articleSearch.disabled=on;els.clearArticleSearchBtn.disabled=on;els.olderArticlesBtn.disabled=on;els.newerArticlesBtn.disabled=on;els.latestArticlesBtn.disabled=on;els.articlePageInput.disabled=on;els.entireGroupSearchBtn.disabled=on||!state.selectedGroup;if(els.thumbnailSize)els.thumbnailSize.disabled=on;if(els.continuousBrowseBtn)els.continuousBrowseBtn.disabled=on;
  if(on){
    const mode=effectiveViewMode();els.articlesList.className=`articles-list ${mode==='gallery'?'media-gallery':'article-list-mode'}${isAllPostsMode()?' binary-list-mode-active':''}`;applyThumbnailSize();
    els.articlesList.innerHTML=mode==='gallery'?'<div class="gallery-loading">'+('<div class="gallery-skeleton"></div>'.repeat(8))+'</div>':('<div class="loading-line"></div>'.repeat(10));
  }else{
    els.articleLimit.disabled=false;els.articleSort.disabled=false;els.contentFilter.disabled=false;els.articleSearch.disabled=false;els.clearArticleSearchBtn.disabled=false;els.entireGroupSearchBtn.disabled=!state.selectedGroup;if(els.thumbnailSize)els.thumbnailSize.disabled=false;if(els.continuousBrowseBtn)els.continuousBrowseBtn.disabled=false;updateArticlePaging();updateArticleSearchUi();applyThumbnailSize();updateContinuousButton();updateBrowseModeControls();
  }
}
function sortArticles(render=true){
  const sort=els.articleSort.value;
  const dateValue=a=>{const t=Date.parse(a.date||'');return Number.isFinite(t)?t:Number(a.article||0)};
  const text=v=>String(v||'').toLocaleLowerCase();
  state.articles.sort((a,b)=>{
    if(sort==='oldest') return dateValue(a)-dateValue(b)||Number(a.article)-Number(b.article);
    if(sort==='size_desc') return Number(b.bytes||0)-Number(a.bytes||0)||Number(b.article)-Number(a.article);
    if(sort==='size_asc') return Number(a.bytes||0)-Number(b.bytes||0)||Number(b.article)-Number(a.article);
    if(sort==='subject_asc') return text(a.subject).localeCompare(text(b.subject))||Number(b.article)-Number(a.article);
    if(sort==='subject_desc') return text(b.subject).localeCompare(text(a.subject))||Number(b.article)-Number(a.article);
    if(sort==='poster_asc') return text(a.from).localeCompare(text(b.from))||Number(b.article)-Number(a.article);
    return dateValue(b)-dateValue(a)||Number(b.article)-Number(a.article);
  });
  if(render) renderArticles();
}
function parseQuickQuery(raw){
  const tokens=(String(raw||'').match(/"[^"]+"|\S+/g)||[]).map(x=>x.replace(/^"|"$/g,''));
  const q={include:[],exclude:[],poster:[],ext:[],filename:[],subject:[],messageId:[]};
  for(const token0 of tokens){
    let token=token0,neg=false;if(token.startsWith('-')&&token.length>1){neg=true;token=token.slice(1)}const low=token.toLocaleLowerCase();
    const add=(bucket,value)=>{if(value)(neg?q.exclude:q[bucket]).push(value)};
    if(low.startsWith('from:')||low.startsWith('poster:')){add('poster',token.slice(token.indexOf(':')+1).toLocaleLowerCase());continue}
    if(low.startsWith('ext:')){const v=low.slice(4).replace(/^\./,'');if(v)q.ext.push(v);continue}
    if(low.startsWith('file:')||low.startsWith('name:')||low.startsWith('filename:')){add('filename',token.slice(token.indexOf(':')+1).toLocaleLowerCase());continue}
    if(low.startsWith('subject:')||low.startsWith('subj:')){add('subject',token.slice(token.indexOf(':')+1).toLocaleLowerCase());continue}
    if(low.startsWith('id:')||low.startsWith('message:')){add('messageId',token.slice(token.indexOf(':')+1).toLocaleLowerCase());continue}
    (neg?q.exclude:q.include).push(low);
  }
  return q;
}
function filteredArticles({ignoreStatus=false}={}){
  const filter=els.contentFilter.value;
  const parsed=parseQuickQuery(state.articleSearchTerm.trim());
  let items=state.articles.map((a,index)=>({a,index})).filter(({a})=>{
    const contentMatch=filter==='all'||(filter==='media'&&['image','video'].includes(a.media?.kind))||(filter==='images'&&a.media?.kind==='image')||(filter==='videos'&&a.media?.kind==='video');
    if(!contentMatch)return false;
    if(filter!=='all'&&(!a.complete||a.small_image_suppressed||state.unsupportedMediaKeys.has(previewKey(a))||state.unpreviewableMediaKeys.has(previewKey(a))))return false;
    if(!state.showBlockedPosters&&isPosterBlocked(a))return false;
    const status=state.articleStatusFilter||'all';if(!ignoreStatus){if(status==='new'&&!isArticleNew(a))return false;if(status==='unseen'&&isArticleSeen(a))return false;if(status==='seen'&&!isArticleSeen(a))return false;}
    const poster=String(a.from||'').toLocaleLowerCase(),ext=String(a.media?.extension||'').toLocaleLowerCase(),filename=String(a.media?.filename||'').toLocaleLowerCase(),subject=String(a.subject||'').toLocaleLowerCase(),messageId=String(a.message_id||'').toLocaleLowerCase();
    const haystack=[subject,poster,filename,messageId].join('\n');
    if(parsed.poster.length&&!parsed.poster.every(x=>poster.includes(x)))return false;
    if(parsed.ext.length&&!parsed.ext.includes(ext))return false;
    if(parsed.filename.length&&!parsed.filename.every(x=>filename.includes(x)))return false;
    if(parsed.subject.length&&!parsed.subject.every(x=>subject.includes(x)))return false;
    if(parsed.messageId.length&&!parsed.messageId.every(x=>messageId.includes(x)))return false;
    if(parsed.include.length&&!parsed.include.every(x=>haystack.includes(x)))return false;
    if(parsed.exclude.length&&parsed.exclude.some(x=>haystack.includes(x)))return false;
    return true;
  });
  if(state.groupRelatedMedia&&state.activeMediaSetKey)items=items.filter(({a})=>mediaSetKey(a)===state.activeMediaSetKey);
  return items;
}
function renderArticleSearchHistory(){
  if(!els.articleSearchHistory)return;const items=(state.articleSearchHistory||[]).slice(0,8);
  if(!items.length){els.articleSearchHistory.classList.add('hidden');els.articleSearchHistory.innerHTML='';return}
  els.articleSearchHistory.innerHTML=`<div class="local-search-history-head"><span>Recent in this group</span><button type="button" data-search-clear-history>Clear</button></div>${items.map((q,i)=>`<button type="button" class="local-search-history-item" data-search-history-index="${i}"><span>⌕</span><b>${escapeHtml(q)}</b></button>`).join('')}`;
  els.articleSearchHistory.querySelectorAll('[data-search-history-index]').forEach(btn=>btn.onclick=e=>{e.preventDefault();applyLocalSearch((state.articleSearchHistory||[])[Number(btn.dataset.searchHistoryIndex)]||'',{commit:true});els.articleSearch.focus()});
  els.articleSearchHistory.querySelector('[data-search-clear-history]')?.addEventListener('click',e=>{e.preventDefault();state.articleSearchHistory=[];renderArticleSearchHistory();captureCurrentGroupState()});
}
function positionArticleSearchHistory(){if(!els.articleSearchHistory||!els.articleSearch)return;const box=els.articleSearch.closest('.article-search-box')||els.articleSearch;const r=box.getBoundingClientRect();const maxW=Math.max(240,Math.min(430,window.innerWidth-32));const width=Math.max(240,Math.min(maxW,r.width));const left=Math.max(16,Math.min(r.left,window.innerWidth-width-16));els.articleSearchHistory.style.left=`${Math.round(left)}px`;els.articleSearchHistory.style.top=`${Math.round(Math.min(window.innerHeight-16,r.bottom+7))}px`;els.articleSearchHistory.style.width=`${Math.round(width)}px`}
function showArticleSearchHistory(){if(!els.articleSearchHistory||!(state.articleSearchHistory||[]).length)return;renderArticleSearchHistory();positionArticleSearchHistory();els.articleSearchHistory.classList.remove('hidden')}
function hideArticleSearchHistory(){setTimeout(()=>els.articleSearchHistory?.classList.add('hidden'),120)}
function rememberLocalSearch(term){const q=String(term||'').trim();if(!q)return;state.articleSearchHistory=[q,...(state.articleSearchHistory||[]).filter(x=>x!==q)].slice(0,8);renderArticleSearchHistory();captureCurrentGroupState()}
function beginLocalSearchReturn(){if(state.articleSearchReturn||state.articleSearchTerm.trim())return;state.articleSearchReturn={scrollTop:Number(els.articlesList?.scrollTop||0),anchors:captureBrowseAnchors(),selectedKey:state.selectedArticleKey||''}}
function updateArticleSearchUi(matchCount=null){
  const active=!!state.articleSearchTerm.trim();
  els.clearArticleSearchBtn.classList.toggle('hidden',!active);
  if(!active){els.articleSearchInfo.classList.add('hidden');els.articleSearchInfo.textContent='';return}
  const count=matchCount==null?filteredArticles().length:matchCount;
  els.articleSearchInfo.textContent=`${count.toLocaleString()} match${count===1?'':'es'} • ${state.articles.length.toLocaleString()} loaded`;
  els.articleSearchInfo.classList.remove('hidden');
}
function applyLocalSearch(value,{commit=false}={}){
  const next=String(value??'');const was=!!state.articleSearchTerm.trim(),will=!!next.trim();if(!was&&will)beginLocalSearchReturn();
  state.articleSearchTerm=next;if(els.articleSearch.value!==next)els.articleSearch.value=next;
  const t0=performance.now();renderArticles();perfRecord('search',performance.now()-t0);
  if(commit&&will)rememberLocalSearch(next);
  if(was&&!will&&state.articleSearchReturn){const ret=state.articleSearchReturn;state.articleSearchReturn=null;requestAnimationFrame(()=>{restoreBrowsePosition(ret.anchors,ret.scrollTop);if(ret.selectedKey){state.selectedArticleKey=ret.selectedKey;updateActiveArticleDomInPlace()}})}
}
function scheduleLocalSearch(value){clearTimeout(state.articleSearchTimer);state.articleSearchTimer=setTimeout(()=>applyLocalSearch(value),55)}
function clearArticleSearch(){
  const ret=state.articleSearchReturn;state.articleSearchTerm='';els.articleSearch.value='';renderArticles();if(ret){state.articleSearchReturn=null;requestAnimationFrame(()=>{restoreBrowsePosition(ret.anchors,ret.scrollTop);if(ret.selectedKey){state.selectedArticleKey=ret.selectedKey;updateActiveArticleDomInPlace()}})}els.articleSearch.focus();
}

function currentEntireSearchCriteria(){const min=Math.max(0,Number(els.entireSearchMinMb?.value||0)||0),max=Math.max(0,Number(els.entireSearchMaxMb?.value||0)||0);return{query:els.entireGroupSearchInput?.value.trim()||'',filters:{kind:els.entireSearchKind?.value||'all',poster:els.entireSearchPoster?.value.trim()||'',min_bytes:Math.round(min*1048576),max_bytes:Math.round(max*1048576),age_days:Number(els.entireSearchAge?.value||0)||0,extensions:(els.entireSearchExtensions?.value||'').split(/[\s,]+/).map(x=>x.trim().replace(/^\./,'').toLowerCase()).filter(Boolean)}}}
function applyEntireSearchCriteria(saved){const f=saved?.filters||{};els.entireGroupSearchInput.value=saved?.query||'';els.entireSearchKind.value=f.kind||'all';els.entireSearchPoster.value=f.poster||'';els.entireSearchMinMb.value=f.min_bytes?String(Math.round(Number(f.min_bytes)/1048576)):'';els.entireSearchMaxMb.value=f.max_bytes?String(Math.round(Number(f.max_bytes)/1048576)):'';els.entireSearchAge.value=String(Number(f.age_days||0));els.entireSearchExtensions.value=(f.extensions||[]).join(', ')}
function renderSavedSearches(){if(!els.savedSearchSelect)return;els.savedSearchSelect.innerHTML='<option value="">— Choose saved search —</option>'+state.savedSearches.map(x=>`<option value="${escapeHtml(x.id)}">${escapeHtml(x.name)}</option>`).join('');els.savedSearchSelect.value=state.savedSearches.some(x=>x.id===state.activeSavedSearchId)?state.activeSavedSearchId:'';els.deleteSavedSearchBtn.disabled=!els.savedSearchSelect.value}
async function loadSavedSearches(){try{const data=await api('/api/saved-searches');state.savedSearches=data.items||[];renderSavedSearches()}catch(_e){state.savedSearches=[]}}
async function saveCurrentSearch(){const criteria=currentEntireSearchCriteria(),existing=state.savedSearches.find(x=>x.id===els.savedSearchSelect.value),name=window.prompt('Name this saved search:',existing?.name||'');if(!name?.trim())return;try{const data=await api('/api/saved-searches/save',{id:existing?.id||'',name:name.trim(),...criteria});state.savedSearches=data.items||[];state.activeSavedSearchId=data.search?.id||'';renderSavedSearches();toast('Saved search stored.','success')}catch(e){toast(e.message,'error')}}
async function deleteSavedSearch(){const id=els.savedSearchSelect.value;if(!id)return;const item=state.savedSearches.find(x=>x.id===id);if(!window.confirm(`Delete saved search “${item?.name||'this search'}”?`))return;try{const data=await api('/api/saved-searches/delete',{id});state.savedSearches=data.items||[];state.activeSavedSearchId='';renderSavedSearches();toast('Saved search deleted.')}catch(e){toast(e.message,'error')}}
function searchFilterSummary(f={}){const bits=[];const kind={images:'Images',videos:'Video',media:'Images + video'}[f.kind];if(kind)bits.push(kind);if(f.poster)bits.push(`poster: ${f.poster}`);if(f.min_bytes)bits.push(`≥ ${formatBytes(f.min_bytes)}`);if(f.max_bytes)bits.push(`≤ ${formatBytes(f.max_bytes)}`);if(f.age_days)bits.push(`last ${f.age_days} days`);if(f.extensions?.length)bits.push(f.extensions.map(x=>'.'+x).join(', '));return bits.join(' • ')}
function openEntireGroupSearch(){
  if(!state.selectedGroup){toast('Choose a newsgroup first.','error');return}
  els.groupSearchModal.classList.remove('hidden');
  els.entireGroupSearchGroup.textContent=state.selectedGroup;
  if(!els.entireGroupSearchInput.value)els.entireGroupSearchInput.value=state.articleSearchTerm.trim();
  renderEntireGroupSearchStatus(state.groupSearchJob);loadSavedSearches();
  setTimeout(()=>els.entireGroupSearchInput.focus(),50);
}
function closeEntireGroupSearch(){els.groupSearchModal.classList.add('hidden')}
function renderEntireGroupSearchStatus(job){
  if(!job){
    els.entireGroupSearchProgress.classList.add('hidden');els.cancelEntireGroupSearchBtn.classList.add('hidden');els.viewEntireGroupSearchResultsBtn.classList.add('hidden');els.startEntireGroupSearchBtn.classList.remove('hidden');els.startEntireGroupSearchBtn.disabled=false;return;
  }
  state.groupSearchJob=job;const status=String(job.status||'queued');const running=['queued','scanning','cancelling'].includes(status);const pct=Math.max(0,Math.min(100,Number(job.percent||0)));
  els.entireGroupSearchProgress.classList.remove('hidden');els.entireGroupSearchPercent.textContent=`${pct.toFixed(pct<10?1:0)}%`;els.entireGroupSearchProgressFill.style.width=`${pct}%`;
  const labels={queued:'Preparing search…',scanning:'Scanning retained headers…',cancelling:'Cancelling scan…',completed:'Search complete',cancelled:'Search cancelled',failed:'Search failed'};
  els.entireGroupSearchStatus.textContent=labels[status]||status;
  const scanned=Number(job.scanned_headers||0),total=Number(job.total_headers||0),matches=Number(job.match_posts||0),headerMatches=Number(job.match_headers||0);
  els.entireGroupSearchStats.textContent=`${scanned.toLocaleString()}${total?' / '+total.toLocaleString():''} headers scanned • ${matches.toLocaleString()} matching post${matches===1?'':'s'} (${headerMatches.toLocaleString()} matching headers)`;
  els.entireGroupSearchError.classList.toggle('hidden',!job.error);els.entireGroupSearchError.textContent=job.error||'';
  els.cancelEntireGroupSearchBtn.classList.toggle('hidden',!running);els.cancelEntireGroupSearchBtn.disabled=status==='cancelling';
  els.viewEntireGroupSearchResultsBtn.classList.toggle('hidden',matches===0);els.viewEntireGroupSearchResultsBtn.disabled=matches===0;
  els.startEntireGroupSearchBtn.classList.toggle('hidden',running);els.startEntireGroupSearchBtn.textContent=running?'Searching…':'Search again';els.startEntireGroupSearchBtn.disabled=running;
}
async function startEntireGroupSearch(){
  const criteria=currentEntireSearchCriteria(),f=criteria.filters,hasFilter=(f.kind&&f.kind!=='all')||f.poster||f.min_bytes||f.max_bytes||f.age_days||(f.extensions&&f.extensions.length);if(!criteria.query&&!hasFilter){toast('Enter search text or choose at least one filter.','error');return}if(f.min_bytes&&f.max_bytes&&f.min_bytes>f.max_bytes){toast('Minimum size cannot exceed maximum size.','error');return}
  if(state.groupSearchJob&&['queued','scanning','cancelling'].includes(state.groupSearchJob.status)){toast('A full-group search is already running.');return}
  els.startEntireGroupSearchBtn.disabled=true;els.startEntireGroupSearchBtn.textContent='Starting…';
  try{const data=await api('/api/group-search/start',{provider_id:state.providerId,group:state.selectedGroup,...criteria});state.groupSearchJob=data.search;renderEntireGroupSearchStatus(data.search);startEntireGroupSearchPolling();}
  catch(e){toast(e.message,'error');els.startEntireGroupSearchBtn.disabled=false;els.startEntireGroupSearchBtn.textContent='Search entire group'}
}
function startEntireGroupSearchPolling(){
  if(state.groupSearchPollTimer){clearInterval(state.groupSearchPollTimer);state.groupSearchPollTimer=null}
  if(!state.groupSearchJob?.id)return;
  const poll=async()=>{
    const id=state.groupSearchJob?.id;if(!id)return;
    try{
      const data=await api('/api/group-search/status',{id});if(state.groupSearchJob?.id!==id)return;const old=state.groupSearchJob?.status;state.groupSearchJob=data.search;renderEntireGroupSearchStatus(data.search);
      if(state.searchMode)renderSearchModeSummary();
      if(!['queued','scanning','cancelling'].includes(data.search.status)){
        if(state.groupSearchPollTimer){clearInterval(state.groupSearchPollTimer);state.groupSearchPollTimer=null}
        if(data.search.status==='completed'){toast(`Full-group search complete: ${Number(data.search.match_posts||0).toLocaleString()} matching posts.`,'success');if(state.searchMode)loadEntireGroupSearchResults(state.articlePage);}
        else if(data.search.status==='failed')toast(data.search.error||'Full-group search failed.','error');
      }
    }catch(e){if(state.groupSearchPollTimer){clearInterval(state.groupSearchPollTimer);state.groupSearchPollTimer=null}toast(e.message,'error')}
  };
  poll();state.groupSearchPollTimer=setInterval(poll,750);
}
async function cancelEntireGroupSearch(){
  if(!state.groupSearchJob?.id)return;try{const data=await api('/api/group-search/cancel',{id:state.groupSearchJob.id});state.groupSearchJob=data.search;renderEntireGroupSearchStatus(data.search)}catch(e){toast(e.message,'error')}
}
function renderSearchModeSummary(){
  const job=state.groupSearchJob;if(!state.searchMode||!job)return;
  const status=job.status==='completed'?'Complete':job.status==='failed'?'Failed':job.status==='cancelled'?'Cancelled':'Scanning';
  const progress=job.total_headers?`${Number(job.percent||0).toFixed(1)}%`:'…';
  els.articleSummary.classList.remove('hidden');els.articlesList.classList.add('has-summary');
  const criteria=[job.query?`text: ${job.query}`:'',searchFilterSummary(job.filters||{})].filter(Boolean).join(' • ')||'Filtered search';els.articleSummary.innerHTML=`<span><b>${Number(state.articlePaging?.result_count||job.match_posts||0).toLocaleString()}</b> matching posts</span><span><b>${Number(job.scanned_headers||0).toLocaleString()}</b> headers scanned</span><span class="search-live-chip"><b>${status}</b> ${progress}</span><span>${escapeHtml(criteria)}</span>`;
}
async function viewEntireGroupSearchResults(){
  if(!state.groupSearchJob?.id)return;state.browsePageBeforeSearch=state.searchMode?state.browsePageBeforeSearch:state.articlePage;state.searchMode=true;const tab=state.browserTabs.find(t=>t.id===state.activeBrowserTabId);if(tab){tab.title=`⌕ ${state.groupSearchJob.query||state.selectedGroup}`;renderBrowserTabs()}state.articleSearchTerm='';els.articleSearch.value='';closeEntireGroupSearch();await loadEntireGroupSearchResults(1);
}
async function loadEntireGroupSearchResults(page=1){
  if(!state.groupSearchJob?.id||!state.selectedGroup)return;
  setArticleLoading(true);const generation=++state.galleryGeneration;state.thumbQueue=[];state.thumbQueued.clear();
  try{
    const data=await api('/api/group-search/results',{id:state.groupSearchJob.id,page:Number(page||1),page_size:Number(els.articleLimit.value)});if(generation!==state.galleryGeneration)return;
    state.groupSearchJob=data.search;state.articles=data.articles||[];state.articlePaging=data.paging||null;state.articlePage=Number(data.paging?.page||1);state.selectedArticleKey='';sortArticles(false);renderArticles();updateArticlePaging();
    els.articleEyebrow.textContent='ENTIRE NEWSGROUP SEARCH';renderSearchModeSummary();
  }catch(e){if(generation===state.galleryGeneration){toast(e.message,'error');state.articles=[];renderArticles()}}
  finally{if(generation===state.galleryGeneration)setArticleLoading(false)}
}
async function exitEntireGroupSearch(){
  state.searchMode=false;state.articleSearchTerm='';els.articleSearch.value='';els.articleEyebrow.textContent='VISUAL NEWSGROUP BROWSER';const tab=state.browserTabs.find(t=>t.id===state.activeBrowserTabId);if(tab){tab.title=tab.group;renderBrowserTabs();saveUiSettings()}await loadArticles({page:state.browsePageBeforeSearch||1});
}
function continuousSentinelMarkup(){
  if(!state.selectedGroup||state.searchMode||!state.continuousMode)return '';
  if(state.continuousLoading)return '<div id="continuousSentinel" class="continuous-sentinel"><span class="mini-spinner"></span><span>Loading older headers…</span></div>';
  if(state.smartBinaryPending)return '<div id="continuousSentinel" class="continuous-sentinel"><span class="mini-spinner"></span><span>Finishing package reconstruction in the background…</span></div>';
  if(!state.articlePaging?.has_older)return '<div id="continuousSentinel" class="continuous-sentinel done"><span>✓ Reached the oldest headers retained by this provider</span></div>';
  if(state.articleSearchTerm.trim())return '<div id="continuousSentinel" class="continuous-sentinel"><span>Loaded-header search is active — automatic loading is paused</span><button id="loadOlderInlineBtn" type="button">Load older manually</button></div>';
  return '<div id="continuousSentinel" class="continuous-sentinel"><span>Keep scrolling to load older headers</span><button id="loadOlderInlineBtn" type="button">Load older now</button></div>';
}
function updateContinuousSentinelInPlace(){
  const old=$('continuousSentinel');if(!old)return;const wrap=document.createElement('div');wrap.innerHTML=continuousSentinelMarkup();const replacement=wrap.firstElementChild;if(replacement)old.replaceWith(replacement);else old.remove();wireContinuousObserver();
}
function continuousJumpHeld(){return Number(state.continuousJumpHoldUntil||0)>performance.now()}
function armContinuousAfterJump(delayMs=1350){
  state.continuousJumpHoldUntil=performance.now()+Math.max(350,Number(delayMs||0));
  if(state.continuousJumpTimer)clearTimeout(state.continuousJumpTimer);
  state.continuousJumpTimer=setTimeout(()=>{state.continuousJumpTimer=null;if(!continuousJumpHeld()){wireContinuousObserver();schedulePredictiveHeaderPrefetch();}},Math.max(380,Number(delayMs||0)+40));
}
function wireContinuousObserver(){
  if(continuousObserver){continuousObserver.disconnect();continuousObserver=null}
  const sentinel=$('continuousSentinel');if(!sentinel)return;
  $('loadOlderInlineBtn')?.addEventListener('click',e=>{e.stopPropagation();loadOlderArticles()});
  if(continuousJumpHeld()||!state.continuousMode||state.searchMode||state.continuousLoading||state.smartBinaryPending||state.articleSearchTerm.trim()||!state.articlePaging?.has_older)return;
  continuousObserver=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)&&!state.continuousLoading&&!continuousJumpHeld())loadOlderArticles();},{root:els.articlesList,rootMargin:'900px 0px',threshold:.01});
  continuousObserver.observe(sentinel);
}
function captureBrowseAnchors(limit=12){
  if(!els.articlesList)return[];const listRect=els.articlesList.getBoundingClientRect();const nodes=els.articlesList.querySelectorAll('.media-card[data-index],.article-row[data-index],.media-set-card[data-set-key],.binary-set-row[data-binary-set-key]');const out=[];
  for(const node of nodes){const r=node.getBoundingClientRect();if(r.bottom<listRect.top-2)continue;if(r.top>listRect.bottom&&out.length)break;if(node.dataset.setKey)out.push({setKey:node.dataset.setKey,offset:r.top-listRect.top});else if(node.dataset.binarySetKey)out.push({binarySetKey:node.dataset.binarySetKey,offset:r.top-listRect.top});else{const a=state.articles[Number(node.dataset.index)];if(a)out.push({key:articleKey(a),offset:r.top-listRect.top})}if(out.length>=limit)break}
  return out;
}
function captureBrowseAnchor(){return captureBrowseAnchors(1)[0]||null}
function restoreBrowsePosition(anchor,fallback){
  const anchors=Array.isArray(anchor)?anchor:(anchor?[anchor]:[]);
  for(const candidate of anchors){let node=null;if(candidate.setKey)node=[...els.articlesList.querySelectorAll('.media-set-card[data-set-key]')].find(x=>x.dataset.setKey===candidate.setKey)||null;else if(candidate.binarySetKey)node=[...els.articlesList.querySelectorAll('.binary-set-row[data-binary-set-key]')].find(x=>x.dataset.binarySetKey===candidate.binarySetKey)||null;else{const index=state.articles.findIndex(a=>articleKey(a)===candidate.key);node=index>=0?els.articlesList.querySelector(`.media-card[data-index="${index}"],.article-row[data-index="${index}"]`):null}if(node){const listRect=els.articlesList.getBoundingClientRect(),r=node.getBoundingClientRect();els.articlesList.scrollTop+=r.top-listRect.top-candidate.offset;return true}}
  els.articlesList.scrollTop=fallback||0;return false;
}
function renderArticles({preserveScroll=true,scrollTop=null,anchor=null}={}){
  const renderStarted=performance.now();
  const keep=scrollTop==null?(preserveScroll?els.articlesList.scrollTop:0):scrollTop;const anchors=preserveScroll?(anchor||captureBrowseAnchors()):null;
  if(thumbObserver){thumbObserver.disconnect();thumbObserver=null}if(continuousObserver){continuousObserver.disconnect();continuousObserver=null}
  const items=filteredArticles(),mode=effectiveViewMode();updateArticleSearchUi(items.length);updateBrowseModeControls();els.articlesList.classList.remove('empty-state','media-gallery','article-list-mode','binary-list-mode-active');
  els.articlesList.classList.add(mode==='gallery'?'media-gallery':'article-list-mode');if(isAllPostsMode())els.articlesList.classList.add('binary-list-mode-active');applyThumbnailSize();
  if(!items.length){
    state.binarySetGroups.clear();state.thumbHolderRegistry.clear();els.articlesList.classList.add('empty-state');
    const noun=els.contentFilter.value==='images'?'images':els.contentFilter.value==='videos'?'videos':els.contentFilter.value==='media'?'media':'posts';const hasSearch=!!state.articleSearchTerm.trim();
    els.articlesList.innerHTML=hasSearch
      ?`<div class="empty-icon">⌕</div><h3>No matches in loaded headers</h3><p>Nothing currently loaded matches “${escapeHtml(state.articleSearchTerm.trim())}”. ${state.continuousMode&&state.articlePaging?.has_older?'Scroll/load older headers to keep expanding this search, or ':''}clear the search or change the Show filter.</p>${continuousSentinelMarkup()}`
      :`<div class="empty-icon">⌁</div><h3>No ${noun} found yet</h3><p>${state.continuousMode&&state.articlePaging?.has_older?'Continuous browsing can keep looking through older headers.':'Try another page, increase Headers/page, or change the Show filter.'}</p>${continuousSentinelMarkup()}`;
    updateSelectionBar();restoreBrowsePosition(anchors,keep);perfRecord('render',performance.now()-renderStarted);requestAnimationFrame(()=>{updateSelectionBar();wireContinuousObserver()});return;
  }
  if(mode==='gallery'){renderGallery(items);rebuildThumbnailHolderRegistry()}else{state.thumbHolderRegistry.clear();renderList(items)}
  updateSelectionBar();restoreBrowsePosition(anchors,keep);perfRecord('render',performance.now()-renderStarted);requestAnimationFrame(()=>{updateSelectionBar();wireContinuousObserver()});
}
function mediaSetKey(a){if(!a?.media?.filename||!['image','video'].includes(a.media?.kind))return'';const name=String(a.media.filename),dot=name.lastIndexOf('.'),stem=dot>0?name.slice(0,dot):name;let base=stem.replace(/(?:[._\- ]?(?:img|image|pic|photo|vid|video)?[._\- ]*)?\d{1,6}$/i,'').replace(/[._\- ]+$/,'').trim();if(base.length<3){const m=String(a.subject||'').match(/^(.{3,}?)\s*[\[(]\s*\d{1,6}\s*\/\s*\d{1,6}\s*[\])]/);if(m)base=m[1].replace(/[._\- ]+$/,'').trim()}if(base.length<3||base.toLowerCase()===stem.toLowerCase())return'';return`${articleGroup(a)}|${a.media.kind}|${base.toLocaleLowerCase()}|${String(a.from||'').toLocaleLowerCase()}`}
function buildMediaSets(items){const buckets=new Map(),singles=[];for(const item of items){const key=mediaSetKey(item.a);if(!key){singles.push(item);continue}if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(item)}const groups=[],ungrouped=[...singles];for(const[key,members]of buckets){if(members.length>=3)groups.push({key,members});else ungrouped.push(...members)}groups.sort((a,b)=>Math.max(...b.members.map(x=>Number(x.a.article||0)))-Math.max(...a.members.map(x=>Number(x.a.article||0))));return{groups,ungrouped}}
function mediaSetTitle(group){const f=group.members[0]?.a?.media?.filename||'Media set',dot=f.lastIndexOf('.'),stem=dot>0?f.slice(0,dot):f;return stem.replace(/(?:[._\- ]?(?:img|image|pic|photo|vid|video)?[._\- ]*)?\d{1,6}$/i,'').replace(/[._\- ]+$/,'').trim()||'Media set'}
function mediaSetRepresentative(group){const candidates=group.members.filter(x=>!state.unpreviewableMediaKeys.has(previewKey(x.a)));const pool=candidates.length?candidates:group.members;return [...pool].sort((x,y)=>{const ax=x.a,ay=y.a;const cx=(state.imageThumbCache.has(previewKey(ax))||state.videoThumbCache.has(previewKey(ax)))?0:1,cy=(state.imageThumbCache.has(previewKey(ay))||state.videoThumbCache.has(previewKey(ay)))?0:1;if(cx!==cy)return cx-cy;const sx=Number(ax.segment_count||1),sy=Number(ay.segment_count||1);if(sx!==sy)return sx-sy;const bx=Number(ax.bytes||0)||Number.MAX_SAFE_INTEGER,by=Number(ay.bytes||0)||Number.MAX_SAFE_INTEGER;if(bx!==by)return bx-by;return Number(ay.article||0)-Number(ax.article||0)})[0]||group.members[0]}
function mediaSetCard(group){const rep=mediaSetRepresentative(group),a=rep.a,index=rep.index,kind=a.media?.kind||'media',title=mediaSetTitle(group),bytes=group.members.reduce((n,x)=>n+Number(x.a.bytes||0),0),cache=kind==='image'?state.imageThumbCache.get(previewKey(a)):state.videoThumbCache.get(previewKey(a)),visual=cache?.url?`<img class="thumb-img" src="${cache.url}" alt="${escapeHtml(title)}" decoding="async" data-thumb-image-index="${index}" data-thumb-role="set-cover">`:`<div class="thumb-loader ${kind==='video'?'video-thumb-loader':''}" data-thumb-index="${index}" data-thumb-role="set-cover"><span></span><small>Loading set cover…</small></div>`;return`<article class="media-set-card" data-set-key="${escapeHtml(group.key)}"><div class="media-set-cover">${visual}<span class="set-badge">${group.members.length.toLocaleString()} ${kind==='image'?'IMAGES':'VIDEOS'}</span><span class="kind-pill ${kind}">${kind.toUpperCase()} SET</span></div><div class="media-set-info"><strong>${escapeHtml(title)}</strong><span>${formatBytes(bytes)} • ${shortDate(a.date)}</span><div class="media-set-actions"><button class="set-open-btn" type="button">Open set</button><button class="set-queue-btn" type="button">＋ Queue all</button></div></div></article>`}
function renderGroupedGallery(items){const{groups,ungrouped}=buildMediaSets(items);if(!groups.length)return false;els.articlesList.innerHTML=`<div class="sets-summary"><strong>${groups.length} related media set${groups.length===1?'':'s'}</strong><span>${ungrouped.length} individual post${ungrouped.length===1?'':'s'}</span></div><div class="media-grid media-sets-grid">${groups.map(mediaSetCard).join('')}${ungrouped.map(({a,index})=>galleryCard(a,index)).join('')}${continuousSentinelMarkup()}</div>`;els.articlesList.querySelectorAll('.media-set-card').forEach(card=>{const open=()=>{state.activeMediaSetKey=card.dataset.setKey;renderArticles({preserveScroll:false})};card.onclick=e=>{if(!e.target.closest('button'))open()};card.querySelector('.set-open-btn').onclick=e=>{e.stopPropagation();open()};card.querySelector('.set-queue-btn').onclick=e=>{e.stopPropagation();const g=groups.find(x=>x.key===card.dataset.setKey);downloadItems(g?g.members.map(x=>x.a):[],e.currentTarget)}});wireGalleryCards();wireThumbnailImages();observeThumbnails();return true}
function renderGallery(items){
  let setBanner='';if(state.groupRelatedMedia&&state.activeMediaSetKey){const members=items.filter(x=>mediaSetKey(x.a)===state.activeMediaSetKey);if(members.length){items=members;setBanner=`<div class="set-focus-bar"><button id="backToSetsBtn" type="button">← All sets</button><div><strong>${escapeHtml(mediaSetTitle({members}))}</strong><span>${members.length} files in this set</span></div><button id="queueFocusedSetBtn" type="button">＋ Queue set</button></div>`}else state.activeMediaSetKey=''}
  if(state.groupRelatedMedia&&!state.activeMediaSetKey&&renderGroupedGallery(items))return;
  els.articlesList.innerHTML=setBanner+`<div class="media-grid">${items.map(({a,index})=>galleryCard(a,index)).join('')}${continuousSentinelMarkup()}</div>`;
  wireGalleryCards();if(state.activeMediaSetKey){$('backToSetsBtn')?.addEventListener('click',()=>{state.activeMediaSetKey='';renderArticles({preserveScroll:false})});$('queueFocusedSetBtn')?.addEventListener('click',e=>downloadItems(items.map(x=>x.a),e.currentTarget));}
  wireThumbnailImages();observeThumbnails();updateNewContentBoundaryDom();
}
function wireGalleryCards(root=els.articlesList){const cards=root?.matches?.('.media-card')?[root]:[...(root?.querySelectorAll?.('.media-card')||[])];cards.forEach(card=>{if(card.dataset.galleryWired==='1')return;card.dataset.galleryWired='1';card.addEventListener('click',e=>{if(e.target.closest('.card-download-btn,.thumb-retry'))return;handleMediaSelectionClick(Number(card.dataset.index),e)});card.addEventListener('dblclick',e=>{if(e.target.closest('.card-download-btn,.thumb-retry'))return;const a=state.articles[Number(card.dataset.index)];if(['image','video'].includes(a?.media?.kind)&&a.complete){e.preventDefault();openMediaViewer(a)}});card.addEventListener('contextmenu',e=>{e.preventDefault();const a=state.articles[Number(card.dataset.index)];if(!a)return;showContextMenu(e.clientX,e.clientY,[{label:'Preview',action:()=>{handleMediaSelectionClick(Number(card.dataset.index),e);renderPreviewDetails(a,true)}},{label:'Add to download queue',disabled:!isSelectableMedia(a),action:()=>downloadItems([a])},{separator:true},{label:isArticleSeen(a)?'Mark post unseen':'Mark post seen',action:()=>setArticlesSeen([a],!isArticleSeen(a),{toastResult:true})},{separator:true},{label:'Copy filename',action:()=>copyText(a.media?.filename||a.subject)},{label:'Copy subject',action:()=>copyText(a.subject||'')},{label:'Copy Message-ID',action:()=>copyText(a.message_id||'')},{separator:true},{label:isPosterBlocked(a)?'Unmute this poster':'Mute this poster',action:()=>mutePoster(a.from)},{label:'Filter to this poster',action:()=>{state.articleSearchTerm=`from:${a.from}`;els.articleSearch.value=state.articleSearchTerm;renderArticles()}},{label:'Show details',action:()=>{state.selectedArticleKey=articleKey(a);renderPreviewDetails(a,false)}}])})});els.articlesList.querySelectorAll('.card-download-btn').forEach(btn=>btn.onclick=e=>{e.stopPropagation();downloadItems([state.articles[Number(btn.dataset.index)]],btn)});els.articlesList.querySelectorAll('[data-retry-thumb]').forEach(btn=>btn.onclick=e=>{e.stopPropagation();const index=Number(btn.dataset.retryThumb),a=state.articles[index];if(a)state.thumbFailureCache.delete(previewKey(a));renderArticles()})}
function activeThumbFailure(a){const key=previewKey(a),f=state.thumbFailureCache.get(key);if(!f)return null;if(Date.now()>Number(f.expires||0)){state.thumbFailureCache.delete(key);return null}return f}
function thumbFailureMarkup(f,kind,index){return `<div class="thumb-error cached-thumb-error"><span>!</span><small>${kind==='video'?'Video thumbnail unavailable':'Preview unavailable'}</small><em class="error-label">${escapeHtml(f.info?.label||'Preview unavailable')}</em><button type="button" class="thumb-retry" data-retry-thumb="${index}">Retry</button></div>`}
function updateNewContentBoundaryDom(){
  if(!els.articlesList||state.searchMode||(els.articleSort?.value||'newest')!=='newest'){els.articlesList?.querySelectorAll('.new-content-boundary').forEach(x=>x.remove());return}
  const nodes=[...els.articlesList.querySelectorAll('.media-card[data-index],.article-row[data-index]:not(.binary-set-member),.binary-set-row[data-binary-set-key]')];els.articlesList.querySelectorAll('.new-content-boundary').forEach(x=>x.remove());if(!nodes.length)return;let sawNew=false,boundaryBefore=null;
  for(const node of nodes){let fresh=false;if(node.dataset.binarySetKey){const group=state.binarySetGroups.get(node.dataset.binarySetKey);fresh=!!group?.members?.some(x=>isArticleNew(x.a));}else{const a=state.articles[Number(node.dataset.index)];fresh=isArticleNew(a)}if(fresh){sawNew=true;continue}if(sawNew){boundaryBefore=node;break}}
  if(!sawNew)return;const d=document.createElement('div');d.className='new-content-boundary';d.innerHTML='<span>NEW SINCE LAST VISIT</span><small>Previously available posts continue below</small>';if(boundaryBefore)boundaryBefore.parentElement.insertBefore(d,boundaryBefore);else{const sentinel=$('continuousSentinel');if(sentinel?.parentElement)sentinel.parentElement.insertBefore(d,sentinel);else nodes[nodes.length-1].parentElement.appendChild(d)}
}
function galleryCard(a,index){
  const key=articleKey(a),selected=state.selectedItems.has(key),prepared=state.previewCache.get(previewKey(a));const kind=a.media?.kind||'post';const complete=!!a.complete;const filename=a.media?.filename||a.subject;const dkey=itemDownloadKey(a);const downloaded=!!a.media&&state.downloadedIndex.has(dkey),queued=!!a.media&&state.queuedIndex.has(dkey);
  let visual='';
  if(kind==='image'&&complete){
    const thumb=state.imageThumbCache.get(previewKey(a)),failure=activeThumbFailure(a);visual=prepared?.url?`<img class="thumb-img" src="${prepared.url}" alt="${escapeHtml(filename)}" decoding="async" data-thumb-image-index="${index}" data-thumb-role="item" data-thumb-fallback="full">`:thumb?.url?`<img class="thumb-img" src="${thumb.url}" alt="${escapeHtml(filename)}" decoding="async" data-thumb-image-index="${index}" data-thumb-role="item">`:failure?thumbFailureMarkup(failure,kind,index):`<div class="thumb-loader" data-thumb-index="${index}" data-thumb-role="item"><span></span><small>Loading preview…</small></div>`;
  }else if(kind==='video'){
    const vthumb=state.videoThumbCache.get(previewKey(a)),failure=activeThumbFailure(a);
    if(vthumb?.url)visual=`<img class="thumb-img" src="${vthumb.url}" alt="Video thumbnail for ${escapeHtml(filename)}" decoding="async" data-thumb-image-index="${index}" data-thumb-role="item"><div class="video-play-overlay"><span>▶</span></div>`;
    else if(complete)visual=failure?thumbFailureMarkup(failure,kind,index):`<div class="thumb-loader video-thumb-loader" data-thumb-index="${index}" data-thumb-role="item"><span></span><small>Loading video thumbnail…</small></div>`;
    else visual=`<div class="video-placeholder"><span>▶</span><small>Incomplete multipart video</small></div>`;
  }else visual=`<div class="post-placeholder"><span>⌁</span><small>No visual preview</small></div>`;
  const partTotal=Number(a.segment_total||a.segment_count||0),partCount=Number(a.segment_count||0);const partBadge=a.media&&partTotal>1?`<span class="card-status ${complete?'complete':'warning'}">${complete?'✓':'⚠'} ${partCount}/${partTotal}</span>`:'';const status=downloaded?'<span class="downloaded-badge">✓ DOWNLOADED</span>':queued?'<span class="queued-badge">⇣ QUEUED</span>':'';
  return `<article class="media-card ${articleStatusClass(a)} ${a.media&&complete?'selectable':''} ${selected?'selected':''} ${state.selectedArticleKey===key?'active keyboard-active':''}" data-index="${index}" data-download-key="${escapeHtml(dkey)}" aria-selected="${selected?'true':'false'}" title="${a.media&&complete?'Click to select • Ctrl-click toggles • Shift-click selects a range • Double-click images to open viewer':'Click to preview'}">
    <div class="thumb-stage">${visual}<span class="kind-pill ${kind}">${kind.toUpperCase()}</span>${partBadge}${status}${articleStatusBadge(a)}
      ${a.media&&complete&&selected?'<span class="selection-check" aria-hidden="true">✓</span>':''}
      ${a.media&&complete?`<button class="card-download-btn" data-index="${index}" title="Add to download queue">＋</button>`:''}
    </div>
    <div class="media-card-info"><strong title="${escapeHtml(filename)}">${escapeHtml(filename)}</strong><div><span>${formatBytes(a.bytes)}</span><span>${shortDate(a.date)}</span>${a.media_meta?.width&&a.media_meta?.height?`<span class="media-dims">${Number(a.media_meta.width).toLocaleString()}×${Number(a.media_meta.height).toLocaleString()}${a.media_meta.duration?' • '+formatDuration(a.media_meta.duration):''}</span>`:''}${a.media?.extension?`<span>${escapeHtml(String(a.media.extension).toUpperCase())}</span>`:''}</div></div>
  </article>`;
}
function normalizeBinarySetBase(raw){
  let base=String(raw||'').replace(/[._\- ]+$/,'').trim();
  base=base.replace(/\.(?:rar|zip|7z)$/i,'');
  return base.replace(/[._\- ]+$/,'').trim();
}
function cleanBinaryPackageTitle(raw){
  let title=String(raw||'').replace(/^\s*[\[({<]+|[\])}>]+\s*$/g,'').trim();
  title=title.replace(/^(?:\d{1,5}\s*(?:\/|of)\s*\d{1,5})\s*[-_. ]*/i,'');
  title=title.replace(/[._]+/g,' ').replace(/\s+-\s+/g,' - ').replace(/\s{2,}/g,' ').trim();
  title=title.replace(/^[-–— ]+|[-–— ]+$/g,'').trim();
  return title||String(raw||'Package').trim()||'Package';
}
function nameResolutionKey(a){return `${state.providerId}|${state.selectedGroup}|${articleKey(a)}`}
function filenameLooksObfuscated(filename,subject=''){
  const name=String(filename||'').replace(/^.*[\\/]/,'').trim(),rawStem=name.replace(/\.[^.]{1,8}$/,'').trim(),stem=rawStem.replace(/[._ -]+/g,'').trim();
  if(!name)return /\byenc\b/i.test(String(subject||''));
  if(/^[a-f0-9]{14,}$/i.test(stem)||/^[a-f0-9]{8}-[a-f0-9-]{18,}$/i.test(rawStem))return true;
  const compact=stem.replace(/[^a-z0-9]/gi,''),separators=(rawStem.match(/[._ -]/g)||[]).length;if(separators===0&&/^[a-z0-9]{28,}$/i.test(compact)&&(compact.match(/\d/g)||[]).length>=5)return true;
  if(compact.length>=20){const digits=(compact.match(/\d/g)||[]).length,vowels=(compact.match(/[aeiou]/gi)||[]).length;if(separators<=1&&digits>=4&&vowels/compact.length<.16)return true}
  return /(?:obfus|scrambl|random)/i.test(String(subject||''))&&/\byenc\b/i.test(String(subject||''));
}
function articleNeedsNameResolution(a,{manual=false}={}){
  if(!a)return false;const filename=String(a.media?.filename||''),deepUpgrade=!!(a.name_resolution?.confidence==='high'&&filenameLooksObfuscated(filename,a.subject)&&!a.name_resolution?.title_hint&&!a.name_resolution?.archive_checked);if(a.name_resolution?.confidence==='high'&&!deepUpgrade)return false;
  const hasRef=!!((a.segments||[]).length||a.article||a.message_id);if(!hasRef)return false;
  if(manual)return deepUpgrade||!!(filename||/\byenc\b/i.test(String(a.subject||''))||a.multipart);
  return deepUpgrade||(!filename?(/\byenc\b/i.test(String(a.subject||''))||!!a.multipart):filenameLooksObfuscated(filename,a.subject));
}
function nameResolutionCandidates({manual=false,limit=8}={}){
  const out=[];for(const a of state.articles){const key=nameResolutionKey(a);if(state.nameResolutionAttempted.has(key)||!articleNeedsNameResolution(a,{manual}))continue;out.push(a);if(out.length>=limit)break}return out;
}
function coalesceResolvedMultipartArticles(articles){
  const buckets=new Map(),passthrough=[];for(const a of articles){const mp=a?.multipart,filename=String(a?.media?.filename||'').trim(),segments=a?.segments||[];if(!a?.name_resolution||!mp||!filename||segments.length!==1){passthrough.push(a);continue}const key=`${articleGroup(a)}|${String(a.from||'').toLocaleLowerCase()}|${filename.toLocaleLowerCase()}|${Number(mp.total||0)}`;if(!buckets.has(key))buckets.set(key,[]);buckets.get(key).push(a)}
  const merged=[...passthrough];for(const members of buckets.values()){members.sort((a,b)=>Number(b.article||0)-Number(a.article||0));let current=[],seen=new Set(),lastTs=0;const flush=()=>{if(!current.length)return;if(current.length===1){merged.push(current[0]);current=[];seen=new Set();lastTs=0;return}const ordered=[...current].sort((a,b)=>Number(a.multipart?.part||1)-Number(b.multipart?.part||1)),first=ordered[0],total=Math.max(...ordered.map(a=>Number(a.multipart?.total||1))),parts=[...new Set(ordered.map(a=>Number(a.multipart?.part||1)))].sort((a,b)=>a-b),segments=ordered.flatMap(a=>(a.segments||[]).map(seg=>({...seg,part:Number(a.multipart?.part||seg.part||1)})));merged.push({...first,article:Math.max(...ordered.map(a=>Number(a.article||0))),segments,segment_count:parts.length,segment_total:total,complete:parts.length===total&&parts.every((n,i)=>n===i+1),bytes:ordered.reduce((n,a)=>n+Number(a.bytes||0),0),name_resolution:ordered.find(a=>a.name_resolution?.title_hint)?.name_resolution||first.name_resolution});current=[];seen=new Set();lastTs=0};for(const a of members){const part=Number(a.multipart?.part||1),ts=Date.parse(a.date||'');const repeat=seen.has(part),gap=lastTs&&Number.isFinite(ts)&&Math.abs(lastTs-ts)>36*60*60*1000;if(repeat||gap)flush();current.push(a);seen.add(part);if(Number.isFinite(ts))lastTs=ts}flush()}return merged;
}
function applyNameResolutionResults(results){
  const byKey=new Map((results||[]).filter(r=>r?.resolved&&r.media?.filename).map(r=>[String(r.client_key||''),r]));if(!byKey.size)return 0;let changed=0;for(const a of state.articles){const r=byKey.get(articleKey(a));if(!r)continue;const before=String(a.media?.filename||'');a.media={...r.media};a.name_resolution={source:r.source||'yEnc header',confidence:r.confidence||'high',original_filename:before,title_hint:r.title_hint||'',metadata_source:r.metadata_source||'',metadata_names:Array.isArray(r.metadata_names)?r.metadata_names:[],archive_source:r.archive_source||'',archive_names:Array.isArray(r.archive_names)?r.archive_names:[],title_source:r.title_source||r.metadata_source||r.archive_source||r.source||'yEnc header',archive_checked:!!r.archive_checked};if(before!==String(r.media.filename||''))changed++}state.articles=coalesceResolvedMultipartArticles(state.articles);sortArticles(false);return changed;
}
function scheduleObfuscatedNameResolution(){
  clearTimeout(state.nameResolutionTimer);state.nameResolutionTimer=null;if(!state.selectedGroup||state.searchMode||!isAllPostsMode()||!state.groupBinarySets||state.nameResolutionInFlight||state.nameResolutionAutoRemaining<=0)return;const candidates=nameResolutionCandidates({limit:Math.min(8,state.nameResolutionAutoRemaining)});if(!candidates.length)return;state.nameResolutionTimer=setTimeout(()=>resolveObfuscatedNames({manual:false}),380);
}
async function resolveObfuscatedNames({manual=false}={}){
  if(state.nameResolutionInFlight||!state.selectedGroup)return;const limit=manual?12:Math.min(8,state.nameResolutionAutoRemaining),candidates=nameResolutionCandidates({manual,limit});if(!candidates.length){if(manual)toast('No unresolved loaded posts need a name probe.','success');return}const group=state.selectedGroup,providerId=state.providerId;for(const a of candidates)state.nameResolutionAttempted.add(nameResolutionKey(a));if(!manual)state.nameResolutionAutoRemaining=Math.max(0,state.nameResolutionAutoRemaining-candidates.length);state.nameResolutionInFlight=true;renderArticles({preserveScroll:true});try{const data=await api('/api/articles/resolve-names',{provider_id:providerId,group,items:candidates.map(a=>({client_key:articleKey(a),article:a.article,message_id:a.message_id,subject:a.subject,from:a.from,date:a.date,bytes:a.bytes,multipart:a.multipart,segments:segmentPayload(a)}))},browseRequestOptions({timeoutMs:45000,timeoutMessage:'Name resolution took too long. NewzDeck stopped waiting; you can retry the remaining posts.'}));if(group!==state.selectedGroup||providerId!==state.providerId)return;const changed=applyNameResolutionResults(data.results||[]);if(manual)toast(data.resolved?`Resolved ${Number(data.resolved).toLocaleString()} post name${Number(data.resolved)===1?'':'s'}${changed?` • ${changed.toLocaleString()} changed`:''}.`:'No additional names could be recovered from this batch.',data.resolved?'success':'');}catch(e){if(manual)toast(e.message,'error')}finally{state.nameResolutionInFlight=false;if(group===state.selectedGroup){renderArticles({preserveScroll:true});scheduleObfuscatedNameResolution()}}
}
function binaryNameResolutionInfo(members){
  const resolved=members.map(x=>x.a?.name_resolution).filter(Boolean),withHint=resolved.find(r=>r.title_hint),hint=withHint?.title_hint||'',source=withHint?.title_source||withHint?.metadata_source||withHint?.archive_source||(resolved.length?'yEnc header':'');return{resolved:resolved.length>0,hint,source};
}
function binarySetDescriptor(a){
  const filename=String(a?.media?.filename||'').replace(/^.*[\\/]/,'').trim();if(!filename)return null;
  let base='',family='',order=0,volume=false,pattern='',m=null;
  if((m=filename.match(/^(.*?)[._\- ]part0*(\d{1,5})\.rar$/i))){base=m[1];family='RAR';order=Number(m[2]);volume=true;pattern='rar_part';}
  else if((m=filename.match(/^(.*?)\.r(\d{2,3})$/i))){base=m[1];family='RAR';order=Number(m[2])+2;volume=true;pattern='rar_legacy';}
  else if((m=filename.match(/^(.*?)\.rar$/i))){base=m[1];family='RAR';order=1;pattern='rar_main';}
  else if((m=filename.match(/^(.*?)\.z(\d{2,3})$/i))){base=m[1];family='ZIP';order=Number(m[2]);volume=true;pattern='zip_split';}
  else if((m=filename.match(/^(.*?)\.zip$/i))){base=m[1];family='ZIP';order=999999;pattern='zip_main';}
  else if((m=filename.match(/^(.*?\.7z)\.(\d{3,5})$/i))){base=m[1];family='7Z';order=Number(m[2]);volume=true;pattern='7z_split';}
  else if((m=filename.match(/^(.*?)\.7z$/i))){base=m[1];family='7Z';order=1;pattern='7z_main';}
  else if((m=filename.match(/^(.*?)\.vol(\d+)[+_](\d+)\.par2$/i))){base=m[1];family='PAR2';order=Number(m[2]);volume=true;pattern='par2_volume';}
  else if((m=filename.match(/^(.*?)\.par2$/i))){base=m[1];family='PAR2';order=1;pattern='par2_main';}
  else if((m=filename.match(/^(.*?)\.(\d{3,5})$/i))){base=m[1];family='SPLIT';order=Number(m[2]);volume=true;pattern='numeric_split';}
  else if((m=filename.match(/^(.*?)\.(sfv|nfo|srr|txt)$/i))){base=m[1];family='SIDECAR';order=999998;pattern='sidecar';}
  else return null;
  base=normalizeBinarySetBase(base);if(base.length<3)return null;
  const poster=String(a.from||'').trim().toLocaleLowerCase(),normalized=base.replace(/\s+/g,' ').toLocaleLowerCase();
  return{key:`${articleGroup(a)}|${poster}|${normalized}`,base,family,order,volume,pattern,filename};
}
function binarySetFamily(group){
  const families=new Set(group.members.map(x=>x.descriptor.family));
  if(families.has('RAR'))return'RAR archive set';if(families.has('7Z'))return'7-Zip archive set';if(families.has('ZIP'))return'ZIP archive set';if(families.has('PAR2')&&families.size===1)return'PAR2 recovery set';if(families.has('SPLIT'))return'Split binary set';return'Binary package';
}
function binaryMemberRole(x){const family=x?.descriptor?.family||'';return family==='PAR2'?'parity':family==='SIDECAR'?'sidecar':'payload'}
function contiguousMissing(values,start=1){
  const nums=[...new Set(values.map(Number).filter(n=>Number.isFinite(n)&&n>=start))].sort((a,b)=>a-b);if(!nums.length)return[];const present=new Set(nums),missing=[];for(let n=start;n<=nums[nums.length-1];n++)if(!present.has(n))missing.push(n);return missing;
}
function binarySequenceHealth(group){
  const missing=[];const members=group.members||[];
  const partRar=members.filter(x=>x.descriptor.pattern==='rar_part');if(partRar.length)for(const n of contiguousMissing(partRar.map(x=>x.descriptor.order)))missing.push(`part${String(n).padStart(2,'0')}.rar`);
  const legacy=members.filter(x=>x.descriptor.pattern==='rar_legacy');if(legacy.length){const nums=legacy.map(x=>x.descriptor.order);if(!members.some(x=>x.descriptor.pattern==='rar_main'))missing.push('.rar');for(const n of contiguousMissing(nums,2))missing.push(`.r${String(n-2).padStart(2,'0')}`)}
  const zips=members.filter(x=>x.descriptor.pattern==='zip_split');if(zips.length){for(const n of contiguousMissing(zips.map(x=>x.descriptor.order)))missing.push(`.z${String(n).padStart(2,'0')}`);if(!members.some(x=>x.descriptor.pattern==='zip_main'))missing.push('.zip')}
  const seven=members.filter(x=>x.descriptor.pattern==='7z_split');if(seven.length)for(const n of contiguousMissing(seven.map(x=>x.descriptor.order)))missing.push(`.7z.${String(n).padStart(3,'0')}`);
  const split=members.filter(x=>x.descriptor.pattern==='numeric_split');if(split.length)for(const n of contiguousMissing(split.map(x=>x.descriptor.order)))missing.push(`.${String(n).padStart(3,'0')}`);
  return{missing:[...new Set(missing)]};
}
function binaryPackageHealth(group){
  const seq=binarySequenceHealth(group),members=group.members||[],incomplete=members.filter(x=>!isSelectableMedia(x.a)),payload=members.filter(x=>binaryMemberRole(x)==='payload'),parity=members.filter(x=>binaryMemberRole(x)==='parity'),sidecars=members.filter(x=>binaryMemberRole(x)==='sidecar'),hasPar2=parity.length>0;
  let level='good',label='Likely complete',detail='All loaded package files are complete and no internal archive-volume gaps were detected.';
  if(seq.missing.length){level='bad';label=`Missing ${seq.missing.length} volume${seq.missing.length===1?'':'s'}`;detail=`Detected archive gap${seq.missing.length===1?'':'s'}: ${seq.missing.slice(0,6).join(', ')}${seq.missing.length>6?'…':''}`;}
  else if(incomplete.length){level=hasPar2?'warn':'bad';label=hasPar2?'Incomplete • PAR2 present':'Incomplete articles';detail=`${incomplete.length} loaded file${incomplete.length===1?' is':'s are'} missing one or more Usenet segments${hasPar2?'; PAR2 recovery files are present in the package.':'.'}`;}
  else if(!payload.length){level='neutral';label='Recovery files';detail='This set contains recovery or sidecar files but no archive payload is loaded yet.';}
  if(group.structural&&group.structuralConfidence==='medium'&&!seq.missing.length&&!incomplete.length&&payload.length){level='warn';label='Probable package';detail=`${group.structuralReason||'Posting structure suggests these files belong together'}. Expand the package to verify before queueing.`;}
  return{level,label,detail,missing:seq.missing,incomplete,payload,parity,sidecars,hasPar2,queueReady:!seq.missing.length&&!incomplete.length&&payload.length>0&&!(group.structural&&group.structuralConfidence==='medium')};
}
function partitionBinaryBucket(members){
  const ordered=[...members].sort((x,y)=>Number(y.a.article||0)-Number(x.a.article||0)),parts=[];let current=[],seen=new Set(),previousTs=0;
  const flush=()=>{if(current.length)parts.push(current);current=[];seen=new Set();previousTs=0};
  for(const x of ordered){const filename=x.descriptor.filename.toLocaleLowerCase(),ts=Date.parse(x.a.date||'');const repeated=seen.has(filename),largeGap=previousTs&&Number.isFinite(ts)&&Math.abs(previousTs-ts)>36*60*60*1000;if(repeated||largeGap)flush();current.push(x);seen.add(filename);if(Number.isFinite(ts))previousTs=ts;}
  flush();return parts;
}
function structuralFileOrdinal(a){
  const subject=String(a?.subject||''),filename=String(a?.media?.filename||''),cut=filename?subject.toLocaleLowerCase().indexOf(filename.toLocaleLowerCase()):-1,prefix=cut>=0?subject.slice(0,cut):subject.split(/\byenc\b/i)[0];
  const rx=/(?:\(|\[|\b)(\d{1,5})\s*(?:\/|of)\s*(\d{1,5})(?:\)|\]|\b)/ig,matches=[];let m;while((m=rx.exec(prefix))){const part=Number(m[1]),total=Number(m[2]);if(part>0&&part<=total&&total>1&&total<=10000)matches.push({part,total})}return matches.length?matches[0]:null;
}
function structuralBinaryDescriptor(a){
  const explicit=binarySetDescriptor(a);if(explicit)return explicit;const filename=String(a?.media?.filename||'').replace(/^.*[\\/]/,'').trim();if(!filename)return null;const ext=(filename.match(/\.([^.]+)$/)||[])[1]?.toLocaleLowerCase()||'',family=ext==='par2'?'PAR2':['sfv','nfo','srr','txt'].includes(ext)?'SIDECAR':ext==='rar'||/^r\d{2,3}$/.test(ext)?'RAR':ext==='zip'||/^z\d{2,3}$/.test(ext)?'ZIP':ext==='7z'?'7Z':/^\d{3,5}$/.test(ext)?'SPLIT':'FILE';return{key:'',base:filename,family,order:0,volume:false,pattern:'structural',filename};
}
function structuralSizePattern(members){
  const sizes=members.map(x=>Number(x.a.bytes||0)).filter(n=>n>=1024*1024).sort((a,b)=>a-b);if(sizes.length<3)return false;const median=sizes[Math.floor(sizes.length/2)]||1,similar=sizes.filter(n=>n/median>=.72&&n/median<=1.28).length;return similar/Math.max(1,sizes.length)>=.65;
}
function makeStructuralGroup(members,positionByIndex,{confidence='high',reason='Posting structure'}={}){
  members=[...members].sort((x,y)=>Number(y.a.article||0)-Number(x.a.article||0));const newest=members[0],firstPosition=Math.min(...members.map(x=>positionByIndex.get(x.index)??Number.MAX_SAFE_INTEGER)),nameResolution=binaryNameResolutionInfo(members),hint=nameResolution.hint||'';
  const title=hint?cleanBinaryPackageTitle(hint):'Obfuscated package',poster=String(newest?.a?.from||'').toLocaleLowerCase(),key=`structural|${articleGroup(newest.a)}|${poster}|${Number(newest.a.article||0)}|${members.length}`;
  const group={key,base:title,displayTitle:title,nameResolution,members,firstPosition,newest,bytes:members.reduce((n,x)=>n+Number(x.a.bytes||0),0),structural:true,structuralConfidence:confidence,structuralReason:reason};group.health=binaryPackageHealth(group);return group;
}
function buildStructuralBinarySets(items,usedKeys,positionByIndex){
  const candidates=[];for(const item of items){const a=item.a,key=articleKey(a);if(usedKeys.has(key)||!a?.media)continue;const filename=String(a.media.filename||''),hint=String(a.name_resolution?.title_hint||'');if(!hint&&!filenameLooksObfuscated(filename,a.subject))continue;const descriptor=structuralBinaryDescriptor(a);if(!descriptor)continue;candidates.push({...item,descriptor});}
  const groups=[],consumed=new Set();
  const hintBuckets=new Map();for(const x of candidates){const hint=String(x.a.name_resolution?.title_hint||'').trim();if(!hint)continue;const poster=String(x.a.from||'').trim().toLocaleLowerCase(),normalized=hint.replace(/[._ -]+/g,' ').trim().toLocaleLowerCase();const key=`${articleGroup(x.a)}|${poster}|${normalized}`;if(!hintBuckets.has(key))hintBuckets.set(key,[]);hintBuckets.get(key).push(x)}
  for(const members of hintBuckets.values()){for(const part of partitionBinaryBucket(members)){if(part.length<2)continue;const group=makeStructuralGroup(part,positionByIndex,{confidence:'high',reason:'Matching recovered archive/metadata title'});groups.push(group);for(const x of part)consumed.add(articleKey(x.a));}}
  const posterBuckets=new Map();for(const x of candidates){if(consumed.has(articleKey(x.a)))continue;const poster=String(x.a.from||'').trim().toLocaleLowerCase();if(!poster)continue;if(!posterBuckets.has(poster))posterBuckets.set(poster,[]);posterBuckets.get(poster).push(x)}
  for(const members of posterBuckets.values()){
    members.sort((x,y)=>Number(y.a.article||0)-Number(x.a.article||0));let current=[];
    const flush=()=>{if(current.length<3){current=[];return}const ordinals=current.map(x=>structuralFileOrdinal(x.a)).filter(Boolean),totals=new Map();for(const o of ordinals)totals.set(o.total,(totals.get(o.total)||0)+1);const bestTotal=[...totals.entries()].sort((a,b)=>b[1]-a[1])[0],ordinalStrong=!!bestTotal&&bestTotal[1]>=Math.max(2,Math.ceil(current.length*.5));const archiveSignals=current.filter(x=>['RAR','ZIP','7Z','SPLIT','PAR2'].includes(x.descriptor.family)).length,sizeStrong=structuralSizePattern(current);if(ordinalStrong||(current.length>=4&&archiveSignals>=Math.ceil(current.length*.6)&&sizeStrong)){const confidence=ordinalStrong?'high':'medium',reason=ordinalStrong?`Matching file counters (${bestTotal[0]} files)`:'Tight posting sequence with matching binary sizes';groups.push(makeStructuralGroup(current,positionByIndex,{confidence,reason}));for(const x of current)consumed.add(articleKey(x.a));}current=[]};
    let prev=null;for(const x of members){if(!prev){current=[x];prev=x;continue}const ts=Date.parse(x.a.date||''),pts=Date.parse(prev.a.date||''),timeGap=Number.isFinite(ts)&&Number.isFinite(pts)?Math.abs(pts-ts):0,articleGap=Math.abs(Number(prev.a.article||0)-Number(x.a.article||0)),sameWindow=(!timeGap||timeGap<=90*1000)&&articleGap<=800;if(!sameWindow)flush();current.push(x);prev=x}flush();
  }
  return groups;
}
function buildBinarySets(items){
  const buckets=new Map(),descriptorByKey=new Map(),positionByIndex=new Map(items.map((item,pos)=>[item.index,pos])),usedKeys=new Set();
  for(const item of items){const descriptor=binarySetDescriptor(item.a);if(!descriptor)continue;descriptorByKey.set(articleKey(item.a),descriptor);if(!buckets.has(descriptor.key))buckets.set(descriptor.key,[]);buckets.get(descriptor.key).push({...item,descriptor});}
  const groups=[];for(const[bucketKey,bucketMembers]of buckets){for(const members of partitionBinaryBucket(bucketMembers)){if(members.length<2||!members.some(x=>binaryMemberRole(x)==='payload'&&x.descriptor.volume))continue;members.sort((x,y)=>(x.descriptor.order-y.descriptor.order)||Number(y.a.article||0)-Number(x.a.article||0));const firstPosition=Math.min(...members.map(x=>positionByIndex.get(x.index)??Number.MAX_SAFE_INTEGER));const newest=members.reduce((best,x)=>Number(x.a.article||0)>Number(best.a.article||0)?x:best,members[0]);const base=members[0].descriptor.base,key=`${bucketKey}|${Number(newest.a.article||0)}`,nameResolution=binaryNameResolutionInfo(members);const group={key,base,displayTitle:cleanBinaryPackageTitle(nameResolution.hint||base),nameResolution,members,firstPosition,newest,bytes:members.reduce((n,x)=>n+Number(x.a.bytes||0),0)};group.health=binaryPackageHealth(group);groups.push(group);for(const x of members)usedKeys.add(articleKey(x.a));}}
  for(const group of buildStructuralBinarySets(items,usedKeys,positionByIndex)){groups.push(group);for(const x of group.members)descriptorByKey.set(articleKey(x.a),x.descriptor)}
  groups.sort((a,b)=>a.firstPosition-b.firstPosition);return{groups,descriptorByKey};
}

function binarySetSelectionState(group){const selectable=group.members.filter(x=>isSelectableMedia(x.a)),selected=selectable.filter(x=>state.selectedItems.has(articleKey(x.a))).length;return{selectable,selected,all:!!selectable.length&&selected===selectable.length,partial:selected>0&&selected<selectable.length};}
function binaryPackageExpandedMarkup(group){
  const h=group.health||binaryPackageHealth(group),missing=h.missing.length?`<span class="binary-package-warning"><b>Missing</b> ${escapeHtml(h.missing.slice(0,8).join(', '))}${h.missing.length>8?'…':''}</span>`:'';
  const resolved=group.nameResolution?.resolved?`<span class="binary-package-name-source"><b>Name source</b> ${escapeHtml(group.nameResolution.source||'yEnc header')}</span>`:'',structural=group.structural?`<span class="binary-package-name-source"><b>Grouping</b> ${escapeHtml(group.structuralReason||'Posting structure')} • ${escapeHtml(group.structuralConfidence||'probable')} confidence</span>`:'';
  return `<div class="binary-package-details"><span><b>Payload</b> ${h.payload.length.toLocaleString()}</span><span><b>PAR2</b> ${h.parity.length.toLocaleString()}</span><span><b>Sidecars</b> ${h.sidecars.length.toLocaleString()}</span><span><b>Header complete</b> ${(group.members.length-h.incomplete.length).toLocaleString()}/${group.members.length.toLocaleString()}</span>${resolved}${structural}${missing}<span class="binary-package-health-note ${h.level}">${escapeHtml(h.detail)}</span></div>`;
}
function binarySetRowMarkup(group){
  const sel=binarySetSelectionState(group),expanded=state.expandedBinarySets.has(group.key),health=group.health||binaryPackageHealth(group),poster=group.newest?.a?.from||'',date=group.newest?.a?.date||'',downloaded=group.members.filter(x=>state.downloadedIndex.has(itemDownloadKey(x.a))).length,queued=group.members.filter(x=>state.queuedIndex.has(itemDownloadKey(x.a))).length;
  const status=downloaded===group.members.length?'<span class="binary-set-state done">✓ Downloaded</span>':queued?`<span class="binary-set-state">⇣ ${queued}/${group.members.length} queued</span>`:'',resolved=group.nameResolution?.resolved?`<span class="binary-name-resolved" title="Recovered from ${escapeHtml(group.nameResolution.source||'yEnc header')}">✓ NAME RESOLVED</span>`:'',structural=group.structural?`<span class="binary-name-resolved" title="${escapeHtml(group.structuralReason||'Connected by posting structure')}">STRUCTURAL MATCH</span>`:'';
  const queueTitle=health.queueReady?'Add every loaded file in this package to the download queue':health.detail;
  return `<div class="binary-set-wrap ${expanded?'expanded':''}" data-binary-set-wrap="${escapeHtml(group.key)}"><div class="binary-set-row ${sel.all?'selected':''} ${sel.partial?'partial':''}" data-binary-set-key="${escapeHtml(group.key)}" aria-selected="${sel.all?'true':'false'}"><button class="binary-set-expand" type="button" title="${expanded?'Collapse':'Show'} package files">${expanded?'▾':'▸'}</button><span class="binary-set-icon">▰</span><div class="binary-set-main"><div class="binary-set-title"><span class="media-chip archive">PACKAGE</span><strong title="${escapeHtml(group.base)}">${escapeHtml(group.displayTitle)}</strong><span class="binary-set-count">${group.members.length.toLocaleString()} files</span><span class="binary-health ${health.level}" title="${escapeHtml(health.detail)}">${health.level==='good'?'✓':health.level==='bad'?'!':health.level==='warn'?'⚠':'•'} ${escapeHtml(health.label)}</span>${status}</div><div class="binary-set-meta"><span>${escapeHtml(binarySetFamily(group))}</span><span>${formatBytes(group.bytes)}</span><span>${shortDate(date)}</span>${health.hasPar2?'<span class="parity-meta">PAR2</span>':''}${resolved}${structural}<span class="poster">${escapeHtml(poster)}</span></div></div><button class="binary-set-select mini-btn" type="button">${sel.all?'✓ Selected':sel.partial?`${sel.selected}/${sel.selectable.length} selected`:'Select package'}</button><button class="binary-set-queue" type="button" ${health.queueReady?'':'disabled'} title="${escapeHtml(queueTitle)}">＋ Download</button></div>${expanded?`${binaryPackageExpandedMarkup(group)}<div class="binary-set-members">${group.members.map(x=>articleRowMarkup(x.a,x.index,{member:true})).join('')}</div>`:''}</div>`;
}
function articleRowMarkup(a,index,{member=false}={}){
  const media=a.media,key=articleKey(a),selected=state.selectedItems.has(key),dkey=itemDownloadKey(a),downloaded=!!media&&state.downloadedIndex.has(dkey),queued=!!media&&state.queuedIndex.has(dkey),binaryMode=isAllPostsMode(),fragment=isUnresolvedMultipartFragment(a),queueable=!fragment&&isSelectableMedia(a);
  const ext=String(media?.extension||'').toUpperCase(),opaque=!!a.opaque_multipart,chip=media?`<span class="media-chip ${media.kind}">${escapeHtml(binaryMode&&ext?ext:media.kind.toUpperCase())}</span>`:opaque?'<span class="media-chip archive">BINARY</span>':'<span class="media-chip file">POST</span>';
  const comp=Number(a.segment_total||0)>1?`<span class="completion ${a.complete?'':'incomplete'}">${Number(a.segment_count||0).toLocaleString()}/${Number(a.segment_total||0).toLocaleString()} segments</span>`:'';const check=queueable&&selected?'<span class="row-selection-check" aria-hidden="true">✓</span>':'';const dl=downloaded?'<span class="completion">✓ Downloaded</span>':queued?'<span class="completion">⇣ Queued</span>':'';
  const filename=String(media?.filename||'').trim(),opaqueTitle=opaque?(a.complete?'Obfuscated multipart binary':'Incomplete multipart binary'):'',primary=binaryMode&&filename?filename:(opaqueTitle||a.subject||filename||'Post'),secondary=binaryMode&&String(a.subject||'').trim()&&String(a.subject||'').trim()!==primary?`<small title="${escapeHtml(a.subject||'')}">${escapeHtml(a.subject||'')}</small>`:'',resolved=a.name_resolution?`<span class="name-resolved-chip" title="Recovered from ${escapeHtml(a.name_resolution.title_source||a.name_resolution.metadata_source||a.name_resolution.archive_source||a.name_resolution.source||'yEnc header')}">✓ Resolved</span>`:'';
  const action=binaryMode&&!member?(queueable?`<button class="article-row-download mini-btn" type="button" data-index="${index}" title="Add this binary to the download queue">＋ Download</button>`:(fragment?'<span class="binary-row-incomplete">Unresolved fragment</span>':opaque&&a.complete?'<span class="binary-row-pending">Resolving name…</span>':!a.complete?'<span class="binary-row-incomplete">Incomplete</span>':'')):'';
  return `<div class="article-row ${member?'binary-set-member':''} ${articleStatusClass(a)} ${queueable?'selectable':''} ${selected?'selected':''} ${state.selectedArticleKey===key?'active keyboard-active':''}" data-index="${index}" data-download-key="${escapeHtml(dkey)}" aria-selected="${selected?'true':'false'}" title="${queueable?'Click to select • Ctrl-click toggles • Shift-click selects a range':'Click to inspect'}"><div class="article-top">${chip}<div class="article-subject"><span title="${escapeHtml(primary)}">${escapeHtml(primary)}</span>${secondary}</div>${resolved}${articleStatusBadge(a)}${check}${action}</div><div class="article-meta"><span>${shortDate(a.date)}</span><span>${formatBytes(a.bytes)}</span><span class="poster">${escapeHtml(a.from)}</span>${opaque?`<span class="opaque-grouping">Grouped by ${escapeHtml(a.opaque_grouping||'yEnc part counter')}</span>`:''}${comp}${dl}</div></div>`;
}
function renderBinarySetPreview(group){
  if(!group)return;const sel=binarySetSelectionState(group),health=group.health||binaryPackageHealth(group),names=group.members.slice(0,8).map(x=>x.a.media?.filename||x.a.subject||'File');els.previewBadge.className='preview-badge active';els.previewBadge.textContent='BINARY PACKAGE';els.previewContent.className='preview-content';els.previewContent.innerHTML=`<div class="preview-details binary-set-preview"><h3>${escapeHtml(group.displayTitle||group.base)}</h3><div class="preview-meta-grid"><div class="meta-card"><label>Package</label><b>${escapeHtml(binarySetFamily(group))}</b></div><div class="meta-card"><label>Files</label><b>${group.members.length.toLocaleString()}</b></div><div class="meta-card"><label>Total size</label><b>${formatBytes(group.bytes)}</b></div><div class="meta-card"><label>Health</label><b>${escapeHtml(health.label)}</b></div></div><div class="binary-set-preview-files">${names.map(n=>`<span>${escapeHtml(n)}</span>`).join('')}${group.members.length>names.length?`<em>+ ${(group.members.length-names.length).toLocaleString()} more files</em>`:''}</div><button id="selectPreviewBinarySet" class="preview-action">${sel.all?'Clear package selection':'Select complete package'}</button><button id="downloadPreviewBinarySet" class="preview-download" ${health.queueReady?'':'disabled'}>＋ Add package to queue</button><p class="preview-note">${escapeHtml(health.detail)} Package health is based on headers currently loaded in this newsgroup and can improve as older headers are loaded.</p></div>`;$('selectPreviewBinarySet')?.addEventListener('click',()=>toggleBinarySetSelection(group));$('downloadPreviewBinarySet')?.addEventListener('click',e=>downloadItems(group.members.map(x=>x.a),e.currentTarget));
}
function toggleBinarySetSelection(group){const sel=binarySetSelectionState(group),clear=sel.all;for(const x of sel.selectable){const key=articleKey(x.a);if(clear)state.selectedItems.delete(key);else state.selectedItems.set(key,x.a)}if(!clear&&sel.selectable.length)state.selectionAnchorKey=articleKey(sel.selectable[0].a);updateSelectionBar();updateSelectionDomInPlace();renderBinarySetPreview(group);}
function wireArticleRows(root=els.articlesList){root.querySelectorAll('.article-row').forEach(r=>{r.onclick=e=>{if(e.target.closest('button'))return;handleMediaSelectionClick(Number(r.dataset.index),e)};r.ondblclick=e=>{const a=state.articles[Number(r.dataset.index)];if(['image','video'].includes(a?.media?.kind)&&a.complete){e.preventDefault();openMediaViewer(a)}};r.oncontextmenu=e=>{e.preventDefault();const a=state.articles[Number(r.dataset.index)];if(!a)return;showContextMenu(e.clientX,e.clientY,[{label:'Preview / details',action:()=>{handleMediaSelectionClick(Number(r.dataset.index),e);renderPreviewDetails(a,true)}},{label:'Add to download queue',disabled:!isSelectableMedia(a),action:()=>downloadItems([a])},{separator:true},{label:isArticleSeen(a)?'Mark post unseen':'Mark post seen',action:()=>setArticlesSeen([a],!isArticleSeen(a),{toastResult:true})},{separator:true},{label:'Copy filename',action:()=>copyText(a.media?.filename||a.subject)},{label:'Copy subject',action:()=>copyText(a.subject||'')},{label:'Copy Message-ID',action:()=>copyText(a.message_id||'')},{separator:true},{label:isPosterBlocked(a)?'Unmute this poster':'Mute this poster',action:()=>mutePoster(a.from)},{label:'Filter to this poster',action:()=>{state.articleSearchTerm=`from:${a.from}`;els.articleSearch.value=state.articleSearchTerm;renderArticles()}},{label:'Show details',action:()=>{state.selectedArticleKey=articleKey(a);renderPreviewDetails(a,false)}}])}});root.querySelectorAll('.article-row-download').forEach(btn=>btn.onclick=e=>{e.stopPropagation();const a=state.articles[Number(btn.dataset.index)];if(a)downloadItems([a],btn)});}
function isUnresolvedMultipartFragment(a){
  const mp=a?.multipart||{},total=Math.max(Number(mp.total||0),Number(a?.segment_total||0)),count=Number(a?.segment_count||0);
  if(a?.multipart_fragment)return true;
  return total>1&&!a?.opaque_multipart&&count<=1&&!a?.media&&/\byenc\b/i.test(String(a?.subject||''));
}
function binaryDisplayUnitInfo(unit){
  if(unit.type==='group'){
    const h=unit.group.health||binaryPackageHealth(unit.group),a=unit.group.newest?.a||{};
    return{queueReady:!!h.queueReady,pending:false,incomplete:!h.queueReady,date:Date.parse(a.date||'')||Number(a.article||0),size:Number(unit.group.bytes||0),name:String(unit.group.displayTitle||unit.group.base||''),files:Number(unit.group.members?.length||0),health:h.level==='good'?0:h.level==='warn'?1:h.level==='neutral'?2:3};
  }
  const a=unit.item.a,fragment=isUnresolvedMultipartFragment(a),queueReady=!fragment&&isSelectableMedia(a),pending=!!(!fragment&&a.complete&&!a.media&&articleNeedsNameResolution(a)&&!state.nameResolutionAttempted.has(nameResolutionKey(a)));
  return{queueReady,pending,incomplete:fragment||(!queueReady&&!pending),fragment,date:Date.parse(a.date||'')||Number(a.article||0),size:Number(a.bytes||0),name:String(a.media?.filename||a.subject||''),files:1,health:queueReady?0:pending?1:3};
}
function binaryMinimumBytes(){const value=Math.max(0,Number(state.binaryMinSizeValue||0)),unit=String(state.binaryMinSizeUnit||'MB').toUpperCase();return value*(unit==='GB'?1024*1024*1024:1024*1024)}
function binaryDisplayUnitPassesStatus(unit){const info=binaryDisplayUnitInfo(unit),mode=state.binaryPackageFilter||'downloadable';if(mode==='all')return true;if(mode==='incomplete')return info.incomplete;return info.queueReady||info.pending}
function binaryDisplayUnitVisible(unit){const info=binaryDisplayUnitInfo(unit);return binaryDisplayUnitPassesStatus(unit)&&info.size>=binaryMinimumBytes()}
function sortBinaryDisplayUnits(units){
  const mode=state.binaryPackageSort||'newest',text=v=>String(v||'').toLocaleLowerCase();return [...units].sort((x,y)=>{const a=binaryDisplayUnitInfo(x),b=binaryDisplayUnitInfo(y);if(mode==='oldest')return a.date-b.date;if(mode==='largest')return b.size-a.size||b.date-a.date;if(mode==='smallest')return a.size-b.size||b.date-a.date;if(mode==='name')return text(a.name).localeCompare(text(b.name))||b.date-a.date;if(mode==='files')return b.files-a.files||b.size-a.size;if(mode==='health')return a.health-b.health||b.date-a.date;return b.date-a.date});
}
function binaryBrowserControlsMarkup(){
  const f=state.binaryPackageFilter||'downloadable',s=state.binaryPackageSort||'newest',v=Math.max(0,Number(state.binaryMinSizeValue||0)),u=['MB','GB'].includes(state.binaryMinSizeUnit)?state.binaryMinSizeUnit:'MB';return `<div class="binary-summary-controls"><label>Show <select class="binary-package-filter"><option value="downloadable" ${f==='downloadable'?'selected':''}>Downloadable</option><option value="all" ${f==='all'?'selected':''}>All</option><option value="incomplete" ${f==='incomplete'?'selected':''}>Incomplete only</option></select></label><label class="binary-summary-min-size" title="Only show reconstructed binaries and packages at or above this total size. 0 disables the cutoff.">Min size <span class="binary-min-size-wrap"><input class="binary-package-min-size" aria-label="Minimum browse size" inputmode="decimal" min="0" max="1000000" step="0.1" type="number" value="${escapeHtml(String(v))}"/><select class="binary-package-min-unit" aria-label="Minimum browse size unit"><option value="MB" ${u==='MB'?'selected':''}>MB</option><option value="GB" ${u==='GB'?'selected':''}>GB</option></select></span></label><label>Sort <select class="binary-package-sort"><option value="newest" ${s==='newest'?'selected':''}>Newest</option><option value="oldest" ${s==='oldest'?'selected':''}>Oldest</option><option value="largest" ${s==='largest'?'selected':''}>Largest</option><option value="smallest" ${s==='smallest'?'selected':''}>Smallest</option><option value="name" ${s==='name'?'selected':''}>Name A–Z</option><option value="files" ${s==='files'?'selected':''}>Most files</option><option value="health" ${s==='health'?'selected':''}>Best health</option></select></label></div>`;
}
function renderList(items){
  state.binarySetGroups.clear();let body='';
  if(isAllPostsMode()&&state.groupBinarySets){
    const built=buildBinarySets(items),groupMemberKeys=new Set(),units=[];for(const group of built.groups){state.binarySetGroups.set(group.key,group);for(const x of group.members)groupMemberKeys.add(articleKey(x.a));units.push({type:'group',group})}for(const item of items){if(!groupMemberKeys.has(articleKey(item.a)))units.push({type:'article',item})}
    const sorted=sortBinaryDisplayUnits(units),visible=sorted.filter(binaryDisplayUnitVisible),queueable=units.filter(u=>binaryDisplayUnitInfo(u).queueReady).length,pending=units.filter(u=>binaryDisplayUnitInfo(u).pending).length,incomplete=units.filter(u=>binaryDisplayUnitInfo(u).incomplete).length,fragments=units.filter(u=>binaryDisplayUnitInfo(u).fragment).length,statusVisible=units.filter(binaryDisplayUnitPassesStatus),statusHidden=units.length-statusVisible.length,sizeHidden=statusVisible.filter(u=>binaryDisplayUnitInfo(u).size<binaryMinimumBytes()).length,obfuscated=items.filter(({a})=>articleNeedsNameResolution(a)).length;
    const resolver=`<button class="binary-resolve-btn mini-btn" type="button" ${state.nameResolutionInFlight?'disabled':''}>${state.nameResolutionInFlight?'Resolving names…':obfuscated?`Resolve names (${obfuscated.toLocaleString()})`:'Resolve more names'}</button>`,scan=state.smartBinaryHeaders?` • ${state.smartBinaryHeaders.toLocaleString()} raw headers scanned`:'';
    body=`<div class="binary-list-summary"><div class="binary-summary-copy"><strong>${queueable.toLocaleString()} downloadable item${queueable===1?'':'s'}</strong><span>${built.groups.length.toLocaleString()} release package${built.groups.length===1?'':'s'} • ${pending.toLocaleString()} resolving • ${incomplete.toLocaleString()} incomplete${fragments?` • ${fragments.toLocaleString()} unresolved segment fragment${fragments===1?'':'s'}`:''}${statusHidden?` • ${statusHidden.toLocaleString()} hidden by Show`:''}${sizeHidden?` • ${sizeHidden.toLocaleString()} below ${escapeHtml(formatBytes(binaryMinimumBytes()))}`:''}${scan}</span></div>${binaryBrowserControlsMarkup()}${resolver}</div>`+(visible.length?visible.map(u=>u.type==='group'?binarySetRowMarkup(u.group):articleRowMarkup(u.item.a,u.item.index)).join(''):`<div class="binary-filter-empty"><strong>No ${state.binaryPackageFilter==='incomplete'?'incomplete':'downloadable'} binaries in this scanned range.</strong><span>${incomplete&&state.binaryPackageFilter==='downloadable'?`${incomplete.toLocaleString()} incomplete/unresolved item${incomplete===1?' is':'s are'} hidden while NewzDeck continues reconstruction. Change Show to All or Incomplete only when you want diagnostics.`:'Load older headers or change the filter.'}</span></div>`);
  }else if(isAllPostsMode()){
    const resolver=`<button class="binary-resolve-btn mini-btn" type="button" ${state.nameResolutionInFlight?'disabled':''}>${state.nameResolutionInFlight?'Resolving names…':'Resolve names'}</button>`;body=`<div class="binary-list-summary raw"><strong>Raw posts</strong><span>${items.length.toLocaleString()} grouped header item${items.length===1?'':'s'} • Raw mode exposes incomplete fragments for troubleshooting</span>${resolver}</div>`+items.map(({a,index})=>articleRowMarkup(a,index)).join('');
  }else body=items.map(({a,index})=>articleRowMarkup(a,index)).join('');
  els.articlesList.innerHTML=body+continuousSentinelMarkup();wireArticleRows();
  els.articlesList.querySelector('.binary-package-filter')?.addEventListener('change',e=>{state.binaryPackageFilter=e.currentTarget.value;captureCurrentGroupState();renderArticles({preserveScroll:false})});els.articlesList.querySelector('.binary-package-sort')?.addEventListener('change',e=>{state.binaryPackageSort=e.currentTarget.value;captureCurrentGroupState();renderArticles({preserveScroll:false})});const packageMinInput=els.articlesList.querySelector('.binary-package-min-size'),packageMinUnit=els.articlesList.querySelector('.binary-package-min-unit'),applyPackageMinSize=()=>{const value=Math.max(0,Math.min(1000000,Number(packageMinInput?.value||0)||0));state.binaryMinSizeValue=value;state.binaryMinSizeUnit=['MB','GB'].includes(packageMinUnit?.value)?packageMinUnit.value:'MB';saveUiSettings();renderArticles({preserveScroll:false})};packageMinInput?.addEventListener('change',applyPackageMinSize);packageMinInput?.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();e.currentTarget.blur()}});packageMinUnit?.addEventListener('change',applyPackageMinSize);
  els.articlesList.querySelectorAll('.binary-set-row').forEach(row=>{const group=state.binarySetGroups.get(row.dataset.binarySetKey);if(!group)return;row.onclick=e=>{if(e.target.closest('button'))return;toggleBinarySetSelection(group)};row.ondblclick=e=>{if(e.target.closest('button'))return;e.preventDefault();if(state.expandedBinarySets.has(group.key))state.expandedBinarySets.delete(group.key);else state.expandedBinarySets.add(group.key);renderArticles({preserveScroll:true})};row.oncontextmenu=e=>{e.preventDefault();const health=group.health||binaryPackageHealth(group);showContextMenu(e.clientX,e.clientY,[{label:'Select entire package',action:()=>{for(const x of group.members.filter(x=>isSelectableMedia(x.a)))state.selectedItems.set(articleKey(x.a),x.a);updateSelectionBar();updateSelectionDomInPlace();renderBinarySetPreview(group)}},{label:'Add package to download queue',disabled:!health.queueReady,action:()=>downloadItems(group.members.map(x=>x.a))},{label:state.expandedBinarySets.has(group.key)?'Collapse package files':'Show package files',action:()=>{if(state.expandedBinarySets.has(group.key))state.expandedBinarySets.delete(group.key);else state.expandedBinarySets.add(group.key);renderArticles({preserveScroll:true})}},{separator:true},{label:'Mark package seen',action:()=>setArticlesSeen(group.members.map(x=>x.a),true,{toastResult:true})}] )};row.querySelector('.binary-set-expand').onclick=e=>{e.stopPropagation();if(state.expandedBinarySets.has(group.key))state.expandedBinarySets.delete(group.key);else state.expandedBinarySets.add(group.key);renderArticles({preserveScroll:true})};row.querySelector('.binary-set-select').onclick=e=>{e.stopPropagation();toggleBinarySetSelection(group)};row.querySelector('.binary-set-queue').onclick=e=>{e.stopPropagation();downloadItems(group.members.map(x=>x.a),e.currentTarget)};});els.articlesList.querySelector('.binary-resolve-btn')?.addEventListener('click',()=>resolveObfuscatedNames({manual:true}));updateNewContentBoundaryDom();scheduleObfuscatedNameResolution();
}

function thumbnailTaskKey(index,pkey,role='item',generation=state.galleryGeneration){return `${generation}|${role}|${index}|${pkey}`}
function thumbnailHolderRegistryKey(index,role='item',generation=state.galleryGeneration){return `${generation}|${role}|${index}`}
function registerThumbnailHolderNode(node,index=null,role=null){
  if(!node)return null;const resolvedIndex=index==null?Number(node.dataset.thumbIndex??node.dataset.thumbImageIndex):Number(index);const resolvedRole=role||node.dataset.thumbRole||'item';if(!Number.isFinite(resolvedIndex))return node;node.dataset.thumbRole=resolvedRole;state.thumbHolderRegistry.set(thumbnailHolderRegistryKey(resolvedIndex,resolvedRole),node);return node;
}
function unregisterThumbnailHolder(index,role='item'){state.thumbHolderRegistry.delete(thumbnailHolderRegistryKey(index,role))}
function rebuildThumbnailHolderRegistry(root=els.articlesList,{clear=true}={}){
  if(clear)state.thumbHolderRegistry.clear();root?.querySelectorAll?.('[data-thumb-index],img.thumb-img[data-thumb-image-index]').forEach(node=>registerThumbnailHolderNode(node));
}
function thumbnailHolder(index,role='item'){
  const key=thumbnailHolderRegistryKey(index,role),cached=state.thumbHolderRegistry.get(key);if(cached?.isConnected){state.thumbHolderRegistryStats.hits++;return cached}if(cached)state.thumbHolderRegistry.delete(key);
  state.thumbHolderRegistryStats.fallbacks++;const safeRole=String(role).replace(/"/g,'\\"');const node=els.articlesList.querySelector(`[data-thumb-index="${index}"][data-thumb-role="${safeRole}"],img.thumb-img[data-thumb-image-index="${index}"][data-thumb-role="${safeRole}"]`);return node?registerThumbnailHolderNode(node,index,role):null;
}
function observeThumbnails({reuse=false,root=els.articlesList}={}){
  if(!reuse||!thumbObserver){
    if(thumbObserver)thumbObserver.disconnect();
    thumbObserver=new IntersectionObserver(entries=>{
      const rootRect=els.articlesList.getBoundingClientRect();
      entries.filter(entry=>entry.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top).forEach(entry=>{
        const holder=entry.target;thumbObserver.unobserve(holder);const r=entry.boundingClientRect;
        const visible=r.bottom>rootRect.top&&r.top<rootRect.bottom;
        const distance=visible?0:Math.min(Math.abs(r.top-rootRect.bottom),Math.abs(rootRect.top-r.bottom));
        queueThumbnail(Number(holder.dataset.thumbIndex),visible?0:1,distance,holder.dataset.thumbRole||'item');
      });
    },{root:els.articlesList,rootMargin:'1000px 0px 1800px 0px',threshold:.01});
  }
  root?.querySelectorAll?.('[data-thumb-index]:not([data-thumb-observed])').forEach(el=>{registerThumbnailHolderNode(el);el.dataset.thumbObserved='1';el.dataset.thumbBornAt=String(Date.now());thumbObserver.observe(el)});
  scheduleThumbnailDemandScan();ensureThumbnailWatchdog();
}
function scheduleThumbnailDemandScan(){
  if(thumbDemandRaf)return;
  thumbDemandRaf=requestAnimationFrame(()=>{thumbDemandRaf=0;scanThumbnailDemand()});
}
function ensureThumbnailWatchdog(){
  if(thumbWatchdogTimer)return;
  thumbWatchdogTimer=setInterval(()=>{if(state.activeView==='browse'&&state.selectedGroup)scanThumbnailDemand()},1000);
}
function thumbnailTaskQueued(index,a,role='item'){
  if(!a)return false;return state.thumbQueued.has(thumbnailTaskKey(index,previewKey(a),role,state.galleryGeneration));
}
function galleryViewportAnchor(rootRect){
  const x=Math.max(rootRect.left+8,Math.min(rootRect.right-8,rootRect.left+rootRect.width*.5));
  for(const y of [rootRect.top+12,rootRect.top+Math.min(rootRect.height*.35,220),rootRect.bottom-12]){
    for(const el of document.elementsFromPoint(x,y)){const card=el.closest?.('.media-card,.media-set-card');if(card&&els.articlesList.contains(card))return card}
  }
  return els.articlesList.querySelector('.media-card,.media-set-card');
}
function thumbnailDemandCandidates(rootRect){
  const anchor=galleryViewportAnchor(rootRect);if(!anchor)return[];const grid=anchor.parentElement;if(!grid)return[];
  const before=state.browseScrollDirection>=0?48:150,after=state.browseScrollDirection>=0?190:72,out=[];let node=anchor;
  for(let i=0;i<before&&node;i++,node=node.previousElementSibling){const holder=node.querySelector?.('[data-thumb-index]');if(holder)out.unshift(holder)}
  node=anchor;for(let i=0;i<after&&node;i++,node=node.nextElementSibling){const holder=node.querySelector?.('[data-thumb-index]');if(holder&&!out.includes(holder))out.push(holder)}
  return out;
}
function thumbnailGeometryKey(index,role='item'){return `${index}|${role}`}
function scanThumbnailDemand(){
  if(!els.articlesList||!state.selectedGroup||effectiveViewMode()!=='gallery')return;
  const root=els.articlesList.getBoundingClientRect(),now=Date.now(),velocity=Math.abs(Number(state.browseScrollVelocity||0)),down=state.browseScrollDirection>=0;
  const idleBoost=(Date.now()-Number(state.lastBrowseScrollTs||0)>700&&state.thumbActive===0)?root.height*1.5:0;const baseLead=Math.max(1900,Math.min(14000,root.height*(2.2+Math.min(5,velocity*2))+state.thumbConcurrency*90+idleBoost));
  const marginAfter=down?baseLead:Math.max(1200,baseLead*.45),marginBefore=down?Math.max(900,baseLead*.35):baseLead;
  const holders=thumbnailDemandCandidates(root),demandTarget=Math.max(12,state.thumbConcurrency*2),alreadyDemanded=state.thumbQueue.length+state.thumbActive;let demanded=alreadyDemanded;
  const geometry=new Map();
  for(const holder of holders){
    const index=Number(holder.dataset.thumbIndex),role=holder.dataset.thumbRole||'item',a=state.articles[index];
    if(!a?.media||!a.complete||!['image','video'].includes(a.media.kind))continue;
    // One layout read per nearby holder per animation frame. Queue scoring below
    // reuses this snapshot instead of repeatedly forcing Chromium layout.
    const r=holder.getBoundingClientRect();const visible=r.bottom>root.top&&r.top<root.bottom,near=r.bottom>root.top-marginBefore&&r.top<root.bottom+marginAfter;
    const distance=visible?0:(r.top>=root.bottom?r.top-root.bottom:root.top-r.bottom);geometry.set(thumbnailGeometryKey(index,role),{visible,distance,top:r.top,bottom:r.bottom});
    if(!near)continue;
    if(!holder.dataset.thumbBornAt)holder.dataset.thumbBornAt=String(now);
    const cached=a.media.kind==='image'?state.imageThumbCache.get(previewKey(a)):state.videoThumbCache.get(previewKey(a));
    if(cached?.url){updateThumbnailDom(index,cached,role);continue}
    const prepared=state.previewCache.get(previewKey(a));
    if(a.media.kind==='image'&&prepared?.url){replaceThumbnailHolderWithImage(holder,index,prepared.url,role,{fallback:true});continue}
    if(!thumbnailTaskQueued(index,a,role)&&queueThumbnail(index,visible?0:1,distance,role))demanded++;
    const born=Number(holder.dataset.thumbBornAt||now);
    if(visible&&a.media.kind==='image'&&now-born>=6000)escalateVisibleImageThumbnail(index,role);
    if(demanded>=demandTarget&&!visible&&((down&&r.top>root.bottom)||(!down&&r.bottom<root.top)))break;
  }
  state.thumbGeometry=geometry;state.thumbGeometryTs=performance.now();
}


function escalateVisibleImageThumbnail(index,role='item'){
  const a=state.articles[index];if(!a?.media||a.media.kind!=='image'||!a.complete||state.thumbEscalationActive>=2)return;
  const pkey=previewKey(a);if(state.previewCache.get(pkey)?.url){const holder=thumbnailHolder(index,role);if(holder)replaceThumbnailHolderWithImage(holder,index,state.previewCache.get(pkey).url,role,{fallback:true});return}
  if(state.thumbEscalations.has(pkey))return;
  const generation=state.galleryGeneration,group=state.selectedGroup,provider=state.providerId;state.thumbEscalationActive++;
  const request=fetchPrepared(a).then(data=>{
    if(!data?.url)return;
    if(generation!==state.galleryGeneration||group!==state.selectedGroup||provider!==state.providerId)return;
    const holder=thumbnailHolder(index,role);if(holder)replaceThumbnailHolderWithImage(holder,index,data.url,role,{fallback:true});
  }).catch(()=>{}).finally(()=>{state.thumbEscalationActive=Math.max(0,state.thumbEscalationActive-1);state.thumbEscalations.delete(pkey);scheduleThumbnailDemandScan()});
  state.thumbEscalations.set(pkey,request);
}
function queueThumbnail(index,priority=1,distance=0,role='item'){
  const a=state.articles[index];if(!a||!a.media||!a.complete||!['image','video'].includes(a.media.kind))return false;
  const pkey=previewKey(a),generation=state.galleryGeneration,qkey=thumbnailTaskKey(index,pkey,role,generation);
  const cached=a.media.kind==='image'?state.imageThumbCache.get(pkey):state.videoThumbCache.get(pkey);
  if(cached?.url){updateThumbnailDom(index,cached,role);return false}
  if(state.thumbQueued.has(qkey))return false;
  const holder=thumbnailHolder(index,role);if(holder&&!holder.dataset.thumbBornAt)holder.dataset.thumbBornAt=String(Date.now());
  state.thumbQueued.add(qkey);state.thumbQueue.push({index,pkey,qkey,kind:a.media.kind,role,priority,distance,bytes:Number(a.bytes||0),queuedAt:Date.now(),generation,group:articleGroup(a),provider:state.providerId});pumpThumbQueue();return true;
}
function liveThumbnailTaskScore(task){
  const geo=state.thumbGeometry.get(thumbnailGeometryKey(task.index,task.role));const visible=geo?!!geo.visible:Number(task.priority||1)===0,distance=geo?Number(geo.distance||0):Math.max(0,Number(task.distance||0));
  const mb=Math.max(0,Number(task.bytes||0)/1048576),sizePenalty=Math.min(240000,Math.log2(1+mb)*26000),ageSec=Math.max(0,(Date.now()-Number(task.queuedAt||Date.now()))/1000),ageCredit=Math.min(sizePenalty*.9,ageSec*14000);
  return(visible?0:1)*1e9+Math.max(0,distance)*1000+Math.max(0,sizePenalty-ageCredit);
}
function pumpThumbQueue(){
  while(state.thumbActive<state.thumbConcurrency&&state.thumbQueue.length){
    const kept=[];for(const t of state.thumbQueue){const live=t.generation===state.galleryGeneration&&t.group===state.selectedGroup&&t.provider===state.providerId&&!!state.articles[t.index];if(live)kept.push(t);else state.thumbQueued.delete(t.qkey||t.pkey)}state.thumbQueue=kept;
    if(!state.thumbQueue.length)return;
    let pos=-1,best=Number.POSITIVE_INFINITY;
    for(let i=0;i<state.thumbQueue.length;i++){const t=state.thumbQueue[i];if(t.kind==='video'&&state.thumbVideoActive>=state.videoThumbConcurrency)continue;if(t.role==='set-cover'&&state.thumbSetActive>=state.setCoverConcurrency)continue;const score=liveThumbnailTaskScore(t);if(score<best){best=score;pos=i}}
    if(pos<0)return;
    const task=state.thumbQueue.splice(pos,1)[0],sampleStarted=performance.now();state.thumbActive++;state.thumbActiveTasks.set(task.qkey,Date.now());if(task.kind==='video')state.thumbVideoActive++;if(task.role==='set-cover')state.thumbSetActive++;
    (async()=>{
      let sampleOK=false;
      try{
        if(task.generation!==state.galleryGeneration||task.group!==state.selectedGroup||task.provider!==state.providerId)return;
        const a=state.articles[task.index];if(!a)return;
        const data=task.kind==='video'?await fetchVideoThumbnail(a):await fetchImageThumbnail(a,task);sampleOK=true;
        if(task.kind==='image'&&data?.suppressed_small){
          a.small_image_suppressed=true;a.media_meta={...(a.media_meta||{}),width:Number(data.width||0),height:Number(data.height||0)};
          state.imageThumbCache.delete(task.pkey);state.selectedItems.delete(articleKey(a));
          if(task.generation===state.galleryGeneration&&task.group===state.selectedGroup&&task.provider===state.providerId){if(!hideUnavailableMediaInPlace(a,task.index,task.role))renderArticles({preserveScroll:true});}
          return;
        }
        if(task.generation===state.galleryGeneration&&task.group===state.selectedGroup&&task.provider===state.providerId)updateThumbnailDom(task.index,data,task.role);
      }catch(e){if(task.generation===state.galleryGeneration&&task.group===state.selectedGroup&&task.provider===state.providerId)markThumbnailError(task.index,e,task.kind,task.role);}
      finally{state.thumbActive--;state.thumbActiveTasks.delete(task.qkey);if(task.kind==='video')state.thumbVideoActive--;if(task.role==='set-cover')state.thumbSetActive--;state.thumbQueued.delete(task.qkey||task.pkey);recordPreviewSample(performance.now()-sampleStarted,sampleOK);pumpThumbQueue();scheduleThumbnailDemandScan();}
    })();
  }
}
async function fetchPrepared(a){
  const key=previewKey(a);if(state.previewCache.has(key))return state.previewCache.get(key);if(state.previewPromises.has(key))return state.previewPromises.get(key);
  const started=performance.now();const request=api('/api/preview/prepare',browsePayload({provider_id:state.providerId,group:articleGroup(a),segments:segmentPayload(a),media:a.media}),browseRequestOptions())
    .then(data=>{boundedCacheSet(state.previewCache,key,data,browseCacheLimits().preview);perfRecord('preview',performance.now()-started);return data})
    .finally(()=>state.previewPromises.delete(key));
  state.previewPromises.set(key,request);return request;
}
async function persistThumbnail(token,dataUrl){
  if(!token||!dataUrl)return {thumbnail_url:dataUrl};
  return api('/api/thumbnail/store',{token,data_url:dataUrl});
}
function captureImageThumbnail(url){
  return new Promise((resolve,reject)=>{
    const img=new Image();
    const finish=(err,value)=>{img.onload=null;img.onerror=null;err?reject(err):resolve(value)};
    img.onload=()=>{try{
      const w=img.naturalWidth,h=img.naturalHeight;if(!w||!h)return finish(new Error('Image dimensions were unavailable.'));
      const max=480,scale=Math.min(1,max/Math.max(w,h)),cw=Math.max(1,Math.round(w*scale)),ch=Math.max(1,Math.round(h*scale));
      const canvas=document.createElement('canvas');canvas.width=cw;canvas.height=ch;const ctx=canvas.getContext('2d',{alpha:false});
      ctx.fillStyle='#0a1119';ctx.fillRect(0,0,cw,ch);ctx.drawImage(img,0,0,cw,ch);finish(null,{dataUrl:canvas.toDataURL('image/jpeg',.78),width:w,height:h});
    }catch(e){finish(e)}};
    img.onerror=()=>finish(new Error('The image could not be decoded for a thumbnail.'));
    img.src=url;
  });
}
async function finishImageThumbnailResponse(a,data){
  const key=previewKey(a);if(data?.suppressed_small)return {...data,url:''};let url=data?.thumbnail_url||'';
  if(!url&&data?.source_url&&data?.thumbnail_token){
    const captured=await captureImageThumbnail(data.source_url);const stored=await persistThumbnail(data.thumbnail_token,captured.dataUrl);url=stored.thumbnail_url||captured.dataUrl;data.width=captured.width;data.height=captured.height;
  }
  if(!url)throw new Error('Could not create a persistent thumbnail for this image.');
  const result={...data,url};boundedCacheSet(state.imageThumbCache,key,result,browseCacheLimits().thumb);state.unpreviewableMediaKeys.delete(key);return result;
}
async function fetchImageThumbnail(a,task=null){
  const key=previewKey(a);if(state.imageThumbCache.has(key))return state.imageThumbCache.get(key);if(state.imageThumbPromises.has(key))return state.imageThumbPromises.get(key);
  const payload=browsePayload({provider_id:state.providerId,group:articleGroup(a),segments:segmentPayload(a),media:a.media,thumbnail_lanes:thumbnailLaneHint(a,task)});const started=performance.now();
  const request=(async()=>{
    let thumbnailError=null;
    try{return await finishImageThumbnailResponse(a,await api('/api/thumbnail/image',payload,browseRequestOptions()))}
    catch(e){thumbnailError=e}

    try{
      const full=await fetchPrepared(a);
      if(full?.url){
        try{return await finishImageThumbnailResponse(a,await api('/api/thumbnail/image',payload,browseRequestOptions()))}
        catch{
          const result={...full,url:full.url,kind:'image',method:'full-preview-fallback',thumbnail_fallback:true};
          boundedCacheSet(state.imageThumbCache,key,result,browseCacheLimits().thumb);state.unpreviewableMediaKeys.delete(key);return result;
        }
      }
    }catch{}
    throw thumbnailError||new Error('Could not load an image preview for this post.');
  })().finally(()=>{perfRecord('thumbnail',performance.now()-started);state.imageThumbPromises.delete(key)});
  state.imageThumbPromises.set(key,request);return request;
}
async function fetchVideoThumbnail(a){
  const key=previewKey(a);if(state.videoThumbCache.has(key))return state.videoThumbCache.get(key);if(state.videoThumbPromises.has(key))return state.videoThumbPromises.get(key);
  const request=api('/api/thumbnail/video',browsePayload({provider_id:state.providerId,group:articleGroup(a),segments:segmentPayload(a),media:a.media}),browseRequestOptions())
    .then(async data=>{
      let url=data.thumbnail_url||'';
      if(!url&&data.sample_url&&data.browser_supported){
        const captured=await captureVideoFrame(data.sample_url);
        if(data.thumbnail_token){const stored=await persistThumbnail(data.thumbnail_token,captured.dataUrl);url=stored.thumbnail_url||captured.dataUrl}else url=captured.dataUrl;data.width=captured.width;data.height=captured.height;data.duration=captured.duration;
      }
      if(!url)throw new Error(data.browser_supported?'Could not decode a frame from the video sample.':'This video format needs FFmpeg for automatic thumbnails.');
      const result={...data,url};boundedCacheSet(state.videoThumbCache,key,result,Math.max(96,Math.floor(browseCacheLimits().thumb*.28)));state.unpreviewableMediaKeys.delete(key);return result;
    })
    .finally(()=>state.videoThumbPromises.delete(key));
  state.videoThumbPromises.set(key,request);return request;
}
function captureVideoFrame(url){
  return new Promise((resolve,reject)=>{
    const video=document.createElement('video');video.muted=true;video.playsInline=true;video.preload='auto';video.src=url;
    video.style.cssText='position:absolute;width:2px;height:2px;opacity:.001;pointer-events:none;left:-10000px;top:0';document.body.appendChild(video);
    let done=false;const finish=(err,value)=>{if(done)return;done=true;clearTimeout(timer);try{video.pause();video.removeAttribute('src');video.load();video.remove();}catch{}err?reject(err):resolve(value)};
    const capture=()=>{try{const w=video.videoWidth,h=video.videoHeight;if(!w||!h)return finish(new Error('The video sample did not expose a frame.'));const maxW=480,scale=Math.min(1,maxW/w),cw=Math.max(1,Math.round(w*scale)),ch=Math.max(1,Math.round(h*scale));const canvas=document.createElement('canvas');canvas.width=cw;canvas.height=ch;const ctx=canvas.getContext('2d');ctx.drawImage(video,0,0,cw,ch);finish(null,{dataUrl:canvas.toDataURL('image/jpeg',.78),width:w,height:h,duration:Number.isFinite(Number(video.duration))?Number(video.duration):0});}catch(e){finish(e)}};
    const timer=setTimeout(()=>finish(new Error('Video thumbnail timed out.')),12000);
    video.addEventListener('error',()=>finish(new Error('The browser could not decode this video sample.')),{once:true});
    video.addEventListener('loadeddata',()=>{
      const d=Number(video.duration);if(Number.isFinite(d)&&d>1&&video.seekable?.length){video.addEventListener('seeked',capture,{once:true});try{video.currentTime=Math.min(.75,d*.05)}catch{capture()}}else capture();
    },{once:true});
    video.load();
  });
}
function thumbnailTokenFromUrl(url){const m=String(url||'').match(/\/thumb\/([0-9a-f]{32})(?:[?#]|$)/i);return m?m[1]:''}
function thumbnailLooksVisuallyBlank(img){
  if(!img||img.dataset.thumbFallback==='full'||!img.naturalWidth||!img.naturalHeight)return false;
  try{
    const size=24,canvas=document.createElement('canvas');canvas.width=size;canvas.height=size;const ctx=canvas.getContext('2d',{willReadFrequently:true});
    if(!ctx)return false;ctx.drawImage(img,0,0,size,size);const px=ctx.getImageData(0,0,size,size).data;
    let minR=255,minG=255,minB=255,maxR=0,maxG=0,maxB=0,sum=0,sum2=0,n=0;
    for(let i=0;i<px.length;i+=4){if(px[i+3]<8)continue;const r=px[i],g=px[i+1],b=px[i+2],y=.2126*r+.7152*g+.0722*b;minR=Math.min(minR,r);minG=Math.min(minG,g);minB=Math.min(minB,b);maxR=Math.max(maxR,r);maxG=Math.max(maxG,g);maxB=Math.max(maxB,b);sum+=y;sum2+=y*y;n++;}
    if(!n)return true;const mean=sum/n,variance=Math.max(0,sum2/n-mean*mean),spread=Math.max(maxR-minR,maxG-minG,maxB-minB);
    return spread<=5&&variance<=3.0;
  }catch{return false}
}
async function recoverVisuallyBlankThumbnail(img){
  if(!img||img.dataset.thumbVisualRecovering==='1')return;img.dataset.thumbVisualRecovering='1';
  const index=Number(img.dataset.thumbImageIndex),role=img.dataset.thumbRole||'item',a=state.articles[index];if(!a?.media||a.media.kind!=='image')return;
  const key=previewKey(a),token=thumbnailTokenFromUrl(img.getAttribute('src')||img.src);state.thumbFailureCache.delete(key);state.imageThumbCache.delete(key);
  try{
    if(token)await api('/api/thumbnail/invalidate',{token,visual_blank:true}).catch(()=>{});
    const full=await fetchPrepared(a);if(!full?.url)throw new Error('Full preview did not provide an image URL.');
    const result={...full,url:full.url,kind:'image',method:'full-preview-visual-recovery',thumbnail_fallback:true};
    boundedCacheSet(state.imageThumbCache,key,result,browseCacheLimits().thumb);state.unpreviewableMediaKeys.delete(key);const current=els.articlesList.querySelector(`img.thumb-img[data-thumb-image-index="${index}"][data-thumb-role="${role}"]`);
    if(current===img){const parent=img.parentElement,loader=document.createElement('div');loader.className='thumb-loader';loader.dataset.thumbIndex=String(index);loader.dataset.thumbRole=role;loader.innerHTML='<span></span><small>Repairing preview…</small>';img.replaceWith(loader);replaceThumbnailHolderWithImage(loader,index,result.url,role,{fallback:!!result.thumbnail_fallback});}
  }catch(e){if(img.isConnected)recoverBrokenThumbnail(img)}
}
function forceThumbnailPaintRefresh(img){
  if(!img||!img.isConnected||img.dataset.thumbPaintRefresh==='1')return;img.dataset.thumbPaintRefresh='1';
  const repaint=()=>{if(!img.isConnected)return;img.classList.add('thumb-paint-refresh');void img.offsetHeight;requestAnimationFrame(()=>{if(!img.isConnected)return;img.classList.remove('thumb-paint-refresh');void img.offsetHeight;requestAnimationFrame(()=>{if(img.isConnected)delete img.dataset.thumbPaintRefresh;});});};
  if(typeof img.decode==='function'){Promise.resolve().then(()=>img.decode()).catch(()=>{}).finally(repaint);}else requestAnimationFrame(repaint);
}
function handleThumbnailImageLoaded(img){
  if(!img||img.dataset.thumbLoadHandled==='1')return;img.dataset.thumbLoadHandled='1';const a=state.articles[Number(img.dataset.thumbImageIndex)];if(a)state.thumbImageRecovery.delete(previewKey(a));
  // r6: normal successful thumbnails stay on Chromium's asynchronous paint path.
  // New native thumbnails are blank-validated before caching, so canvas readback and
  // forced offsetHeight reflows are reserved for exceptional/manual recovery only.
}
function wireThumbnailImages(root=els.articlesList){
  root?.querySelectorAll('img.thumb-img[data-thumb-image-index]:not([data-thumb-image-wired])').forEach(img=>{
    img.dataset.thumbImageWired='1';img.addEventListener('load',()=>handleThumbnailImageLoaded(img),{once:true});img.addEventListener('error',()=>recoverBrokenThumbnail(img),{once:true});
    if(img.complete)queueMicrotask(()=>{if(!img.isConnected)return;if(img.naturalWidth&&img.naturalHeight)handleThumbnailImageLoaded(img);else recoverBrokenThumbnail(img)});
  });
}
async function recoverBrokenThumbnail(img){
  if(!img||img.dataset.thumbRecovering==='1')return;img.dataset.thumbRecovering='1';const index=Number(img.dataset.thumbImageIndex),role=img.dataset.thumbRole||'item',a=state.articles[index];if(!a?.media)return;
  const key=previewKey(a),kind=a.media.kind,attempt=Number(state.thumbImageRecovery.get(key)||0)+1;state.thumbImageRecovery.set(key,attempt);state.thumbFailureCache.delete(key);if(kind==='image')state.imageThumbCache.delete(key);else state.videoThumbCache.delete(key);
  const token=thumbnailTokenFromUrl(img.getAttribute('src')||img.src);if(token)api('/api/thumbnail/invalidate',{token}).catch(()=>{});
  const parent=img.parentElement;parent?.querySelector('.video-play-overlay')?.remove();const loader=document.createElement('div');loader.className=`thumb-loader ${kind==='video'?'video-thumb-loader':''}`;loader.dataset.thumbIndex=String(index);loader.dataset.thumbRole=role;loader.innerHTML=`<span></span><small>${attempt===1?'Recovering thumbnail…':'Loading full preview fallback…'}</small>`;img.replaceWith(loader);registerThumbnailHolderNode(loader,index,role);
  if(attempt===1){queueThumbnail(index,0,0,role);return}
  try{const data=await fetchPrepared(a);if(!data?.url)throw new Error('Full preview did not provide an image URL.');const holder=thumbnailHolder(index,role);if(!holder)return;if(kind!=='image')throw new Error('Full-image fallback is only available for image posts.');replaceThumbnailHolderWithImage(holder,index,data.url,role,{fallback:true});}
  catch(e){const holder=thumbnailHolder(index,role);if(!holder)return;unregisterThumbnailHolder(index,role);holder.className='thumb-error';holder.removeAttribute('data-thumb-index');holder.innerHTML=`<span>!</span><small>Thumbnail unavailable</small><em>${escapeHtml(String(e?.message||e||'Preview unavailable').slice(0,140))}</em><button type="button" class="thumb-retry">Retry</button>`;holder.querySelector('.thumb-retry')?.addEventListener('click',ev=>{ev.stopPropagation();state.thumbImageRecovery.delete(key);holder.className=`thumb-loader ${kind==='video'?'video-thumb-loader':''}`;holder.setAttribute('data-thumb-index',String(index));holder.dataset.thumbRole=role;registerThumbnailHolderNode(holder,index,role);holder.innerHTML='<span></span><small>Retrying preview…</small>';queueThumbnail(index,0,0,role)})}
}
function replaceThumbnailHolderWithImage(holder,index,url,role='item',{isVideo=false,fallback=false}={}){
  const a=state.articles[index];if(!holder||!a||!url)return null;
  const img=document.createElement('img');img.className='thumb-img';img.alt=isVideo?`Video thumbnail for ${a.media?.filename||'video'}`:(a.media?.filename||'Image');img.decoding='async';img.dataset.thumbImageIndex=String(index);img.dataset.thumbRole=role;img.dataset.thumbImageWired='1';if(fallback)img.dataset.thumbFallback='full';
  img.addEventListener('load',()=>handleThumbnailImageLoaded(img),{once:true});
  img.addEventListener('error',()=>recoverBrokenThumbnail(img),{once:true});
  holder.replaceWith(img);registerThumbnailHolderNode(img,index,role);
  if(isVideo)img.insertAdjacentHTML('afterend','<div class="video-play-overlay"><span>▶</span></div>');
  img.src=url;return img;
}
function updateThumbnailDom(index,data,role='item'){
  const holder=thumbnailHolder(index,role),a=state.articles[index],isVideo=a?.media?.kind==='video';if(a&&data)a.media_meta={...(a.media_meta||{}),width:Number(data.width||0),height:Number(data.height||0),duration:Number(data.duration||0)};if(!holder)return;
  replaceThumbnailHolderWithImage(holder,index,data.url,role,{isVideo});const card=els.articlesList.querySelector(`.media-card[data-index="${index}"]`),meta=card?.querySelector('.media-card-info > div');if(meta&&a?.media_meta?.width&&a.media_meta.height&&!meta.querySelector('.media-dims'))meta.insertAdjacentHTML('beforeend',`<span class="media-dims">${a.media_meta.width.toLocaleString()}×${a.media_meta.height.toLocaleString()}${a.media_meta.duration?' • '+formatDuration(a.media_meta.duration):''}</span>`);
}
function friendlyPreviewError(error){
  const data=error?.data||{};const message=data.error||error?.message||String(error||'Preview unavailable');
  return {message,label:data.error_label||'Preview unavailable',code:data.error_code||'preview_failed',retryable:data.retryable!==false};
}
function isDefinitiveUnsupportedMedia(info){return info?.retryable===false&&info?.code==='decode_failed'}
function rememberPreviewUnavailable(a,info){
  if(!a)return false;
  const key=previewKey(a);state.unpreviewableMediaKeys.add(key);
  if(isDefinitiveUnsupportedMedia(info))state.unsupportedMediaKeys.add(key);
  state.thumbFailureCache.set(key,{info,expires:isDefinitiveUnsupportedMedia(info)?Number.MAX_SAFE_INTEGER:Date.now()+(info.retryable?120000:1800000)});
  const articleId=articleKey(a);state.selectedItems.delete(articleId);if(state.selectedArticleKey===articleId){state.selectedArticleKey='';resetPreview()}if(state.viewerKey===articleId)closeMediaViewer();
  return true;
}
function rememberUnsupportedMedia(a,info){return !!(a&&isDefinitiveUnsupportedMedia(info)&&rememberPreviewUnavailable(a,info))}
function restoreAfterGalleryMutation(anchors,scrollTop){restoreBrowsePosition(anchors,scrollTop);updateArticleSearchUi();updateSelectionBar();wireContinuousObserver()}
function hideUnavailableMediaInPlace(a,index,role='item'){
  if(!a||els.contentFilter.value==='all')return false;const keep=els.articlesList.scrollTop,anchors=captureBrowseAnchors();
  if(role==='set-cover'){
    const holder=thumbnailHolder(index,'set-cover'),card=holder?.closest('.media-set-card');if(!card)return false;const setKey=card.dataset.setKey;
    const members=filteredArticles().filter(x=>mediaSetKey(x.a)===setKey&&x.a.complete);
    const rep=members.length?mediaSetRepresentative({key:setKey,members}):null;
    if(rep){const cover=card.querySelector('.media-set-cover');cover?.querySelectorAll('.thumb-img,.thumb-loader,.thumb-error,.video-play-overlay').forEach(n=>n.remove());if(cover){const k=rep.a.media?.kind||'image';cover.insertAdjacentHTML('afterbegin',`<div class="thumb-loader ${k==='video'?'video-thumb-loader':''}" data-thumb-index="${rep.index}" data-thumb-role="set-cover"><span></span><small>Loading set cover…</small></div>`);registerThumbnailHolderNode(cover.querySelector('[data-thumb-index]'),rep.index,'set-cover');queueThumbnail(rep.index,0,0,'set-cover')}}else card.remove();
  }else els.articlesList.querySelector(`.media-card[data-index="${index}"]`)?.remove();
  restoreAfterGalleryMutation(anchors,keep);return true;
}
function hideUnavailableArticleByKey(a){const index=state.articles.findIndex(x=>articleKey(x)===articleKey(a));return index>=0?hideUnavailableMediaInPlace(a,index,'item'):false}
function markThumbnailError(index,error,kind='image',role='item'){
  const info=friendlyPreviewError(error),a=state.articles[index];
  if(a&&rememberPreviewUnavailable(a,info)&&els.contentFilter.value!=='all'){if(hideUnavailableMediaInPlace(a,index,role))return;renderArticles({preserveScroll:true});return}
  if(a&&!state.thumbFailureCache.has(previewKey(a)))state.thumbFailureCache.set(previewKey(a),{info,expires:Date.now()+(info.retryable?120000:1800000)});
  const holder=thumbnailHolder(index,role);if(!holder)return;
  unregisterThumbnailHolder(index,role);holder.className='thumb-error';holder.removeAttribute('data-thumb-index');holder.innerHTML=`<span>!</span><small>${kind==='video'?'Video thumbnail unavailable':'Preview unavailable'}</small><em class="error-label">${escapeHtml(info.label)}</em><em>${escapeHtml(String(info.message||'').slice(0,140))}</em>${info.retryable?'<button type="button" class="thumb-retry">Retry</button>':''}`;
  holder.querySelector('.thumb-retry')?.addEventListener('click',e=>{e.stopPropagation();const a=state.articles[index];if(a)state.thumbFailureCache.delete(previewKey(a));holder.className=`thumb-loader ${kind==='video'?'video-thumb-loader':''}`;holder.setAttribute('data-thumb-index',String(index));holder.dataset.thumbRole=role;registerThumbnailHolderNode(holder,index,role);holder.innerHTML=`<span></span><small>Retrying ${kind==='video'?'video thumbnail':'preview'}…</small>`;queueThumbnail(index,0,0,role);});
}

function isSelectableMedia(a){return !!(a?.media&&a.complete)}
function selectRangeTo(index,{add=false}={}){
  const clicked=state.articles[index];if(!isSelectableMedia(clicked))return;
  const visible=filteredArticles();const clickedKey=articleKey(clicked);const clickedPos=visible.findIndex(x=>articleKey(x.a)===clickedKey);const anchorPos=visible.findIndex(x=>articleKey(x.a)===state.selectionAnchorKey);
  if(!add)state.selectedItems.clear();
  if(clickedPos<0||anchorPos<0){state.selectedItems.set(clickedKey,clicked);state.selectionAnchorKey=clickedKey;return}
  const start=Math.min(anchorPos,clickedPos),end=Math.max(anchorPos,clickedPos);
  for(let i=start;i<=end;i++){const item=visible[i]?.a;if(isSelectableMedia(item))state.selectedItems.set(articleKey(item),item)}
}
function handleMediaSelectionClick(index,e){
  const a=state.articles[index];if(!a)return;const key=articleKey(a);const selectable=isSelectableMedia(a);const additive=!!(e.ctrlKey||e.metaKey);const range=!!e.shiftKey;
  if(selectable){
    if(range){selectRangeTo(index,{add:additive});}
    else if(additive){if(state.selectedItems.has(key))state.selectedItems.delete(key);else state.selectedItems.set(key,a);state.selectionAnchorKey=key;}
    else{state.selectedItems.clear();state.selectedItems.set(key,a);state.selectionAnchorKey=key;}
  }
  state.selectedArticleKey=key;updateSelectionBar();updateSelectionDomInPlace();updateActiveArticleDomInPlace();renderPreviewDetails(a,true);document.querySelector('.preview-pane')?.classList.add('open');
}
function viewportSelectableArticles(){
  if(!state.selectedGroup)return[];const listRect=els.articlesList.getBoundingClientRect();const seen=new Set(),out=[];
  els.articlesList.querySelectorAll('.media-card[data-index],.article-row[data-index],.binary-set-row[data-binary-set-key]').forEach(node=>{const r=node.getBoundingClientRect();if(r.bottom<=listRect.top||r.top>=listRect.bottom)return;if(node.dataset.binarySetKey){const group=state.binarySetGroups.get(node.dataset.binarySetKey);for(const x of group?.members||[]){const a=x.a,key=articleKey(a);if(isSelectableMedia(a)&&!seen.has(key)){seen.add(key);out.push(a)}}return}const a=state.articles[Number(node.dataset.index)];if(!isSelectableMedia(a))return;const key=articleKey(a);if(!seen.has(key)){seen.add(key);out.push(a)}});return out;
}
function updateSelectionBar(){
  const count=state.selectedItems.size;const loaded=filteredArticles().map(x=>x.a).filter(isSelectableMedia);const viewport=(state.selectedGroup)?viewportSelectableArticles():[],noun=isAllPostsMode()?'file':'item';
  els.selectionBar.classList.toggle('hidden',!(state.selectedGroup));els.selectionCount.textContent=`${count.toLocaleString()} ${noun}${count===1?'':'s'} selected${count?' across loaded headers':''}`;els.downloadSelectedBtn.textContent=`＋ Add selected to queue${count?` (${count.toLocaleString()})`:''}`;els.downloadSelectedBtn.disabled=count===0;els.clearSelectionBtn.disabled=count===0;els.selectVisibleBtn.disabled=viewport.length===0;els.selectLoadedBtn.disabled=loaded.length===0;els.invertSelectionBtn.disabled=loaded.length===0;
}
function selectViewport(){for(const a of viewportSelectableArticles())state.selectedItems.set(articleKey(a),a);updateSelectionBar();updateSelectionDomInPlace();if(state.viewerOpen)updateViewerSelectionState();}
function selectAllLoaded(){for(const a of filteredArticles().map(x=>x.a)){if(isSelectableMedia(a))state.selectedItems.set(articleKey(a),a)}updateSelectionBar();updateSelectionDomInPlace();if(state.viewerOpen)updateViewerSelectionState();}
function invertVisibleSelection(){for(const a of filteredArticles().map(x=>x.a)){if(!isSelectableMedia(a))continue;const key=articleKey(a);if(state.selectedItems.has(key))state.selectedItems.delete(key);else state.selectedItems.set(key,a)}updateSelectionBar();updateSelectionDomInPlace();if(state.viewerOpen)updateViewerSelectionState();}
function clearSelection(){state.selectedItems.clear();state.selectionAnchorKey='';updateSelectionBar();updateSelectionDomInPlace();if(state.viewerOpen)updateViewerSelectionState();}
function setView(mode){if(isAllPostsMode()||state.viewMode===mode)return;state.viewMode=mode;localStorage.setItem('usenetViewMode',mode);saveUiSettings();rotateBrowsePreviewSession();renderArticles();}
function updateActiveArticleDomInPlace(){
  els.articlesList.querySelectorAll('.media-card[data-index],.article-row[data-index]').forEach(node=>{const a=state.articles[Number(node.dataset.index)];const active=!!a&&articleKey(a)===state.selectedArticleKey;node.classList.toggle('active',active);node.classList.toggle('keyboard-active',active)});
}
function selectArticle(index){
  const a=state.articles[index];if(!a)return;state.selectedArticleKey=articleKey(a);updateActiveArticleDomInPlace();renderPreviewDetails(a,true);document.querySelector('.preview-pane')?.classList.add('open');
}
function viewerSetMembers(a){const key=mediaSetKey(a);if(!key)return[];return filteredArticles().map(x=>x.a).filter(x=>x.complete&&['image','video'].includes(x.media?.kind)&&mediaSetKey(x)===key)}
function viewerItems(){let items=filteredArticles().map(x=>x.a).filter(a=>['image','video'].includes(a.media?.kind)&&a.complete);const current=viewerCurrentArticle();if(state.viewerSetOnly&&current){const key=mediaSetKey(current);if(key)items=items.filter(a=>mediaSetKey(a)===key)}else if(state.groupRelatedMedia&&state.activeMediaSetKey)items=items.filter(a=>mediaSetKey(a)===state.activeMediaSetKey);return items}
function viewerCurrentArticle(){return state.articles.find(a=>articleKey(a)===state.viewerKey)||null}
function viewerActiveDownloads(){const c=state.downloadSnapshot?.counts||{};return Number(c.downloading||0)+Number(c.queued||0)+Number(c.retry_wait||0)>0}
function viewerInfoMarkup(a,data=null){const dims=data?.width&&data?.height?`${Number(data.width).toLocaleString()} × ${Number(data.height).toLocaleString()}`:'Loading…';const set=viewerSetMembers(a);return `<div class="viewer-info-grid"><span>Filename</span><b>${escapeHtml(a.media?.filename||a.subject||'—')}</b><span>Poster</span><b>${escapeHtml(a.from||'—')}</b><span>Newsgroup</span><b>${escapeHtml(articleGroup(a)||'—')}</b><span>Article</span><b>#${Number(a.article||0).toLocaleString()} • ${Number(a.segment_count||0)}/${Number(a.segment_total||0)} parts</b><span>Size</span><b>${formatBytes(data?.size||a.bytes||0)}</b><span>Dimensions</span><b>${escapeHtml(dims)}</b><span>Date</span><b>${escapeHtml(a.date?new Date(a.date).toLocaleString():'—')}</b>${set.length>=3?`<span>Media set</span><b>${set.length.toLocaleString()} related files</b>`:''}<span>Message-ID</span><code>${escapeHtml(a.message_id||'—')}</code><span>Subject</span><b class="viewer-info-wide">${escapeHtml(a.subject||'—')}</b></div>`}
function updateViewerInfo(a,data=null){if(!els.viewerInfo||!a)return;els.viewerInfo.innerHTML=viewerInfoMarkup(a,data);els.viewerInfo.classList.toggle('hidden',!state.viewerInfoOpen);els.viewerInfoBtn?.classList.toggle('active',state.viewerInfoOpen)}
function updateViewerSelectionState(){
  const a=viewerCurrentArticle();if(!a)return;const selected=state.selectedItems.has(articleKey(a));els.viewerSelectBtn.textContent=selected?'✓ Selected':'Select';els.viewerSelectBtn.classList.toggle('active',selected);const downloaded=state.downloadedIndex.has(itemDownloadKey(a)),queued=state.queuedIndex.has(itemDownloadKey(a));els.viewerQueueBtn.textContent=downloaded?'✓ Downloaded':queued?'⇣ Queued':'⇣ Download';els.viewerQueueBtn.disabled=downloaded||queued;
  const set=viewerSetMembers(a);if(els.viewerSetBtn){els.viewerSetBtn.classList.toggle('hidden',set.length<3);els.viewerSetBtn.classList.toggle('active',state.viewerSetOnly&&set.length>=3);els.viewerSetBtn.textContent=set.length>=3?(state.viewerSetOnly?`Set ${set.length}`:`View set ${set.length}`):'View set'}
}
function applyViewerZoom(){
  const a=viewerCurrentArticle(),img=els.viewerStage.querySelector('img');const isImage=a?.media?.kind==='image';const mode=state.viewerMode||'fit';state.viewerFit=mode==='fit';
  for(const btn of [els.viewerFitBtn,els.viewerFillBtn,els.viewerActualBtn,els.viewerZoomOutBtn,els.viewerZoomInBtn,els.viewerRotateBtn])if(btn)btn.disabled=!isImage;
  els.viewerStage.classList.toggle('video-mode',!isImage);els.viewerStage.classList.toggle('fit',isImage&&mode==='fit');els.viewerStage.classList.toggle('fill',isImage&&mode==='fill');els.viewerStage.classList.toggle('actual',isImage&&mode==='actual');els.viewerStage.classList.toggle('pannable',isImage&&mode==='actual');els.viewerFitBtn?.classList.toggle('active',isImage&&mode==='fit');els.viewerFillBtn?.classList.toggle('active',isImage&&mode==='fill');els.viewerActualBtn?.classList.toggle('active',isImage&&mode==='actual'&&Math.abs(state.viewerZoom-1)<.01);els.viewerZoomLabel.textContent=!isImage?'Video':mode==='fit'?'Fit':mode==='fill'?'Fill':`${Math.round(state.viewerZoom*100)}%`;
  if(!img)return;img.classList.add('viewer-image-rotatable');img.style.transform=`rotate(${state.viewerRotation}deg)`;if(mode!=='actual'){img.style.width='';img.style.height='';return}if(img.naturalWidth){img.style.width=`${Math.max(1,Math.round(img.naturalWidth*state.viewerZoom))}px`;img.style.height='auto'}
}
function setViewerMode(mode){state.viewerMode=['fit','fill','actual'].includes(mode)?mode:'fit';if(state.viewerMode!=='actual')state.viewerZoom=1;applyViewerZoom();if(els.viewerStage){els.viewerStage.scrollLeft=0;els.viewerStage.scrollTop=0}}
function setViewerFit(fit){setViewerMode(fit?'fit':'actual')}
function setViewerFill(){setViewerMode('fill')}
function setViewerActual(){state.viewerZoom=1;setViewerMode('actual')}
function zoomViewer(delta,anchor=null){const a=viewerCurrentArticle(),img=els.viewerStage.querySelector('img');if(a?.media?.kind!=='image'||!img)return;const oldZoom=state.viewerMode==='actual'?state.viewerZoom:Math.min(1,Math.max(.1,(img.clientWidth||img.naturalWidth)/(img.naturalWidth||1)));const rect=els.viewerStage.getBoundingClientRect(),ax=anchor?.x??rect.width/2,ay=anchor?.y??rect.height/2;const contentX=els.viewerStage.scrollLeft+ax,contentY=els.viewerStage.scrollTop+ay;state.viewerMode='actual';state.viewerFit=false;state.viewerZoom=Math.max(.1,Math.min(8,Math.round((Math.max(.1,oldZoom)+delta)*100)/100));applyViewerZoom();requestAnimationFrame(()=>{const ratio=state.viewerZoom/Math.max(.01,oldZoom);els.viewerStage.scrollLeft=Math.max(0,contentX*ratio-ax);els.viewerStage.scrollTop=Math.max(0,contentY*ratio-ay)})}
function rotateViewer(){const a=viewerCurrentArticle();if(a?.media?.kind!=='image')return;state.viewerRotation=(state.viewerRotation+90)%360;applyViewerZoom()}
function toggleViewerInfo(){state.viewerInfoOpen=!state.viewerInfoOpen;updateViewerInfo(viewerCurrentArticle())}
function toggleViewerSet(){const a=viewerCurrentArticle(),members=viewerSetMembers(a);if(members.length<3)return;state.viewerSetOnly=!state.viewerSetOnly;updateViewerSelectionState();renderMediaViewer(a,{keepMode:true})}
function scheduleViewerPreload(){clearTimeout(state.viewerPreloadTimer);state.viewerPreloadTimer=setTimeout(async()=>{if(!state.viewerOpen||viewerActiveDownloads())return;const items=viewerItems(),pos=items.findIndex(a=>articleKey(a)===state.viewerKey),neighbors=[items[pos+1],items[pos-1]].filter(Boolean).filter(a=>!state.previewCache.has(previewKey(a)));if(!neighbors.length)return;const started=performance.now();await Promise.allSettled(neighbors.map(a=>fetchPrepared(a)));perfRecord('viewer_preload',performance.now()-started)},350)}
function closeMediaViewer(){if(!els.mediaViewer)return;clearTimeout(state.viewerPreloadTimer);const ret=state.viewerReturnState;state.viewerOpen=false;state.viewerKey='';state.viewerSetOnly=false;state.viewerInfoOpen=false;state.viewerDrag=null;els.mediaViewer.classList.add('hidden');els.viewerStage.innerHTML='';els.viewerInfo?.classList.add('hidden');state.viewerReturnState=null;if(ret)requestAnimationFrame(()=>{restoreBrowsePosition(ret.anchors,ret.scrollTop);if(ret.key){state.selectedArticleKey=ret.key;updateActiveArticleDomInPlace();const idx=state.articles.findIndex(x=>articleKey(x)===ret.key);const node=idx>=0?els.articlesList.querySelector(`[data-index="${idx}"]`):null;if(node){const list=els.articlesList.getBoundingClientRect(),r=node.getBoundingClientRect();if(r.top<list.top||r.bottom>list.bottom)node.scrollIntoView({block:'nearest'})}}})}
async function openMediaViewer(a){
  if(!a?.media||!['image','video'].includes(a.media.kind)||!a.complete)return;state.viewerReturnState={scrollTop:Number(els.articlesList.scrollTop||0),anchors:captureBrowseAnchors(),key:articleKey(a)};state.viewerOpen=true;state.viewerKey=articleKey(a);state.selectedArticleKey=articleKey(a);state.viewerMode='fit';state.viewerFit=true;state.viewerZoom=1;state.viewerRotation=0;state.viewerSetOnly=!!(state.groupRelatedMedia&&state.activeMediaSetKey);state.viewerInfoOpen=false;els.mediaViewer.classList.remove('hidden');await renderMediaViewer(a)
}
async function renderMediaViewer(a,{keepMode=false}={}){
  if(!state.viewerOpen||!a)return;const key=articleKey(a),isVideo=a.media?.kind==='video';state.viewerKey=key;if(!keepMode){state.viewerRotation=0;if(isVideo)state.viewerMode='fit'}els.viewerTitle.textContent=a.media?.filename||a.subject;els.viewerMeta.textContent=`${a.from||'Unknown poster'} • ${formatBytes(a.bytes)} • ${shortDate(a.date)} • ${a.segment_count}/${a.segment_total} parts`;els.viewerStage.innerHTML=`<div class="viewer-loading"><span></span><p>Loading ${isVideo?'video':'full image'}…</p></div>`;updateViewerSelectionState();updateViewerInfo(a);applyViewerZoom();
  const items=viewerItems(),pos=items.findIndex(x=>articleKey(x)===key);const set=viewerSetMembers(a);els.viewerPosition.textContent=pos>=0?`${(pos+1).toLocaleString()} of ${items.length.toLocaleString()}${state.viewerSetOnly&&set.length>=3?' • media set':''}`:'';els.viewerPrevBtn.disabled=pos<=0;els.viewerNextBtn.disabled=pos<0||pos>=items.length-1;
  try{
    const data=await fetchPrepared(a);if(!state.viewerOpen||state.viewerKey!==key)return;
    if(isVideo){els.viewerStage.innerHTML=`<video class="viewer-video" controls autoplay preload="metadata" src="${data.url}"></video>`;const video=els.viewerStage.querySelector('video');video?.addEventListener('loadedmetadata',()=>{if(!state.viewerOpen||state.viewerKey!==key)return;const dims=video.videoWidth&&video.videoHeight?` • ${video.videoWidth.toLocaleString()}×${video.videoHeight.toLocaleString()}`:'';els.viewerMeta.textContent=`${a.from||'Unknown poster'} • ${formatBytes(data.size||a.bytes)}${dims}${Number.isFinite(video.duration)?' • '+formatDuration(video.duration):''} • ${shortDate(a.date)}`;updateViewerInfo(a,{...data,width:video.videoWidth,height:video.videoHeight})},{once:true})}
    else{const img=document.createElement('img');img.alt=data.filename||a.media.filename||'';img.draggable=false;img.src=data.url;els.viewerStage.replaceChildren(img);const loaded=()=>{if(!state.viewerOpen||state.viewerKey!==key)return;const dims=img.naturalWidth&&img.naturalHeight?` • ${img.naturalWidth.toLocaleString()}×${img.naturalHeight.toLocaleString()}`:'';els.viewerMeta.textContent=`${a.from||'Unknown poster'} • ${formatBytes(data.size||a.bytes)}${dims} • ${shortDate(a.date)}`;updateViewerInfo(a,{...data,width:img.naturalWidth,height:img.naturalHeight});applyViewerZoom()};if(img.complete&&img.naturalWidth)loaded();else img.addEventListener('load',loaded,{once:true})}
    applyViewerZoom();scheduleViewerPreload();
  }catch(e){if(state.viewerOpen&&state.viewerKey===key)els.viewerStage.innerHTML=`<div class="viewer-error"><strong>Could not load ${isVideo?'video':'image'}</strong><span>${escapeHtml(e.message)}</span></div>`}
}
function navigateViewer(delta){const items=viewerItems();if(!items.length)return;let pos=items.findIndex(a=>articleKey(a)===state.viewerKey);if(pos<0)pos=0;const next=Math.max(0,Math.min(items.length-1,pos+delta));if(next===pos)return;const a=items[next];state.selectedArticleKey=articleKey(a);renderMediaViewer(a);renderPreviewDetails(a,false)}
function toggleViewerSelection(){const a=viewerCurrentArticle();if(!a)return;const key=articleKey(a);if(state.selectedItems.has(key))state.selectedItems.delete(key);else{state.selectedItems.set(key,a);state.selectionAnchorKey=key}updateViewerSelectionState();updateSelectionBar();updateSelectionDomInPlace()}
function viewerWheel(e){if(!state.viewerOpen||viewerCurrentArticle()?.media?.kind!=='image'||isEditableTarget(e.target))return;e.preventDefault();const r=els.viewerStage.getBoundingClientRect();zoomViewer(e.deltaY<0?.15:-.15,{x:e.clientX-r.left,y:e.clientY-r.top})}
function viewerPointerDown(e){if(!state.viewerOpen||state.viewerMode!=='actual'||e.button!==0||!e.target.closest('img'))return;state.viewerDrag={x:e.clientX,y:e.clientY,left:els.viewerStage.scrollLeft,top:els.viewerStage.scrollTop};els.viewerStage.classList.add('dragging');try{els.viewerStage.setPointerCapture(e.pointerId)}catch{}}
function viewerPointerMove(e){const d=state.viewerDrag;if(!d)return;els.viewerStage.scrollLeft=d.left-(e.clientX-d.x);els.viewerStage.scrollTop=d.top-(e.clientY-d.y)}
function viewerPointerUp(e){if(!state.viewerDrag)return;state.viewerDrag=null;els.viewerStage.classList.remove('dragging');try{els.viewerStage.releasePointerCapture(e.pointerId)}catch{}}

function updateSelectionDomInPlace(){
  els.articlesList.querySelectorAll('.media-card[data-index],.article-row[data-index]').forEach(node=>{const a=state.articles[Number(node.dataset.index)];if(!a)return;const selected=state.selectedItems.has(articleKey(a));node.classList.toggle('selected',selected);node.setAttribute('aria-selected',selected?'true':'false');const stage=node.querySelector('.thumb-stage');if(stage){stage.querySelector('.selection-check')?.remove();if(selected&&isSelectableMedia(a))stage.insertAdjacentHTML('beforeend','<span class="selection-check" aria-hidden="true">✓</span>')}const top=node.querySelector('.article-top');if(top){top.querySelector('.row-selection-check')?.remove();if(selected&&isSelectableMedia(a))top.insertAdjacentHTML('beforeend','<span class="row-selection-check" aria-hidden="true">✓</span>')}});
  els.articlesList.querySelectorAll('.binary-set-row[data-binary-set-key]').forEach(node=>{const group=state.binarySetGroups.get(node.dataset.binarySetKey);if(!group)return;const sel=binarySetSelectionState(group);node.classList.toggle('selected',sel.all);node.classList.toggle('partial',sel.partial);node.setAttribute('aria-selected',sel.all?'true':'false');const btn=node.querySelector('.binary-set-select');if(btn)btn.textContent=sel.all?'✓ Selected':sel.partial?`${sel.selected}/${sel.selectable.length} selected`:'Select set';});
}
function resetPreview(){
  els.previewBadge.className='preview-badge';els.previewBadge.textContent='READY';els.previewContent.className='preview-content preview-empty';
  els.previewContent.innerHTML=isAllPostsMode()
    ?'<div class="preview-orb">☷</div><h3>Binary newsgroup browser</h3><p>All Posts uses a compact filename-first list. Connected RAR, ZIP, 7-Zip, PAR2, and split-file volumes can collapse into one selectable package.</p><div class="feature-mini"><span>✓</span> Connected binary sets</div><div class="feature-mini"><span>✓</span> Multipart file assembly</div><div class="feature-mini"><span>✓</span> Queue complete sets together</div>'
    :'<div class="preview-orb">▦</div><h3>Visual newsgroup browser</h3><p>Image and video thumbnails load as you scroll. Click one for a larger preview, then download only what you want.</p><div class="feature-mini"><span>✓</span> Faster image + video thumbnails</div><div class="feature-mini"><span>✓</span> yEnc + multipart assembly</div><div class="feature-mini"><span>✓</span> Selective downloads</div>';
}
function renderPreviewDetails(a,auto=false){
  markArticleSeen(a);els.previewBadge.className=`preview-badge ${a.media?'active':''}`;els.previewBadge.textContent=a.media?a.media.kind.toUpperCase():'ARTICLE';
  const canDownload=!!(a.media&&a.complete),canPreview=!!(canDownload&&['image','video'].includes(a.media?.kind));const mediaName=a.media?.filename||'No directly downloadable binary detected';const cached=state.previewCache.get(previewKey(a));
  if(cached&&canPreview){showPreparedPreview(a,cached);return}
  els.previewContent.className='preview-content';
  if(auto&&a.media?.kind==='image'&&a.complete){
    els.previewBadge.textContent='LOADING';els.previewContent.innerHTML=`<div class="preview-loading"><div class="preview-spinner"></div><h3>Loading image…</h3><p>${escapeHtml(mediaName)}</p></div>`;preparePreview(a);return;
  }
  const previewLabel=canPreview?(a.media?.kind==='video'?'Load video preview':'Load preview'):a.media?.kind==='file'?'No preview for this file type':a.media&&!a.complete?'Multipart set is incomplete':'No media detected';
  els.previewContent.innerHTML=`<div class="preview-details"><h3>${escapeHtml(a.subject)}</h3><div class="preview-meta-grid"><div class="meta-card"><label>Detected</label><b>${escapeHtml(a.media?.kind||'Article')}</b></div><div class="meta-card"><label>Size</label><b>${formatBytes(a.bytes)}</b></div><div class="meta-card"><label>Segments</label><b>${a.segment_count}/${a.segment_total}</b></div><div class="meta-card"><label>Date</label><b>${escapeHtml(shortDate(a.date))}</b></div></div><div class="meta-card" style="margin-bottom:12px"><label>Binary file</label><b title="${escapeHtml(mediaName)}">${escapeHtml(mediaName)}</b></div><div class="preview-identity-grid"><div><label>Newsgroup</label><b>${escapeHtml(articleGroup(a))}</b></div><div><label>Poster</label><b>${escapeHtml(a.from||'—')}</b></div><div class="wide"><label>Message-ID</label><code>${escapeHtml(a.message_id||'—')}</code></div></div><button id="preparePreviewBtn" class="preview-action" ${canPreview?'':'disabled'}>${previewLabel}</button>${canDownload?'<button id="downloadPreviewBtn" class="preview-download">＋ Add this file to queue</button>':''}<p class="preview-note">Images and videos can be previewed in-app. Other binary files can be selected and queued directly without downloading their bodies during search.</p></div>`;
  if(canPreview)$('preparePreviewBtn').onclick=()=>preparePreview(a);if(canDownload)$('downloadPreviewBtn').onclick=e=>downloadItems([a],e.currentTarget);
}

async function preparePreview(a){
  els.previewBadge.textContent='LOADING';
  try{const data=await fetchPrepared(a);if(state.selectedArticleKey===articleKey(a))showPreparedPreview(a,data);updateThumbnailDom(state.articles.indexOf(a),data);}
  catch(e){const info=friendlyPreviewError(e);if(rememberUnsupportedMedia(a,info)){if(!hideUnavailableArticleByKey(a))renderArticles({preserveScroll:true});toast('Post hidden from media views because no supported binary attachment was found.');return}toast(e.message,'error');if(state.selectedArticleKey===articleKey(a))renderPreviewFailure(a,e)}
}
function showPreparedPreview(a,data){
  els.previewBadge.textContent='PREVIEW';els.previewBadge.className='preview-badge active';els.previewContent.className='preview-content';
  const media=data.kind==='image'?`<img src="${data.url}" alt="${escapeHtml(data.filename)}">`:`<video src="${data.url}" controls autoplay preload="metadata"></video>`;
  const viewerButton=['image','video'].includes(data.kind)?'<button id="openViewerBtn" class="preview-download">⛶ Open media viewer</button>':'';
  els.previewContent.innerHTML=`<div class="media-stage">${media}</div><div class="media-filebar"><strong>${escapeHtml(data.filename)}</strong><span>${formatBytes(data.size)} • ${data.cached?'cached locally':'retrieved from Usenet'}</span>${viewerButton}<button id="downloadPreparedBtn" class="preview-download">＋ Add to queue</button></div>`;
  $('openViewerBtn')?.addEventListener('click',()=>openMediaViewer(a));$('downloadPreparedBtn').onclick=e=>downloadItems([a],e.currentTarget);
}
function renderPreviewFailure(a,error){
  const info=friendlyPreviewError(error);els.previewBadge.textContent='ERROR';els.previewContent.className='preview-content';els.previewContent.innerHTML=`<div class="preview-failure"><span>!</span><div class="preview-failure-code">${escapeHtml(info.label)}</div><h3>Could not preview this post</h3><p>${escapeHtml(info.message)}</p>${info.retryable?'<button id="retryPreviewBtn" class="preview-action">Retry preview</button>':''}</div>`;if(info.retryable)$('retryPreviewBtn').onclick=()=>preparePreview(a);
}

function browserSetCollectionId(){return `browser-${Date.now().toString(36)}-${Math.random().toString(36).slice(2,10)}`}
function browserSetCollectionRole(a){
  const filename=String(a?.media?.filename||'').toLocaleLowerCase(),descriptor=binarySetDescriptor(a);if(descriptor?.family==='SIDECAR')return'auxiliary';
  if(filename.endsWith('.par2'))return /\.vol\d+[+_]\d+\.par2$/i.test(filename)?'recovery_par2':'par2';return'payload';
}
function browserSetCollectionAssignments(items){
  const assignments=new Map();if(!isAllPostsMode()||!state.groupBinarySets||!state.binarySetGroups.size)return assignments;const keys=new Set(items.map(articleKey));
  for(const group of state.binarySetGroups.values()){
    if(!group.members.length||!group.members.every(x=>isSelectableMedia(x.a)&&keys.has(articleKey(x.a))))continue;
    const collectionId=browserSetCollectionId(),required=group.members.filter(x=>browserSetCollectionRole(x.a)!=='auxiliary').length;
    const meta={id:collectionId,name:group.displayTitle||group.base,expected:group.members.length,required};for(const x of group.members)assignments.set(articleKey(x.a),meta);
  }
  return assignments;
}
async function downloadItems(items,button=null){
  const valid=items.filter(a=>a?.media&&a.complete);if(!valid.length){toast(isAllPostsMode()?'No complete downloadable binaries selected.':'No complete media items selected.','error');return}
  const old=button?.textContent;if(button){button.disabled=true;button.textContent='Adding…'}
  try{
    const collectionAssignments=browserSetCollectionAssignments(valid),collectionIds=new Set();
    const byGroup=new Map();for(const a of valid){const g=articleGroup(a);if(!g)continue;if(!byGroup.has(g))byGroup.set(g,[]);byGroup.get(g).push(a)}
    let added=0,dupes=0;const warnings=[];
    for(const [group,groupItems] of byGroup){
      const payload=groupItems.map(a=>{const collection=collectionAssignments.get(articleKey(a)),role=collection?browserSetCollectionRole(a):'';if(collection)collectionIds.add(collection.id);return{segments:segmentPayload(a),media:a.media,subject:a.subject||'',from:a.from||'',message_id:a.message_id||'',...(collection?{source:'browser_set',collection_id:collection.id,collection_name:collection.name,collection_expected:collection.expected,collection_required_expected:collection.required,destination_subdir:collection.name,collection_role:role,is_auxiliary:role==='auxiliary',is_par2:role==='par2'||role==='recovery_par2',is_par2_volume:role==='recovery_par2'}:{})}});
      const data=await api('/api/downloads/add',{provider_id:state.providerId,group,items:payload});added+=data.added?.length||0;dupes+=data.duplicates?.length||0;if(data.disk_warning)warnings.push(data.disk_warning)
    }
    if(added){const packageCount=collectionIds.size;toast(packageCount?`${added} file${added===1?'':'s'} added as ${packageCount} grouped package${packageCount===1?'':'s'}.`:`${added} file${added===1?'':'s'} added to the download queue.`,'success')}
    if(dupes)toast(`${dupes} item${dupes===1?' was':'s were'} already queued.`);if(warnings[0])toast(warnings[0],'error');
    for(const x of valid)state.selectedItems.delete(articleKey(x));updateSelectionBar();renderArticles();await loadDownloads();
  }catch(e){toast(e.message,'error')}finally{if(button){button.disabled=false;button.textContent=old}if(state.viewerOpen)updateViewerSelectionState()}
}


function uiMotionReduced(){return !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches}
function replayUiAnimation(el,cls='ui-fresh',ms=460){if(!el||uiMotionReduced())return;el.classList.remove(cls);void el.offsetWidth;el.classList.add(cls);window.setTimeout(()=>el.classList.remove(cls),ms)}
function animateMainView(view){const map={browse:els.browseView,downloads:els.downloadsView,diagnostics:els.diagnosticsView,automation:els.automationView,discover:els.discoverView};requestAnimationFrame(()=>replayUiAnimation(map[view],'view-enter',420))}
function animateDynamicSurface(el){requestAnimationFrame(()=>replayUiAnimation(el,'content-enter',360))}
function formatSpeed(n){return n>0?`${formatBytes(n)}/s`:'—'}
function formatEta(seconds){seconds=Number(seconds||0);if(!Number.isFinite(seconds)||seconds<=0)return '—';if(seconds<60)return `${Math.ceil(seconds)}s`;if(seconds<3600)return `${Math.ceil(seconds/60)}m`;const h=Math.floor(seconds/3600),m=Math.ceil((seconds%3600)/60);return `${h}h ${m}m`}
function setMainView(view){
  if(state.activeView==='browse'&&view!=='browse'){state.browseScrollTop=els.articlesList.scrollTop;rotateBrowsePreviewSession()}
  state.activeView=view;els.browseView.classList.toggle('hidden',view!=='browse');els.downloadsView.classList.toggle('hidden',view!=='downloads');els.diagnosticsView.classList.toggle('hidden',view!=='diagnostics');els.automationView?.classList.toggle('hidden',view!=='automation');els.discoverView?.classList.toggle('hidden',view!=='discover');
  $('navBrowse').classList.toggle('active',view==='browse');$('navDownloads').classList.toggle('active',view==='downloads');$('navDiagnostics').classList.toggle('active',view==='diagnostics');$('navDiscover')?.classList.toggle('active',view==='discover');document.querySelectorAll('.sidebar [data-auto-tab]').forEach(b=>b.classList.toggle('active',view==='automation'&&b.dataset.autoTab===state.automationTab));
  document.querySelectorAll('.sidebar .nav-item').forEach(b=>{if(b.classList.contains('active'))b.setAttribute('aria-current','page');else b.removeAttribute('aria-current')});
  animateMainView(view);
  if(view==='downloads'){loadDownloads({livePatch:true});scheduleNextDownloadPoll(0)}else if(view==='diagnostics')loadDiagnostics();else if(view==='automation'){loadAutomation({quiet:true});renderAutomation()}else if(view==='discover'){initDiscoverControls();loadDiscover()}else if(view==='browse')requestAnimationFrame(()=>{els.articlesList.scrollTop=state.browseScrollTop||0;wireContinuousObserver();scheduleThumbnailDemandScan();schedulePredictiveHeaderPrefetch()});
}
function formatUptime(seconds){seconds=Math.max(0,Number(seconds||0));const d=Math.floor(seconds/86400),h=Math.floor((seconds%86400)/3600),m=Math.floor((seconds%3600)/60);return d?`${d}d ${h}h`:h?`${h}h ${m}m`:`${m}m`}
function healthClass(status){return status==='connected'?'good':status==='error'?'bad':'standby'}
async function loadDiagnostics(){
  try{state.diagnosticsSnapshot=await api('/api/diagnostics');renderDiagnostics()}catch(e){if(state.activeView==='diagnostics')toast(e.message,'error')}
}
function renderDiagnostics(){
  const d=state.diagnosticsSnapshot||{},conn=d.connections||{},storage=d.storage||{},disk=storage.disk||{},cache=storage.thumbnail_cache||{};
  $('diagMemory').textContent=formatBytes(d.memory_bytes||0);$('diagDiskFree').textContent=formatBytes(disk.free||0);$('diagDiskPath').textContent=disk.path||'Download folder';
  const pipelineDepth=Math.max(1,...(Array.isArray(conn.pools)?conn.pools.map(x=>Number(x.pipeline_enabled===false?1:x.pipeline_depth||1)): [1]));$('diagConnections').textContent=Number(conn.active||0).toLocaleString();const connTarget=Number(conn.effective_capacity||conn.capacity||0);$('diagConnectionsDetail').textContent=`${Number(conn.open||0)} warm • ${connTarget} active target / ${Number(conn.capacity||0)} download slots${Number(conn.configured||0)?` • ${Number(conn.configured||0)} configured`:''} • pipeline ×${pipelineDepth}`;
  $('diagRetries').textContent=Number(conn.retries||0).toLocaleString();$('diagFailures').textContent=`${Number(conn.failed_segments||0).toLocaleString()} failed segments`;
  $('diagThumbCache').textContent=formatBytes(cache.bytes||0);$('diagThumbFiles').textContent=`${Number(cache.files||0).toLocaleString()} cached thumbnails`; $('diagUptime').textContent=formatUptime(d.uptime_seconds||0);
  const cloud=d.metadata_cloud||{},cloudStatus=String(cloud.status||'unknown').toUpperCase();if($('diagCloudStatus')){$('diagCloudStatus').textContent=cloudStatus;$('diagCloudStatus').className=`cloud-health ${cloud.status||'unknown'}`;const cloudBits=[];if(cloud.server_version)cloudBits.push(`Server v${cloud.server_version}`);if(cloud.tmdb_status&&cloud.tmdb_status!=='unknown')cloudBits.push(`TMDB ${String(cloud.tmdb_status).toUpperCase()}`);if(cloud.circuit_open)cloudBits.push(`retry in ~${Number(cloud.circuit_retry_seconds||0)}s`);if(cloud.cached_fallbacks)cloudBits.push(`${Number(cloud.cached_fallbacks)} cached fallback${Number(cloud.cached_fallbacks)===1?'':'s'}`);$('diagCloudDetail').textContent=cloudBits.join(' • ')||(cloud.url||'api.newzdeck.com');$('diagCloudAuth').textContent=cloud.authenticated?'REGISTERED':'NOT REGISTERED';$('diagCloudAuth').className=`cloud-health ${cloud.authenticated?'online':'unknown'}`;$('diagCloudAuthDetail').textContent=cloud.compatible===false?`Client update required • minimum v${cloud.min_client_version||'?'}`:(cloud.authenticated?'Per-installation credential active':'Will register automatically when required');}
  const providers=d.providers||[];const good=providers.filter(p=>p.status==='connected').length,bad=providers.filter(p=>p.status==='error').length;$('diagProviderSummary').textContent=providers.length?`${good} active • ${bad} with recent errors • ${providers.length-good-bad} standby`:'No providers configured';
  $('providerHealthRows').innerHTML=providers.length?providers.map(p=>{const pool=p.pool||{},rate=p.success_rate==null?'—':`${Number(p.success_rate).toFixed(1)}%`,lat=p.last_latency_ms?`${Number(p.last_latency_ms).toFixed(0)} ms`:'—';return `<div class="provider-health-row"><span><strong>${escapeHtml(p.name)}</strong><small>${escapeHtml(p.host)}:${Number(p.port)}</small><em class="provider-role-note">${escapeHtml((p.role||'primary')+' provider')}</em></span><span><b class="health-pill ${healthClass(p.status)}">${escapeHtml(String(p.status||'standby').toUpperCase())}</b></span><span>${lat}</span><span>${rate}</span><span>${Number(pool.active||0)}/${Number(pool.capacity||0)}<small>${Number(pool.open||0)} warm</small></span><span>${formatBytes(p.bytes||0)}</span><span>${Number(pool.retries||0).toLocaleString()}</span><span class="health-error" title="${escapeHtml(p.last_error||'')}">${escapeHtml(p.last_error||'—')}</span></div>`}).join(''):'<div class="diag-empty">Add an NNTP provider to see health information.</div>';
  const dl=d.downloads||{},counts=dl.counts||{},searches=d.searches||[],tel=dl.telemetry||{},thumbDecode=d.thumbnail_decode||{},thumbTransfer=d.thumbnail_transfer||{},thumbHelper=thumbDecode.helper||{},thumbCatalog=d.thumbnail_catalog||{},thumbToken=thumbCatalog.token_cache||{};$('diagEngineActivity').innerHTML=`<div><span>Download engine</span><strong>${Number(counts.downloading||0)} downloading • ${Number(counts.queued||0)} queued</strong></div><div><span>Transfer speed</span><strong>${formatSpeed(dl.speed_bps||0)}</strong></div><div><span>Pipeline rates</span><strong>Net ${formatSpeed(tel.network_rate_bps||0)} • Decode ${Number(tel.decode_rate_bps||0)?formatSpeed(tel.decode_rate_bps):'—'} • Disk ${Number(tel.disk_rate_bps||0)?formatSpeed(tel.disk_rate_bps):'—'}</strong></div><div><span>Active-card continuity</span><strong>${Number(tel.active_card_continuity_bridges||0).toLocaleString()} SAB handoff bridge${Number(tel.active_card_continuity_bridges||0)===1?'':'s'}</strong></div><div><span>Hidden-transfer cleanup</span><strong>${Number(tel.removed_orphan_cleanup_count||0).toLocaleString()} verified cleanup${Number(tel.removed_orphan_cleanup_count||0)===1?'':'s'}</strong></div><div><span>Thumbnail BODY</span><strong>${Number(thumbTransfer.runs||0)?`avg ${Math.round(Number(thumbTransfer.average_ms||0))} ms • ${Number(thumbTransfer.parallel_runs||0)} parallel • max ${Number(thumbTransfer.max_lanes||1)} lanes`:'No samples yet'}</strong></div><div><span>Thumbnail decode</span><strong>${Number(thumbDecode.runs||0)?`avg ${Math.round(Number(thumbDecode.average_decode_ms||0))} ms • wait ${Math.round(Number(thumbDecode.average_wait_ms||0))} ms • WIC ${Number(thumbDecode.wic_runs||0)} / fallback ${Number(thumbDecode.fallback_runs||0)}`:`${Number(thumbDecode.workers||0)} workers • no samples yet`}</strong></div><div><span>Native thumbnail workers</span><strong>${Number(thumbHelper.jobs||0)?`${Number(thumbHelper.jobs||0)} jobs • ${Number(thumbHelper.process_launches_avoided||0)} launches avoided • ${Number(thumbHelper.reuse_rate_percent||0)}% reuse • ${Number(thumbHelper.blank_rejections||0)} native blank rejects`:`${Number(thumbHelper.workers||0)} persistent workers ready`}</strong></div><div><span>Thumbnail RAM index</span><strong>${Number(thumbCatalog.entries||0).toLocaleString()} entries • ${Number(thumbCatalog.hits||0).toLocaleString()} hits • ${Number(thumbCatalog.filesystem_fallbacks||0).toLocaleString()} FS fallbacks • token ${Number(thumbToken.hits||0).toLocaleString()} hits</strong></div><div><span>Next-page warming</span><strong>${Number(state.speculativeThumbStats.completed||0)} warmed • ${Number(state.speculativeThumbStats.cancelled||0)} yielded</strong></div><div><span>Thumbnail DOM registry</span><strong>${Number(state.thumbHolderRegistry.size||0).toLocaleString()} live • ${Number(state.thumbHolderRegistryStats.hits||0).toLocaleString()} direct hits • ${Number(state.thumbHolderRegistryStats.fallbacks||0).toLocaleString()} fallbacks</strong></div><div><span>Recovery health</span><strong>${Number(tel.soft_misses||0)} soft misses • ${Number(tel.native_parts||0).toLocaleString()} native blocks</strong></div><div><span>Header searches</span><strong>${searches.length} entire-group search${searches.length===1?'':'es'} active</strong></div><div><span>Browser timings</span><strong>${escapeHtml(perfSummaryText())}</strong></div><div><span>Preview cache</span><strong>${formatBytes(storage.preview_cache_bytes||0)}</strong></div><div><span>Download scratch</span><strong>${formatBytes(storage.download_temp_bytes||0)}</strong></div><div><span>Persistent data</span><strong>${formatBytes(storage.data_bytes||0)}</strong></div><div><span>NZB automation</span><strong>${d.automation?.watch_enabled?`Watch on • ${Number(d.automation.watch_imported||0)} imported${Number(d.automation.watch_failed||0)?` • ${Number(d.automation.watch_failed)} failed`:''}`:'Watch folder off'}${d.automation?.bandwidth?.active?` • cap ${Number(d.automation.bandwidth.limit_mb_s||0)} MB/s`:''}</strong></div>`;
  const events=d.events||[];$('diagEvents').innerHTML=events.length?events.slice(0,30).map(e=>`<div class="diag-event ${escapeHtml(e.level||'info')}"><span>${new Date(Number(e.ts||0)*1000).toLocaleTimeString()}</span><div><strong>${escapeHtml((e.area||'app').toUpperCase())}</strong><p>${escapeHtml(e.message||'')}</p></div></div>`).join(''):'<div class="diag-empty">No recent reliability events. That is a good sign.</div>';
}
async function probeProviders(){const b=$('probeProvidersBtn'),old=b.textContent;b.disabled=true;b.textContent='Testing…';try{const r=await api('/api/diagnostics/probe',{});state.diagnosticsSnapshot=r.diagnostics;renderDiagnostics();const failed=(r.results||[]).filter(x=>!x.ok).length;toast(failed?`${failed} provider test${failed===1?'':'s'} failed.`:'Provider health tests passed.',failed?'error':'success')}catch(e){toast(e.message,'error')}finally{b.disabled=false;b.textContent=old}}
async function copyDiagnostics(){try{const d=await api('/api/diagnostics/report');const report=`${d.report}\nBrowser timings: ${perfSummaryText()}`;if(navigator.clipboard?.writeText){await navigator.clipboard.writeText(report);toast('Diagnostic report copied.','success')}else{window.prompt('Copy diagnostic report:',report)}}catch(e){toast(e.message,'error')}}
function downloadVisible(job){
  const term=String(state.downloadSearchTerm||'').trim().toLowerCase();if(term){const hay=[job.filename,job.collection_name,job.provider_name,job.origin_provider_name,job.group,job.status,job.post_status,job.category].join(' ').toLowerCase();if(!hay.includes(term))return false;}
  const f=state.downloadFilter,s=job.status,post=String(job.post_status||'');
  if(f==='active')return ['downloading','retry_wait','cancelling'].includes(s);
  if(f==='queued')return s==='queued';
  if(f==='post'){
    // A terminal SAB transfer failure is a Failed download, not post-processing.
    // Keep completed/import-side failures in Post-processing so Retry Import remains
    // available, but route bad/expired posts only to the Failed tab.
    if(['failed','cancelled'].includes(s))return false;
    return ['queued','waiting','verifying','repairing','extracting','importing','needs_password','needs_tool','needs_attention','blocked','failed','cancelled'].includes(post);
  }
  if(f==='completed')return s==='completed'&&['','completed','not_needed','disabled'].includes(post);
  if(f==='failed')return ['failed','cancelled'].includes(s)||['failed','needs_attention','needs_tool','blocked','cancelled'].includes(post);
  return true;
}
function updateDownloadNavSummary(downloads=state.downloadSnapshot||{}){
  const c=downloads.counts||{},retryWaiting=Number(c.retry_wait||0),activeNow=Number(c.downloading||0)+Number(c.cancelling||0)+retryWaiting,queueActivity=activeNow+Number(c.queued||0);
  if(els.downloadNavBadge){els.downloadNavBadge.textContent=queueActivity;els.downloadNavBadge.classList.toggle('hidden',queueActivity===0)}
}
async function loadDownloads({render=true,livePatch=false,quiet=false}={}){
  const requestId=++downloadSnapshotRequestId;
  try{
    const downloads=await api('/api/downloads',null,{timeoutMs:3500,timeoutMessage:'Downloads status took too long to respond. NewzDeck will retry automatically.'});
    // Reject both an older browser request and an older backend snapshot. The
    // latter matters when Windows resumes from sleep and queued HTTP responses can
    // complete in an unexpected order.
    const snapshotSeq=Number(downloads?.snapshot_seq||0);
    if(requestId<downloadSnapshotAppliedId||(snapshotSeq&&snapshotSeq<downloadSnapshotAppliedSeq))return downloads;
    downloadSnapshotAppliedId=requestId;if(snapshotSeq)downloadSnapshotAppliedSeq=snapshotSeq;
    state.downloadSnapshot=downloads;recalculatePreviewConcurrency();updateDownloadNavSummary(downloads);
    const changed=rebuildDownloadIndexes();
    const settingsOpen=els.settingsModal&&!els.settingsModal.classList.contains('hidden');
    if(render&&state.activeView==='downloads'&&!settingsOpen)renderDownloads({livePatch});
    if(changed){if(state.activeView==='browse'&&state.viewMode==='list'&&state.selectedGroup)renderArticles();else updateDownloadBadgesInPlace();if(state.viewerOpen)updateViewerSelectionState();}
    return downloads;
  }catch(e){if(!quiet&&requestId===downloadSnapshotRequestId&&!state.serviceTransition&&state.activeView==='downloads')toast(e.message,'error')}
}
function downloadCompletedSortValue(item){
  const completed=Number(item?.completed_ts||0);
  if(Number.isFinite(completed)&&completed>0)return completed;
  const started=Number(item?.started_ts||0), created=Number(item?.created_ts||0);
  return Math.max(Number.isFinite(started)?started:0,Number.isFinite(created)?created:0);
}
function sortDownloadsForCurrentView(items){
  const out=[...(items||[])];
  if(state.downloadFilter==='completed'){
    out.sort((a,b)=>{
      const aCompleted=Number(a?.completed_ts||0), bCompleted=Number(b?.completed_ts||0);
      if(aCompleted!==bCompleted && (aCompleted>0||bCompleted>0))return bCompleted-aCompleted;
      const aRank=Number(a?.history_rank??1e9), bRank=Number(b?.history_rank??1e9);
      if(aRank!==bRank && (aRank<1e9||bRank<1e9))return aRank-bRank;
      const byFallback=downloadCompletedSortValue(b)-downloadCompletedSortValue(a);
      if(byFallback)return byFallback;
      return String(b?.id||'').localeCompare(String(a?.id||''));
    });
  }
  return out;
}
function visibleDownloadJobs(){return sortDownloadsForCurrentView((state.downloadSnapshot?.jobs||[]).filter(downloadVisible))}
function updateDownloadSelectionBar(){
  const count=state.selectedDownloads.size;els.downloadSelectionBar.classList.toggle('hidden',count===0);els.downloadSelectionCount.textContent=`${count.toLocaleString()} selected`;
}
function handleDownloadRowSelection(id,e){
  if(e.target.closest('button,select,a,input'))return;const jobs=visibleDownloadJobs(),add=!!(e.ctrlKey||e.metaKey),range=!!e.shiftKey;
  if(range&&state.downloadSelectionAnchor){const a=jobs.findIndex(j=>String(j.id)===state.downloadSelectionAnchor),b=jobs.findIndex(j=>String(j.id)===id);if(!add)state.selectedDownloads.clear();if(a>=0&&b>=0){for(let i=Math.min(a,b);i<=Math.max(a,b);i++)state.selectedDownloads.add(String(jobs[i].id));}else state.selectedDownloads.add(id)}
  else if(add){if(state.selectedDownloads.has(id))state.selectedDownloads.delete(id);else state.selectedDownloads.add(id);state.downloadSelectionAnchor=id}
  else{state.selectedDownloads.clear();state.selectedDownloads.add(id);state.downloadSelectionAnchor=id}
  renderDownloads();
}
function downloadRetryCountdown(job){const ts=Number(job.retry_at_ts||0);if(!ts)return 0;return Math.max(0,Math.ceil(ts-Date.now()/1000))}
function downloadDiagnosticsText(job){
  const errors=Array.isArray(job.segment_errors)?job.segment_errors:[];
  const lines=[
    `NewzDeck download diagnostics`,
    `File: ${job.filename||''}`,
    `Status: ${job.status||''}`,
    `Status detail: ${job.status_detail||''}`,
    `Newsgroup: ${job.group||''}`,
    `Primary provider: ${job.provider_name||''}`,
    `Origin provider: ${job.origin_provider_name||''}`,
    `Blocks: ${Number(job.successful_parts||0)} good / ${Number(job.total_parts||0)} total; ${Number(job.failed_parts||0)} failed`,
    `Downloaded: ${formatBytes(job.downloaded_bytes||0)} / ${formatBytes(job.expected_bytes||0)}`,
    `Current speed: ${formatSpeed(job.speed_bps||0)}; peak: ${formatSpeed(job.peak_speed_bps||0)}; connections: ${Number(job.connections_used||0)}`,
    `Pipeline: ${job.pipeline||'standard'}; native decoded parts: ${Number(job.native_parts||0)}`,
    `Retries: ${Number(job.retry_count||0)}; recovered blocks: ${Number(job.recovered_parts||0)}; reused blocks: ${Number(job.resumed_parts||0)}`,
    `Failure: ${job.error_label||''} ${job.error||''}`,
    `Suggested action: ${job.error_suggestion||''}`,
  ];
  if(errors.length){
    lines.push('',`Failed blocks (${errors.length} shown):`);
    for(const f of errors){
      lines.push(`- Part ${f.part||Number(f.index||0)+1}: ${f.label||f.code||'failed'} — ${f.error||''}`);
      for(const a of (f.attempts||[]))lines.push(`    ${a.provider||'Provider'} attempt ${a.attempt||'?'}: ${a.label||a.code||''} — ${a.error||''}`);
    }
  }
  return lines.join('\n');
}
function toggleDownloadDetails(id){const key=String(id);if(state.expandedDownloads.has(key))state.expandedDownloads.delete(key);else state.expandedDownloads.add(key);renderDownloads()}
function copyDownloadJobDiagnostics(id){const job=(state.downloadSnapshot?.jobs||[]).find(j=>String(j.id)===String(id));if(job)copyText(downloadDiagnosticsText(job))}
function packageStatusLabel(pkg){
  const s=String(pkg.status||'queued'),p=String(pkg.post_status||'');
  if(String(pkg.direct_unpack_status||'')==='active'&&s==='downloading')return 'DOWNLOADING + UNPACKING';
  // Transfer failure is terminal download state even though SAB labels its history
  // post-processing field Failed. Do not mislabel a bad post as POST FAILED.
  if(s==='failed')return 'FAILED';if(s==='cancelled')return 'CANCELLED';
  if(p==='repairing')return 'REPAIRING';if(p==='verifying')return 'VERIFYING';if(p==='extracting')return 'EXTRACTING';if(p==='importing')return 'IMPORTING';
  if(p==='needs_password')return 'PASSWORD NEEDED';if(p==='failed')return String(pkg.import_status||'')==='failed'?'IMPORT FAILED':'POST FAILED';
  const labels={post_processing:'POST-PROCESSING',repair_needed:'REPAIR NEEDED',retry_wait:'RETRY WAIT',downloading:'DOWNLOADING',queued:'QUEUED',failed:'FAILED',cancelled:'CANCELLED',completed:'COMPLETED'};
  return labels[s]||String(s).replaceAll('_',' ').toUpperCase();
}
function postPipelineHtml(pkg){
  const p=String(pkg.post_status||''),status=String(pkg.status||'');
  const stages=[['download','Download'],['verify','Verify'],['repair','Repair'],['extract','Unpack'],['import','Import'],['done','Done']];
  if(String(pkg.direct_unpack_status||'')==='active'){return `<div class="package-pipeline">${stages.map(([key,label])=>`<span class="${['download','extract'].includes(key)?'active':''}"><i></i>${label}</span>`).join('')}</div>`;}
  let rank=0;
  if(status==='completed'||status==='repair_needed'||p)rank=1;
  if(['verifying','repairing','extracting','importing','completed','not_needed','needs_tool','failed','needs_password'].includes(p))rank=2;
  if(['repairing','extracting','importing','completed'].includes(p))rank=3;
  if(['extracting','importing','completed'].includes(p))rank=4;
  if(['importing','completed'].includes(p))rank=5;
  if(['completed','not_needed','disabled'].includes(p)||status==='completed'&&!p)rank=6;
  const active=p==='repairing'?'repair':p==='extracting'?'extract':p==='importing'?'import':p==='verifying'?'verify':status==='downloading'?'download':'';
  return `<div class="package-pipeline">${stages.map(([key,label],i)=>`<span class="${i<rank?'done':''} ${key===active?'active':''}"><i></i>${label}</span>`).join('')}</div>`;
}
function packageHealthHtml(pkg){
  const h=pkg.health||{},state=String(h.state||'healthy');
  if(state==='healthy')return `<span class="package-health healthy">✓ HEALTHY</span>`;
  const needed=Number(h.estimated_blocks_needed||0),available=Number(h.recovery_blocks_available||0);
  const detail=needed?`${needed} needed • ${available} available`:h.missing_articles?`${Number(h.missing_articles)} unavailable article blocks`:'';
  return `<span class="package-health ${escapeHtml(state)}">${escapeHtml(h.label||'Needs attention')}${detail?` • ${escapeHtml(detail)}`:''}</span>`;
}
function postProgressPresentation(item,keyPrefix='job'){
  const status=String(item?.post_status||''),active=['queued','verifying','repairing','extracting','importing'].includes(status);
  let progress=Math.max(0,Math.min(100,Number(item?.post_progress||0))),known=item?.post_progress_known===true;
  const id=String(item?.id||item?.identity||'');
  if(!id||!active)return {status,progress,known,indeterminate:active&&!known};
  const key=`${keyPrefix}:${id}`,now=Date.now(),prior=state.postProgressMemory.get(key);
  if(known){state.postProgressMemory.set(key,{status,progress,known:true,ts:now});}
  else if(prior&&prior.status===status&&prior.known===true&&now-Number(prior.ts||0)<=2500){progress=Number(prior.progress||0);known=true;}
  else if(!prior||prior.status!==status){state.postProgressMemory.set(key,{status,progress:0,known:false,ts:now});}
  return {status,progress,known,indeterminate:active&&!known};
}
function downloadPackage(pkg,allJobs){
  const ids=new Set((pkg.job_ids||[]).map(String)),children=allJobs.filter(j=>ids.has(String(j.id))),visibleChildren=children.filter(downloadVisible);
  const expanded=state.expandedCollections.has(String(pkg.id));
  const expected=Number(pkg.expected_bytes||0),done=Number(pkg.downloaded_bytes||0),pct=expected?Math.max(0,Math.min(100,Math.round(done/expected*100))):0;
  const postView=postProgressPresentation(pkg,'package'),postStatus=postView.status,postProgress=postView.progress,postActive=['queued','verifying','repairing','extracting','importing'].includes(postStatus),postKnown=postView.known,postIndeterminate=postView.indeterminate;
  const packageProgressPct=String(pkg.status||'')==='completed'&&postActive?(postKnown?postProgress:35):pct;
  const packageProgressClass=String(pkg.status||'')==='completed'&&postActive?`post-active${postIndeterminate?' indeterminate':''}`:'';
  const packageProgressText=String(pkg.status||'')==='completed'&&postActive?(postKnown?`${postStatus.replaceAll('_',' ')} ${postProgress}%`:`${postStatus.replaceAll('_',' ')} • working`):`${pct}% • ${formatBytes(done)} / ${formatBytes(expected)}`;
  const packageEtaSeconds=Number(pkg.eta_seconds||0)>0?Number(pkg.eta_seconds):Number(pkg.speed_bps||0)>0&&expected>done?((expected-done)/Number(pkg.speed_bps)):0;
  const eta=packageEtaSeconds>0?formatEta(packageEtaSeconds):'';
  const h=pkg.health||{},recoveryDeferred=Number(pkg.deferred_recovery_files||0);
  const canPause=children.some(j=>['queued','downloading'].includes(j.status)&&!j.paused),canResume=children.some(j=>['queued','downloading'].includes(j.status)&&j.paused),canRetry=!pkg.release_failure_recorded&&children.some(j=>['failed','cancelled','retry_wait'].includes(j.status));
  const canCancel=children.some(j=>['queued','downloading','retry_wait','cancelling'].includes(j.status));
  const canRecovery=recoveryDeferred>0&&(Number(h.missing_bytes||0)>0||['repairable','repair_tool_needed','recovery_limited','incomplete'].includes(String(h.state||'')));
  const speed=Number(pkg.speed_bps||0)?formatSpeed(pkg.speed_bps):pkg.status==='completed'&&Number(pkg.peak_speed_bps||0)?`Peak ${formatSpeed(pkg.peak_speed_bps)}`:'—';
  const recoveryText=Number(h.recovery_blocks_queued||0)||Number(h.recovery_blocks_deferred||0)?`${Number(h.recovery_blocks_queued||0)} recovery blocks queued • ${Number(h.recovery_blocks_deferred||0)} deferred`:'No recovery volumes needed';
  const body=expanded?`<div class="download-package-body">${visibleChildren.length?visibleChildren.map(downloadRow).join(''):'<div class="package-empty-filter">No files in this package match the active filter.</div>'}</div>`:'';
  const automationLabel=String(pkg.automation_label||''),automationRelease=String(pkg.automation_release_title||''),automationDestination=String(pkg.automation_destination||''),displayName=String(pkg.display_name||pkg.name||'Imported NZB');
  const oneTimeMedia=String(pkg.automation_source||'')==='manual_media_grab';
  const automationLine=automationLabel?`<div class="package-automation-target">${automationRelease?`<div class="package-automation-release" title="${escapeHtml(automationRelease)}"><span>Release</span><b>${escapeHtml(automationRelease)}</b></div>`:`<div class="package-automation-release"><b>${oneTimeMedia?'One-time media import':'Automation download'}</b></div>`}${automationDestination?`<div class="package-automation-destination" title="${escapeHtml(automationDestination)}"><span>${oneTimeMedia?'Destination':'Library'}</span><b>${escapeHtml(automationDestination)}</b></div>`:''}</div>`:'';
  const canRetryImport=['needs_attention','failed'].includes(String(pkg.post_status||''))&&['automation_grab','manual_media_grab'].includes(String(pkg.automation_source||''))&&String(pkg.status||'')==='completed';
  return `<section class="download-package ${escapeHtml(String(pkg.status||''))}" data-package-id="${escapeHtml(String(pkg.id))}">
    <div class="download-package-head">
      <button type="button" class="package-chevron" data-package-toggle="${escapeHtml(String(pkg.id))}" title="${expanded?'Collapse':'Expand'} package">${expanded?'⌄':'›'}</button>
      <div class="package-title"><div class="package-title-line"><strong title="${escapeHtml(automationRelease||pkg.name||'Imported NZB')}">${escapeHtml(displayName)}</strong>${pkg.category?`<em class="package-category">${escapeHtml(pkg.category)}</em>`:''}<em class="download-priority ${escapeHtml(pkg.priority||'normal')}">${escapeHtml(String(pkg.priority||'normal').toUpperCase())}</em></div>${automationLine}<small>${Number(pkg.files||0)} required files${Number(pkg.optional_files||0)?` • ${Number(pkg.optional_files)} optional${Number(pkg.optional_skipped_files||0)?` (${Number(pkg.optional_skipped_files)} skipped)`:''}`:''} • ${formatBytes(expected)}${Number(pkg.recovery_files||0)?` • ${Number(pkg.recovery_files)} recovery file${Number(pkg.recovery_files)===1?'':'s'}`:''}${Number(pkg.average_speed_bps||0)&&['completed','failed'].includes(String(pkg.status||''))?` • avg ${formatSpeed(pkg.average_speed_bps)}`:''}${Number(pkg.duration_seconds||0)&&['completed','failed'].includes(String(pkg.status||''))?` • ${formatEta(pkg.duration_seconds)}`:''}</small>${packageHealthHtml(pkg)}</div>
      <div class="package-status"><span class="download-status-chip ${escapeHtml(String(pkg.status||''))}">${escapeHtml(packageStatusLabel(pkg))}</span><small>${escapeHtml(pkg.post_message||recoveryText)}</small></div>
      <div class="package-progress"><div class="download-progress-track ${packageProgressClass}"><div class="download-progress-fill" style="width:${packageProgressPct}%"></div></div><small><span>${packageProgressText}${String(pkg.direct_unpack_status||'')==='active'&&String(pkg.status||'')!=='completed'?` • ${postKnown?`Unpack ${postProgress}%`:'Unpacking'}`:''}</span><span>${String(pkg.status||'')==='completed'&&postActive?(postKnown?'Post-processing':'Working…'):`${speed}${eta?` • ETA ${eta}`:''}`}</span></small></div>
      <div class="package-connections"><b>${Number(pkg.connections_used||0)} conn.</b><span>${Number(pkg.completed_files||0)}/${Number(pkg.files||0)} files</span></div>
      <div class="package-actions"><select class="package-priority-select" data-package-priority="${pkg.id}" title="Package priority"><option value="high" ${pkg.priority==='high'?'selected':''}>High</option><option value="normal" ${pkg.priority==='normal'?'selected':''}>Normal</option><option value="low" ${pkg.priority==='low'?'selected':''}>Low</option></select>${children.some(j=>j.status==='queued')?`<button data-package-action="move_top" data-package-id="${pkg.id}" title="Move package to top">↑ Top</button><button data-package-action="move_bottom" data-package-id="${pkg.id}" title="Move package to bottom">↓ Bottom</button>`:''}${canPause?`<button data-package-action="pause" data-package-id="${pkg.id}">Pause</button>`:''}${canResume?`<button data-package-action="resume" data-package-id="${pkg.id}">Resume</button>`:''}${canRetry?`<button data-package-action="retry" data-package-id="${pkg.id}">Retry failed</button>`:''}${canRetryImport?`<button class="recovery" data-package-retry-import="${pkg.id}">Retry import</button>`:''}${canRecovery?`<button class="recovery" data-package-action="fetch_recovery" data-package-id="${pkg.id}">Fetch recovery</button>`:''}${canCancel?`<button class="danger" data-package-action="cancel" data-package-id="${pkg.id}">Cancel</button>`:''}<button class="danger subtle" data-package-action="remove" data-package-id="${pkg.id}">Remove</button></div>
      <div class="package-pipeline-wrap">${postPipelineHtml(pkg)}</div>
    </div>${body}</section>`;
}
function downloadStructureSignature(d,allJobs,collections){
  const jobs=(allJobs||[]).map(j=>[String(j.id||''),String(j.status||''),String(j.post_status||''),!!j.paused,String(j.priority||''),String(j.collection_id||''),Number(j.queue_order||0),!!j.release_failure_recorded,String(j.integrity_status||''),!!j.post_message,state.expandedDownloads.has(String(j.id||''))?1:0]);
  const packages=(collections||[]).map(p=>[String(p.id||''),String(p.status||''),String(p.post_status||''),String(p.priority||''),Number(p.queue_order||0),String(p.health?.state||''),Number(p.deferred_recovery_files||0),(p.job_ids||[]).map(String).join(','),state.expandedCollections.has(String(p.id||''))?1:0]);
  return JSON.stringify([state.downloadFilter,String(state.downloadSearchTerm||''),jobs,packages]);
}
function patchProgressContainerLive(current,fresh){
  if(!current||!fresh)return;
  current.className=fresh.className;
  const currentTrack=current.querySelector('.download-progress-track'),freshTrack=fresh.querySelector('.download-progress-track');
  if(currentTrack&&freshTrack){
    currentTrack.className=freshTrack.className;
    const currentFill=currentTrack.querySelector('.download-progress-fill'),freshFill=freshTrack.querySelector('.download-progress-fill');
    if(currentFill&&freshFill){const nextWidth=freshFill.style.width||'';if(currentFill.style.width!==nextWidth)currentFill.style.width=nextWidth;}
  }
  const currentSmall=current.querySelector('small'),freshSmall=fresh.querySelector('small');
  if(currentSmall&&freshSmall){
    const a=[...currentSmall.children],b=[...freshSmall.children];
    if(a.length===b.length){for(let i=0;i<a.length;i++){if(a[i].textContent!==b[i].textContent)a[i].textContent=b[i].textContent;}}
    else currentSmall.innerHTML=freshSmall.innerHTML;
  }
}
function copyLiveSections(current,fresh,selectors){
  if(!current||!fresh)return;
  current.className=fresh.className;
  for(const selector of selectors){
    const a=current.querySelector(selector),b=fresh.querySelector(selector);if(!a||!b)continue;
    if(selector==='.package-progress'||selector==='.download-progress-cell'){patchProgressContainerLive(a,b);continue;}
    a.className=b.className;a.innerHTML=b.innerHTML;
  }
}
function patchDownloadRowLive(row,job){
  const template=document.createElement('template');template.innerHTML=downloadRow(job).trim();const fresh=template.content.firstElementChild;if(!fresh)return;
  copyLiveSections(row,fresh,['.download-status-wrap','.download-progress-cell','.download-meta','.download-health-chips','.download-post-row']);
}
function patchDownloadPackageLive(section,pkg,allJobs){
  const template=document.createElement('template');template.innerHTML=downloadPackage(pkg,allJobs).trim();const fresh=template.content.firstElementChild;if(!fresh)return;
  copyLiveSections(section,fresh,['.package-status','.package-progress','.package-connections','.package-title > small','.package-health','.package-pipeline-wrap']);
  if(state.expandedCollections.has(String(pkg.id))){
    const jobsById=new Map((allJobs||[]).map(j=>[String(j.id),j]));
    section.querySelectorAll('.download-row[data-id]').forEach(row=>{const job=jobsById.get(String(row.dataset.id));if(job)patchDownloadRowLive(row,job)});
  }
}
function patchDownloadsLive(allJobs,collections){
  if(!els.downloadsList||!els.downloadsList.children.length)return false;
  const packageById=new Map((collections||[]).map(p=>[String(p.id),p]));
  const jobById=new Map((allJobs||[]).map(j=>[String(j.id),j]));
  for(const section of els.downloadsList.querySelectorAll('.download-package[data-package-id]')){const pkg=packageById.get(String(section.dataset.packageId));if(!pkg)return false;patchDownloadPackageLive(section,pkg,allJobs)}
  for(const row of els.downloadsList.querySelectorAll(':scope > .download-row[data-id]')){const job=jobById.get(String(row.dataset.id));if(!job)return false;patchDownloadRowLive(row,job)}
  return true;
}
function renderDownloads({livePatch=false}={}){
  const d=state.downloadSnapshot||{}, c=d.counts||{}, jobs=visibleDownloadJobs();
  const retryWaiting=Number(c.retry_wait||0), activeNow=(c.downloading||0)+(c.cancelling||0)+retryWaiting, queueActivity=activeNow+(c.queued||0);
  const allJobs=d.jobs||[],collections=sortDownloadsForCurrentView(d.collections||[]);
  const missingBlocks=allJobs.reduce((n,j)=>n+Number(j.failed_parts||0),0);
  const retryCount=allJobs.reduce((n,j)=>n+Number(j.retry_count||0),0);
  const recoveredCount=allJobs.reduce((n,j)=>n+Number(j.recovered_parts||0),0);
  $('dlActiveCount').textContent=activeNow;$('dlCompletedCount').textContent=c.completed||0;$('dlFailedCount').textContent=(c.failed||0)+(c.cancelled||0);$('dlFolder').textContent=d.folder||'Downloads\\NewzDeck';
  $('dlSpeed').textContent=formatSpeed(d.total_speed_bps||0);if($('dlAverageSpeed'))$('dlAverageSpeed').textContent=`avg ${formatSpeed(d.average_speed_bps||0)}`;if($('dlRemaining'))$('dlRemaining').textContent=formatBytes(d.remaining_bytes||0);if($('dlQueueEta'))$('dlQueueEta').textContent=d.queue_eta_seconds?`ETA ${formatEta(d.queue_eta_seconds)}`:'ETA —';
  const lifetime=d.statistics||{};
  if($('dlLifetimeDownloaded'))$('dlLifetimeDownloaded').textContent=formatBytes(Number(lifetime.total_downloaded_bytes||0));
  if($('dlLifetimeFiles'))$('dlLifetimeFiles').textContent=Number(lifetime.completed_files||0).toLocaleString();
  if($('dlLifetimeTime'))$('dlLifetimeTime').textContent=Number(lifetime.transfer_seconds||0)>0?formatUptime(lifetime.transfer_seconds):'—';
  if($('dlLifetimeAverage'))$('dlLifetimeAverage').textContent=Number(lifetime.average_speed_bps||0)>0?formatSpeed(lifetime.average_speed_bps):'—';
  if($('dlLifetimePeak'))$('dlLifetimePeak').textContent=Number(lifetime.peak_speed_bps||0)>0?formatSpeed(lifetime.peak_speed_bps):'—';
  if($('dlLifetimeRecovered'))$('dlLifetimeRecovered').textContent=Number(lifetime.recovered_blocks||0).toLocaleString();
  if($('dlStatsSince')){const since=Number(lifetime.tracking_since_ts||0);$('dlStatsSince').textContent=since?`Tracking since ${new Date(since*1000).toLocaleDateString(undefined,{year:'numeric',month:'short',day:'numeric'})}`:'Lifetime statistics';}

  if($('dlMissingBlocks'))$('dlMissingBlocks').textContent=missingBlocks.toLocaleString();if($('dlRetryStats'))$('dlRetryStats').textContent=`${retryCount.toLocaleString()} provider retries • ${recoveredCount.toLocaleString()} recovered`;
  const conn=d.connections||{},yenc=conn.yenc||{},telemetry=d.telemetry||{},engine=d.engine||{},pipelineDepth=Math.max(1,...(Array.isArray(conn.pools)?conn.pools.map(x=>Number(x.pipeline_enabled===false?1:x.pipeline_depth||1)):[1]));
  const slotUtil=Number(telemetry.slot_utilization_pct||0),rarActive=Number(telemetry.rar_lanes_active||0),rarTarget=Number(telemetry.rar_lanes_target||0),inflight=Number(telemetry.inflight_articles||0),sabEngine=String(engine.name||'').toLowerCase()==='sabnzbd';
  const connTarget=Number(conn.effective_capacity||conn.capacity||0),sabActive=Number(conn.active||0),sabLive=Number(conn.live_active ?? conn.active ?? 0),sabCapacity=Number(conn.capacity||conn.configured||0);$('dlConnections').textContent=sabEngine?(sabCapacity?sabCapacity.toLocaleString():'—'):Number(conn.active||0).toLocaleString();$('dlConnectionsDetail').textContent=sabEngine?(engine.ready===false?`SAB engine reconnecting • ${sabCapacity.toLocaleString()} allocated`:conn.provider_stalled?`${sabCapacity.toLocaleString()} allocated • checking a sustained provider stall`:conn.provider_transient_idle?`${sabCapacity.toLocaleString()} allocated • SAB reconnect window`:`SAB-managed pool • up to ${sabCapacity.toLocaleString()} parallel connections${sabLive>0?` • ${sabLive.toLocaleString()} live now`:''}`):`${Number(conn.open||0)} warm • ${connTarget} active target / ${Number(conn.capacity||0)} download slots${Number(conn.configured||0)?` • ${Number(conn.configured||0)} configured`:''} • pipeline ×${pipelineDepth}${yenc.available?` • native yEnc x${Number(yenc.workers||0)}`:' • Python yEnc fallback'}${slotUtil?` • ${slotUtil.toFixed(0)}% target busy`:''}`;
  if($('dlNetworkRate'))$('dlNetworkRate').textContent=formatSpeed(telemetry.network_rate_bps||d.total_speed_bps||0);if($('dlDecodeRate'))$('dlDecodeRate').textContent=sabEngine?'Engine-managed':(Number(telemetry.decode_rate_bps||0)?formatSpeed(telemetry.decode_rate_bps):'—');if($('dlDiskRate'))$('dlDiskRate').textContent=sabEngine?'Engine-managed':(Number(telemetry.disk_rate_bps||0)?formatSpeed(telemetry.disk_rate_bps):'—');if($('dlSoftMisses'))$('dlSoftMisses').textContent=Number(telemetry.soft_misses||0).toLocaleString();if($('dlNativeParts'))$('dlNativeParts').textContent=sabEngine?'—':Number(telemetry.native_parts||0).toLocaleString();const bw=telemetry.bandwidth||{};if($('dlBandwidthState'))$('dlBandwidthState').textContent=bw.active?`${Number(bw.limit_mb_s||0).toFixed(Number(bw.limit_mb_s||0)%1?1:0)} MB/s`:(bw.enabled?'Unlimited now':'Unlimited');
  if($('dlEngineState'))$('dlEngineState').textContent=telemetry.engine_label||`NNTP → async yEnc → resumable partial • ${inflight.toLocaleString()} articles in flight${rarTarget>1?` • RAR read-ahead ${rarActive}/${rarTarget}`:''}`;
  if(els.downloadOrganization)els.downloadOrganization.value=state.downloadOrganization||'flat';
  els.downloadNavBadge.textContent=queueActivity;els.downloadNavBadge.classList.toggle('hidden',queueActivity===0);els.pauseDownloadsBtn.textContent=d.paused?'Resume queue':'Pause queue';
  $('downloadQueueState').textContent=d.paused?'Queue paused':`${c.downloading||0} active • ${c.queued||0} queued${retryWaiting?` • ${retryWaiting} waiting to retry`:''}${Number(d.post_processing_active||0)?` • ${Number(d.post_processing_active)} post-processing`:''}${Number(d.remaining_bytes||0)?` • ${formatBytes(d.remaining_bytes)} remaining`:''}`;
  const problemBanner=$('downloadProblemBanner');
  if(problemBanner){
    const failed=Number(c.failed||0), problemJobs=allJobs.filter(j=>Number(j.failed_parts||0)>0||['failed','retry_wait'].includes(j.status)||String(j.integrity_status||'')==='repair_needed').length;
    const repairable=collections.filter(x=>['repairable','repair_tool_needed'].includes(String(x.health?.state||''))).length;
    const providerIssue=sabEngine&&!!conn.provider_stalled&&!d.paused&&Number(conn.active||0)===0;
    const adapterVersion=String(engine.adapter_version||'').trim();
    const runtimeMismatch=sabEngine&&adapterVersion&&adapterVersion!==UI_VERSION;
    if(runtimeMismatch){
      problemBanner.classList.remove('hidden','recovering');problemBanner.classList.add('critical');
      problemBanner.innerHTML=`<div><strong>NewzDeck background runtime is from a different version</strong><span>This UI is v${escapeHtml(UI_VERSION)}, but the active download engine is adapter v${escapeHtml(adapterVersion)}.</span></div><div class="problem-banner-note">Fully exit the tray app and stop the NewzDeck background service, then launch this build again. Queue state is preserved.</div>`;
    }else if(problemJobs){
      problemBanner.classList.remove('hidden');problemBanner.classList.toggle('critical',failed>0);problemBanner.classList.toggle('recovering',failed===0&&(retryWaiting>0||repairable>0));
      problemBanner.innerHTML=`<div><strong>${repairable?`${repairable} NZB package${repairable===1?'':'s'} can use PAR2 recovery`:failed?`${failed} download${failed===1?'':'s'} need attention`:retryWaiting?`${retryWaiting} download${retryWaiting===1?' is':'s are'} recovering automatically`:'Download recovery active'}</strong><span>${missingBlocks?`${missingBlocks.toLocaleString()} unavailable block${missingBlocks===1?'':'s'} • `:''}${retryCount.toLocaleString()} provider retries • ${recoveredCount.toLocaleString()} blocks recovered from alternate providers</span></div><div class="problem-banner-note">Verified data is preserved. NewzDeck retries only missing blocks and can fetch deferred PAR2 recovery data when needed.</div>`;
    }else if(providerIssue){
      const providerMessage=String(conn.provider_summary||'').trim(),probe=conn.provider_test||{},probeText=String(probe.summary||'').trim();problemBanner.classList.remove('hidden','critical');problemBanner.classList.add('recovering');problemBanner.innerHTML=`<div><strong>Usenet download engine has no live NNTP connection</strong><span>${escapeHtml(providerMessage||probeText||'NewzDeck is verifying the provider configuration, testing a real NNTP login, and reloading SABnzbd provider workers automatically.')}</span></div><div class="problem-banner-note">Provider state: ${Number(conn.configured_servers||0)}/${Number(conn.expected_servers||0)} configured • ${Number(conn.runtime_servers||0)}/${Number(conn.expected_servers||0)} runtime workers. The NZB is preserved; do not Grab it again.</div>`;
    }else{problemBanner.classList.add('hidden');problemBanner.classList.remove('critical','recovering');problemBanner.innerHTML=''}
  }
  const validIds=new Set(allJobs.map(j=>String(j.id)));for(const id of [...state.selectedDownloads])if(!validIds.has(id))state.selectedDownloads.delete(id);for(const id of [...state.expandedDownloads])if(!validIds.has(id))state.expandedDownloads.delete(id);const validCollections=new Set(collections.map(x=>String(x.id)));for(const id of [...state.expandedCollections])if(!validCollections.has(id))state.expandedCollections.delete(id);updateDownloadSelectionBar();
  const structureSignature=downloadStructureSignature(d,allJobs,collections);
  if(livePatch&&structureSignature===downloadDomSignature&&patchDownloadsLive(allJobs,collections))return;
  downloadDomSignature=structureSignature;
  const visibleCollectionIds=new Set();const packageHtml=[];
  for(const pkg of collections){const ids=new Set((pkg.job_ids||[]).map(String)),matching=allJobs.some(j=>ids.has(String(j.id))&&downloadVisible(j));if(!matching)continue;visibleCollectionIds.add(String(pkg.id));packageHtml.push(downloadPackage(pkg,allJobs));}
  const standalone=jobs.filter(j=>!j.collection_id||!visibleCollectionIds.has(String(j.collection_id))&&!collections.some(p=>String(p.id)===String(j.collection_id)));
  if(!packageHtml.length&&!standalone.length){const emptyCopy={active:['No active downloads','Downloads that are transferring or waiting to retry appear here.'],queued:['Nothing queued','Packages waiting for their turn appear here.'],post:['Nothing post-processing','Verification, repair and unpack activity appears here.'],completed:['No completed downloads','Finished downloads remain here until you clear completed history.'],failed:['No failed downloads','Downloads that need attention appear here.']}[state.downloadFilter]||['Nothing here','There are no downloads in this category.'];els.downloadsList.innerHTML=`<div class="downloads-empty"><span>⇣</span><h3>${emptyCopy[0]}</h3><p>${emptyCopy[1]}</p></div>`;return}
  els.downloadsList.innerHTML=packageHtml.join('')+standalone.map(downloadRow).join('');
  els.downloadsList.querySelectorAll('[data-package-toggle]').forEach(btn=>btn.onclick=e=>{e.stopPropagation();const id=String(btn.dataset.packageToggle);if(state.expandedCollections.has(id))state.expandedCollections.delete(id);else state.expandedCollections.add(id);renderDownloads()});
  els.downloadsList.querySelectorAll('[data-package-action]').forEach(btn=>btn.onclick=e=>{e.stopPropagation();const pkg=collections.find(x=>String(x.id)===String(btn.dataset.packageId));if(!pkg)return;const action=btn.dataset.packageAction;if(action==='fetch_recovery')downloadControl('fetch_recovery','',pkg.id);else downloadControl(action,'',null,pkg.job_ids||[])});
  els.downloadsList.querySelectorAll('[data-package-retry-import]').forEach(btn=>btn.onclick=e=>{e.stopPropagation();retryAutomationImport(btn.dataset.packageRetryImport,btn).then(()=>setTimeout(()=>loadDownloads(),700))});
  els.downloadsList.querySelectorAll('[data-package-priority]').forEach(sel=>{sel.onclick=e=>e.stopPropagation();sel.onchange=e=>{e.stopPropagation();const pkg=collections.find(x=>String(x.id)===String(sel.dataset.packagePriority));if(pkg)downloadControl('priority','',sel.value,pkg.job_ids||[])}});
  els.downloadsList.querySelectorAll('.download-row[data-id]').forEach(row=>{
    const job=allJobs.find(j=>String(j.id)===String(row.dataset.id));row.onclick=e=>handleDownloadRowSelection(row.dataset.id,e);
    if(job?.status==='queued'){row.draggable=true;row.addEventListener('dragstart',e=>{state.dragDownloadId=row.dataset.id;row.classList.add('dragging');e.dataTransfer.effectAllowed='move'});row.addEventListener('dragend',()=>{state.dragDownloadId='';row.classList.remove('dragging');els.downloadsList.querySelectorAll('.drag-over').forEach(x=>x.classList.remove('drag-over'))});row.addEventListener('dragover',e=>{if(!state.dragDownloadId||state.dragDownloadId===row.dataset.id)return;e.preventDefault();row.classList.add('drag-over')});row.addEventListener('dragleave',()=>row.classList.remove('drag-over'));row.addEventListener('drop',e=>{e.preventDefault();row.classList.remove('drag-over');reorderQueuedDownload(state.dragDownloadId,row.dataset.id)})}
    row.addEventListener('contextmenu',e=>{e.preventDefault();if(!job)return;showContextMenu(e.clientX,e.clientY,[
      {label:job.paused?'Resume':'Pause',disabled:!['queued','downloading'].includes(job.status),action:()=>downloadControl(job.paused?'resume':'pause',job.id)},
      {label:Number(job.successful_parts||0)?'Retry missing blocks':'Retry',disabled:!['failed','cancelled','retry_wait'].includes(job.status),action:()=>downloadControl('retry',job.id)},
      {label:'Copy failure diagnostics',disabled:!job.error&&!Number(job.failed_parts||0),action:()=>copyDownloadJobDiagnostics(job.id)},
      {label:'Enter archive password',disabled:String(job.post_status||'')!=='needs_password',action:()=>openArchivePassword(job.id)},
      {separator:true},{label:'High priority',action:()=>downloadControl('priority',job.id,'high')},{label:'Normal priority',action:()=>downloadControl('priority',job.id,'normal')},{label:'Low priority',action:()=>downloadControl('priority',job.id,'low')},{label:'Move to top',action:()=>downloadControl('move_top',job.id)},{label:'Move to bottom',action:()=>downloadControl('move_bottom',job.id)},{separator:true},{label:'Open download folder',action:()=>api('/api/downloads/open-folder',{}).catch(err=>toast(err.message,'error'))},{label:['downloading','cancelling'].includes(job.status)||['queued','verifying','repairing','extracting','importing'].includes(String(job.post_status||''))?'Force remove':'Remove',action:()=>downloadControl('remove',job.id)}]);});
  });
  els.downloadsList.querySelectorAll('[data-dl-action]').forEach(btn=>btn.onclick=e=>{e.stopPropagation();downloadControl(btn.dataset.dlAction,btn.dataset.id)});
  els.downloadsList.querySelectorAll('[data-dl-password]').forEach(btn=>btn.onclick=e=>{e.stopPropagation();openArchivePassword(btn.dataset.dlPassword)});
  els.downloadsList.querySelectorAll('[data-dl-details]').forEach(btn=>btn.onclick=e=>{e.stopPropagation();toggleDownloadDetails(btn.dataset.dlDetails)});
  els.downloadsList.querySelectorAll('[data-dl-copy]').forEach(btn=>btn.onclick=e=>{e.stopPropagation();copyDownloadJobDiagnostics(btn.dataset.dlCopy)});
}

function downloadRow(job){
  const expected=Number(job.expected_bytes||0),done=Number(job.downloaded_bytes||0),postView=postProgressPresentation(job,'job'),postStatus=postView.status,postProgress=postView.progress;
  const activePost=['queued','verifying','repairing','extracting','importing'].includes(postStatus),waitingPost=postStatus==='waiting',blockedPost=['blocked','needs_password','failed','cancelled','needs_tool'].includes(postStatus),repairNeeded=String(job.integrity_status||'')==='repair_needed';
  const postKnown=postView.known,postIndeterminate=postView.indeterminate;
  let transferPct=expected?Math.round(done/expected*100):0;
  if(job.status==='completed')transferPct=100;else transferPct=Math.max(0,Math.min(99,transferPct));
  let pct=transferPct,progressText=`${transferPct}%`;
  if(job.status==='completed'&&activePost){pct=postKnown?postProgress:35;progressText=postKnown?`${postStatus.replaceAll('_',' ')} ${postProgress}%`:`${postStatus.replaceAll('_',' ')} • working`}
  else if(job.status==='completed'&&(waitingPost||blockedPost)){pct=100;progressText='Transfer 100%'}
  const connections=Number(job.connections_used||0),total=Number(job.total_parts||0),processed=Number(job.processed_parts??job.current_part??0),good=Number(job.successful_parts??job.current_part??0),failed=Number(job.failed_parts||0),retries=Number(job.retry_count||0),resumed=Number(job.resumed_parts||0);
  const blockHealth=total?`${good}/${total} good${failed?` • ${failed} unavailable`:''}${connections&&job.status==='downloading'?` • ${connections} conn.`:''}`:'';
  const size=job.status==='completed'?formatBytes(job.actual_size||done):`${formatBytes(done)}${expected?' / '+formatBytes(expected):''}`;const eta=job.status==='downloading'&&Number(job.speed_bps||0)>0&&expected>done?formatEta((expected-done)/Number(job.speed_bps)):'';
  const retrySecs=downloadRetryCountdown(job);
  let actions='';
  if(['queued','downloading'].includes(job.status))actions=`<button class="pause" data-dl-action="${job.paused?'resume':'pause'}" data-id="${job.id}">${job.paused?'Resume':'Pause'}</button><button class="danger" data-dl-action="cancel" data-id="${job.id}">Cancel</button><button class="danger" data-dl-action="remove" data-id="${job.id}" title="Stop immediately and remove this queue entry">Remove</button>`;
  else if(job.status==='retry_wait')actions=`<button data-dl-action="retry" data-id="${job.id}">Retry now</button><button class="danger" data-dl-action="cancel" data-id="${job.id}">Cancel</button><button class="danger" data-dl-action="remove" data-id="${job.id}">Remove</button>`;
  else if(job.status==='cancelling')actions=`<button class="danger" data-dl-action="remove" data-id="${job.id}">Force remove</button>`;
  else if(['failed','cancelled'].includes(job.status))actions=`${job.release_failure_recorded?'':`<button data-dl-action="retry" data-id="${job.id}">${good?'Retry missing':'Retry'}</button>`}<button class="danger" data-dl-action="remove" data-id="${job.id}">Remove</button>`;
  else if(job.status==='completed')actions=`${postStatus==='needs_password'?`<button class="password-action" data-dl-password="${job.id}">Enter password</button>`:''}${activePost?`<button class="danger" data-dl-action="cancel" data-id="${job.id}">Stop post</button>`:''}<button class="danger" data-dl-action="remove" data-id="${job.id}">Remove</button>`;
  const expanded=state.expandedDownloads.has(String(job.id));actions+=`<button class="details" data-dl-details="${job.id}">${expanded?'Hide details':'Details'}</button>`;
  const selected=state.selectedDownloads.has(String(job.id));let statusLabel=job.paused&&['queued','downloading'].includes(job.status)?'PAUSED':String(job.status||'').toUpperCase().replaceAll('_',' ');if(job.status==='retry_wait')statusLabel=retrySecs?`RETRY ${retrySecs}s`:'RETRYING';if(job.status==='completed'&&String(job.integrity_status||'')==='optional_missing')statusLabel='OPTIONAL SKIPPED';
  if(job.status==='completed'&&activePost)statusLabel=postStatus==='queued'?'POST QUEUED':postStatus.toUpperCase();
  else if(job.status==='completed'&&waitingPost)statusLabel='WAITING FOR NZB';
  else if(job.status==='completed'&&postStatus==='blocked')statusLabel='POST BLOCKED';
  else if(job.status==='completed'&&postStatus==='needs_password')statusLabel='PASSWORD NEEDED';
  else if(job.status==='completed'&&postStatus==='failed')statusLabel='POST FAILED';
  else if(job.status==='completed'&&postStatus==='cancelled')statusLabel='POST STOPPED';
  if(repairNeeded&&!['repairing','extracting','importing'].includes(postStatus))statusLabel='REPAIR NEEDED';
  const priority=String(job.priority||'normal'),recovered=Number(job.recovered_parts||0);const recoverySources=Object.entries(job.recovery_sources||{}).map(([name,count])=>`${name}: ${count}`).join(', ');const providerRoute=job.origin_provider_name&&job.origin_provider_name!==job.provider_name?`${escapeHtml(job.origin_provider_name)} → <b>${escapeHtml(job.provider_name||'')}</b>`:escapeHtml(job.provider_name||'');const postLabel=postStatus?postStatus.replaceAll('_',' ').toUpperCase():'';const nzb=job.source==='nzb'?`<span class="nzb-badge" title="${escapeHtml(job.collection_name||'Imported NZB')}">NZB</span>`:'';const role=String(job.collection_role||'');const roleBadge=role==='recovery_par2'?'<span class="role-badge recovery">PAR2 RECOVERY</span>':role==='par2'?'<span class="role-badge par2">PAR2 INDEX</span>':role==='auxiliary'?'<span class="role-badge auxiliary">OPTIONAL</span>':'';const post=postStatus&&postStatus!=='disabled'?`<span class="post-chip ${escapeHtml(postStatus)}">${escapeHtml(postLabel)}${postKnown&&activePost?` ${postProgress}%`:''}</span>`:'';
  const softRecheck=job.status==='retry_wait'&&['soft_missing','propagation'].includes(String(job.error_code||''));
  const healthChips=`${repairNeeded?`<span class="block-chip repair">PAR2 REPAIR • ${Number(job.repair_missing_blocks||failed)} MISSING</span>`:''}${failed&&!repairNeeded?`<span class="block-chip ${softRecheck?'retry':'bad'}">${softRecheck?'RECHECK':'MISSING'} ${failed}</span>`:''}${recovered?`<span class="recovery-chip" title="${escapeHtml(recoverySources)}">RECOVERED ${recovered}</span>`:''}${resumed?`<span class="block-chip reused">REUSED ${resumed}</span>`:''}${retries?`<span class="block-chip retry">PROVIDER RETRIES ${retries}</span>`:''}${job.transfer_phase&&job.status==='downloading'?`<span class="block-chip phase">${escapeHtml(String(job.transfer_phase).toUpperCase())}</span>`:''}`;
  const error=job.error?`<div class="download-error"><div class="download-error-head"><span class="download-error-code">${escapeHtml(job.error_label||'DOWNLOAD FAILED')}</span>${failed&&total?`<span>${failed} of ${total} blocks unavailable</span>`:''}</div><div class="download-error-message">${escapeHtml(job.error)}</div>${job.error_suggestion?`<div class="download-error-help"><b>What to do:</b> ${escapeHtml(job.error_suggestion)}</div>`:''}</div>`:'';
  const details=expanded?downloadDetailPanel(job):'';const detailText=job.status==='completed'&&postStatus&&postStatus!=='disabled'?(job.post_message||job.status_detail):(job.status_detail||'');
  const progressClass=activePost?`post-active${postIndeterminate?' indeterminate':''}`:(failed?'degraded':'');
  const rowName=String(job.display_name||job.filename||'Download'),releaseTitle=String(job.automation_release_title||''),sourceFilename=String(job.source_filename||job.filename||'');
  const identityLine=releaseTitle?`<span class="download-automation-release">Release: ${escapeHtml(releaseTitle)}${sourceFilename&&sourceFilename!==releaseTitle?` • payload ${escapeHtml(sourceFilename)}`:''}</span>`:'';
  return `<div class="download-row selectable ${selected?'selected':''} ${job.paused?'paused':''} ${job.status==='queued'?'queue-draggable':''} ${failed?'has-block-errors':''}" data-id="${job.id}">${job.status==='queued'?'<span class="queue-drag-grip" title="Drag to reorder">⋮⋮</span>':''}<div class="download-name"><strong title="${escapeHtml(releaseTitle||sourceFilename)}">${escapeHtml(rowName)}</strong>${identityLine}<span>${escapeHtml(job.group||'')} • <span class="download-provider-route">${providerRoute}</span>${nzb}${roleBadge}${post}<em class="download-priority ${escapeHtml(priority)}">${escapeHtml(priority.toUpperCase())}</em></span><div class="download-health-chips">${healthChips}</div></div><div class="download-status-wrap"><span class="download-status-chip ${escapeHtml(job.status)} ${activePost?'post-active':''} ${postStatus==='blocked'?'blocked':''}">${escapeHtml(statusLabel)}</span>${detailText?`<small>${escapeHtml(detailText)}</small>`:''}</div><div class="download-progress-cell"><div class="download-progress-track ${progressClass}"><div class="download-progress-fill" style="width:${pct}%"></div></div><small><span>${progressText}${eta?` • ETA ${eta}`:''}</span><span>${job.status==='downloading'&&!job.paused?formatSpeed(job.speed_bps):size}</span></small></div><div class="download-meta"><b>${size}</b><span>${blockHealth||`${processed}/${total} processed`}</span></div><div class="download-row-actions">${actions}</div>${error}${job.post_message&&postStatus&&!['not_needed','disabled'].includes(postStatus)?`<div class="download-post-row"><b>${postStatus==='waiting'?'NZB state':'Post-processing'}</b><span>${escapeHtml(job.post_message)}</span></div>`:''}${details}</div>`;
}
function downloadDetailPanel(job){
  const errors=Array.isArray(job.segment_errors)?job.segment_errors:[], total=Number(job.total_parts||0),good=Number(job.successful_parts||0),failed=Number(job.failed_parts||0),processed=Number(job.processed_parts||0),retrySecs=downloadRetryCountdown(job);const recoverySources=Object.entries(job.recovery_sources||{}).map(([name,count])=>`${String(name)}: ${Number(count)}`).join(' • ')||'None';
  const metrics=[['Block health',`${good} good • ${failed} unavailable • ${Math.max(0,total-processed)} not processed`],['Current / peak speed',`${formatSpeed(job.speed_bps||0)} / ${formatSpeed(job.peak_speed_bps||0)}`],['Average speed',Number(job.average_speed_bps||0)?formatSpeed(job.average_speed_bps):'—'],['Transfer time',Number(job.duration_seconds||0)?formatEta(job.duration_seconds):'—'],['Connections',String(Number(job.connections_used||0))],['Pipeline',`${job.pipeline||'standard'}${Number(job.native_parts||0)?` • ${Number(job.native_parts)} native blocks`:''}`],['Retries',String(Number(job.retry_count||0))],['Recovered',`${Number(job.recovered_parts||0)} block(s) • ${recoverySources}`],['Reused on this run',`${Number(job.resumed_parts||0)} verified block(s)`],['Integrity',String(job.integrity_status||'unknown').replaceAll('_',' ')],['PAR2 need',Number(job.repair_missing_bytes||0)?`${formatBytes(job.repair_missing_bytes)} • ${Number(job.repair_missing_blocks||0)} article blocks`:'—'],['Provider',job.provider_name||'—'],['Source',job.source==='nzb'?`NZB${job.collection_name?` • ${job.collection_name}`:''}`:'NewzDeck browser'],['Last activity',job.last_activity_ts?new Date(Number(job.last_activity_ts)*1000).toLocaleTimeString():'—'],['Last real progress',job.last_progress_ts?new Date(Number(job.last_progress_ts)*1000).toLocaleTimeString():'—'],['Next retry',job.status==='retry_wait'?(retrySecs?`in ${retrySecs}s`:'starting now'):'—'],['Post-processing',String(job.post_status||'')?`${String(job.post_status).replaceAll('_',' ')}${job.post_progress_known===true?` • ${Number(job.post_progress||0)}%`:job.post_indeterminate?' • working':''}${job.post_message?` • ${String(job.post_message)}`:''}`:'—']];
  let failures='';
  if(errors.length){failures=`<div class="download-block-failures"><div class="download-detail-heading"><strong>Failed article blocks</strong><span>Showing ${errors.length}${errors.length>=40?' most recent':''}</span></div>${errors.map(f=>{const attempts=(f.attempts||[]).map(a=>`<div class="download-attempt"><b>${escapeHtml(a.provider||'Provider')}</b><span>${escapeHtml(a.label||a.code||'Failed')}</span><code>${escapeHtml(a.error||'')}</code></div>`).join('');return `<div class="download-block-failure"><div class="block-failure-title"><b>Part ${Number(f.part||Number(f.index||0)+1)}</b><span class="failure-kind ${escapeHtml(f.code||'')}">${escapeHtml(f.label||f.code||'Failed')}</span>${f.bytes?`<span>${formatBytes(f.bytes)}</span>`:''}</div><div class="block-failure-ref">${f.article!=null?`Article #${escapeHtml(f.article)} • `:''}${f.message_id?`Message-ID ${escapeHtml(f.message_id)}`:'No Message-ID available'}</div><div class="block-failure-message">${escapeHtml(f.error||'')}</div>${attempts?`<div class="download-attempts">${attempts}</div>`:''}</div>`}).join('')}</div>`}
  return `<div class="download-detail-panel"><div class="download-detail-top"><div><div class="download-detail-heading"><strong>Transfer diagnostics</strong><span>Block-level history for this file</span></div><div class="download-detail-grid">${metrics.map(([k,v])=>`<div><span>${escapeHtml(k)}</span><b>${escapeHtml(v)}</b></div>`).join('')}</div></div><div class="download-detail-actions"><button type="button" data-dl-copy="${job.id}">Copy diagnostics</button></div></div>${job.error_suggestion?`<div class="download-recovery-advice"><b>Recovery guidance</b><span>${escapeHtml(job.error_suggestion)}</span></div>`:''}${failures}</div>`;
}
async function reorderQueuedDownload(sourceId,targetId){if(!sourceId||!targetId||sourceId===targetId)return;const queued=(state.downloadSnapshot?.jobs||[]).filter(j=>j.status==='queued').map(j=>String(j.id));const from=queued.indexOf(String(sourceId)),to=queued.indexOf(String(targetId));if(from<0||to<0)return;const [moved]=queued.splice(from,1);queued.splice(to,0,moved);await downloadControl('reorder','',queued)}
function openArchivePassword(jobId){state.archivePasswordJobId=String(jobId||'');if(!state.archivePasswordJobId)return;els.archivePasswordInput.value='';els.archivePasswordModal.classList.remove('hidden');setTimeout(()=>els.archivePasswordInput.focus(),30)}
function closeArchivePassword(){els.archivePasswordModal.classList.add('hidden');els.archivePasswordInput.value='';state.archivePasswordJobId=''}
async function submitArchivePassword(){const password=els.archivePasswordInput.value;if(!password){toast('Enter the archive password.','error');return}const id=state.archivePasswordJobId;els.archivePasswordSubmitBtn.disabled=true;try{await downloadControl('post_password',id,password);closeArchivePassword();toast('Password accepted. Retrying post-processing.','success')}finally{els.archivePasswordSubmitBtn.disabled=false}}
async function downloadControl(action,id='',value=null,ids=null){try{state.downloadSnapshot=await api('/api/downloads/control',{action,id,value,ids});recalculatePreviewConcurrency();if(ids||id){if(['remove','cancel','retry'].includes(action))for(const x of (ids||[id]))state.selectedDownloads.delete(String(x))}rebuildDownloadIndexes();renderDownloads();updateDownloadBadgesInPlace();if(state.viewerOpen)updateViewerSelectionState()}catch(e){toast(e.message,'error')}}
async function downloadBatch(action,value=null){const ids=[...state.selectedDownloads];if(!ids.length)return;await downloadControl(action,'',value,ids)}

function isEditableTarget(target){return !!target?.closest?.('input,textarea,select,[contenteditable="true"]')}
function keyboardMove(deltaMode){
  const visible=filteredArticles();if(!visible.length)return;let pos=visible.findIndex(x=>articleKey(x.a)===state.selectedArticleKey);if(pos<0)pos=0;
  let delta=0;if(deltaMode==='left')delta=-1;else if(deltaMode==='right')delta=1;else{let cols=1;if(effectiveViewMode()==='gallery'){const grid=els.articlesList.querySelector('.media-grid');if(grid){const tpl=getComputedStyle(grid).gridTemplateColumns;cols=Math.max(1,tpl.split(' ').filter(Boolean).length)}}delta=deltaMode==='up'?-cols:cols}
  const next=Math.max(0,Math.min(visible.length-1,pos+delta));const item=visible[next];if(!item)return;state.selectedArticleKey=articleKey(item.a);updateActiveArticleDomInPlace();renderPreviewDetails(item.a,false);requestAnimationFrame(()=>{let node=els.articlesList.querySelector(`[data-index="${item.index}"]`);if(!node&&isAllPostsMode()&&state.groupBinarySets){for(const group of state.binarySetGroups.values()){if(group.members.some(x=>x.index===item.index)){node=els.articlesList.querySelector(`.binary-set-row[data-binary-set-key="${CSS.escape(group.key)}"]`);break}}}node?.scrollIntoView({block:'nearest',inline:'nearest'})});
}
function handleKeyboardShortcuts(e){
  if(state.viewerOpen){
    if(e.key==='Escape'){e.preventDefault();closeMediaViewer();return}
    if(e.key==='ArrowLeft'){e.preventDefault();navigateViewer(-1);return}
    if(e.key==='ArrowRight'){e.preventDefault();navigateViewer(1);return}
    if(e.key===' '){e.preventDefault();toggleViewerSelection();return}
    if(e.key==='Enter'||e.key.toLowerCase()==='f'){e.preventDefault();setViewerFit(true);return}
    if(e.key.toLowerCase()==='g'){e.preventDefault();setViewerFill();return}
    if(e.key.toLowerCase()==='i'){e.preventDefault();toggleViewerInfo();return}
    if(e.key.toLowerCase()==='s'){e.preventDefault();toggleViewerSet();return}
    if(e.key==='0'){e.preventDefault();setViewerActual();return}
    if(e.key==='+'||e.key==='='){e.preventDefault();zoomViewer(.25);return}
    if(e.key==='-'||e.key==='_'){e.preventDefault();zoomViewer(-.25);return}
    if(e.key.toLowerCase()==='r'){e.preventDefault();rotateViewer();return}
    return;
  }
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='w'&&state.activeView==='browse'&&state.activeBrowserTabId){e.preventDefault();closeBrowserTab(state.activeBrowserTabId);return}
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='t'&&state.activeView==='browse'&&state.selectedGroup){e.preventDefault();openGroupInNewTab(state.selectedGroup);return}
  if(isEditableTarget(e.target)||state.activeView!=='browse'||!state.selectedGroup||!els.providerModal.classList.contains('hidden')||!els.settingsModal.classList.contains('hidden')||!els.groupSearchModal.classList.contains('hidden'))return;
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='f'){e.preventDefault();els.articleSearch.focus();els.articleSearch.select();showArticleSearchHistory();return}
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='a'){e.preventDefault();selectAllLoaded();return}
  if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){e.preventDefault();keyboardMove(e.key.replace('Arrow','').toLowerCase());return}
  if(e.key===' '){const a=state.articles.find(x=>articleKey(x)===state.selectedArticleKey);if(a&&isSelectableMedia(a)){e.preventDefault();const key=articleKey(a);if(state.selectedItems.has(key))state.selectedItems.delete(key);else{state.selectedItems.set(key,a);state.selectionAnchorKey=key}updateSelectionBar();updateSelectionDomInPlace()}return}
  if(e.key==='Enter'){const a=state.articles.find(x=>articleKey(x)===state.selectedArticleKey);if(['image','video'].includes(a?.media?.kind)&&a.complete){e.preventDefault();openMediaViewer(a)}return}
}


function renderOnlineUpdate(d={}){
  state.onlineUpdate=d;
  if(!els.onlineUpdateStatus)return;
  const latest=String(d.latest_version||d.current_version||UI_VERSION),available=!!d.update_available;
  if(d.online_feed===false){els.onlineUpdateStatus.textContent='Private development build';els.onlineUpdateDetail.textContent='No public update channel is configured. Manual Setup EXE updates remain available.';els.installOnlineUpdateBtn.disabled=true;$('aboutBtn')?.classList.remove('update-available');els.onlineReleaseNotes?.classList.add('hidden');return;}
  if(d.feed_error&&!d.latest_version){els.onlineUpdateStatus.textContent='Update check unavailable';els.onlineUpdateDetail.textContent=d.feed_error;els.installOnlineUpdateBtn.disabled=true;$('aboutBtn')?.classList.remove('update-available');return;}
  els.onlineUpdateStatus.textContent=available?`NewzDeck v${latest} available`:`NewzDeck v${UI_VERSION} is current`;
  if(available){
    const verified=!!d.verified_download;els.onlineUpdateDetail.textContent=verified?`Verified installer ready${d.installer_size?` • ${formatBytes(d.installer_size)}`:''}`:'Release found, but no SHA-256 checksum is published yet.';
    els.installOnlineUpdateBtn.disabled=!verified;$('aboutBtn')?.classList.toggle('update-available',true);
  }else{els.onlineUpdateDetail.textContent=d.checked_at?`Checked ${new Date(Number(d.checked_at)*1000).toLocaleString()}`:'No newer release found.';els.installOnlineUpdateBtn.disabled=true;$('aboutBtn')?.classList.remove('update-available');}
  const notes=String(d.release_notes||'').trim();if(notes&&available){els.onlineReleaseNotes.classList.remove('hidden');els.onlineReleaseNotes.innerHTML=`<b>Release notes</b><p>${escapeHtml(notes.slice(0,3000)).replace(/\n/g,'<br>')}</p>`}else els.onlineReleaseNotes.classList.add('hidden');
}
async function checkOnlineUpdates(force=false,{quiet=false}={}){
  if(els.checkUpdatesBtn){els.checkUpdatesBtn.disabled=true;if(!quiet)els.checkUpdatesBtn.textContent='Checking…'}
  try{const d=await api(`/api/update/status?online=1${force?'&force=1':''}`);renderOnlineUpdate(d);return d}catch(e){if(!quiet)toast(e.message,'error');if(els.onlineUpdateStatus){els.onlineUpdateStatus.textContent='Update check unavailable';els.onlineUpdateDetail.textContent=e.message}return null}finally{if(els.checkUpdatesBtn){els.checkUpdatesBtn.disabled=false;els.checkUpdatesBtn.textContent='Check now'}}
}
function beginManagedUpdateUiExit(resultEl,message){
  if(resultEl){resultEl.className='test-result';resultEl.textContent=message||'Update ready. Closing NewzDeck and handing off to Setup…'}
  // The native update coordinator closes the actual Edge/Chrome app-mode window.
  // window.close() is an immediate best-effort path so the UI disappears before
  // Setup appears; the native WM_CLOSE path remains authoritative if Chromium
  // declines a script-requested close.
  setTimeout(()=>{try{window.close()}catch{}},180);
}
async function installOnlineUpdate(){
  if(!state.onlineUpdate?.update_available)return;
  els.installOnlineUpdateBtn.disabled=true;els.onlineUpdateResult.className='test-result';els.onlineUpdateResult.textContent='Downloading and verifying the NewzDeck installer…';
  try{const d=await api('/api/update/online-install',{});if(d.handoff)beginManagedUpdateUiExit(els.onlineUpdateResult,d.message);else{els.onlineUpdateResult.className='test-result';els.onlineUpdateResult.textContent=d.message||'Verified update installer is ready.'}}
  catch(e){els.onlineUpdateResult.className='test-result error';els.onlineUpdateResult.textContent=e.message;els.installOnlineUpdateBtn.disabled=!state.onlineUpdate?.verified_download}
}
async function openAboutModal(){
  els.aboutModal.classList.remove('hidden');
  els.updateResult.className='test-result hidden';els.updateResult.textContent='';els.onlineUpdateResult.className='test-result hidden';els.onlineUpdateResult.textContent='';
  try{
    const d=await api('/api/update/status');
    els.aboutInstallStatus.textContent=d.installed?'Installed Windows app':'Portable app';
    els.aboutRuntimeStatus.textContent=d.private_runtime?'Private Python runtime ready':'Runtime bootstrap required';
    els.aboutInstallPath.textContent=d.app_dir||'';els.aboutInstallPath.title=d.app_dir||'';
    els.aboutDataPath.textContent=d.data_dir||'';els.aboutDataPath.title=d.data_dir||'';
    els.updatePackageInput.disabled=false;els.installUpdateBtn.disabled=!els.updatePackageInput.files?.[0];
  }catch(e){toast(e.message,'error')}
  checkOnlineUpdates(false,{quiet:true});
}
function closeAboutModal(){els.aboutModal.classList.add('hidden')}
async function installSelectedUpdate(){
  const file=els.updatePackageInput.files?.[0];if(!file)return;
  if(!/^(NewzDeck|UsenetBrowser).*Setup.*\.exe$/i.test(file.name)&&!/^NewzDeckSetup.*\.exe$/i.test(file.name)){toast('Select a NewzDeckSetup.exe package.','error');return}
  els.installUpdateBtn.disabled=true;els.updateResult.className='test-result';els.updateResult.textContent='Staging update package…';
  try{
    const r=await fetch('/api/update/install',{method:'POST',headers:{'Content-Type':'application/octet-stream','X-Filename':encodeURIComponent(file.name)},body:file});
    let d={};try{d=await r.json()}catch{}
    if(!r.ok)throw new Error(d.error||`Update failed (${r.status})`);
    if(d.handoff)beginManagedUpdateUiExit(els.updateResult,d.message);else{els.updateResult.className='test-result';els.updateResult.textContent=d.message||'Update package staged.'}
  }catch(e){els.updateResult.className='test-result error';els.updateResult.textContent=e.message;els.installUpdateBtn.disabled=false}
}

$('manageProvidersBtn').onclick=openProviderModal;$('settingsBtn').onclick=()=>openSettingsModal('general');$('aboutBtn').onclick=openAboutModal;els.aboutCloseBtn.onclick=closeAboutModal;els.aboutModal.addEventListener('click',e=>{if(e.target===els.aboutModal)closeAboutModal()});els.openDataFolderBtn.onclick=async()=>{try{await api('/api/app/open-data',{})}catch(e){toast(e.message,'error')}};if(els.checkUpdatesBtn)els.checkUpdatesBtn.onclick=()=>checkOnlineUpdates(true);if(els.installOnlineUpdateBtn)els.installOnlineUpdateBtn.onclick=installOnlineUpdate;els.updatePackageInput.onchange=()=>{const f=els.updatePackageInput.files?.[0];els.updatePackageName.textContent=f?`${f.name} • ${formatBytes(f.size)}`:'No package selected';els.installUpdateBtn.disabled=!f};els.installUpdateBtn.onclick=installSelectedUpdate;document.querySelectorAll('[data-close]').forEach(b=>b.onclick=()=>closeProviderModal());els.providerModal.addEventListener('click',e=>{if(e.target===els.providerModal)closeProviderModal()});$('newProviderBtn').onclick=newProvider;$('providerRole').onchange=()=>{if($('providerRole').value==='recovery'){$('providerUseBrowsing').checked=false;$('providerUsePreviews').checked=false;$('providerUseDownloads').checked=false;$('providerUseRecovery').checked=true}};
els.settingsCloseBtn.onclick=closeSettingsModal;els.settingsCancelBtn.onclick=closeSettingsModal;els.settingsSaveBtn.onclick=saveSettingsModal;els.settingsModal.addEventListener('click',e=>{if(e.target===els.settingsModal)closeSettingsModal()});document.querySelectorAll('[data-settings-tab]').forEach(b=>b.onclick=()=>{switchSettingsTab(b.dataset.settingsTab);if(b.dataset.settingsTab==='background')refreshServiceSettings()});$('settingsChooseFolderBtn').onclick=settingsChooseDownloadFolder;$('settingsChooseWatchFolderBtn').onclick=settingsChooseWatchFolder;$('settingsBackupBtn').onclick=exportConfigBackup;$('settingsRestoreBtn').onclick=()=>$('settingsRestoreInput').click();$('settingsRestoreInput').onchange=()=>restoreConfigBackup($('settingsRestoreInput').files?.[0]);$('settingsClearThumbCacheBtn').onclick=async()=>{try{const r=await api('/api/cache/clear',{});state.imageThumbCache.clear();state.videoThumbCache.clear();state.imageThumbPromises.clear();state.videoThumbPromises.clear();toast(`Cleared ${Number(r.removed||0).toLocaleString()} cached thumbnails.`,'success')}catch(e){toast(e.message,'error')}};$('settingsClearPreviewCacheBtn').onclick=async()=>{try{const r=await api('/api/cache/preview/clear',{});state.previewCache.clear();state.previewPromises.clear();resetPreview();toast(`Cleared ${Number(r.removed||0).toLocaleString()} cached preview file${Number(r.removed||0)===1?'':'s'} (${formatBytes(Number(r.removed_bytes||0))}).`,'success')}catch(e){toast(e.message,'error')}};$('settingsOpenDataBtn').onclick=async()=>{try{await api('/api/app/open-data',{})}catch(e){toast(e.message,'error')}};$('settingsProvidersBtn').onclick=()=>{closeSettingsModal();openProviderModal()};$('settingsDiagnosticsBtn').onclick=()=>{closeSettingsModal();setMainView('diagnostics')};if($('installServiceBtn'))$('installServiceBtn').onclick=installBackgroundService;if($('startServiceBtn'))$('startServiceBtn').onclick=()=>serviceSettingsControl('start');if($('stopServiceBtn'))$('stopServiceBtn').onclick=()=>serviceSettingsControl('stop');if($('restartServiceBtn'))$('restartServiceBtn').onclick=()=>serviceSettingsControl('restart');if($('repairServiceBtn'))$('repairServiceBtn').onclick=()=>serviceSettingsControl('repair');if($('launchTrayBtn'))$('launchTrayBtn').onclick=()=>serviceSettingsControl('launch_tray');if($('settingsTrayAutostart'))$('settingsTrayAutostart').onchange=async()=>{try{const r=await api('/api/service/control',{action:'tray_autostart',enabled:$('settingsTrayAutostart').checked});renderServiceSettings(r)}catch(e){toast(e.message,'error')}};
els.providerSelect.onchange=()=>{const oldGroup=state.selectedGroup,oldProvider=state.providerId;captureCurrentGroupState();if(oldGroup)endGroupVisit(oldGroup,oldProvider);if(state.groupSearchJob&&['queued','scanning','cancelling'].includes(state.groupSearchJob.status))api('/api/group-search/cancel',{id:state.groupSearchJob.id}).catch(()=>{});if(state.groupSearchPollTimer){clearInterval(state.groupSearchPollTimer);state.groupSearchPollTimer=null}closeMediaViewer();state.providerId=els.providerSelect.value;state.groups=[];state.groupsTotal=0;state.trackedGroupStatus={};startTrackedGroupRefresh();state.selectedGroup='';state.articles=[];state.nameResolutionAttempted.clear();state.nameResolutionAutoRemaining=24;clearTimeout(state.nameResolutionTimer);state.nameResolutionTimer=null;state.selectedArticleKey='';state.selectedItems.clear();state.selectionAnchorKey='';state.articlePage=1;state.articlePaging=null;state.loadedPages.clear();state.articleSearchTerm='';state.searchMode=false;state.groupSearchJob=null;state.continuousLoading=false;state.activeBrowserTabId='';els.articleSearch.value='';state.galleryGeneration++;state.thumbQueue=[];state.thumbQueued.clear();renderBrowserTabs();saveUiSettings();updateProviderState();renderGroups();els.groupsMoreWrap.classList.add('hidden');els.articleTitle.textContent='Articles';els.articleEyebrow.textContent='NO GROUP SELECTED';els.articleSummary.classList.add('hidden');els.entireGroupSearchBtn.disabled=true;updateSelectionBar();updateArticlePaging();updateArticleSearchUi();resetPreview();};
$('groupSearchBtn').onclick=()=>loadGroups();els.groupAllBtn.onclick=()=>{state.groupMode='all';renderGroups()};els.groupFavoritesBtn.onclick=()=>{state.groupMode='favorites';renderGroups()};els.groupRecentBtn.onclick=()=>{state.groupMode='recent';renderGroups()};if(els.newBookmarkFolderBtn)els.newBookmarkFolderBtn.onclick=createBookmarkFolder;if(els.clearRecentBtn)els.clearRecentBtn.onclick=clearCurrentProviderRecentGroups;
$('refreshGroupsBtn').onclick=()=>loadGroups({refresh:true});els.groupSearch.addEventListener('keydown',e=>{if(e.key==='Enter')loadGroups()});let groupSearchDebounce=null;els.groupSearch.addEventListener('input',()=>{clearTimeout(groupSearchDebounce);groupSearchDebounce=setTimeout(()=>loadGroups(),280)});els.groupSort.onchange=()=>loadGroups();els.loadMoreGroupsBtn.onclick=()=>loadGroups({append:true});
$('refreshArticlesBtn').onclick=()=>state.searchMode?loadEntireGroupSearchResults(state.articlePage):loadArticles({page:state.articlePage,append:false,refresh:true});els.articleLimit.onchange=()=>{state.articlePage=1;saveUiSettings();if(state.searchMode)loadEntireGroupSearchResults(1);else loadArticles({page:1,append:false})};els.articleSort.onchange=()=>sortArticles();els.contentFilter.onchange=async()=>{state.activeMediaSetKey='';state.expandedBinarySets.clear();const all=isAllPostsMode();if(all)state.nameResolutionAutoRemaining=Math.max(state.nameResolutionAutoRemaining,24);updateBrowseModeControls();resetPreview();saveUiSettings();if(all&&state.selectedGroup){state.loadedPages.clear();state.articlePage=1;state.articlePaging=null;els.articlesList.scrollTop=0;await loadArticles({page:1,append:false,refresh:true})}else{rotateBrowsePreviewSession();renderArticles({preserveScroll:false})}};els.galleryViewBtn.onclick=()=>setView('gallery');els.listViewBtn.onclick=()=>setView('list');
function releaseFarOffscreenThumbnails(){
  if(!els.articlesList||effectiveViewMode()!=='gallery')return;const root=els.articlesList.getBoundingClientRect(),grid=els.articlesList.querySelector('.media-grid');if(!grid)return;
  const distance=Math.max(root.height*7,5200),down=state.browseScrollDirection>=0;let released=0,inspected=0,node=down?grid.firstElementChild:grid.lastElementChild;
  while(node&&released<80&&inspected<320){const next=down?node.nextElementSibling:node.previousElementSibling;inspected++;const img=node.querySelector?.('img.thumb-img[data-thumb-image-index]');
    if(img){const r=node.getBoundingClientRect(),far=down?r.bottom<root.top-distance:r.top>root.bottom+distance;if(!far)break;const index=Number(img.dataset.thumbImageIndex),role=img.dataset.thumbRole||'item',a=state.articles[index];if(a?.media){const loader=document.createElement('div');loader.className=`thumb-loader ${a.media.kind==='video'?'video-thumb-loader':''}`;loader.dataset.thumbIndex=String(index);loader.dataset.thumbRole=role;loader.innerHTML='<span></span><small>Cached preview</small>';img.parentElement?.querySelector('.video-play-overlay')?.remove();img.replaceWith(loader);released++}}
    node=next;
  }
  if(released)observeThumbnails({reuse:true});scheduleBrowsingMemoryTrim();
}

function scheduleFarThumbnailRelease(){if(state.thumbReleaseTimer)return;state.thumbReleaseTimer=setTimeout(()=>{state.thumbReleaseTimer=null;releaseFarOffscreenThumbnails()},550)}
function onBrowseScrollPerformance(){
  const now=performance.now(),top=els.articlesList.scrollTop,dt=Math.max(16,now-Number(state.lastBrowseScrollTs||now)),raw=(top-Number(state.lastBrowseScrollTop||top))/dt;state.browseScrollVelocity=state.browseScrollVelocity*.65+raw*.35;if(Math.abs(raw)>.015)state.browseScrollDirection=raw>=0?1:-1;state.lastBrowseScrollTop=top;state.lastBrowseScrollTs=now;scheduleThumbnailDemandScan();schedulePredictiveHeaderPrefetch();scheduleFarThumbnailRelease();scheduleBrowsingMemoryTrim();
}
els.articlesList.addEventListener('scroll',onBrowseScrollPerformance,{passive:true});
els.thumbnailSize.onchange=()=>{state.thumbnailSize=els.thumbnailSize.value;applyThumbnailSize();saveUiSettings();renderArticles()};els.continuousBrowseBtn.onclick=()=>{state.continuousMode=!state.continuousMode;updateContinuousButton();saveUiSettings();updateArticlePaging();renderArticles()};els.groupRelatedBtn.onclick=()=>{state.groupRelatedMedia=!state.groupRelatedMedia;state.activeMediaSetKey='';recalculatePreviewConcurrency();updateGroupRelatedButton();saveUiSettings();renderArticles({preserveScroll:false})};els.binaryPackagesBtn.onclick=()=>{if(state.groupBinarySets)return;state.groupBinarySets=true;state.nameResolutionAutoRemaining=Math.max(state.nameResolutionAutoRemaining,24);state.expandedBinarySets.clear();updateBrowseModeControls();saveUiSettings();renderArticles({preserveScroll:false})};els.rawPostsBtn.onclick=()=>{if(!state.groupBinarySets)return;state.groupBinarySets=false;state.expandedBinarySets.clear();updateBrowseModeControls();saveUiSettings();renderArticles({preserveScroll:false})};els.mutedPostersBtn.onclick=()=>{state.showBlockedPosters=!state.showBlockedPosters;updateMutedPostersButton();renderArticles()};
if(els.articleStatusFilter)els.articleStatusFilter.onchange=()=>{state.articleStatusFilter=els.articleStatusFilter.value;renderArticles({preserveScroll:true});captureCurrentGroupState()};if(els.jumpFirstUnseenBtn)els.jumpFirstUnseenBtn.onclick=jumpToFirstUnseen;if(els.markAllSeenBtn)els.markAllSeenBtn.onclick=markAllCurrentGroupSeen;if(els.markSelectedSeenBtn)els.markSelectedSeenBtn.onclick=()=>markSelectedSeen(true);if(els.markSelectedUnseenBtn)els.markSelectedUnseenBtn.onclick=()=>markSelectedSeen(false);
els.articleSearch.addEventListener('input',()=>scheduleLocalSearch(els.articleSearch.value));els.articleSearch.addEventListener('focus',showArticleSearchHistory);els.articleSearch.addEventListener('blur',hideArticleSearchHistory);window.addEventListener('resize',()=>{if(!els.articleSearchHistory?.classList.contains('hidden'))positionArticleSearchHistory()});document.querySelector('.media-browser-toolbar')?.addEventListener('scroll',()=>{if(!els.articleSearchHistory?.classList.contains('hidden'))positionArticleSearchHistory()},{passive:true});els.articleSearch.addEventListener('keydown',e=>{if(e.key==='Escape'&&state.articleSearchTerm){e.preventDefault();clearArticleSearch();return}if(e.key==='Enter'){e.preventDefault();clearTimeout(state.articleSearchTimer);applyLocalSearch(els.articleSearch.value,{commit:true});els.articleSearchHistory?.classList.add('hidden')}});els.clearArticleSearchBtn.onclick=clearArticleSearch;
els.entireGroupSearchBtn.onclick=openEntireGroupSearch;els.closeGroupSearchModalBtn.onclick=closeEntireGroupSearch;els.savedSearchSelect.onchange=()=>{state.activeSavedSearchId=els.savedSearchSelect.value;const x=state.savedSearches.find(v=>v.id===state.activeSavedSearchId);els.deleteSavedSearchBtn.disabled=!x;if(x)applyEntireSearchCriteria(x)};els.saveCurrentSearchBtn.onclick=saveCurrentSearch;els.deleteSavedSearchBtn.onclick=deleteSavedSearch;els.groupSearchModal.addEventListener('click',e=>{if(e.target===els.groupSearchModal)closeEntireGroupSearch()});els.startEntireGroupSearchBtn.onclick=startEntireGroupSearch;els.cancelEntireGroupSearchBtn.onclick=cancelEntireGroupSearch;els.viewEntireGroupSearchResultsBtn.onclick=viewEntireGroupSearchResults;els.entireGroupSearchInput.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();startEntireGroupSearch()}});els.exitGroupSearchBtn.onclick=exitEntireGroupSearch;
els.olderArticlesBtn.onclick=()=>state.searchMode||!state.continuousMode?goToArticlePage(state.articlePage+1):loadOlderArticles();els.newerArticlesBtn.onclick=()=>goToArticlePage(state.articlePage-1);els.latestArticlesBtn.onclick=()=>goToArticlePage(1);els.articlePageInput.addEventListener('change',()=>goToArticlePage(els.articlePageInput.value));els.articlePageInput.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();goToArticlePage(els.articlePageInput.value)}});
els.clearSelectionBtn.onclick=clearSelection;els.selectVisibleBtn.onclick=selectViewport;els.selectLoadedBtn.onclick=selectAllLoaded;els.invertSelectionBtn.onclick=invertVisibleSelection;els.downloadSelectedBtn.onclick=e=>downloadItems(Array.from(state.selectedItems.values()),e.currentTarget);
els.viewerCloseBtn.onclick=closeMediaViewer;els.viewerPrevBtn.onclick=()=>navigateViewer(-1);els.viewerNextBtn.onclick=()=>navigateViewer(1);els.viewerFitBtn.onclick=()=>setViewerFit(true);els.viewerFillBtn.onclick=setViewerFill;els.viewerActualBtn.onclick=setViewerActual;els.viewerZoomOutBtn.onclick=()=>zoomViewer(-.25);els.viewerZoomInBtn.onclick=()=>zoomViewer(.25);els.viewerRotateBtn.onclick=rotateViewer;els.viewerSetBtn.onclick=toggleViewerSet;els.viewerInfoBtn.onclick=toggleViewerInfo;els.viewerSelectBtn.onclick=toggleViewerSelection;els.viewerQueueBtn.onclick=e=>{const a=viewerCurrentArticle();if(a)downloadItems([a],e.currentTarget)};els.mediaViewer.addEventListener('click',e=>{if(e.target===els.mediaViewer)closeMediaViewer()});els.viewerStage.addEventListener('wheel',viewerWheel,{passive:false});els.viewerStage.addEventListener('pointerdown',viewerPointerDown);els.viewerStage.addEventListener('pointermove',viewerPointerMove);els.viewerStage.addEventListener('pointerup',viewerPointerUp);els.viewerStage.addEventListener('pointercancel',viewerPointerUp);els.viewerStage.addEventListener('dblclick',e=>{if(viewerCurrentArticle()?.media?.kind!=='image')return;e.preventDefault();state.viewerMode==='fit'?setViewerActual():setViewerFit(true)});

// ---- v2.4.0 Discover ------------------------------------------------------
function discoverSourceName(item){return String(item?.provider||'').toLowerCase()==='tmdb'?'TMDB':'Metadata'}
function discoverDateText(item){const d=item?.next_episode?.date||item?.date||item?.release_date||'';return d?autoFmtDate(d):(item?.year||'Date unknown')}
function discoverRatingText(item){const r=Number(item?.rating);return Number.isFinite(r)&&r>0?`★ ${r.toFixed(1)}`:''}
function discoverLibraryBadge(item){const s=item?.library_status||{};if(!s.in_library)return '';if(s.wanted)return '<span class="discover-status wanted">WANTED</span>';if(s.has_file)return '<span class="discover-status library">IN LIBRARY</span>';return `<span class="discover-status monitored">${s.monitored?'MONITORED':'IN LIBRARY'}</span>`}
function discoverRegister(item){state.discoverItems.push(item);return state.discoverItems.length-1}
function discoverPosterMarkup(item,{eager=false}={}){if(item?.poster_url)return `<img loading="${eager?'eager':'lazy'}" decoding="async" fetchpriority="${eager?'high':'low'}" src="${escapeHtml(item.poster_url)}" alt="${escapeHtml(item.title||'Poster')}">`;const words=String(item?.title||'NewzDeck').split(/\s+/).slice(0,5).join(' ');return `<div class="discover-poster-fallback"><span>${item?.kind==='tv'?'TV':'MOVIE'}</span><strong>${escapeHtml(words)}</strong><em>${item?.year||''}</em></div>`}
function discoverCard(item){const i=discoverRegister(item),genres=(item.genres||[]).slice(0,2).join(' • '),date=item.next_episode?.date?`Next ${discoverDateText(item)}`:discoverDateText(item),liked=item.liked?' active':'';return `<article class="discover-card" data-discover-detail="${i}"><div class="discover-card-poster">${discoverPosterMarkup(item)}<span class="discover-kind ${item.kind==='tv'?'tv':'movie'}">${item.kind==='tv'?'TV':'MOVIE'}</span>${discoverLibraryBadge(item)}<div class="discover-card-hover"><button class="primary-btn compact" data-discover-open="${i}">Details</button><button class="secondary-btn compact" data-discover-quick-add="${i}" ${(item.library_status||{}).in_library?'disabled title="Already in library"':''}>＋ Add</button></div></div><div class="discover-card-copy"><h3 title="${escapeHtml(item.title||'')}">${escapeHtml(item.title||'Untitled')}</h3><p><span>${escapeHtml(String(date||''))}</span>${discoverRatingText(item)?`<b>${discoverRatingText(item)}</b>`:''}</p>${genres?`<small>${escapeHtml(genres)}</small>`:`<small>${escapeHtml(discoverSourceName(item))}${item.vote_count?` • ${Number(item.vote_count).toLocaleString()} votes`:''}</small>`}<div class="discover-card-actions"><button class="discover-icon-btn${liked}" data-discover-like="${i}" title="More like this">♥</button><button class="discover-icon-btn" data-discover-hide="${i}" title="Not interested">×</button></div></div></article>`}
function discoverDetailKey(item){return `${item?.kind||'movie'}:${item?.tmdb_id||item?.metadata_id||item?.title||''}`}
function discoverCachedDetail(item){const key=discoverDetailKey(item),value=state.discoverDetailCache[key],ts=Number(state.discoverDetailCacheTs[key]||0);return value&&Date.now()-ts<10*60*1000?value:null}
function fetchDiscoverDetail(item,{force=false}={}){if(!item)return Promise.reject(new Error('Discover item is missing'));const key=discoverDetailKey(item),cached=!force&&discoverCachedDetail(item);if(cached)return Promise.resolve(cached);if(state.discoverDetailInflight[key])return state.discoverDetailInflight[key];const p=metadataApi('/api/discover/detail',{provider:'tmdb',metadata_id:item.metadata_id||item.tmdb_id,tmdb_id:item.tmdb_id,kind:item.kind,title:item.title,year:item.year}).then(d=>{const value=d.item||item;state.discoverDetailCache[key]=value;state.discoverDetailCacheTs[key]=Date.now();return value}).finally(()=>{delete state.discoverDetailInflight[key]});state.discoverDetailInflight[key]=p;return p}
function scheduleDiscoverDetailPrefetch(item,element){if(!item||discoverCachedDetail(item))return;const key=discoverDetailKey(item);clearTimeout(state.discoverDetailPrefetchTimers[key]);state.discoverDetailPrefetchTimers[key]=setTimeout(()=>{delete state.discoverDetailPrefetchTimers[key];if(element&&!element.matches(':hover,:focus-within'))return;fetchDiscoverDetail(item).catch(()=>{})},180)}
function cancelDiscoverDetailPrefetch(item){const key=discoverDetailKey(item);clearTimeout(state.discoverDetailPrefetchTimers[key]);delete state.discoverDetailPrefetchTimers[key]}
function discoverWireCards(){document.querySelectorAll('[data-discover-detail]').forEach(c=>{const item=state.discoverItems[Number(c.dataset.discoverDetail)];c.onclick=e=>{if(e.target.closest('button'))return;openDiscoverDetail(item)};c.onmouseenter=()=>scheduleDiscoverDetailPrefetch(item,c);c.onmouseleave=()=>cancelDiscoverDetailPrefetch(item)});document.querySelectorAll('[data-discover-open]').forEach(b=>b.onclick=e=>{e.stopPropagation();openDiscoverDetail(state.discoverItems[Number(b.dataset.discoverOpen)])});document.querySelectorAll('[data-discover-quick-add]').forEach(b=>b.onclick=e=>{e.stopPropagation();openDiscoverDetail(state.discoverItems[Number(b.dataset.discoverQuickAdd)],{focusAdd:true})});document.querySelectorAll('[data-discover-like]').forEach(b=>b.onclick=e=>{e.stopPropagation();discoverPreference('like',state.discoverItems[Number(b.dataset.discoverLike)],b)});document.querySelectorAll('[data-discover-hide]').forEach(b=>b.onclick=e=>{e.stopPropagation();discoverPreference('hide',state.discoverItems[Number(b.dataset.discoverHide)],b)})}
function discoverFiltered(items){const hide=$('discoverHideLibrary')?.checked;return (items||[]).filter(x=>!(hide&&(x.library_status||{}).in_library))}
function discoverEmpty(title,text='Try changing your filters or refreshing Discover.'){return `<div class="discover-empty"><span>✦</span><h3>${escapeHtml(title)}</h3><p>${escapeHtml(text)}</p></div>`}
function discoverErrorBlock(errors){const rows=(errors||[]).filter(Boolean);return rows.length?`<div class="discover-provider-warning"><b>Discover could not load all TMDB data.</b><span>${escapeHtml(rows.slice(0,2).join(' • '))}</span></div>`:''}
function discoverSection(section){const items=discoverFiltered(section.items||[]);if(!items.length)return '';const forYouGrid=section?.id==='for_you'&&state.discoverTab==='for_you';const layout=forYouGrid?'discover-grid discover-for-you-grid':'discover-row';return `<section class="discover-section${forYouGrid?' discover-for-you-section':''}"><div class="discover-section-head"><div><h2>${escapeHtml(section.title||'Discover')}</h2><p>${escapeHtml(section.subtitle||'')}</p></div><span>${items.length} title${items.length===1?'':'s'}</span></div><div class="${layout}">${items.map(discoverCard).join('')}</div></section>`}
function renderDiscoverHome(data,mode='home'){state.discoverItems=[];let sections=data?.sections||[];if(mode==='for_you')sections=sections.filter(x=>x.id==='for_you');const featured=mode==='home'||mode==='new'?data?.featured:null;let hero='';if(featured){const i=discoverRegister(featured);hero=`<section class="discover-hero" style="${featured.backdrop_url?`background-image:linear-gradient(90deg,rgba(5,12,20,.96),rgba(5,12,20,.45)),url('${escapeHtml(featured.backdrop_url)}')`:''}"><div class="discover-hero-poster">${discoverPosterMarkup(featured,{eager:true})}</div><div class="discover-hero-copy"><span>${mode==='new'?'NEW RELEASE SPOTLIGHT':'FEATURED FOR YOU'}</span><h2>${escapeHtml(featured.title||'')}</h2><p>${escapeHtml((featured.overview||'').slice(0,420)||'Explore this title in NewzDeck Discover.')}</p><div>${featured.year?`<b>${featured.year}</b>`:''}${discoverRatingText(featured)?`<b>${discoverRatingText(featured)}</b>`:''}${(featured.genres||[]).slice(0,3).map(g=>`<em>${escapeHtml(g)}</em>`).join('')}</div><button class="primary-btn" data-discover-open="${i}">View details</button></div></section>`}const body=sections.map(discoverSection).join('');$('discoverContent').innerHTML=discoverErrorBlock(data?.errors)+hero+(body||discoverEmpty(mode==='for_you'?'Recommendations are still learning':'No releases found'));discoverWireCards();animateDynamicSurface($('discoverContent'))}
function discoverPaginationMarkup(data,where='bottom'){const current=Math.max(1,Number(data?.page||state.discoverPage||1)),total=Math.max(1,Number(data?.total_pages||1));if(total<=1)return '';const pages=[];for(let p=Math.max(1,current-2);p<=Math.min(total,current+2);p++)pages.push(p);if(!pages.includes(1))pages.unshift(1);if(!pages.includes(total))pages.push(total);const compact=[];let prev=0;for(const p of pages){if(prev&&p-prev>1)compact.push('gap');compact.push(p);prev=p}return `<nav class="discover-pagination ${where}" aria-label="Discover pages"><div class="discover-pagination-buttons"><button class="secondary-btn compact" data-discover-page="1" ${current<=1?'disabled':''} title="First page">« First</button><button class="secondary-btn compact" data-discover-page="${current-1}" ${current<=1?'disabled':''}>‹ Previous</button>${compact.map(p=>p==='gap'?'<span class="discover-page-gap">…</span>':`<button class="discover-page-number${p===current?' active':''}" data-discover-page="${p}" ${p===current?'aria-current="page"':''}>${p}</button>`).join('')}<button class="secondary-btn compact" data-discover-page="${current+1}" ${current>=total?'disabled':''}>Next ›</button><button class="secondary-btn compact" data-discover-page="${total}" ${current>=total?'disabled':''} title="Last available page">Last »</button></div><label class="discover-page-jump">Page <input data-discover-page-input type="number" min="1" max="${total}" value="${current}" inputmode="numeric"> <span>of ${total}</span></label></nav>`}
function wireDiscoverPagination(){document.querySelectorAll('[data-discover-page]').forEach(b=>b.onclick=()=>changeDiscoverPage(Number(b.dataset.discoverPage||1)));document.querySelectorAll('[data-discover-page-input]').forEach(inp=>{const go=()=>changeDiscoverPage(Number(inp.value||1));inp.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();go()}};inp.onchange=go})}
function changeDiscoverPage(page){const max=Math.max(1,Number(document.querySelector('[data-discover-page-input]')?.max||250));const next=Math.max(1,Math.min(max,Math.round(Number(page)||1)));if(next===Number(state.discoverPage||1))return;state.discoverPage=next;els.discoverView?.scrollTo({top:0,behavior:'smooth'});loadDiscover({refresh:true})}
function renderDiscoverBrowse(data,title='Results'){state.discoverItems=[];const items=discoverFiltered(data?.items||[]),total=Number(data?.total_results||items.length),page=Math.max(1,Number(data?.page||1)),pages=Math.max(1,Number(data?.total_pages||1));state.discoverPage=page;const availability=Number(data?.source_total_pages||0)>500?' available':'';const pager=discoverPaginationMarkup({...data,page,total_pages:pages},'top');$('discoverContent').innerHTML=discoverErrorBlock(data?.errors)+`<section class="discover-section discover-browse-section"><div class="discover-section-head discover-browse-head"><div><h2>${escapeHtml(title)}</h2><p>${total.toLocaleString()} matching title${total===1?'':'s'}${pages>1?` • page ${page} of ${pages}${availability}`:''}${Number(data?.page_size||0)?` • up to ${Number(data.page_size)} per page`:''}</p></div></div>${pager}${items.length?`<div class="discover-grid discover-browse-grid">${items.map(discoverCard).join('')}</div>`:discoverEmpty('No matching titles')}${discoverPaginationMarkup({...data,page,total_pages:pages},'bottom')}</section>`;discoverWireCards();wireDiscoverPagination();animateDynamicSurface($('discoverContent'))}
function discoverLoading(text='Loading Discover…'){$('discoverContent').innerHTML=`<div class="discover-loading"><span></span><h3>${escapeHtml(text)}</h3><p>Fetching TMDB metadata, artwork, and recommendations through the NewzDeck Metadata Service.</p></div>`}
async function loadDiscoverGenres(kind){kind=kind==='tv'?'tv':'movie';if((state.discoverGenres[kind]||[]).length){renderDiscoverGenreOptions(kind);return}try{const d=await metadataApi('/api/discover/genres',{kind});state.discoverGenres[kind]=d.genres||[];renderDiscoverGenreOptions(kind)}catch(e){console.warn('Discover genres unavailable',e)}}
function renderDiscoverGenreOptions(kind){const select=$('discoverGenre');if(!select)return;const prior=select.value;select.innerHTML='<option value="">Any genre</option>'+((state.discoverGenres[kind]||[]).map(g=>`<option value="${escapeHtml(g.id)}">${escapeHtml(g.name)}</option>`).join(''));if([...select.options].some(o=>o.value===prior))select.value=prior}
function initDiscoverControls(){const year=$('discoverYear');if(year&&year.options.length<=1){const now=new Date().getFullYear();for(let y=now+2;y>=1900;y--){const o=document.createElement('option');o.value=String(y);o.textContent=String(y);year.appendChild(o)}}loadDiscoverGenres(state.discoverTab==='tv'?'tv':'movie')}
function setDiscoverFilterVisibility(){const filtered=['tv','movies'].includes(state.discoverTab);$('discoverFilters')?.classList.toggle('hidden',!filtered);if(filtered){const kind=state.discoverTab==='tv'?'tv':'movie';$('discoverKind').value=kind;$('discoverKind').disabled=true;$('discoverReleaseTypeWrap')?.classList.toggle('hidden',kind!=='movie');loadDiscoverGenres(kind)}else $('discoverKind').disabled=false;document.querySelectorAll('#discoverTabs [data-discover-tab]').forEach(b=>b.classList.toggle('active',b.dataset.discoverTab===state.discoverTab))}
function discoverFilterPayload(kind){const sel=$('discoverGenre');return {kind,year:$('discoverYear')?.value||'',sort:$('discoverSort')?.value||'popularity',genre:sel?.value||'',genre_name:sel?.selectedOptions?.[0]?.textContent==='Any genre'?'':sel?.selectedOptions?.[0]?.textContent||'',min_rating:$('discoverMinRating')?.value||'',language:$('discoverLanguage')?.value||'',release_type:kind==='movie'?($('discoverReleaseType')?.value||''):'',page:Math.max(1,Number(state.discoverPage||1))}}
async function loadDiscover({refresh=false}={}){if(state.activeView!=='discover')return;const token=++state.discoverLoadToken;setDiscoverFilterVisibility();const q=String($('discoverSearch')?.value||'').trim();if(q){discoverLoading(`Searching for “${q}” • page ${Math.max(1,Number(state.discoverPage||1))}…`);try{const kinds=state.discoverTab==='tv'?['tv']:state.discoverTab==='movies'?['movie']:['tv','movie'];const results=await Promise.all(kinds.map(kind=>metadataApi('/api/discover/browse',{...discoverFilterPayload(kind),query:q})));if(token!==state.discoverLoadToken)return;const items=results.flatMap(x=>x.items||[]),errors=results.flatMap(x=>x.errors||[]),total=results.reduce((n,x)=>n+Number(x.total_results||0),0),pages=Math.max(1,...results.map(x=>Number(x.total_pages||1)));renderDiscoverBrowse({items,errors,total_results:total||items.length,page:Math.max(1,Number(state.discoverPage||1)),total_pages:pages,page_size:results.reduce((n,x)=>n+Number(x.page_size||0),0)||items.length},`Search results for “${q}”`)}catch(e){if(token===state.discoverLoadToken)$('discoverContent').innerHTML=discoverEmpty('Search failed',e.message)}return}
  if(state.discoverTab==='new'){discoverLoading('Loading new releases…');try{const data=await metadataApi('/api/discover/new',{});if(token!==state.discoverLoadToken)return;state.discover=data;renderDiscoverHome(data,'new')}catch(e){if(token===state.discoverLoadToken)$('discoverContent').innerHTML=discoverEmpty('New Releases could not load',e.message)}return}
  if(['home','for_you'].includes(state.discoverTab)){const mode=state.discoverTab,cached=state.discoverPayloadCache?.[mode],cachedAt=Number(state.discoverPayloadCacheTs?.[mode]||0),fresh=!!cached&&(Date.now()-cachedAt)<120000;if(cached){state.discover=cached;renderDiscoverHome(cached,mode);if(fresh&&!refresh)return}else discoverLoading(mode==='for_you'?'Building your recommendations…':'Loading Discover…');try{const data=await metadataApi('/api/discover/home',{mode});if(token!==state.discoverLoadToken)return;state.discover=data;state.discoverPayloadCache[mode]=data;state.discoverPayloadCacheTs[mode]=Date.now();renderDiscoverHome(data,mode)}catch(e){if(token===state.discoverLoadToken&&!cached)$('discoverContent').innerHTML=discoverEmpty('Discover could not load',e.message);else if(token===state.discoverLoadToken&&cached)console.warn('Discover refresh failed; keeping cached page',e)}return}
  const kind=state.discoverTab==='tv'?'tv':'movie';discoverLoading(`Loading ${kind==='tv'?'TV shows':'movies'} • page ${Math.max(1,Number(state.discoverPage||1))}…`);try{const data=await metadataApi('/api/discover/browse',discoverFilterPayload(kind));if(token!==state.discoverLoadToken)return;renderDiscoverBrowse(data,kind==='tv'?'Discover TV Shows':'Discover Movies')}catch(e){if(token===state.discoverLoadToken)$('discoverContent').innerHTML=discoverEmpty('Discover could not load',e.message)}}
function activateDiscoverTab(tab){state.discoverTab=tab||'home';state.discoverPage=1;$('discoverSearch').value='';setDiscoverFilterVisibility();loadDiscover()}
async function discoverPreference(action,item,button=null){if(!item)return;const old=button?.textContent;if(button)button.disabled=true;try{await metadataApi('/api/discover/preference',{action,item});state.discoverPayloadCache.for_you=null;state.discoverPayloadCacheTs.for_you=0;if(action==='hide'){state.discoverPayloadCache.home=null;state.discoverPayloadCacheTs.home=0;toast(`${item.title} hidden from Discover.`);await loadDiscover({refresh:true})}else{item.liked=action==='like';toast(action==='like'?'Recommendations updated.':'Discover preference cleared.','success');if(button)button.classList.toggle('active',action==='like')}}catch(e){toast(e.message,'error')}finally{if(button){button.disabled=false;if(old!=null)button.textContent=old}}}
function discoverFacts(item){const facts=[];if(item.year)facts.push(String(item.year));if(item.certification)facts.push(String(item.certification));if(item.runtime)facts.push(`${Math.round(Number(item.runtime))} min`);if(item.status)facts.push(String(item.status));if(item.network)facts.push(String(item.network));if(item.number_of_seasons)facts.push(`${item.number_of_seasons} season${Number(item.number_of_seasons)===1?'':'s'}`);if(item.number_of_episodes)facts.push(`${item.number_of_episodes} episodes`);if(item.language)facts.push(String(item.language).toUpperCase());if(item.rating)facts.push(`★ ${Number(item.rating).toFixed(1)}`);return facts}
function discoverPeople(title,rows,role=false){if(!(rows||[]).length)return '';return `<section class="discover-detail-section"><h3>${escapeHtml(title)}</h3><div class="discover-people">${rows.slice(0,16).map(x=>`<div class="${x.tmdb_id?'discover-person-link':''}" ${x.tmdb_id?`data-discover-person="${x.tmdb_id}"`:''}>${x.image_url?`<img loading="lazy" src="${escapeHtml(x.image_url)}" alt="">`:'<span>●</span>'}<strong>${escapeHtml(x.name||'')}</strong>${role&&x.role?`<small>${escapeHtml(x.role)}</small>`:x.character?`<small>${escapeHtml(x.character)}</small>`:''}</div>`).join('')}</div></section>`}
function discoverAttribution(item){return `<div class="discover-attribution">Metadata and artwork provided by <a href="https://www.themoviedb.org" target="_blank" rel="noreferrer">TMDB</a>. This product uses the TMDB API but is not endorsed or certified by TMDB.</div>`}
function discoverDetailRecommendations(title,rows){if(!(rows||[]).length)return '';return `<section class="discover-detail-section"><h3>${escapeHtml(title)}</h3><div class="discover-row discover-detail-row">${rows.slice(0,12).map(discoverCard).join('')}</div></section>`}
function discoverReleaseDates(item){const rows=[];if(item.digital_release_date)rows.push(`Digital ${autoFmtDate(item.digital_release_date)}`);if(item.physical_release_date)rows.push(`Physical ${autoFmtDate(item.physical_release_date)}`);if(item.theatrical_release_date)rows.push(`Theatrical ${autoFmtDate(item.theatrical_release_date)}`);return rows.length?`<p class="discover-small"><b>Release dates:</b> ${escapeHtml(rows.join(' • '))}</p>`:''}
function renderDiscoverDetail(item,{focusAdd=false}={}){state.discoverCurrentDetail=item;state.discoverPersonReturn=null;$('discoverDetailTitle').textContent=item.title||'Title';$('discoverDetailEyebrow').textContent=item.kind==='tv'?'TV SERIES • TMDB':'MOVIE • TMDB';$('discoverDetailMeta').textContent=[item.year||'',discoverRatingText(item),(item.genres||[]).slice(0,3).join(' • ')].filter(Boolean).join(' • ');const backdrop=$('discoverDetailBackdrop');backdrop.style.backgroundImage=item.backdrop_url?`linear-gradient(180deg,rgba(5,11,18,.12),rgba(5,11,18,.95)),url("${String(item.backdrop_url).replace(/"/g,'')}")`:'';backdrop.classList.toggle('empty',!item.backdrop_url);const status=item.library_status||{};const roots=item.kind==='tv'?(state.automation?.config?.tv_roots||[]):state.automation?.config?.movie_roots||[];const profiles=state.automation?.profiles||[];const facts=discoverFacts(item);let actions='';if(status.in_library){actions=`<button class="primary-btn" id="discoverOpenLibrary">Open in Automation</button><button class="secondary-btn" id="discoverSearchNzb">⌕ Search NZB</button>`}else{actions=`<div class="discover-add-controls"><label>Root folder<select id="discoverAddRoot"><option value="">${roots.length?'Automatic • storage-aware':'Set up root later'}</option>${roots.map(r=>`<option value="${escapeHtml(r)}">${escapeHtml(r)}</option>`).join('')}</select></label><label>Quality<select id="discoverAddProfile">${profiles.map(p=>`<option value="${escapeHtml(p.id)}">${escapeHtml(p.name)}</option>`).join('')}</select></label><label>Monitoring<select id="discoverAddMonitor" title="Choose what NewzDeck should automatically monitor">${automationMonitoringOptions(item.kind,item.kind==='movie'?'movie':'all')}</select></label></div><button class="primary-btn" id="discoverAddAutomation">＋ Add to Automation</button><button class="secondary-btn" id="discoverSearchNzb">⌕ Search NZB Now</button>`}
  const next=item.next_episode?.date?`<p class="discover-small"><b>Next episode:</b> S${String(item.next_episode.season||0).padStart(2,'0')}E${String(item.next_episode.episode||0).padStart(2,'0')} • ${escapeHtml(item.next_episode.name||'')} • ${escapeHtml(autoFmtDate(item.next_episode.date))}</p>`:'';const extraLinks=[item.trailer_url?`<button class="secondary-btn" id="discoverTrailerBtn">▶ Trailer</button>`:'',item.official_site?`<button class="secondary-btn" id="discoverOfficialBtn">Official site ↗</button>`:''].join('');$('discoverDetailBody').innerHTML=`<div class="discover-detail-main"><div class="discover-detail-poster">${discoverPosterMarkup(item)}${discoverLibraryBadge(item)}</div><div class="discover-detail-copy"><div class="discover-facts">${facts.map(x=>`<span>${escapeHtml(x)}</span>`).join('')}</div><p class="discover-overview">${escapeHtml(item.overview||'No overview is available from TMDB.')}</p>${next}${discoverReleaseDates(item)}${(item.companies||[]).length?`<p class="discover-small"><b>Production:</b> ${escapeHtml(item.companies.join(', '))}</p>`:''}${(item.countries||[]).length?`<p class="discover-small"><b>Country:</b> ${escapeHtml(item.countries.join(', '))}</p>`:''}<div class="discover-detail-actions">${actions}${extraLinks}<button class="discover-like-action${item.liked?' active':''}" id="discoverLikeBtn">♥ More like this</button><button class="discover-hide-action" id="discoverHideBtn">Not interested</button></div>${discoverAttribution(item)}</div></div>${discoverPeople('Cast',item.cast||[])}${discoverPeople('Creators & Crew',item.crew||[],true)}${discoverDetailRecommendations('Recommended For You',item.recommendations||[])}${discoverDetailRecommendations('Similar Titles',item.similar||[])}`;
  $('discoverOpenLibrary')?.addEventListener('click',()=>{const id=(item.library_status||{}).library_id;if(!id)return;state.automationTab=item.kind==='tv'?'tv':'movies';setMainView('automation');renderAutomation();setTimeout(()=>openAutomationItem(id),80)});$('discoverAddAutomation')?.addEventListener('click',()=>addDiscoverToAutomation(item));$('discoverSearchNzb')?.addEventListener('click',()=>openDiscoverReleaseSearch(item));$('discoverLikeBtn')?.addEventListener('click',async e=>{await discoverPreference('like',item,e.currentTarget);e.currentTarget.textContent='♥ More like this'});$('discoverHideBtn')?.addEventListener('click',async()=>{await discoverPreference('hide',item);$('discoverDetailModal').classList.add('hidden')});$('discoverTrailerBtn')?.addEventListener('click',()=>window.open(item.trailer_url,'_blank','noopener'));$('discoverOfficialBtn')?.addEventListener('click',()=>window.open(item.official_site,'_blank','noopener'));document.querySelectorAll('[data-discover-person]').forEach(el=>el.onclick=()=>openDiscoverPerson(el.dataset.discoverPerson));discoverWireCards();if(focusAdd)setTimeout(()=>$('discoverAddRoot')?.focus(),50)}
async function openDiscoverDetail(item,opts={}){if(!item)return;const token=++state.discoverDetailToken;$('discoverDetailTitle').textContent=item.title||'Loading…';$('discoverDetailEyebrow').textContent=item.kind==='tv'?'TV SERIES • TMDB':'MOVIE • TMDB';$('discoverDetailMeta').textContent=item.year||'';$('discoverDetailBackdrop').style.backgroundImage='';$('discoverDetailBody').innerHTML='<div class="discover-loading"><span></span><p>Loading TMDB title details…</p></div>';$('discoverDetailModal').classList.remove('hidden');const cached=discoverCachedDetail(item);try{const automationReady=state.automation?Promise.resolve(true):loadAutomation({quiet:true,render:false});const detailReady=cached?Promise.resolve(cached):fetchDiscoverDetail(item);const [,detail]=await Promise.all([automationReady,detailReady]);if(token!==state.discoverDetailToken||$('discoverDetailModal').classList.contains('hidden'))return;renderDiscoverDetail(detail||item,opts)}catch(e){if(token===state.discoverDetailToken)$('discoverDetailBody').innerHTML=discoverEmpty('Could not load title details',e.message)}}
async function openDiscoverPerson(tmdbId){if(!tmdbId)return;state.discoverPersonReturn=state.discoverCurrentDetail;$('discoverDetailEyebrow').textContent='PERSON • TMDB';$('discoverDetailTitle').textContent='Loading…';$('discoverDetailMeta').textContent='';$('discoverDetailBackdrop').style.backgroundImage='';$('discoverDetailBackdrop').classList.add('empty');$('discoverDetailBody').innerHTML='<div class="discover-loading"><span></span><p>Loading person and filmography…</p></div>';try{const d=await metadataApi('/api/discover/person',{tmdb_id:tmdbId}),p=d.person||{};$('discoverDetailTitle').textContent=p.name||'Person';$('discoverDetailMeta').textContent=[p.department,p.birthday,p.place_of_birth].filter(Boolean).join(' • ');$('discoverDetailBody').innerHTML=`<div class="discover-detail-main"><div class="discover-person-profile">${p.profile_url?`<img src="${escapeHtml(p.profile_url)}" alt="">`:`<div class="discover-poster-fallback"><strong>${escapeHtml(p.name||'')}</strong></div>`}</div><div class="discover-detail-copy"><button class="secondary-btn compact" id="discoverPersonBack">← Back to title</button><p class="discover-overview discover-person-bio">${escapeHtml(p.biography||'No biography is available from TMDB.')}</p>${p.homepage?`<button class="secondary-btn" id="discoverPersonSite">Official site ↗</button>`:''}${discoverAttribution({})}</div></div><section class="discover-detail-section"><h3>Known For / Filmography</h3><div class="discover-grid discover-person-credits">${(p.credits||[]).slice(0,30).map(discoverCard).join('')}</div></section>`;$('discoverPersonBack').onclick=()=>{if(state.discoverPersonReturn)renderDiscoverDetail(state.discoverPersonReturn)};$('discoverPersonSite')?.addEventListener('click',()=>window.open(p.homepage,'_blank','noopener'));discoverWireCards()}catch(e){$('discoverDetailBody').innerHTML=discoverEmpty('Could not load person details',e.message)}}
async function addDiscoverToAutomation(item){const b=$('discoverAddAutomation'),old=b?.textContent;if(b){b.disabled=true;b.textContent='Adding…'}try{const mode=$('discoverAddMonitor')?.value||automationMonitoringMode(item.kind),payload={provider:'tmdb',metadata_id:String(item.metadata_id||item.tmdb_id||''),tmdb_id:item.tmdb_id,kind:item.kind,title:item.title,year:item.year,poster_url:item.poster_url||'',overview:item.overview||'',genres:item.genres||[],rating:item.rating,network:item.network||'',monitored:mode!=='none',monitor_mode:mode,quality_profile_id:$('discoverAddProfile')?.value||'',root_folder:$('discoverAddRoot')?.value||''};const d=await api('/api/automation/media/add',payload);await loadAutomation({quiet:true});item.library_status={in_library:true,library_id:d.item.id,monitored:mode!=='none',wanted:false,has_file:false};toast(`${item.title} added • ${automationMonitoringChoices(item.kind).find(x=>x.value===mode)?.label||'Monitoring configured'}.`,'success');renderDiscoverDetail(item)}catch(e){toast(e.message,'error');if(b){b.disabled=false;b.textContent=old}}}
function renderDiscoverReleaseRows(item,d){const rows=d.releases||[];$('releaseSearchTitle').textContent=item.title;$('releaseSearchSubtitle').textContent=`Discover search • ${Number(d.searched_indexers||0)} enabled indexer${Number(d.searched_indexers||0)===1?'':'s'} • Grab organizes once without adding to Automation`;$('releaseSearchBody').innerHTML=(d.errors||[]).map(x=>`<div class="release-indexer-error">${escapeHtml(x.indexer)}: ${escapeHtml(x.error)}</div>`).join('')+(rows.length?`<div class="release-table"><div class="release-row header"><span>Release</span><span>Quality</span><span>Size</span><span>Age</span><span>Score</span><span></span></div>${rows.map((r,i)=>{const age=r.published?Math.max(0,(Date.now()/1000-r.published)/86400):null;return `<div class="release-row ${r.accepted?'accepted':'rejected'}"><span><strong>${escapeHtml(r.title)}</strong><small>${escapeHtml(r.indexer||'')} • ${escapeHtml((r.reasons||[]).join(' • '))}</small></span><span>${escapeHtml(r.parsed?.quality||'Unknown')}<small>${r.current_quality&&r.current_quality!=='Unknown'?`Current: ${escapeHtml(r.current_quality)} → `:''}${escapeHtml([r.parsed?.codec,r.parsed?.hdr,r.parsed?.audio].filter(Boolean).join(' • '))}${r.automatic_eligible?' • AUTO OK':' • MANUAL ONLY'}</small></span><span>${r.size?formatBytes(r.size):'—'}</span><span>${age==null?'—':age<1?`${Math.max(1,Math.round(age*24))}h`:`${Math.round(age)}d`}</span><span><b class="release-score ${r.score>=0?'positive':'negative'}">${r.score>=0?'+':''}${r.score}</b></span><span><button class="primary-btn compact" data-grab-discover-release="${i}">Grab & Organize</button></span></div>`}).join('')}</div>`:automationEmpty('⌕','No releases found','Add or configure a Newznab indexer, or try again later.'));document.querySelectorAll('[data-grab-discover-release]').forEach(b=>b.onclick=()=>grabAutomationRelease(rows[Number(b.dataset.grabDiscoverRelease)],b))}
async function openDiscoverReleaseSearch(item){const libraryId=(item.library_status||{}).library_id;if(libraryId){$('discoverDetailModal').classList.add('hidden');return openReleaseSearch(libraryId)}$('releaseSearchTitle').textContent=item.title;$('releaseSearchSubtitle').textContent='Searching enabled Newznab indexers from Discover…';$('releaseSearchBody').innerHTML='<div class="release-loading">Searching indexers and scoring releases…</div>';$('releaseSearchModal').classList.remove('hidden');try{const d=await metadataApi('/api/discover/releases/search',{kind:item.kind,title:item.title,year:item.year,tmdb_id:item.tmdb_id||item.metadata_id||'',metadata_id:item.metadata_id||item.tmdb_id||'',provider:item.provider||item.metadata_provider||'tmdb',root_folder:$('discoverAddRoot')?.value||'',quality_profile_id:$('discoverAddProfile')?.value||''});renderDiscoverReleaseRows(item,d)}catch(e){$('releaseSearchBody').innerHTML=automationEmpty('!','Search failed',e.message)}}


// ---- Media Automation + Smart Import & Library Organization ----------------
function autoFmtDate(v){if(!v)return 'Date unknown';const d=new Date(`${String(v).slice(0,10)}T12:00:00`);return Number.isNaN(d.getTime())?String(v):d.toLocaleDateString(undefined,{year:'numeric',month:'short',day:'numeric'})}
function autoProfile(id){return (state.automation?.profiles||[]).find(p=>String(p.id)===String(id))||(state.automation?.profiles||[])[0]||null}
function autoItem(id){return (state.automation?.library||[]).find(x=>String(x.id)===String(id))||null}
function automationViewDataSignature(data,tab=state.automationTab){
  if(!data)return '';
  try{
    if(tab==='tv'||tab==='movies'){const kind=tab==='tv'?'tv':'movie';return JSON.stringify((data.library||[]).filter(x=>x.kind===kind));}
    if(tab==='wanted')return JSON.stringify(data.wanted||{});
    if(tab==='calendar')return JSON.stringify(data.calendar||[]);
    if(tab==='history')return JSON.stringify(data.history||data.activity||[]);
    if(tab==='health')return JSON.stringify(data.health||{});
    if(tab==='profiles')return JSON.stringify(data.profiles||[]);
    if(tab==='indexers')return JSON.stringify(data.indexers||[]);
    return JSON.stringify([data.config||{},data.indexers||[]]);
  }catch(_e){return String(Date.now())}
}
function automationSurfaceBusy(){
  const content=$('automationContent'),active=document.activeElement;
  if(content&&active&&content.contains(active)&&isEditableTarget(active))return true;
  return ['automationAddModal','automationItemModal','releaseSearchModal','qualityProfileModal','indexerModal'].some(id=>{const el=$(id);return el&&!el.classList.contains('hidden')});
}
function updateAutomationLiveIndicators(){
  renderAutomationBadges();
  if(state.activeView!=='automation')return;
  if(state.automationTab==='setup'){
    const c=state.automation?.config||{},a=state.automation?.automatic||{},q=a.quiet_hours||{},status=$('automaticDownloadStatus');
    if(status){
      const enabled=!!c.automatic_grab_enabled;
      status.className=`setup-status ${enabled?(q.active?'warning':'good'):''}`;
      status.textContent=enabled?(q.active?`◷ Quiet hours • resumes ${q.resume_ts?new Date(Number(q.resume_ts)*1000).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'}):c.automatic_quiet_end}`:(a.running?`● ${automationRunDetail(a)}`:'✓ Continuous Automation enabled')):'Continuous Automation is off';
    }
    const runtime=$('automationContent')?.querySelector('.continuous-runtime-strip');
    if(runtime){const cells=runtime.querySelectorAll('b');if(cells[0])cells[0].textContent=c.automatic_feed_enabled?`${Number(a.last_feed_count||0)} recent`:'Off';if(cells[1])cells[1].textContent=String(Number(a.last_feed_matches||0));if(cells[2])cells[2].textContent=String(Number(a.active_targets||0));if(cells[3])cells[3].textContent=autoTimeUntil(a.next_cycle_ts)}
  }
}
async function loadAutomation({quiet=false,render=true,background=false}={}){
  const before=automationViewDataSignature(state.automation,state.automationTab);
  try{
    const next=await api('/api/automation/summary');state.automation=next;state.automationLoadError='';renderAutomationBadges();
    if(state.activeView==='automation'){
      if(background){
        updateAutomationLiveIndicators();
        const after=automationViewDataSignature(next,state.automationTab);
        if(state.automationTab!=='setup'&&before!==after&&!automationSurfaceBusy())renderAutomation({animate:false});
      }else if(render)renderAutomation();
    }
    return true;
  }
  catch(e){state.automationLoadError=e.message||'Automation could not be loaded.';if(state.activeView==='automation'&&render&&!background)renderAutomation({animate:false});if(!quiet)toast(state.automationLoadError,'error');return false;}
}
const AUTOMATION_BADGE_CACHE_KEY='newzdeckAutomationSidebarCountsV2';
let automationLastPositiveBadgeCounts=null;
let automationSidebarLastResponse=null;
let automationStartupPrimeGeneration=0;
let automationSidebarStartupUntil=0;
function normalizedAutomationBadgeCounts(c={}){return {tv:Number(c.tv||0),movies:Number(c.movies||0),missing:Number(c.missing||0),upgrades:Number(c.upgrades||0),indexers:c.indexers==null?null:Number(c.indexers||0)}}
function automationBadgeMediaTotal(c={}){const v=normalizedAutomationBadgeCounts(c);return v.tv+v.movies}
function automationBadgeWantedTotal(c={}){const v=normalizedAutomationBadgeCounts(c);return v.missing+v.upgrades}
function rememberAutomationBadgeCounts(c={}){try{const v=normalizedAutomationBadgeCounts(c);localStorage.setItem(AUTOMATION_BADGE_CACHE_KEY,JSON.stringify({...v,ts:Date.now()}))}catch(_e){}}
function restoreAutomationBadgeCounts(){try{const raw=JSON.parse(localStorage.getItem(AUTOMATION_BADGE_CACHE_KEY)||'null');if(raw&&typeof raw==='object'&&automationBadgeMediaTotal(raw)>0){automationLastPositiveBadgeCounts=normalizedAutomationBadgeCounts(raw);applyAutomationBadgeCounts(raw,{remember:false,preservePositive:false});return true}}catch(_e){}return false}
function applyAutomationBadgeCounts(c={},options={}){
  let values=normalizedAutomationBadgeCounts(c);
  const preservePositive=options.preservePositive!==false;
  const positive=automationBadgeMediaTotal(values)>0;
  if(positive)automationLastPositiveBadgeCounts={...values};
  else if(preservePositive&&automationLastPositiveBadgeCounts&&automationBadgeMediaTotal(automationLastPositiveBadgeCounts)>0)values={...automationLastPositiveBadgeCounts};
  const set=(id,n)=>{const e=$(id);if(!e)return;const value=Number(n||0);e.textContent=String(value);if(value>0){e.classList.remove('hidden');e.hidden=false;e.style.setProperty('display','inline-flex','important')}else{e.classList.add('hidden');e.hidden=true;e.style.setProperty('display','none','important')}};
  set('tvNavBadge',values.tv);set('movieNavBadge',values.movies);set('wantedNavBadge',values.missing+values.upgrades);
  if($('autoTvCount'))$('autoTvCount').textContent=values.tv;if($('autoMovieCount'))$('autoMovieCount').textContent=values.movies;if($('autoMissingCount'))$('autoMissingCount').textContent=values.missing;if($('autoUpgradeCount'))$('autoUpgradeCount').textContent=values.upgrades;if($('autoIndexerCount')&&values.indexers!=null)$('autoIndexerCount').textContent=values.indexers;
  if(options.remember!==false&&automationBadgeMediaTotal(values)>0)rememberAutomationBadgeCounts(values);
  return values;
}
function renderAutomationBadges(){applyAutomationBadgeCounts(state.automation?.counts||{},{preservePositive:Date.now()<automationSidebarStartupUntil})}
async function loadAutomationSidebarCounts(){
  try{
    const counts=await api('/api/automation/sidebar-counts',null,{timeoutMs:5000,timeoutMessage:'Automation sidebar counts are still loading.'});
    automationSidebarLastResponse=counts||{};applyAutomationBadgeCounts(counts||{},{preservePositive:true});return counts||{};
  }catch(_e){return null}
}
function primeAutomationSidebarCounts(){
  restoreAutomationBadgeCounts();
  const generation=++automationStartupPrimeGeneration;
  automationSidebarStartupUntil=Date.now()+45000;
  const delays=[0,350,800,1500,2600,4200,6500,9500,14000,21000,30000,42000];
  for(const delay of delays)setTimeout(async()=>{
    if(generation!==automationStartupPrimeGeneration)return;
    const counts=await loadAutomationSidebarCounts();
    if(generation!==automationStartupPrimeGeneration)return;
    // Do not consider a transient zero snapshot authoritative during startup.
    // Continue the scheduled probes until a populated media-library snapshot is seen.
    if(counts&&automationBadgeMediaTotal(counts)>0)automationLastPositiveBadgeCounts=normalizedAutomationBadgeCounts(counts);
  },delay);
  // Full Automation summary is useful for Discover/Automation later, but it must
  // never be allowed to erase a positive sidebar snapshot while startup settles.
  setTimeout(()=>void loadAutomation({quiet:true,render:false,background:true}),500);
  setTimeout(()=>void loadAutomation({quiet:true,render:false,background:true}),5000);
  setTimeout(()=>void loadAutomation({quiet:true,render:false,background:true}),15000);
}
async function activateAutomationTab(tab){state.automationTab=tab||'tv';document.querySelectorAll('#automationTabs [data-auto-tab]').forEach(b=>b.classList.toggle('active',b.dataset.autoTab===state.automationTab));document.querySelectorAll('.sidebar [data-auto-tab]').forEach(b=>b.classList.toggle('active',state.activeView==='automation'&&b.dataset.autoTab===state.automationTab));if(state.activeView!=='automation')setMainView('automation');if(!state.automation){$('automationContent').innerHTML=automationEmpty('◌','Loading automation…','Reading your media automation configuration.');await loadAutomation({quiet:false});}renderAutomation();}
function setAutomationTab(tab){void activateAutomationTab(tab)}
function openAutomationSetup(){void activateAutomationTab('setup')}
function openAutomationIndexers(){void activateAutomationTab('indexers')}
function automationEmpty(icon,title,text,button=''){return `<div class="automation-empty"><span>${icon}</span><h3>${escapeHtml(title)}</h3><p>${escapeHtml(text)}</p>${button}</div>`}
function automationLibraryCard(item){
  let status='';let missing=0,total=0,have=0;
  if(item.kind==='tv'){for(const s of item.seasons||[])for(const ep of s.episodes||[]){total++;if(ep.has_file)have++;else if(ep.monitored!==false&&ep.air_date&&ep.air_date<=new Date().toISOString().slice(0,10))missing++}status=`${have}/${total} episodes${missing?` • ${missing} missing`:''}`}
  else{const available=item.availability_date||item.digital_release_date||item.physical_release_date||item.release_date;status=item.movie_file?`${item.movie_file.quality||'File found'}${item.movie_file.cutoff_met?' • cutoff met':' • upgrade wanted'}`:(available&&available<=new Date().toISOString().slice(0,10)?'Missing':'Waiting for release')}
  if(item.library_root_status==='offline')status='ROOT OFFLINE • last-known file state preserved';
  const poster=item.poster_url?`<img src="${escapeHtml(item.poster_url)}" alt="">`:`<div class="automation-poster-placeholder">${item.kind==='tv'?'TV':'MOVIE'}</div>`;
  const autoOn=!!state.automation?.config?.automatic_grab_enabled&&automationMonitoringMode(item)!=='none';
  return `<article class="automation-media-card ${item.library_root_status==='offline'?'root-offline':''}" data-auto-item="${escapeHtml(item.id)}"><div class="automation-poster">${poster}${item.library_root_status==='offline'?'<em class="root-offline-badge">ROOT OFFLINE</em>':''}</div><div class="automation-card-body"><h3>${escapeHtml(item.title)}</h3><p>${item.year||''}${item.status&&item.status!=='unknown'?` • ${escapeHtml(item.status)}`:''}${item.kind==='tv'&&item.library_title?` • Library: ${escapeHtml(item.library_title)}`:''}</p><div class="automation-card-status">${escapeHtml(status)}</div><div class="automation-monitor-row"><span class="automation-monitor-chip ${automationMonitoringMode(item)==='none'?'off':''}">${escapeHtml(automationMonitoringLabel(item))}</span>${autoOn?'<span class="continuous-monitor-dot" title="Continuous Automation is watching this title">Watching</span>':''}</div><div class="automation-card-footer"><span>${escapeHtml(autoProfile(item.quality_profile_id)?.name||'Quality profile')}</span><button class="secondary-btn compact" data-open-auto="${escapeHtml(item.id)}">Manage</button></div></div></article>`
}
function automationLibrarySortLabel(item){return String(item?.title||item?.library_title||'').trim()}
function compareAutomationLibraryItems(a,b){const titleOrder=automationLibrarySortLabel(a).localeCompare(automationLibrarySortLabel(b),undefined,{sensitivity:'base',numeric:true});if(titleOrder)return titleOrder;const yearOrder=Number(a?.year||0)-Number(b?.year||0);if(yearOrder)return yearOrder;return String(a?.id||'').localeCompare(String(b?.id||''),undefined,{sensitivity:'base',numeric:true})}
function renderAutomationLibrary(kind){const items=(state.automation?.library||[]).filter(x=>x.kind===kind).slice().sort(compareAutomationLibraryItems);$('automationTitle').textContent=kind==='tv'?'TV Library':'Movie Library';$('automationSubtitle').textContent=kind==='tv'?'Monitor series, seasons, and individual episodes.':'Monitor movies and identify missing or upgradeable files.';$('automationAddBtn').classList.remove('hidden');$('automationScanBtn').classList.remove('hidden');$('automationContent').innerHTML=items.length?`<div class="automation-library-grid">${items.map(automationLibraryCard).join('')}</div>`:automationEmpty(kind==='tv'?'▣':'◈',kind==='tv'?'No TV series yet':'No movies yet',`Add your first ${kind==='tv'?'series':'movie'} to begin monitoring.`,`<button class="primary-btn" id="autoEmptyAdd">＋ Add ${kind==='tv'?'series':'movie'}</button>`);$('autoEmptyAdd')?.addEventListener('click',openAutomationAdd);document.querySelectorAll('[data-open-auto]').forEach(b=>b.onclick=e=>{e.stopPropagation();openAutomationItem(b.dataset.openAuto)});document.querySelectorAll('[data-auto-item]').forEach(c=>c.onclick=()=>openAutomationItem(c.dataset.autoItem))}
function wantedRow(x,type){const current=type==='upgrade'?`<span class="wanted-current">Current: ${escapeHtml(x.current_quality||'Unknown')} → ${escapeHtml(x.cutoff||'cutoff')}</span>`:'';const auto=(state.automation?.automatic?.target_states||{})[x.target_key||'']||{},policy=x.automation_policy||{};const labels={queued:'QUEUED',grabbed:'QUEUED',queueing:'QUEUEING',searching:'SEARCHING',waiting:'WAITING',needs_root:'ROOT OFFLINE',error:'RETRYING',retrying:'RETRYING',downloading:'DOWNLOADING',processing:'PROCESSING',cancelling:'CANCELLING',release_detected:'RELEASE FOUND',quiet_hours:'QUIET',imported:'IMPORTED'};const pct=Number(auto.progress||0)>0?` ${Math.round(Number(auto.progress))}%`:'';const ast=labels[auto.status]?`<span class="wanted-pill auto ${escapeHtml(auto.status)}" title="${escapeHtml(auto.message||'')}">${labels[auto.status]}${pct}</span>`:'';const pst=policy.label?`<span class="wanted-pill policy ${escapeHtml(policy.status||'')}" title="${escapeHtml(policy.message||'')}">${escapeHtml(policy.label)}</span>`:'';const availability=x.kind==='movie'&&x.availability?` • ${x.availability==='home'?'Digital/physical release':x.availability==='assumed_home'?'Home-release fallback':'Theatrical release'}`:'';const why=`<span class="wanted-why"><b>${escapeHtml(x.reason_label|| (type==='upgrade'?'Quality below cutoff':'Missing file'))}</b><small>${escapeHtml(x.reason_detail||'')}${policy.message?` • ${escapeHtml(policy.message)}`:''}${auto.last_selection_reason?` • Last choice: ${escapeHtml(auto.last_selection_reason)}`:''}</small></span>`;return `<div class="wanted-row ${policy.status&&policy.status!=='eligible'&&policy.status!=='manual'?'policy-paused':''}"><div><strong>${escapeHtml(x.label)}</strong><small>${escapeHtml(x.episode_name||'')}${x.date?` • ${autoFmtDate(x.date)}`:''}${availability}${auto.message?` • ${escapeHtml(auto.message)}`:''}</small></div>${why}${current}<span class="wanted-pill ${type}">${type==='upgrade'?'UPGRADE':'MISSING'}</span>${pst}${ast}<button class="primary-btn compact" data-release-search="${escapeHtml(x.item_id)}" data-season="${x.season??''}" data-episode="${x.episode??''}">Search releases</button></div>`}
function autoTimeUntil(ts){const n=Number(ts||0);if(!n)return '—';const sec=Math.round(n-Date.now()/1000);if(sec<=0)return 'Due now';if(sec<90)return `${sec}s`;const m=Math.round(sec/60);if(m<90)return `${m} min`;const h=Math.round(m/60);return `${h} hr`}
function automationRunDetail(a){
  if(!a?.running)return '';
  const p=a.progress||{},total=Number(p.total||0),processed=Number(p.processed||0),target=String(p.target||'').trim(),phase=String(p.phase||'').trim();
  if(total>0&&target)return `Checking ${Math.min(total,processed+1)}/${total} • ${target}`;
  if(phase==='release-feed')return 'Checking the release feed…';
  if(phase==='wanted')return 'Building current Wanted targets…';
  if(phase==='starting')return 'Starting Continuous Automation…';
  return p.detail||'Checking release sources now…';
}
function renderAutomationWanted(){
  const w=state.automation?.wanted||{missing:[],upgrades:[]},a=state.automation?.automatic||{},c=state.automation?.config||{},q=a.quiet_hours||{};
  $('automationTitle').textContent='Wanted';$('automationSubtitle').textContent=c.automatic_grab_enabled?'Continuous Automation is watching releases and will queue qualifying media automatically.':'Monitored media that is missing or below its quality cutoff.';$('automationAddBtn').classList.add('hidden');$('automationScanBtn').classList.remove('hidden');
  const mode=!c.automatic_grab_enabled?'MANUAL':q.active?'QUIET HOURS':a.running?'CHECKING':'WATCHING';
  const modeClass=c.automatic_grab_enabled&&!q.active?'good':q.active?'warning':'';
  const banner=`<div class="automation-card continuous-automation-banner"><div class="automation-card-head"><div><b>${c.automatic_grab_enabled?'Continuous Automation':'Automatic Downloads OFF'}</b><small>${!c.automatic_grab_enabled?'Enable Continuous Automation in Setup to search and grab monitored releases automatically.':q.active?`New grabs are deferred until ${new Date(Number(q.resume_ts||0)*1000).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'})}. RSS monitoring continues in the background.`:(a.running?automationRunDetail(a):a.last_result||'NewzDeck is monitoring the Wanted list in the background.')}</small></div><span class="setup-status ${modeClass}">${mode}</span></div>${c.automatic_grab_enabled?`<div class="continuous-status-grid"><div><span>RELEASE FEED</span><strong>${c.automatic_feed_enabled?`${Number(a.last_feed_count||0)} recent`:'OFF'}</strong><small>${c.automatic_feed_enabled?`next poll ${autoTimeUntil(a.next_feed_poll_ts)}`:'Enable in Setup'}</small></div><div><span>LAST MATCHES</span><strong>${Number(a.last_feed_matches||0)}</strong><small>RSS/new-release candidates</small></div><div><span>ACTIVE TARGETS</span><strong>${Number(a.active_targets||0)}</strong><small>queued / downloading / processing</small></div><div><span>NEXT CYCLE</span><strong>${a.running?'In progress':autoTimeUntil(a.next_cycle_ts)}</strong><small>${a.running&&Number(a.running_seconds||0)>0?`${Math.max(1,Math.round(Number(a.running_seconds)/60))} min elapsed`:a.smart_retry_enabled?'smart retry active':'fixed retry schedule'}</small></div></div>`:''}</div>`;
  const pc=w.policy_counts||{},backlogPaused=Number(pc.backlog_paused||0),upgradesPaused=Number(pc.upgrades_paused||0),pausedTotal=backlogPaused+upgradesPaused;
  const policyCallout=c.automatic_grab_enabled&&pausedTotal?`<div class="wanted-policy-callout"><div><b>${pausedTotal} Wanted item${pausedTotal===1?' is':'s are'} paused by Automation settings</b><small>${backlogPaused?`${backlogPaused} existing backlog item${backlogPaused===1?'':'s'} will stay visible here but will not be searched automatically while <strong>Search existing missing backlog</strong> is off.`:''}${backlogPaused&&upgradesPaused?' ':''}${upgradesPaused?`${upgradesPaused} quality upgrade${upgradesPaused===1?' is':'s are'} waiting because <strong>Automatically grab quality upgrades</strong> is off.`:''} Manual <strong>Search releases</strong> always remains available.</small></div><button class="secondary-btn compact" id="wantedPolicySetupBtn">Review Automation settings</button></div>`:'';
  $('automationContent').innerHTML=banner+policyCallout+`<div class="wanted-section"><div class="automation-section-head"><div><div class="eyebrow">MISSING</div><h2>${w.missing.length} item${w.missing.length===1?'':'s'}</h2></div></div>${w.missing.length?w.missing.map(x=>wantedRow(x,'missing')).join(''):automationEmpty('✓','Nothing missing','All released monitored media is present.')}</div><div class="wanted-section"><div class="automation-section-head"><div><div class="eyebrow">QUALITY UPGRADES</div><h2>${w.upgrades.length} item${w.upgrades.length===1?'':'s'}</h2></div></div>${w.upgrades.length?w.upgrades.map(x=>wantedRow(x,'upgrade')).join(''):automationEmpty('★','No upgrades wanted','Everything currently meets its profile cutoff.')}</div>`;$('wantedPolicySetupBtn')?.addEventListener('click',()=>setAutomationTab('setup'));wireReleaseSearchButtons()
}
function calendarLocalDate(d=new Date()){const y=d.getFullYear(),m=String(d.getMonth()+1).padStart(2,'0'),day=String(d.getDate()).padStart(2,'0');return `${y}-${m}-${day}`}
function calendarDateObj(value){const m=String(value||'').match(/^(\d{4})-(\d{2})-(\d{2})$/);return m?new Date(Number(m[1]),Number(m[2])-1,Number(m[3]),12,0,0):new Date(value)}
function calendarDayLabel(value){const d=calendarDateObj(value),today=calendarLocalDate(),tomorrow=calendarLocalDate(new Date(Date.now()+86400000));if(value===today)return 'Today';if(value===tomorrow)return 'Tomorrow';return d.toLocaleDateString([],{weekday:'long',month:'short',day:'numeric'})}
function calendarStatusLabel(e){return e?.status_label||({upcoming:'Upcoming',today:e?.kind==='tv'?'Airs today':'Available today',missing:'Missing',upgrade:'Upgrade wanted',imported:'Imported'}[e?.status]||'Monitoring')}
function calendarStatusClass(e){return ['upcoming','today','missing','upgrade','imported'].includes(e?.status)?e.status:'upcoming'}
function calendarFilteredEvents(){let events=[...(state.automation?.calendar||[])];const kind=state.automationCalendarKind||'all',status=state.automationCalendarStatus||'all';if(kind!=='all')events=events.filter(e=>e.kind===kind);if(status==='upcoming')events=events.filter(e=>e.status==='upcoming'||e.status==='today');else if(status==='action')events=events.filter(e=>e.status==='missing'||e.status==='upgrade');else if(status==='imported')events=events.filter(e=>e.status==='imported');return events}
function calendarEventPoster(e,cls=''){return e.poster_url?`<img class="${cls}" src="${escapeHtml(e.poster_url)}" alt="" loading="lazy">`:`<div class="calendar-poster-placeholder ${cls}">${e.kind==='tv'?'TV':'MOVIE'}</div>`}
function calendarEventTitle(e){return e.kind==='tv'?`${escapeHtml(e.label||'')} <span>${escapeHtml(e.subtitle||'')}</span>`:`${escapeHtml(e.label||'')} <span>${escapeHtml(e.subtitle||'')}</span>`}
function calendarOpenItem(id){if(id)openAutomationItem(id)}
function calendarSetView(view){state.automationCalendarView=view==='month'?'month':'guide';localStorage.setItem('newzdeckAutomationCalendarView',state.automationCalendarView);renderAutomationCalendar()}
function calendarSetMonth(offset=0){let d;if(state.automationCalendarMonth){const [y,m]=state.automationCalendarMonth.split('-').map(Number);d=new Date(y,m-1,1)}else d=new Date(new Date().getFullYear(),new Date().getMonth(),1);d.setMonth(d.getMonth()+offset);state.automationCalendarMonth=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;state.automationCalendarSelectedDate=`${state.automationCalendarMonth}-01`;renderAutomationCalendar()}
function calendarJumpToday(){const d=new Date();state.automationCalendarMonth=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;state.automationCalendarSelectedDate=calendarLocalDate(d);renderAutomationCalendar()}
function calendarWireControls(){document.querySelectorAll('[data-cal-view]').forEach(b=>b.onclick=()=>calendarSetView(b.dataset.calView));$('calendarKindFilter')?.addEventListener('change',e=>{state.automationCalendarKind=e.target.value;localStorage.setItem('newzdeckAutomationCalendarKind',e.target.value);renderAutomationCalendar()});$('calendarStatusFilter')?.addEventListener('change',e=>{state.automationCalendarStatus=e.target.value;localStorage.setItem('newzdeckAutomationCalendarStatus',e.target.value);renderAutomationCalendar()});$('calendarRangeFilter')?.addEventListener('change',e=>{state.automationCalendarRange=Number(e.target.value||30);localStorage.setItem('newzdeckAutomationCalendarRange',String(state.automationCalendarRange));renderAutomationCalendar()});$('calendarPrevMonth')?.addEventListener('click',()=>calendarSetMonth(-1));$('calendarNextMonth')?.addEventListener('click',()=>calendarSetMonth(1));$('calendarTodayBtn')?.addEventListener('click',calendarJumpToday);document.querySelectorAll('[data-cal-date]').forEach(b=>b.onclick=()=>{state.automationCalendarSelectedDate=b.dataset.calDate;renderAutomationCalendar()});document.querySelectorAll('[data-open-calendar-item]').forEach(b=>b.onclick=e=>{e.stopPropagation();calendarOpenItem(b.dataset.openCalendarItem)})}
function calendarSummary(events){const today=calendarLocalDate(),todayObj=calendarDateObj(today),weekEnd=new Date(todayObj);weekEnd.setDate(weekEnd.getDate()+6);const weekEndS=calendarLocalDate(weekEnd),month=today.slice(0,7);const thisWeek=events.filter(e=>e.date>=today&&e.date<=weekEndS).length,needs=events.filter(e=>e.status==='missing'||e.status==='upgrade').length,thisMonth=events.filter(e=>String(e.date||'').slice(0,7)===month).length,imported=events.filter(e=>e.status==='imported').length;return {thisWeek,needs,thisMonth,imported}}
function renderCalendarHero(allEvents){const stats=calendarSummary(allEvents),continuous=!!state.automation?.config?.automatic_grab_enabled,next=allEvents.find(e=>e.date>=calendarLocalDate()&&(e.status==='upcoming'||e.status==='today'))||allEvents.find(e=>e.date>=calendarLocalDate());return `<section class="release-calendar-hero"><div class="calendar-hero-copy"><div class="eyebrow">RELEASE PLANNER</div><h2>${next?'Next up':'Your monitored schedule'}</h2>${next?`<div class="calendar-next-up">${calendarEventPoster(next,'calendar-next-poster')}<div><strong>${escapeHtml(next.label||'')}</strong><span>${escapeHtml(next.subtitle||'')}</span><small>${calendarDayLabel(next.date)} • ${escapeHtml(calendarStatusLabel(next))}</small></div></div>`:`<p>Upcoming TV episodes and movie releases will appear here as NewzDeck refreshes metadata.</p>`}</div><div class="calendar-hero-stats"><div><span>THIS WEEK</span><b>${stats.thisWeek}</b><small>monitored releases</small></div><div class="${stats.needs?'attention':''}"><span>NEEDS ACTION</span><b>${stats.needs}</b><small>missing / upgrades</small></div><div><span>THIS MONTH</span><b>${stats.thisMonth}</b><small>calendar events</small></div><div class="${continuous?'live':''}"><span>AUTOMATION</span><b>${continuous?'WATCHING':'MANUAL'}</b><small>${continuous?'Continuous monitoring active':'Enable in Setup'}</small></div></div></section>`}
function renderCalendarToolbar(){const view=state.automationCalendarView||'guide';return `<div class="release-calendar-toolbar"><div class="calendar-view-switch" role="group" aria-label="Calendar view"><button class="${view==='guide'?'active':''}" data-cal-view="guide"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 5h14M5 12h14M5 19h14"></path><circle cx="2.5" cy="5" r=".5"></circle><circle cx="2.5" cy="12" r=".5"></circle><circle cx="2.5" cy="19" r=".5"></circle></svg>Guide</button><button class="${view==='month'?'active':''}" data-cal-view="month"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"></rect><path d="M7 3v4M17 3v4M3 10h18"></path></svg>Calendar</button></div><div class="calendar-filter-strip"><label>Media<select id="calendarKindFilter"><option value="all" ${state.automationCalendarKind==='all'?'selected':''}>All media</option><option value="tv" ${state.automationCalendarKind==='tv'?'selected':''}>TV shows</option><option value="movie" ${state.automationCalendarKind==='movie'?'selected':''}>Movies</option></select></label><label>Status<select id="calendarStatusFilter"><option value="all" ${state.automationCalendarStatus==='all'?'selected':''}>All status</option><option value="upcoming" ${state.automationCalendarStatus==='upcoming'?'selected':''}>Upcoming</option><option value="action" ${state.automationCalendarStatus==='action'?'selected':''}>Needs action</option><option value="imported" ${state.automationCalendarStatus==='imported'?'selected':''}>Imported</option></select></label>${view==='guide'?`<label>Range<select id="calendarRangeFilter"><option value="7" ${state.automationCalendarRange===7?'selected':''}>Next 7 days</option><option value="14" ${state.automationCalendarRange===14?'selected':''}>Next 14 days</option><option value="30" ${state.automationCalendarRange===30?'selected':''}>Next 30 days</option><option value="90" ${state.automationCalendarRange===90?'selected':''}>Next 90 days</option></select></label>`:''}<button class="secondary-btn compact calendar-today-button" id="calendarTodayBtn">Today</button></div></div>`}
function renderCalendarGuide(events){const today=calendarLocalDate(),startObj=calendarDateObj(today);startObj.setDate(startObj.getDate()-7);const start=calendarLocalDate(startObj),endObj=calendarDateObj(today);endObj.setDate(endObj.getDate()+Math.max(7,Number(state.automationCalendarRange||30)));const end=calendarLocalDate(endObj);events=events.filter(e=>e.date>=start&&e.date<=end);const groups=new Map();for(const e of events){if(!groups.has(e.date))groups.set(e.date,[]);groups.get(e.date).push(e)}if(!events.length)return automationEmpty('▦','Nothing in this range','Try a wider date range or different Calendar filters.');return `<div class="calendar-guide">${[...groups].map(([date,rows])=>`<section class="calendar-guide-day ${date===today?'is-today':''}"><header><div><span>${calendarDateObj(date).toLocaleDateString([],{weekday:'short'}).toUpperCase()}</span><b>${calendarDateObj(date).getDate()}</b></div><div><strong>${calendarDayLabel(date)}</strong><small>${rows.length} release${rows.length===1?'':'s'}</small></div></header><div class="calendar-guide-events">${rows.map(e=>`<article class="calendar-guide-event status-${calendarStatusClass(e)}" data-open-calendar-item="${escapeHtml(e.item_id)}">${calendarEventPoster(e,'calendar-guide-poster')}<div class="calendar-guide-time"><b>${e.kind==='tv'?'EPISODE':'MOVIE'}</b><span>${escapeHtml(e.network||e.availability_label||'Release')}</span></div><div class="calendar-guide-main"><div class="calendar-guide-title"><strong>${escapeHtml(e.label||'')}</strong><span>${escapeHtml(e.subtitle||'')}</span></div><div class="calendar-guide-meta"><span class="calendar-kind ${e.kind}">${e.kind==='tv'?'TV':'MOVIE'}</span>${e.quality?`<span>${escapeHtml(e.quality)}</span>`:''}<span>${escapeHtml(e.network||e.availability_label||'')}</span></div></div><span class="calendar-status-badge ${calendarStatusClass(e)}">${escapeHtml(calendarStatusLabel(e))}</span><button class="calendar-open-button" data-open-calendar-item="${escapeHtml(e.item_id)}">Details</button></article>`).join('')}</div></section>`).join('')}</div>`}
function renderCalendarMonth(events){if(!state.automationCalendarMonth){const d=new Date();state.automationCalendarMonth=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`};const [year,month]=state.automationCalendarMonth.split('-').map(Number),first=new Date(year,month-1,1,12),gridStart=new Date(first);gridStart.setDate(1-first.getDay());const selected=state.automationCalendarSelectedDate||calendarLocalDate();const monthLabel=first.toLocaleDateString([],{month:'long',year:'numeric'}),cells=[];for(let i=0;i<42;i++){const d=new Date(gridStart);d.setDate(gridStart.getDate()+i);const ds=calendarLocalDate(d),rows=events.filter(e=>e.date===ds),inMonth=d.getMonth()===month-1,isToday=ds===calendarLocalDate();cells.push(`<button class="calendar-month-cell ${inMonth?'':'outside'} ${isToday?'today':''} ${selected===ds?'selected':''}" data-cal-date="${ds}"><div class="calendar-month-date"><span>${d.getDate()}</span>${rows.length?`<b>${rows.length}</b>`:''}</div><div class="calendar-month-events">${rows.slice(0,3).map(e=>`<span class="calendar-month-event ${calendarStatusClass(e)} ${e.kind}" data-open-calendar-item="${escapeHtml(e.item_id)}"><i></i><em>${escapeHtml(e.kind==='tv'?(e.subtitle||e.label):(e.label||''))}</em></span>`).join('')}${rows.length>3?`<small>+${rows.length-3} more</small>`:''}</div></button>`)}const selectedRows=events.filter(e=>e.date===selected);return `<div class="calendar-month-layout"><div class="calendar-month-main"><div class="calendar-month-nav"><button class="ghost-btn" id="calendarPrevMonth" title="Previous month">‹</button><div><strong>${monthLabel}</strong><span>${events.filter(e=>String(e.date||'').slice(0,7)===state.automationCalendarMonth).length} monitored release${events.filter(e=>String(e.date||'').slice(0,7)===state.automationCalendarMonth).length===1?'':'s'}</span></div><button class="ghost-btn" id="calendarNextMonth" title="Next month">›</button></div><div class="calendar-weekdays">${['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(x=>`<span>${x}</span>`).join('')}</div><div class="calendar-month-grid">${cells.join('')}</div></div><aside class="calendar-day-panel"><div class="eyebrow">DAY DETAILS</div><h3>${calendarDayLabel(selected)}</h3><p>${selectedRows.length?`${selectedRows.length} monitored release${selectedRows.length===1?'':'s'}`:'Nothing scheduled'}</p><div class="calendar-day-panel-list">${selectedRows.length?selectedRows.map(e=>`<button class="calendar-day-panel-event status-${calendarStatusClass(e)}" data-open-calendar-item="${escapeHtml(e.item_id)}">${calendarEventPoster(e,'calendar-day-panel-poster')}<span><b>${escapeHtml(e.label||'')}</b><small>${escapeHtml(e.subtitle||e.availability_label||'')}</small><em>${escapeHtml(calendarStatusLabel(e))}</em></span></button>`).join(''):`<div class="calendar-day-empty"><span>○</span><b>Clear day</b><small>Select another date to see its monitored releases.</small></div>`}</div></aside></div>`}
function renderAutomationCalendar(){const all=state.automation?.calendar||[],events=calendarFilteredEvents(),continuous=!!state.automation?.config?.automatic_grab_enabled;$('automationTitle').textContent='Release Calendar';$('automationSubtitle').textContent=continuous?'Your monitored release schedule, with Continuous Automation status built in.':'Plan upcoming TV episodes and movie releases in Guide or Calendar view.';$('automationAddBtn').classList.add('hidden');$('automationScanBtn').classList.add('hidden');$('automationContent').innerHTML=`<div class="release-calendar-shell">${renderCalendarHero(all)}${renderCalendarToolbar()}<section class="release-calendar-surface">${state.automationCalendarView==='month'?renderCalendarMonth(events):renderCalendarGuide(events)}</section><div class="calendar-legend"><span><i class="upcoming"></i>Upcoming</span><span><i class="today"></i>Today</span><span><i class="missing"></i>Missing</span><span><i class="upgrade"></i>Upgrade</span><span><i class="imported"></i>Imported</span></div></div>`;calendarWireControls()}

function automationHistoryLabel(r){const kind=String(r.kind||'activity').replace(/[-_]/g,' ');return kind.replace(/\b\w/g,m=>m.toUpperCase())}
function renderAutomationHistory(){const rows=state.automation?.history||state.automation?.activity||[];$('automationTitle').textContent='Automation History';$('automationSubtitle').textContent='A local audit trail of metadata refreshes, library reconciliation, grabs, downloads, imports, and recovery events.';$('automationAddBtn').classList.add('hidden');$('automationScanBtn').classList.add('hidden');$('automationContent').innerHTML=rows.length?`<div class="automation-history">${rows.map(r=>{const d=r.details||{},when=new Date(Number(r.ts||0)*1000);const size=Number(d.file_size||d.release_size||0);const detail=[d.quality,d.from_quality&&d.to_quality?`${d.from_quality} → ${d.to_quality}`:'',d.selection_source==='feed'?'RSS/new-release feed':d.selection_source==='scheduled-search'?'Scheduled Wanted search':'',d.indexer||'',size?formatBytes(size):'',d.destination||d.path||'',d.root||''].filter(Boolean).join(' • ');const release=d.release_title?`<small class="history-release" title="${escapeHtml(d.release_title)}">Release: ${escapeHtml(d.release_title)}</small>`:'';return `<article class="history-row history-${escapeHtml(r.kind||'activity')}"><div class="history-dot"></div><div><div class="history-head"><strong>${escapeHtml(automationHistoryLabel(r))}</strong><time>${Number.isNaN(when.getTime())?'':when.toLocaleString()}</time></div><p>${escapeHtml(r.message||'Automation event')}</p>${release}${detail?`<small>${escapeHtml(detail)}</small>`:''}${d.item_id?`<button class="history-open" data-open-auto="${escapeHtml(d.item_id)}">Open title</button>`:''}</div></article>`}).join('')}</div>`:automationEmpty('◷','No Automation history yet','Library scans, metadata updates, automatic grabs, and imports will appear here.');document.querySelectorAll('[data-open-auto]').forEach(b=>b.onclick=()=>openAutomationItem(b.dataset.openAuto))}
async function clearAutomationBlacklist(targetKey,guid=''){
  try{
    const r=await api('/api/automation/blacklist/clear',{target_key:targetKey,guid});
    await loadAutomation({quiet:true});renderAutomation();
    toast(`Removed ${Number(r.removed||0)} release blacklist entr${Number(r.removed||0)===1?'y':'ies'}. Automation can reconsider the release.`,'success');
  }catch(e){toast(e.message,'error')}
}
function renderAutomationHealth(){
  const h=state.automation?.health||{},a=state.automation?.automatic||{},roots=h.roots||[],bl=h.blacklists||[],ih=h.indexer_health||[];
  $('automationTitle').textContent='Automation Health';
  $('automationSubtitle').textContent='Live readiness, Root Folder availability, release recovery, and indexer reliability for unattended Automation.';
  $('automationAddBtn').classList.add('hidden');$('automationScanBtn').classList.add('hidden');
  const metadataStatus=String(h.metadata?.status||'ready');
  const rootOffline=roots.filter(x=>!x.online).length;
  $('automationContent').innerHTML=`
    <div class="automation-health-grid">
      <article class="automation-health-card ${metadataStatus==='ready'?'good':'warning'}"><span>METADATA</span><strong>${metadataStatus==='ready'?'READY':'CHECK'}</strong><small>${escapeHtml(h.metadata?.url||'Not configured')}</small></article>
      <article class="automation-health-card ${rootOffline?'warning':'good'}"><span>ROOT FOLDERS</span><strong>${Number(h.roots_online||0)}/${Number(h.roots_total||0)}</strong><small>${rootOffline?`${rootOffline} offline`:'All configured roots online'}</small></article>
      <article class="automation-health-card ${Number(h.indexers_enabled||0)?'good':'warning'}"><span>INDEXERS</span><strong>${Number(h.indexers_enabled||0)}/${Number(h.indexers_total||0)}</strong><small>enabled</small></article>
      <article class="automation-health-card"><span>MONITORED</span><strong>${Number(h.monitored_tv||0)+Number(h.monitored_movies||0)}</strong><small>${Number(h.monitored_tv||0)} TV • ${Number(h.monitored_movies||0)} movies</small></article>
      <article class="automation-health-card ${Number(h.wanted_missing||0)+Number(h.wanted_upgrades||0)?'attention':'good'}"><span>WANTED</span><strong>${Number(h.wanted_missing||0)+Number(h.wanted_upgrades||0)}</strong><small>${Number(h.wanted_missing||0)} missing • ${Number(h.wanted_upgrades||0)} upgrades</small></article>
      <article class="automation-health-card ${Number(h.blacklist_count||0)?'attention':'good'}"><span>FAILED RELEASES</span><strong>${Number(h.blacklist_count||0)}</strong><small>${Number(h.blacklist_count||0)?'automatically blacklisted':'No bad releases retained'}</small></article>
      <article class="automation-health-card ${Number(h.needs_attention_count||0)?'warning':'good'}"><span>NEEDS ATTENTION</span><strong>${Number(h.needs_attention_count||0)}</strong><small>${Number(h.needs_attention_count||0)?'preserved imports waiting for action':'No blocked imports'}</small></article>
      <article class="automation-health-card ${h.feed_enabled?'good':''}"><span>RELEASE FEED</span><strong>${h.feed_enabled?'ACTIVE':'OFF'}</strong><small>${h.feed_enabled?`${Number(h.last_feed_count||0)} recent releases • last poll ${h.last_feed_poll_ts?new Date(Number(h.last_feed_poll_ts)*1000).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'}):'pending'}`:'Enable Continuous feed polling in Setup'}</small></article>
      <article class="automation-health-card ${h.quiet_hours?.active?'warning':h.quiet_hours?.enabled?'good':''}"><span>QUIET HOURS</span><strong>${h.quiet_hours?.active?'ACTIVE':h.quiet_hours?.enabled?'READY':'OFF'}</strong><small>${h.quiet_hours?.enabled?`${escapeHtml(h.quiet_hours.start||'')} – ${escapeHtml(h.quiet_hours.end||'')}`:'No automatic grab blackout window'}</small></article>
    </div>
    <div class="automation-health-columns">
      <section class="automation-health-panel"><div class="automation-section-head"><div><div class="eyebrow">STORAGE</div><h2>Root Folders</h2></div></div>
        ${roots.length?roots.map(r=>`<div class="automation-health-row"><span class="health-dot ${r.online?'good':'bad'}"></span><div><strong>${escapeHtml(r.kind)}</strong><small>${escapeHtml(r.path)}</small></div><b>${r.online?'ONLINE':'OFFLINE'}</b></div>`).join(''):automationEmpty('◇','No Root Folders','Configure TV and Movie Root Folders in Setup.')}
      </section>
      <section class="automation-health-panel"><div class="automation-section-head"><div><div class="eyebrow">RELEASE SOURCES</div><h2>Indexer Reliability</h2></div></div>
        ${ih.length?ih.map(x=>`<div class="automation-health-row"><span class="health-dot ${Number(x.penalty||0)>=36?'bad':Number(x.penalty||0)>0?'warn':'good'}"></span><div><strong>${escapeHtml(x.name)}</strong><small>${Number(x.recent_successes||0)} successful • ${Number(x.recent_failures||0)} failed in 24h</small></div><b>${Number(x.penalty||0)?`-${Number(x.penalty)} score`:'HEALTHY'}</b></div>`).join(''):`<div class="automation-health-empty">Indexer reliability starts learning after automatic downloads complete or fail.</div>`}
      </section>
    </div>
    ${(h.needs_attention||[]).length?`<section class="automation-health-panel automation-blacklist-panel"><div class="automation-section-head"><div><div class="eyebrow">PRESERVED DOWNLOADS</div><h2>Imports Needing Attention</h2><p>Downloaded files are preserved. Fix the Root Folder/storage issue, then retry without downloading the NZB again.</p></div></div><div class="automation-blacklist-list">${(h.needs_attention||[]).map((x,i)=>`<div class="automation-blacklist-row"><div><strong>${escapeHtml(x.name||'Automation package')}</strong><span>${escapeHtml(x.message||'Import needs attention')}</span></div><button class="primary-btn compact" data-retry-import="${i}">Retry import</button></div>`).join('')}</div></section>`:''}
    <section class="automation-health-panel automation-blacklist-panel"><div class="automation-section-head"><div><div class="eyebrow">SELF-HEALING</div><h2>Failed Release Blacklist</h2><p>NewzDeck automatically skips these exact NZBs and tries the next-best qualifying release.</p></div>${bl.length?'<button class="secondary-btn compact" id="clearAllReleaseBlacklist">Clear all</button>':''}</div>
      ${bl.length?`<div class="automation-blacklist-list">${bl.map((x,i)=>`<div class="automation-blacklist-row"><div><strong>${escapeHtml(x.target_label||x.target_key||'Automation target')}</strong><span>${escapeHtml(x.title||'Unknown release')}</span><small>${escapeHtml(x.indexer||'Unknown indexer')} • ${escapeHtml(x.reason||'Download failed')} • ${x.failed_ts?new Date(Number(x.failed_ts)*1000).toLocaleString():''}</small></div><button class="secondary-btn compact" data-clear-blacklist="${i}">Retry release</button></div>`).join('')}</div>`:automationEmpty('✓','No failed releases blacklisted','Automatic failures will appear here. NewzDeck will immediately search for another candidate.')}
    </section>`;
  document.querySelectorAll('[data-retry-import]').forEach(b=>b.onclick=()=>{const x=(h.needs_attention||[])[Number(b.dataset.retryImport)];if(x)retryAutomationImport(x.collection_id,b)});
  document.querySelectorAll('[data-clear-blacklist]').forEach(b=>b.onclick=()=>{const x=bl[Number(b.dataset.clearBlacklist)];if(x)clearAutomationBlacklist(x.target_key,x.guid||'')});
  $('clearAllReleaseBlacklist')?.addEventListener('click',()=>clearAutomationBlacklist('',''));
}
async function retryAutomationImport(collectionId,button){const old=button?.textContent||'';if(button){button.disabled=true;button.textContent='Retrying…'}try{const r=await api('/api/automation/import/retry',{collection_id:collectionId});toast(r.message||'Import retry started.','success');setTimeout(async()=>{await loadAutomation({quiet:true});renderAutomation()},900)}catch(e){toast(e.message,'error')}finally{if(button?.isConnected){button.disabled=false;button.textContent=old}}}

// Automation profile/indexer editor handlers.
// These were referenced by the UI wiring but missing from the browser bundle,
// which aborted top-level script execution before initializeApp() could run.
function qualityProfileLines(value=''){return String(value||'').split(/\r?\n/).map(x=>x.trim()).filter(Boolean)}
function refreshQualityCutoff(selected=''){
  const select=$('qualityProfileCutoff');if(!select)return;
  const qualities=qualityProfileLines($('qualityProfileQualities')?.value||'');
  const current=String(selected||select.value||'');
  select.innerHTML=qualities.map(q=>`<option value="${escapeHtml(q)}">${escapeHtml(q)}</option>`).join('');
  select.value=qualities.includes(current)?current:(qualities[0]||'');
}
function qualityProfileFormatsText(rows=[]){
  return (Array.isArray(rows)?rows:[]).map(f=>`${String(f?.name||'Preference').trim()} | ${(f?.contains||[]).join(', ')} | ${Number(f?.score||0)}`).join('\n');
}
function parseQualityProfileFormats(value=''){
  return qualityProfileLines(value).map(line=>{
    const parts=line.split('|').map(x=>x.trim()),name=parts[0]||'Preference';
    const contains=String(parts[1]||'').split(',').map(x=>x.trim()).filter(Boolean);
    const score=Number(parts[2]||0);
    return {name,contains,score:Number.isFinite(score)?Math.trunc(score):0};
  }).filter(x=>x.contains.length||x.name);
}
function openQualityProfile(id=''){
  const p=(state.automation?.profiles||[]).find(x=>String(x.id)===String(id))||null;
  $('qualityProfileId').value=p?.id||'';
  $('qualityProfileTitle').textContent=p?'Edit Quality Profile':'New Quality Profile';
  $('qualityProfileName').value=p?.name||'';
  $('qualityProfileQualities').value=(p?.qualities||['2160p','1080p','720p','WEB']).join('\n');
  $('qualityProfileMinSize').value=Number(p?.min_size_mb||0);
  $('qualityProfileMaxSize').value=Number(p?.max_size_gb||0);
  $('qualityProfileFormats').value=qualityProfileFormatsText(p?.custom_formats||[]);
  $('qualityProfileGroups').value=(p?.preferred_groups||[]).join('\n');
  $('qualityProfileRejectTerms').value=(p?.reject_terms||[]).join('\n');
  refreshQualityCutoff(p?.cutoff||'');
  $('qualityProfileDelete').classList.toggle('hidden',!p);
  $('qualityProfileModal').classList.remove('hidden');
  setTimeout(()=>$('qualityProfileName')?.focus(),30);
}
async function saveQualityProfile(){
  const button=$('qualityProfileSave'),old=button?.textContent||'Save profile';
  const payload={
    id:$('qualityProfileId')?.value||'',
    name:$('qualityProfileName')?.value.trim()||'',
    qualities:qualityProfileLines($('qualityProfileQualities')?.value||''),
    cutoff:$('qualityProfileCutoff')?.value||'',
    min_size_mb:Number($('qualityProfileMinSize')?.value||0),
    max_size_gb:Number($('qualityProfileMaxSize')?.value||0),
    custom_formats:parseQualityProfileFormats($('qualityProfileFormats')?.value||''),
    preferred_groups:qualityProfileLines($('qualityProfileGroups')?.value||''),
    reject_terms:qualityProfileLines($('qualityProfileRejectTerms')?.value||'')
  };
  if(button){button.disabled=true;button.textContent='Saving…'}
  try{
    await api('/api/automation/profile/save',payload);
    await loadAutomation({quiet:true,render:false});
    $('qualityProfileModal').classList.add('hidden');
    if(state.activeView==='automation'&&state.automationTab==='profiles')renderAutomation({animate:false});
    toast('Quality profile saved.','success');
  }catch(e){toast(e.message,'error')}
  finally{if(button?.isConnected){button.disabled=false;button.textContent=old}}
}
async function deleteQualityProfile(){
  const id=$('qualityProfileId')?.value||'';if(!id)return;
  const name=$('qualityProfileName')?.value.trim()||'this quality profile';
  if(!confirm(`Delete ${name}? Existing library items keep their current profile assignment until you choose another profile.`))return;
  const button=$('qualityProfileDelete'),old=button?.textContent||'Delete';
  if(button){button.disabled=true;button.textContent='Deleting…'}
  try{
    await api('/api/automation/profile/delete',{id});
    await loadAutomation({quiet:true,render:false});
    $('qualityProfileModal').classList.add('hidden');
    if(state.activeView==='automation'&&state.automationTab==='profiles')renderAutomation({animate:false});
    toast('Quality profile deleted.','success');
  }catch(e){toast(e.message,'error')}
  finally{if(button?.isConnected){button.disabled=false;button.textContent=old}}
}
function openIndexerModal(id=''){
  const x=(state.automation?.indexers||[]).find(v=>String(v.id)===String(id))||null;
  $('indexerId').value=x?.id||'';
  $('indexerModalTitle').textContent=x?'Edit Indexer':'Add Indexer';
  $('indexerName').value=x?.name||'';
  $('indexerEnabled').value=x?.enabled===false?'false':'true';
  $('indexerUrl').value=x?.url||'';
  $('indexerApiKey').value='';
  $('indexerApiKey').placeholder=x?.api_key_configured?'Saved key • leave blank to keep':'API key';
  $('indexerTvCategories').value=x?.categories_tv||'5000';
  $('indexerMovieCategories').value=x?.categories_movies||'2000';
  $('indexerDelete').classList.toggle('hidden',!x);
  $('indexerTest').classList.toggle('hidden',!x);
  const result=$('indexerTestResult');result.className='test-result hidden';result.textContent='';
  $('indexerModal').classList.remove('hidden');
  setTimeout(()=>$('indexerName')?.focus(),30);
}
function indexerEditorPayload(){
  const id=$('indexerId')?.value||'',saved=(state.automation?.indexers||[]).find(x=>String(x.id)===String(id));
  return {
    id,
    name:$('indexerName')?.value.trim()||'',
    enabled:$('indexerEnabled')?.value!=='false',
    url:$('indexerUrl')?.value.trim()||'',
    api_key:$('indexerApiKey')?.value.trim()||'',
    allow_empty_key:!!saved?.api_key_configured,
    categories_tv:$('indexerTvCategories')?.value.trim()||'5000',
    categories_movies:$('indexerMovieCategories')?.value.trim()||'2000'
  };
}
async function saveIndexer(){
  const button=$('indexerSave'),old=button?.textContent||'Save indexer';
  if(button){button.disabled=true;button.textContent='Saving…'}
  try{
    const d=await api('/api/automation/indexer/save',indexerEditorPayload());
    await loadAutomation({quiet:true,render:false});
    if(d?.indexer?.id)$('indexerId').value=d.indexer.id;
    $('indexerModal').classList.add('hidden');
    if(state.activeView==='automation'&&state.automationTab==='indexers')renderAutomation({animate:false});
    toast('Indexer saved.','success');
  }catch(e){toast(e.message,'error')}
  finally{if(button?.isConnected){button.disabled=false;button.textContent=old}}
}
async function testIndexer(){
  const id=$('indexerId')?.value||'',result=$('indexerTestResult'),button=$('indexerTest'),old=button?.textContent||'Test';
  if(!id){result.className='test-result error';result.textContent='Save this indexer before testing the connection.';return}
  if(button){button.disabled=true;button.textContent='Testing…'}
  result.className='test-result';result.textContent='Testing Newznab capabilities…';
  try{
    const d=await api('/api/automation/indexer/test',{id});
    result.className='test-result success';result.textContent=`Connected${d?.latency_ms?` • ${Math.round(Number(d.latency_ms))} ms`:''}${d?.server?` • ${d.server}`:''}`;
  }catch(e){result.className='test-result error';result.textContent=e.message}
  finally{if(button?.isConnected){button.disabled=false;button.textContent=old}}
}
async function deleteIndexer(){
  const id=$('indexerId')?.value||'';if(!id)return;
  const name=$('indexerName')?.value.trim()||'this indexer';
  if(!confirm(`Delete ${name}?`))return;
  const button=$('indexerDelete'),old=button?.textContent||'Delete';
  if(button){button.disabled=true;button.textContent='Deleting…'}
  try{
    await api('/api/automation/indexer/delete',{id});
    await loadAutomation({quiet:true,render:false});
    $('indexerModal').classList.add('hidden');
    if(state.activeView==='automation'&&state.automationTab==='indexers')renderAutomation({animate:false});
    toast('Indexer deleted.','success');
  }catch(e){toast(e.message,'error')}
  finally{if(button?.isConnected){button.disabled=false;button.textContent=old}}
}

function renderAutomationProfiles(){const ps=state.automation?.profiles||[];$('automationTitle').textContent='Quality Profiles';$('automationSubtitle').textContent='Define acceptable qualities, upgrade cutoffs, and preferred release terms.';$('automationAddBtn').classList.add('hidden');$('automationScanBtn').classList.add('hidden');$('automationContent').innerHTML=`<div class="automation-section-head"><div><div class="eyebrow">DECISION ENGINE</div><h2>${ps.length} quality profile${ps.length===1?'':'s'}</h2></div><button class="primary-btn" id="newQualityProfileBtn">＋ New profile</button></div><div class="profile-grid">${ps.map(p=>`<article class="profile-card" data-profile="${escapeHtml(p.id)}"><div><h3>${escapeHtml(p.name)}</h3><p>Cutoff: <b>${escapeHtml(p.cutoff||'—')}</b></p></div><ol>${(p.qualities||[]).slice(0,8).map(q=>`<li class="${q===p.cutoff?'cutoff':''}">${escapeHtml(q)}${q===p.cutoff?' <span>cutoff</span>':''}</li>`).join('')}</ol><div class="profile-formats">${(p.custom_formats||[]).map(f=>`<span>${escapeHtml(f.name)} ${Number(f.score||0)>=0?'+':''}${Number(f.score||0)}</span>`).join('')||'<span>No preferred terms</span>'}${Number(p.min_size_mb||0)?`<span>Min ${Number(p.min_size_mb)} MB</span>`:''}${Number(p.max_size_gb||0)?`<span>Max ${Number(p.max_size_gb)} GB</span>`:''}${(p.preferred_groups||[]).length?`<span>${(p.preferred_groups||[]).length} preferred group${p.preferred_groups.length===1?'':'s'}</span>`:''}${(p.reject_terms||[]).length?`<span>${(p.reject_terms||[]).length} reject term${p.reject_terms.length===1?'':'s'}</span>`:''}</div><button class="secondary-btn" data-edit-profile="${escapeHtml(p.id)}">Edit profile</button></article>`).join('')}</div>`;$('newQualityProfileBtn').onclick=()=>openQualityProfile();document.querySelectorAll('[data-edit-profile]').forEach(b=>b.onclick=()=>openQualityProfile(b.dataset.editProfile))}
function renderAutomationIndexers(){const idx=state.automation?.indexers||[];$('automationTitle').textContent='Indexers';$('automationSubtitle').textContent='Connect Newznab indexers for interactive and automatic TV/movie release searches.';$('automationAddBtn').classList.add('hidden');$('automationScanBtn').classList.add('hidden');$('automationContent').innerHTML=`<div class="automation-section-head"><div><div class="eyebrow">NEWZNAB</div><h2>${idx.length} indexer${idx.length===1?'':'s'}</h2></div><button class="primary-btn" id="newIndexerBtn">＋ Add indexer</button></div>${idx.length?`<div class="indexer-list">${idx.map(x=>`<div class="indexer-row"><span class="indexer-state ${x.enabled?'on':'off'}"></span><div><strong>${escapeHtml(x.name)}</strong><small>${escapeHtml(x.url)} • TV ${escapeHtml(x.categories_tv||'5000')} • Movies ${escapeHtml(x.categories_movies||'2000')}</small></div><span class="indexer-key">${x.api_key_configured?'API key saved':'No API key'}</span><button class="secondary-btn compact" data-edit-indexer="${escapeHtml(x.id)}">Edit</button></div>`).join('')}</div>`:automationEmpty('⌁','No indexers configured','Add a Newznab-compatible indexer to search for TV and movie releases.')}`;$('newIndexerBtn').onclick=()=>openIndexerModal();document.querySelectorAll('[data-edit-indexer]').forEach(b=>b.onclick=()=>openIndexerModal(b.dataset.editIndexer))}
function rootRows(kind,roots){const label=kind==='tv'?'TV':'Movie';return `<div class="automation-root-list" data-root-kind="${kind}">${roots.length?roots.map((r,i)=>`<div><strong title="${escapeHtml(r)}">${escapeHtml(r)}</strong><button type="button" class="danger-lite" data-remove-root="${kind}" data-root-index="${i}">Remove</button></div>`).join(''):'<p>No root folders configured.</p>'}</div><div class="automation-root-actions"><button type="button" class="secondary-btn" data-add-root="${kind}">＋ Add root folder</button><div class="automation-root-path-row"><input data-root-path="${kind}" placeholder="Or enter a full ${label} folder path…"><button type="button" class="secondary-btn" data-add-root-path="${kind}">Add path</button></div></div><small class="metadata-provider-note">${roots.length} configured root${roots.length===1?'':'s'} • Multiple drives and UNC paths are supported.</small>`}
function renderAutomationSetup(){
  const c=state.automation?.config||{},idx=state.automation?.indexers||[],enabled=idx.filter(x=>x.enabled!==false),a=state.automation?.automatic||{},q=a.quiet_hours||{};
  $('automationTitle').textContent='Automation Setup';
  $('automationSubtitle').textContent='Continuous release monitoring, explainable decisions, high-speed downloads, and safe media import.';
  $('automationAddBtn').classList.add('hidden');$('automationScanBtn').classList.add('hidden');
  $('automationContent').innerHTML=`<div class="automation-setup-grid">
    <article class="automation-setup-card automation-indexer-setup-card"><div class="eyebrow">INDEXERS</div><h2>Release Search</h2><p>Newznab indexers supply both targeted search results and the lightweight RSS/new-release feed used by Continuous Automation.</p><div class="setup-status ${enabled.length?'good':''}">${enabled.length?`✓ ${enabled.length} enabled`:'No indexers configured'}</div><div class="setup-card-actions"><button class="primary-btn" id="setupAddIndexerBtn">＋ Add indexer</button><button class="secondary-btn" id="setupManageIndexersBtn">Manage</button></div></article>
    <article class="automation-setup-card automation-metadata-service-card"><div class="eyebrow">NEWZDECK CLOUD</div><h2>Metadata Service</h2><p>Discover and Automation use NewzDeck's hosted metadata service for TMDB titles, seasons, episodes, artwork, release dates, and availability. Future episodes are discovered automatically during background refreshes.</p><label>Metadata Service URL <small>(advanced)</small><input id="automationMetadataServiceUrl" value="${escapeHtml(c.metadata_service_url||'https://api.newzdeck.com')}" placeholder="https://api.newzdeck.com"></label><div class="setup-status ${c.metadata_service_authenticated?'good':''}" id="automationMetadataServiceStatus">${c.metadata_service_authenticated?'✓ Cloud installation authenticated':'Cloud authentication is established automatically on first metadata request'}</div><small class="metadata-provider-note">Default: https://api.newzdeck.com • No local Metadata Server or TMDB key is required on this PC.</small><div class="setup-card-actions"><button class="primary-btn" id="saveMetadataServiceBtn">Save metadata service</button><button class="secondary-btn" id="testMetadataServiceBtn">Test connection</button></div></article>
    <article class="automation-setup-card"><div class="eyebrow">TV LIBRARY</div><h2>Root folders</h2>${rootRows('tv',c.tv_roots||[])}<small class="metadata-provider-note">Example: D:\Media\TV Shows</small></article>
    <article class="automation-setup-card"><div class="eyebrow">MOVIE LIBRARY</div><h2>Root folders</h2>${rootRows('movie',c.movie_roots||[])}<small class="metadata-provider-note">Example: D:\Media\Movies</small></article>
    <article class="automation-setup-card automation-auto-card"><div class="eyebrow">CONTINUOUS AUTOMATION</div><h2>Always-on Monitoring</h2><p>NewzDeck can watch recent Newznab RSS releases every few minutes, discover newly aired episodes through metadata refreshes, fall back to scheduled Wanted searches, automatically retry misses, and queue acceptable releases without opening the app.</p>
      <div class="setup-status ${c.automatic_grab_enabled?(q.active?'warning':'good'):''}" id="automaticDownloadStatus">${c.automatic_grab_enabled?(q.active?`◷ Quiet hours • resumes ${q.resume_ts?new Date(Number(q.resume_ts)*1000).toLocaleTimeString([],{hour:'numeric',minute:'2-digit'}):c.automatic_quiet_end}`:(a.running?`● ${automationRunDetail(a)}`:'✓ Continuous Automation enabled')):'Continuous Automation is off'}</div>
      <div class="continuous-toggle-list">
        <label class="automation-check continuous-toggle"><input type="checkbox" id="automaticGrabEnabled" ${c.automatic_grab_enabled?'checked':''}><span><b>Enable Continuous Automation</b><small>Monitor and automatically grab qualifying releases for monitored media.</small></span></label>
        <label class="automation-check continuous-toggle"><input type="checkbox" id="automaticFeedEnabled" ${c.automatic_feed_enabled!==false?'checked':''}><span><b>Watch Newznab RSS/new-release feeds</b><small>Fast path for newly posted releases without repeated full searches.</small></span></label>
        <label class="automation-check continuous-toggle"><input type="checkbox" id="automaticSmartRetryEnabled" ${c.automatic_smart_retry_enabled!==false?'checked':''}><span><b>Smart retry timing</b><small>Retry fresh releases quickly, then back off while the release feed keeps watching.</small></span></label>
        <label class="automation-check continuous-toggle"><input type="checkbox" id="automaticBacklogEnabled" ${c.automatic_backlog_enabled?'checked':''}><span><b>Search existing missing backlog</b><small>Automatically search and grab released media that was already missing when Continuous Automation was enabled. When off, those items stay visible in Wanted as BACKLOG PAUSED and can still be searched manually.</small></span></label>
        <label class="automation-check continuous-toggle"><input type="checkbox" id="automaticUpgradesEnabled" ${c.automatic_upgrades_enabled?'checked':''}><span><b>Automatically grab quality upgrades</b><small>Continue upgrading existing media until the configured profile cutoff is met.</small></span></label>
        <label class="automation-check continuous-toggle"><input type="checkbox" id="automaticSeasonPacksEnabled" ${c.automatic_season_packs_enabled!==false?'checked':''}><span><b>Allow season packs as fallback</b><small>Search individual episodes first. Only try a complete pack when the entire fully aired monitored season is still missing and every individual search found no acceptable release.</small></span></label>
        <label class="automation-check continuous-toggle"><input type="checkbox" id="automaticNotificationsEnabled" ${c.automatic_notifications_enabled?'checked':''}><span><b>Windows notifications</b><small>Show notifications for automatic grabs, imports, upgrades, and important failures.</small></span></label>
      </div>
      <div class="automation-template-grid continuous-settings-grid">
        <label>Poll release feed every<select id="automaticFeedInterval">${[2,5,10,15,30,60].map(n=>`<option value="${n}" ${Number(c.automatic_feed_interval_minutes||5)===n?'selected':''}>${n<60?`${n} minutes`:'1 hour'}</option>`).join('')}</select><small>NewzDeck polls each enabled indexer's latest RSS results, then matches them locally against Wanted.</small></label>
        <label>Full Wanted sweep<select id="automaticSearchInterval"><option value="5" ${Number(c.automatic_search_interval_minutes||15)===5?'selected':''}>Every 5 minutes</option><option value="10" ${Number(c.automatic_search_interval_minutes||15)===10?'selected':''}>Every 10 minutes</option><option value="15" ${Number(c.automatic_search_interval_minutes||15)===15?'selected':''}>Every 15 minutes</option><option value="30" ${Number(c.automatic_search_interval_minutes||15)===30?'selected':''}>Every 30 minutes</option><option value="60" ${Number(c.automatic_search_interval_minutes||15)===60?'selected':''}>Every hour</option><option value="180" ${Number(c.automatic_search_interval_minutes||15)===180?'selected':''}>Every 3 hours</option></select><small>Targeted TV/movie searches catch backlog or releases the RSS feed did not expose.</small></label>
        <label>Base retry when nothing matches<select id="automaticRetryMinutes"><option value="15" ${Number(c.automatic_retry_minutes||60)===15?'selected':''}>15 minutes</option><option value="30" ${Number(c.automatic_retry_minutes||60)===30?'selected':''}>30 minutes</option><option value="60" ${Number(c.automatic_retry_minutes||60)===60?'selected':''}>1 hour</option><option value="120" ${Number(c.automatic_retry_minutes||60)===120?'selected':''}>2 hours</option><option value="360" ${Number(c.automatic_retry_minutes||60)===360?'selected':''}>6 hours</option></select><small>Smart Retry may temporarily use a shorter interval right after an episode/movie becomes available.</small></label>
        <label>New release delay<select id="automaticReleaseDelay"><option value="0" ${Number(c.automatic_release_delay_minutes||0)===0?'selected':''}>No delay</option><option value="5" ${Number(c.automatic_release_delay_minutes||5)===5?'selected':''}>5 minutes</option><option value="10" ${Number(c.automatic_release_delay_minutes||5)===10?'selected':''}>10 minutes</option><option value="15" ${Number(c.automatic_release_delay_minutes||5)===15?'selected':''}>15 minutes</option><option value="30" ${Number(c.automatic_release_delay_minutes||5)===30?'selected':''}>30 minutes</option></select></label>
        <label>Automation queue depth<select id="automaticQueueDepth">${[5,10,25,50,100].map(n=>`<option value="${n}" ${Number(c.automatic_queue_depth||25)===n?'selected':''}>${n} items</option>`).join('')}</select><small>Controls how far Continuous Automation can fill the queue. The proven v3.3.1 high-throughput downloader remains protected and unchanged.</small></label>
        <label>Refresh episode/release metadata<select id="automaticMetadataHours"><option value="1" ${Number(c.automatic_metadata_refresh_hours||6)===1?'selected':''}>Every hour</option><option value="3" ${Number(c.automatic_metadata_refresh_hours||6)===3?'selected':''}>Every 3 hours</option><option value="6" ${Number(c.automatic_metadata_refresh_hours||6)===6?'selected':''}>Every 6 hours</option><option value="12" ${Number(c.automatic_metadata_refresh_hours||6)===12?'selected':''}>Every 12 hours</option><option value="24" ${Number(c.automatic_metadata_refresh_hours||6)===24?'selected':''}>Daily</option></select></label>
        <label>Reconcile library files<select id="automaticLibraryScanMinutes">${[5,15,30,60,180,360].map(n=>`<option value="${n}" ${Number(c.automatic_library_scan_minutes||30)===n?'selected':''}>${n<60?`Every ${n} minutes`:n===60?'Every hour':`Every ${n/60} hours`}</option>`).join('')}</select><small>Detects files moved, added, replaced, or deleted outside NewzDeck.</small></label>
        <label>Storage safety reserve<select id="automaticStorageReserveGb">${[2,5,10,20,50].map(n=>`<option value="${n}" ${Number(c.automatic_storage_reserve_gb||5)===n?'selected':''}>${n} GB free reserve</option>`).join('')}</select></label>
        <label>Movie search availability<select id="automaticMovieAvailability"><option value="digital_physical" ${String(c.automatic_movie_availability||'digital_physical')==='digital_physical'?'selected':''}>Digital / physical release (recommended)</option><option value="theatrical" ${String(c.automatic_movie_availability||'digital_physical')==='theatrical'?'selected':''}>Theatrical release date</option></select></label>
      </div>
      <div class="quiet-hours-box"><label class="automation-check quiet-hours-toggle"><input type="checkbox" id="automaticQuietHoursEnabled" ${c.automatic_quiet_hours_enabled?'checked':''}><span><b>Quiet hours</b><small>Keep monitoring, but defer new automatic grabs during this window.</small></span></label><div class="quiet-hours-times"><label>Start<input id="automaticQuietStart" type="time" value="${escapeHtml(c.automatic_quiet_start||'01:00')}"></label><span>to</span><label>End<input id="automaticQuietEnd" type="time" value="${escapeHtml(c.automatic_quiet_end||'07:00')}"></label></div><small>Existing downloads continue. Your global bandwidth schedule can separately cap transfer speed during selected hours.</small><button class="secondary-btn compact" id="openBandwidthScheduleBtn" type="button">Open bandwidth schedule</button></div>
      <div class="continuous-runtime-strip"><div><span>Feed</span><b>${c.automatic_feed_enabled?`${Number(a.last_feed_count||0)} recent`:'Off'}</b></div><div><span>Feed matches</span><b>${Number(a.last_feed_matches||0)}</b></div><div><span>Active targets</span><b>${Number(a.active_targets||0)}</b></div><div><span>Next cycle</span><b>${autoTimeUntil(a.next_cycle_ts)}</b></div></div>
      <small class="metadata-provider-note">${a.last_cycle_ts?`Last cycle: ${new Date(Number(a.last_cycle_ts)*1000).toLocaleString()} • ${escapeHtml(a.last_result||'Completed')}`:'No automatic cycle has run yet.'}${a.last_error?`<br><span class="error-text">Last issue: ${escapeHtml(a.last_error)}</span>`:''}${(a.last_feed_errors||[]).length?`<br><span class="error-text">Feed issue: ${escapeHtml((a.last_feed_errors||[])[0])}</span>`:''}</small>
      <div class="setup-card-actions"><button class="primary-btn" id="saveAutomaticDownloadsBtn">Save Continuous Automation</button><button class="secondary-btn" id="runAutomationNowBtn" ${c.automatic_grab_enabled?'':'disabled'}>Run Now</button><button class="secondary-btn" id="refreshAutomationMetadataBtn">Refresh metadata</button></div>
    </article>
    <article class="automation-setup-card automation-plex-card"><div class="eyebrow">COMPLETED DOWNLOADS</div><h2>Smart Import & Library Organization</h2><p>Completed Automation grabs and one-time Discover media grabs are inspected, identified, quality-compared, transactionally imported, and renamed into clean TV/movie folders after verification, repair, and extraction.</p>
      <label class="automation-check"><input type="checkbox" id="plexOrganizeEnabled" ${c.plex_organize_enabled!==false?'checked':''}> Automatically organize completed media grabs</label>
      <label class="automation-check"><input type="checkbox" id="plexReplaceUpgrades" ${c.plex_replace_upgrades!==false?'checked':''}> Replace an existing library file after a verified upgrade</label>
      <label class="automation-check"><input type="checkbox" id="plexCleanupStaging" ${c.plex_cleanup_staging!==false?'checked':''}> Clean empty staging folders after import</label>
      <label class="automation-check"><input type="checkbox" id="plexIncludeQuality" ${c.plex_include_quality?'checked':''}> Include quality in library filename</label>
      <div class="automation-template-grid"><label>TV show folder<input id="plexTvFolderTemplate" value="${escapeHtml(c.tv_folder_template||'{library_title}')}"></label><label>TV season folder<input id="plexTvSeasonTemplate" value="${escapeHtml(c.tv_season_template||'Season {season}')}"></label><label>TV episode filename<input id="plexTvFileTemplate" value="${escapeHtml(c.tv_file_template||'{library_title} - {episode_token} - {episode_title}')}"></label><label>Movie folder<input id="plexMovieFolderTemplate" value="${escapeHtml(c.movie_folder_template||'{title} ({year})')}"></label><label>Movie filename<input id="plexMovieFileTemplate" value="${escapeHtml(c.movie_file_template||'{title} ({year})')}"></label></div>
      <small class="metadata-provider-note">Available fields: {title}, {year}, {quality}; TV also supports {library_title}, {season}, {episode}, {episode_token}, {episode_title}. {library_title} is the safe series identity NewzDeck uses for country/version collisions. File extensions are preserved automatically.</small>
      <div class="setup-card-actions"><button class="primary-btn" id="savePlexOrganizationBtn">Save import settings</button></div>
    </article>
  </div>`;
  $('setupAddIndexerBtn').onclick=()=>openIndexerModal();$('setupManageIndexersBtn').onclick=openAutomationIndexers;
  $('saveMetadataServiceBtn').onclick=saveMetadataService;$('testMetadataServiceBtn').onclick=testMetadataService;
  $('saveAutomaticDownloadsBtn').onclick=saveAutomaticDownloads;$('runAutomationNowBtn').onclick=runAutomationNow;$('refreshAutomationMetadataBtn').onclick=refreshAutomationMetadata;
  $('automaticGrabEnabled').onchange=()=>{$('runAutomationNowBtn').disabled=!$('automaticGrabEnabled').checked};
  $('openBandwidthScheduleBtn').onclick=()=>openSettingsModal('automation');
  $('savePlexOrganizationBtn').onclick=savePlexOrganization;
  document.querySelectorAll('[data-add-root]').forEach(b=>b.onclick=()=>addAutomationRoot(b.dataset.addRoot));
  document.querySelectorAll('[data-add-root-path]').forEach(b=>b.onclick=()=>addAutomationRootPath(b.dataset.addRootPath));
  document.querySelectorAll('[data-root-path]').forEach(i=>i.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();addAutomationRootPath(i.dataset.rootPath)}});
  document.querySelectorAll('[data-remove-root]').forEach(b=>b.onclick=()=>removeAutomationRoot(b.dataset.removeRoot,Number(b.dataset.rootIndex)));
}
async function saveMetadataService(){const url=String($('automationMetadataServiceUrl')?.value||'').trim();try{await api('/api/automation/config/save',{metadata_service_url:url});await loadAutomation({quiet:true});renderAutomation();toast('Metadata Service URL saved.','success')}catch(e){toast(e.message,'error')}}
async function testMetadataService(){const b=$('testMetadataServiceBtn'),box=$('automationMetadataServiceStatus'),old=b?.textContent||'';if(b){b.disabled=true;b.textContent='Testing…'}try{const url=String($('automationMetadataServiceUrl')?.value||'').trim();if(url&&url!==String(state.automation?.config?.metadata_service_url||''))await api('/api/automation/config/save',{metadata_service_url:url});const r=await metadataApi('/api/automation/metadata/service-test',{}),upstream=String(r.tmdb_status||'unknown').toLowerCase(),tmdbHealthy=r.tmdb_configured&&!['degraded','offline'].includes(upstream);if(box){box.className=`setup-status ${tmdbHealthy?'good':''}`;box.textContent=`${tmdbHealthy?'✓':'!'} Connected • ${r.version||'service'} • ${Math.round(Number(r.latency_ms||0))} ms${r.auth_mode==='installation'&&r.authenticated?' • Installation authenticated':''}${r.tmdb_configured?` • TMDB ${upstream==='unknown'?'ready':upstream}`:' • TMDB token missing'}`}if(!tmdbHealthy&&r.tmdb_last_error)toast(`Cloud is reachable, but TMDB is degraded: ${r.tmdb_last_error}`,'error');else toast(tmdbHealthy?(r.auth_mode==='installation'?'NewzDeck Cloud authentication and TMDB are ready.':'Metadata Service and TMDB are ready.'):'Metadata Service connected, but TMDB is not ready.',tmdbHealthy?'success':'error')}catch(e){if(box){box.className='setup-status';box.textContent='Connection failed'}toast(e.message,'error')}finally{if(b?.isConnected){b.disabled=false;b.textContent=old}}}
async function saveAutomaticDownloads(){
  const data={automatic_grab_enabled:$('automaticGrabEnabled').checked,automatic_feed_enabled:$('automaticFeedEnabled').checked,automatic_feed_interval_minutes:Number($('automaticFeedInterval').value||5),automatic_smart_retry_enabled:$('automaticSmartRetryEnabled').checked,automatic_backlog_enabled:$('automaticBacklogEnabled').checked,automatic_upgrades_enabled:$('automaticUpgradesEnabled').checked,automatic_season_packs_enabled:$('automaticSeasonPacksEnabled').checked,automatic_notifications_enabled:$('automaticNotificationsEnabled').checked,automatic_quiet_hours_enabled:$('automaticQuietHoursEnabled').checked,automatic_quiet_start:$('automaticQuietStart').value||'01:00',automatic_quiet_end:$('automaticQuietEnd').value||'07:00',automatic_search_interval_minutes:Number($('automaticSearchInterval').value||15),automatic_retry_minutes:Number($('automaticRetryMinutes').value||60),automatic_release_delay_minutes:Number($('automaticReleaseDelay').value||0),automatic_queue_depth:Number($('automaticQueueDepth').value||25),automatic_metadata_refresh_hours:Number($('automaticMetadataHours').value||6),automatic_library_scan_minutes:Number($('automaticLibraryScanMinutes').value||30),automatic_storage_reserve_gb:Number($('automaticStorageReserveGb').value||5),automatic_movie_availability:$('automaticMovieAvailability').value||'digital_physical'};
  try{await api('/api/automation/config/save',data);await loadAutomation();renderAutomation();toast(data.automatic_grab_enabled?'Continuous Automation enabled. NewzDeck will monitor releases in the background.':'Continuous Automation settings saved.','success')}catch(e){toast(e.message,'error')}
}
async function runAutomationNow(){const b=$('runAutomationNowBtn'),old=b?.textContent||'';if(b){b.disabled=true;b.textContent='Starting…'}try{const r=await api('/api/automation/run-now',{});toast(r.running?'Automation is already running.':'Automation check started in the background.','success');setTimeout(async()=>{await loadAutomation({quiet:true});if(state.automationTab==='setup')renderAutomation()},1800)}catch(e){toast(e.message,'error')}finally{if(b?.isConnected){b.disabled=false;b.textContent=old}}}
async function refreshAutomationMetadata(){const b=$('refreshAutomationMetadataBtn'),old=b?.textContent||'';if(b){b.disabled=true;b.textContent='Refreshing…'}try{const r=await metadataApi('/api/automation/metadata/refresh',{});await loadAutomation({quiet:true});if(state.automationTab==='setup')renderAutomation();toast(`Metadata refreshed for ${Number(r.updated||0)} title${Number(r.updated||0)===1?'':'s'}${Number(r.new_episodes||0)?` • ${Number(r.new_episodes)} new episode${Number(r.new_episodes)===1?'':'s'}`:''}${Number(r.migrated_to_tmdb||0)?` • ${Number(r.migrated_to_tmdb)} migrated to TMDB`:''}.`,'success')}catch(e){toast(e.message,'error')}finally{if(b?.isConnected){b.disabled=false;b.textContent=old}}}
async function savePlexOrganization(){
  const data={plex_organize_enabled:$('plexOrganizeEnabled').checked,plex_replace_upgrades:$('plexReplaceUpgrades').checked,plex_cleanup_staging:$('plexCleanupStaging').checked,plex_include_quality:$('plexIncludeQuality').checked,tv_folder_template:$('plexTvFolderTemplate').value.trim(),tv_season_template:$('plexTvSeasonTemplate').value.trim(),tv_file_template:$('plexTvFileTemplate').value.trim(),movie_folder_template:$('plexMovieFolderTemplate').value.trim(),movie_file_template:$('plexMovieFileTemplate').value.trim()};
  try{await api('/api/automation/config/save',data);await loadAutomation();renderAutomation();toast('Smart Import settings saved.','success')}catch(e){toast(e.message,'error')}
}
function renderAutomation({animate=true}={}){if(!state.automation){const msg=state.automationLoadError||'Reading automation library.';$('automationContent').innerHTML=state.automationLoadError?automationEmpty('!','Automation setup could not be loaded',msg,'<button class="primary-btn" id="retryAutomationBtn">Retry</button>'):automationEmpty('◌','Loading…',msg);$('retryAutomationBtn')?.addEventListener('click',()=>loadAutomation({quiet:false}));return}renderAutomationBadges();document.querySelectorAll('#automationTabs [data-auto-tab]').forEach(b=>b.classList.toggle('active',b.dataset.autoTab===state.automationTab));document.querySelectorAll('.sidebar [data-auto-tab]').forEach(b=>b.classList.toggle('active',state.activeView==='automation'&&b.dataset.autoTab===state.automationTab));if(state.automationTab==='tv')renderAutomationLibrary('tv');else if(state.automationTab==='movies')renderAutomationLibrary('movie');else if(state.automationTab==='wanted')renderAutomationWanted();else if(state.automationTab==='calendar')renderAutomationCalendar();else if(state.automationTab==='history')renderAutomationHistory();else if(state.automationTab==='health')renderAutomationHealth();else if(state.automationTab==='profiles')renderAutomationProfiles();else if(state.automationTab==='indexers')renderAutomationIndexers();else renderAutomationSetup();if(animate)animateDynamicSurface($('automationContent'))}
function automationRootsForKind(kind){return kind==='movie'?(state.automation?.config?.movie_roots||[]):state.automation?.config?.tv_roots||[]}
function automationMonitoringChoices(kind){return kind==='movie'?[{value:'movie',label:'Missing + quality upgrades',detail:'Keep the movie monitored until it is present, then continue upgrades until the selected quality cutoff is met.'},{value:'missing',label:'Missing movie only',detail:'Monitor until a movie file is present. Do not keep it wanted for later quality upgrades.'},{value:'none',label:'Unmonitored',detail:'Add the movie to the library without automatic searching or downloads.'}]:[{value:'all',label:'All episodes',detail:'Monitor released backlog and future episodes, including quality upgrades. Continuous Automation searches older backlog only when Search existing missing backlog is enabled.'},{value:'future',label:'Future episodes',detail:'Monitor episodes airing today or later. Existing backlog is left alone.'},{value:'missing',label:'Missing episodes',detail:'Monitor released episodes that do not have a file, without seeking quality upgrades once found. Older backlog is automatically searched only when Search existing missing backlog is enabled.'},{value:'none',label:'Unmonitored',detail:'Add the series to the library without automatic episode searching or downloads.'}]}
function automationMonitoringMode(itemOrKind,mode=''){const kind=typeof itemOrKind==='string'?itemOrKind:(itemOrKind?.kind||'tv');const item=typeof itemOrKind==='object'?itemOrKind:null;if(item?.monitored===false)return 'none';const allowed=new Set(automationMonitoringChoices(kind).map(x=>x.value));const candidate=String(mode||item?.monitor_mode||'');return allowed.has(candidate)?candidate:(kind==='movie'?'movie':'all')}
function automationMonitoringLabel(item){const mode=automationMonitoringMode(item);return automationMonitoringChoices(item?.kind||'tv').find(x=>x.value===mode)?.label||'Monitored'}
function automationMonitoringOptions(kind,selected=''){const mode=automationMonitoringMode(kind,selected);return automationMonitoringChoices(kind).map(x=>`<option value="${x.value}" ${x.value===mode?'selected':''}>${escapeHtml(x.label)}</option>`).join('')}
function automationMonitoringHelp(kind,mode){return automationMonitoringChoices(kind).find(x=>x.value===mode)?.detail||''}
function refreshAutomationAddMonitoringOptions(){const kind=$('automationAddKind')?.value||'tv',select=$('automationAddMonitor');if(!select)return;const previous=select.value;select.innerHTML=automationMonitoringOptions(kind,previous);const help=$('automationAddMonitorHelp');if(help)help.textContent=automationMonitoringHelp(kind,select.value)}
function refreshAutomationAddProfileOptions(){const select=$('automationAddProfile');if(!select)return;const previous=select.value;const profiles=state.automation?.profiles||[];select.innerHTML=profiles.map(p=>`<option value="${escapeHtml(p.id)}" ${p.id===previous?'selected':''}>${escapeHtml(p.name)}</option>`).join('')}
function refreshAutomationAddRootOptions(){const kind=$('automationAddKind').value,roots=automationRootsForKind(kind),select=$('automationAddRoot');if(!select)return;select.innerHTML=`<option value="">${roots.length?'Automatic • first configured root':'No root configured • set up later'}</option>`+roots.map(r=>`<option value="${escapeHtml(r)}">${escapeHtml(r)}</option>`).join('');select.title=roots.length?'Choose which configured drive/folder should own this title.':'Add root folders in Automation Setup.'}
function openAutomationAdd(){const m=$('automationAddModal');$('automationAddKind').value=state.automationTab==='movies'?'movie':'tv';refreshAutomationAddRootOptions();refreshAutomationAddProfileOptions();refreshAutomationAddMonitoringOptions();$('automationMetadataQuery').value='';$('automationManualTitle').value='';$('automationManualYear').value='';$('automationMetadataResults').innerHTML='<div class="metadata-hint">Search TMDB, choose how NewzDeck should monitor the title, then add it to your library.</div>';m.classList.remove('hidden');$('automationMetadataQuery').focus()}
function closeAutomationAdd(){$('automationAddModal').classList.add('hidden')}
async function searchAutomationMetadata(){const q=$('automationMetadataQuery').value.trim();if(!q)return;const b=$('automationMetadataSearchBtn'),old=b.textContent;b.disabled=true;b.textContent='Searching…';$('automationMetadataResults').innerHTML='<div class="metadata-hint">Searching metadata…</div>';try{const d=await metadataApi('/api/automation/metadata/search',{kind:$('automationAddKind').value,query:q});const rows=d.results||[];$('automationMetadataResults').innerHTML=rows.length?rows.map((r,i)=>`<article class="metadata-result"><div class="metadata-thumb">${r.poster_url?`<img src="${escapeHtml(r.poster_url)}" alt="">`:'◌'}</div><div><strong>${escapeHtml(r.title)}</strong><span>${r.year||'Year unknown'} • ${r.provider==='tmdb'?'TMDB':r.provider==='tvmaze'?'TVmaze':r.provider==='wikidata'?'Wikidata':'Metadata'}</span><p>${escapeHtml((r.overview||'').slice(0,220))}</p></div><button class="primary-btn" data-add-metadata="${i}">Add</button></article>`).join(''):automationEmpty('⌕','No matches','Try a different title.');document.querySelectorAll('[data-add-metadata]').forEach(btn=>btn.onclick=()=>addAutomationMedia(rows[Number(btn.dataset.addMetadata)]))}catch(e){$('automationMetadataResults').innerHTML=`<div class="metadata-error">${escapeHtml(e.message)}</div>`}finally{b.disabled=false;b.textContent=old}}
async function addAutomationMedia(meta={}){const kind=meta.kind||$('automationAddKind').value,mode=$('automationAddMonitor')?.value||automationMonitoringMode(kind),payload={...meta,kind,monitored:mode!=='none',monitor_mode:mode,quality_profile_id:$('automationAddProfile')?.value||'',root_folder:$('automationAddRoot')?.value||''};if(!meta.title){payload.title=$('automationManualTitle').value.trim();payload.year=$('automationManualYear').value;if(!payload.title){toast('Enter a title first.','error');return}}try{await api('/api/automation/media/add',payload);closeAutomationAdd();await loadAutomation();state.automationTab=payload.kind==='movie'?'movies':'tv';renderAutomation();toast(`${payload.title||meta.title} added • ${automationMonitoringChoices(kind).find(x=>x.value===mode)?.label||'Monitoring configured'}.`,'success')}catch(e){toast(e.message,'error')}}
async function openAutomationItem(id){const item=autoItem(id);if(!item)return;$('automationItemTitle').textContent=item.title;$('automationItemEyebrow').textContent=item.kind==='tv'?'TV SERIES':'MOVIE';$('automationItemMeta').textContent=`${item.year||''}${item.status?` • ${item.status}`:''}`;const profiles=state.automation?.profiles||[];const roots=item.kind==='tv'?(state.automation?.config?.tv_roots||[]):state.automation?.config?.movie_roots||[];let body=`<div class="automation-item-hero">${item.poster_url?`<img src="${escapeHtml(item.poster_url)}" alt="">`:'<div class="automation-poster-placeholder large">MEDIA</div>'}<div><p>${escapeHtml(item.overview||'No description available.')}</p><div class="automation-item-facts">${[item.rating?`★ ${Number(item.rating).toFixed(1)}`:'',(item.genres||[]).slice(0,3).join(' • '),item.network||'',item.runtime?`${item.runtime} min`:''].filter(Boolean).map(x=>`<span>${escapeHtml(x)}</span>`).join('')}</div><div class="automation-item-settings ${item.kind==='tv'?'tv-settings':'movie-settings'}"><label class="auto-item-monitor-field">Monitoring type<select id="autoItemMonitorMode">${automationMonitoringOptions(item.kind,automationMonitoringMode(item))}</select><small>${escapeHtml(automationMonitoringHelp(item.kind,automationMonitoringMode(item)))}</small></label><label class="auto-item-profile-field">Quality profile<select id="autoItemProfile">${profiles.map(p=>`<option value="${escapeHtml(p.id)}" ${p.id===item.quality_profile_id?'selected':''}>${escapeHtml(p.name)}</option>`).join('')}</select></label><label class="auto-item-root-field">Root folder<select id="autoItemRoot"><option value="">Automatic root (first configured)</option>${roots.map(r=>`<option value="${escapeHtml(r)}" ${r===item.root_folder?'selected':''}>${escapeHtml(r)}</option>`).join('')}</select></label>${item.kind==='tv'?`<label class="auto-item-library-field">Library name<input id="autoItemLibraryTitle" value="${escapeHtml(String(item.library_title_source||'').toLowerCase()==='manual'?(item.library_title||''):'')}" placeholder="Automatic series name"><small>Automatic uses the show title only (for example Silo). Same-title country editions are disambiguated when needed (for example Big Brother (US)). Enter a value only to override automatic naming.</small></label>`:''}</div><div class="automation-item-actions"><button class="secondary-btn" id="autoItemSave">Save</button><button class="secondary-btn" id="autoItemScan">Scan files</button><button class="secondary-btn" id="autoItemRefresh">Refresh metadata</button><button class="secondary-btn" id="autoItemOpenFolder">Open folder</button>${item.kind==='movie'?'<button class="primary-btn" id="autoItemSearch">Search releases</button>':''}<button class="danger-btn" id="autoItemDelete">Remove</button></div></div></div>`;
 if(item.library_root_status==='offline')body+=`<div class="media-file-status root-offline"><strong>Root Folder is offline</strong><span>NewzDeck is preserving the last-known library state and will not mark files missing or auto-grab replacements until this root is reachable again.</span><small>${escapeHtml(item.root_folder||'Automatic root')}</small></div>`;
 if(item.kind==='movie'){const f=item.movie_file,home=item.availability_date||item.digital_release_date||item.physical_release_date;body+=`<div class="media-file-status ${f?'present':'missing'}"><strong>${f?'File found':'No matching movie file found'}</strong><span>${f?`${escapeHtml(f.quality||'Unknown')} • ${formatBytes(f.size||0)}${f.media_info?` • ${escapeHtml([f.media_info.video_codec,f.media_info.hdr,f.media_info.audio_codec].filter(x=>x&&x!=='Unknown').join(' • '))}`:''}${f.cutoff_met?' • Cutoff met':' • Upgrade wanted'}`:`${home?'Home release':'Theatrical release'}: ${autoFmtDate(home||item.release_date)}`}</span>${f?`<small>${escapeHtml(f.path||'')}</small>`:''}</div>`}
 else{body+=`<div class="season-list">${(item.seasons||[]).map(s=>`<details class="season-card"><summary><span><strong>Season ${s.season_number}</strong><small>${(s.episodes||[]).filter(e=>e.has_file).length}/${(s.episodes||[]).length} episodes available</small></span><span class="season-summary-actions"><label title="Monitor every episode in this season"><input type="checkbox" data-season-monitor="${s.season_number}" ${s.monitored!==false?'checked':''}> Monitor</label><em>${(s.episodes||[]).filter(e=>e.monitored!==false&&!e.has_file&&e.air_date&&e.air_date<=new Date().toISOString().slice(0,10)).length} missing</em></span></summary><div class="season-tools"><button class="secondary-btn compact" data-season-pack-search="${escapeHtml(item.id)}" data-season="${s.season_number}">Search Season ${s.season_number} pack</button><small>Season-pack search uses the same release scoring and imports each identified episode independently.</small></div><div class="episode-list">${(s.episodes||[]).map(ep=>`<div class="episode-row ${ep.has_file?'present':'missing'}"><label><input type="checkbox" data-episode-monitor="${s.season_number}:${ep.episode_number}" ${ep.monitored!==false?'checked':''}></label><div><strong>S${String(s.season_number).padStart(2,'0')}E${String(ep.episode_number).padStart(2,'0')} · ${escapeHtml(ep.name||'Episode')}</strong><small>${autoFmtDate(ep.air_date)}${ep.has_file?` • ${escapeHtml(ep.file_quality||'File found')}${ep.media_info?` • ${escapeHtml([ep.media_info.video_codec,ep.media_info.hdr,ep.media_info.audio_codec].filter(x=>x&&x!=='Unknown').join(' • '))}`:''}${ep.cutoff_met?' • cutoff met':' • upgrade wanted'}`:' • no file'}</small></div><button class="secondary-btn compact" data-release-search="${escapeHtml(item.id)}" data-season="${s.season_number}" data-episode="${ep.episode_number}">Search</button></div>`).join('')}</div></details>`).join('')||automationEmpty('▣','No episode metadata','Refresh metadata to retrieve seasons and episodes from the NewzDeck Metadata Service.')}</div>`}
 const allItemEvents=(state.automation?.history||[]).filter(r=>String(r?.details?.item_id||'')===String(item.id)),itemEvents=allItemEvents.slice(0,8),lastInspection=allItemEvents.find(r=>r.kind==='import-inspection'&&Array.isArray(r?.details?.inspections));const itemBlacklists=(state.automation?.health?.blacklists||[]).filter(r=>String(r.target_key||'').includes(String(item.id))).slice(0,8);if(itemEvents.length||itemBlacklists.length){body+=`<section class="automation-intelligence-panel"><div class="automation-section-head"><div><div class="eyebrow">RELEASE INTELLIGENCE</div><h3>Recent decisions</h3></div></div>${lastInspection?`<details class="import-inspector" open><summary><span><b>Import Inspector</b><small>${Number(lastInspection.details.imported||0)} imported • ${Number(lastInspection.details.ignored||0)} ignored • ${Number(lastInspection.details.needs_attention||0)} need attention</small></span><em>${lastInspection.details.season_pack?'SEASON PACK':'LAST IMPORT'}</em></summary><div class="import-inspector-table">${(lastInspection.details.inspections||[]).slice(0,20).map(x=>`<div class="import-inspector-row action-${String(x.action||'').toLowerCase().replace(/_/g,'-')}"><span><strong>${escapeHtml((x.source||'').split(/[\/]/).pop()||'Media file')}</strong><small>${escapeHtml(x.identified||'Unknown media')}</small></span><span>${escapeHtml(x.quality||'—')}</span><span><b>${escapeHtml(x.action||'REVIEW')}</b><small>${escapeHtml(x.reason||'')}</small></span><span title="${escapeHtml(x.destination||'')}">${escapeHtml(x.destination||'—')}</span></div>`).join('')}</div></details>`:''}${itemBlacklists.length?`<div class="item-blacklist-list">${itemBlacklists.map(x=>`<div><b>BLACKLISTED</b><span>${escapeHtml(x.title||'Release')}</span><small>${escapeHtml(x.reason||'Failed/rejected release')}</small></div>`).join('')}</div>`:''}${itemEvents.length?`<div class="item-event-list">${itemEvents.map(r=>`<div><b>${escapeHtml(automationHistoryLabel(r))}</b><span>${escapeHtml(r.message||'Automation event')}</span></div>`).join('')}</div>`:''}</section>`;}
 $('automationItemBody').innerHTML=body;$('automationItemModal').classList.remove('hidden');$('autoItemSave').onclick=()=>saveAutomationItem(item);$('autoItemScan').onclick=()=>scanAutomationLibrary(item.id);$('autoItemRefresh').onclick=()=>refreshAutomationItem(item.id);$('autoItemOpenFolder').onclick=()=>openAutomationFolder(item.id);$('autoItemDelete').onclick=()=>deleteAutomationItem(item);$('autoItemSearch')?.addEventListener('click',()=>openReleaseSearch(item.id));document.querySelectorAll('[data-season-monitor]').forEach(c=>c.onchange=async e=>{e.stopPropagation();try{await api('/api/automation/media/update',{id:item.id,season_number:Number(c.dataset.seasonMonitor),season_monitored:c.checked});void loadAutomation({quiet:true,background:true})}catch(err){toast(err.message,'error')}});document.querySelectorAll('[data-episode-monitor]').forEach(c=>c.onchange=async()=>{const [season,episode]=c.dataset.episodeMonitor.split(':');try{await api('/api/automation/media/update',{id:item.id,season_number:Number(season),episode_number:Number(episode),episode_monitored:c.checked});void loadAutomation({quiet:true,background:true})}catch(e){toast(e.message,'error')}});wireReleaseSearchButtons()}
async function refreshAutomationItem(id){try{toast('Refreshing metadata…');await api('/api/automation/media/refresh',{id});await loadAutomation({quiet:true});await openAutomationItem(id);toast('Metadata refreshed.','success')}catch(e){toast(e.message,'error')}}
async function openAutomationFolder(id){try{await api('/api/automation/media/open-folder',{id})}catch(e){toast(e.message,'error')}}
async function saveAutomationItem(item){
  const mode=$('autoItemMonitorMode')?.value||automationMonitoringMode(item);
  const b=$('autoItemSave'),old=b?.textContent||'Save';
  if(b){b.disabled=true;b.textContent='Saving…'}
  try{
    const payload={id:item.id,monitored:mode!=='none',monitor_mode:mode,quality_profile_id:$('autoItemProfile').value,root_folder:$('autoItemRoot').value};
    if(item.kind==='tv'){
      const entered=$('autoItemLibraryTitle')?.value.trim()||'',prior=String(item.library_title||'').trim();
      if(entered!==prior)payload.library_title=entered;
    }
    const result=await api('/api/automation/media/update',payload);
    const saved=result?.item;
    if(saved&&state.automation?.library){
      const index=state.automation.library.findIndex(x=>String(x?.id||'')===String(saved.id||''));
      if(index>=0)state.automation.library[index]=saved;
      if(String(item?.id||'')===String(saved.id||''))Object.assign(item,saved);
    }
    toast(`Monitoring & library naming saved • ${automationMonitoringChoices(item.kind).find(x=>x.value===mode)?.label||'Updated'}.`,'success');
    // The persisted media update is authoritative. Full Automation summary
    // recalculation (Wanted, Calendar, health, counts) can be relatively expensive
    // after changing All/Future monitoring because many episode targets change at
    // once. Refresh it asynchronously so the Save acknowledgement is immediate.
    void loadAutomation({quiet:true,background:true});
  }catch(e){
    toast(e.message,'error');
  }finally{
    if(b){b.disabled=false;b.textContent=old}
  }
}
async function deleteAutomationItem(item){if(!confirm(`Remove ${item.title} from NewzDeck monitoring? Your media files will not be deleted.`))return;try{await api('/api/automation/media/delete',{id:item.id});$('automationItemModal').classList.add('hidden');await loadAutomation();toast('Removed from monitoring.')}catch(e){toast(e.message,'error')}}
async function scanAutomationLibrary(id=''){const b=$('automationScanBtn');if(b){b.disabled=true;b.textContent='Scanning…'}try{const d=await api('/api/automation/library/scan',{id});await loadAutomation();if(id)await openAutomationItem(id);const offline=(d.offline_roots||[]).length,changes=(d.changes||[]).length;toast(`Scan complete: ${d.matched} media file${d.matched===1?'':'s'} matched${changes?` • ${changes} change${changes===1?'':'s'}`:''}${offline?` • ${offline} root${offline===1?'':'s'} offline`:''}.`,offline?'warning':'success')}catch(e){toast(e.message,'error')}finally{if(b){b.disabled=false;b.textContent='↻ Scan library'}}}
function wireReleaseSearchButtons(){document.querySelectorAll('[data-release-search]').forEach(b=>b.onclick=()=>openReleaseSearch(b.dataset.releaseSearch,b.dataset.season===''?null:Number(b.dataset.season),b.dataset.episode===''?null:Number(b.dataset.episode)));document.querySelectorAll('[data-season-pack-search]').forEach(b=>b.onclick=e=>{e.preventDefault();e.stopPropagation();openReleaseSearch(b.dataset.seasonPackSearch,Number(b.dataset.season),null)})}
async function openReleaseSearch(itemId,season=null,episode=null){
  const item=autoItem(itemId);if(!item)return;
  const seasonPack=item.kind==='tv'&&season!=null&&episode==null;
  state.releaseSearchContext={itemId,season,episode,seasonPack};
  $('releaseSearchTitle').textContent=seasonPack?`${item.title} · Season ${Number(season)} Pack`:season!=null?`${item.title} · S${String(season).padStart(2,'0')}E${String(episode).padStart(2,'0')}`:item.title;
  $('releaseSearchSubtitle').textContent=`Searching enabled Newznab indexers • profile: ${autoProfile(item.quality_profile_id)?.name||'Default'} • ${seasonPack?'season-pack candidates will be mapped to individual episodes during import':'every candidate is explained by the same decision engine used by Automation'}`;
  $('releaseSearchBody').innerHTML='<div class="release-loading">Searching indexers and evaluating title, target, quality, size, preferences, blacklist, and import safety…</div>';
  $('releaseSearchModal').classList.remove('hidden');
  try{
    const searchRequest=()=>api('/api/automation/releases/search',{item_id:itemId,season,episode},{timeoutMs:30000,timeoutMessage:'Indexer search did not return within 30 seconds. NewzDeck stopped waiting; check the per-indexer errors in Automation → Health.'});let d;try{d=await searchRequest()}catch(firstError){if(!/failed to fetch|networkerror|load failed/i.test(String(firstError?.message||'')))throw firstError;await new Promise(r=>setTimeout(r,750));d=await searchRequest()}const rows=d.releases||[];
    const summary=rows.length?`<div class="release-decision-summary"><div><span>SEARCHED INDEXERS</span><strong>${Number(d.searched_indexers||0)}</strong></div><div><span>CANDIDATES</span><strong>${rows.length}</strong></div><div><span>ELIGIBLE</span><strong>${rows.filter(x=>x.automatic_eligible).length}</strong></div><div><span>BLACKLISTED</span><strong>${Number(d.blacklist_count||0)}</strong></div><div><span>${seasonPack?'MISSING EPISODES':'CURRENT QUALITY'}</span><strong>${seasonPack?Number((d.pack_episode_numbers||[]).length):escapeHtml(d.current_quality||'Missing')}</strong></div></div>`:'';
    const failedHistory=Array.isArray(d.failed_releases)?d.failed_releases:[];
    const failedBanner=failedHistory.length?`<div class="release-failed-history"><div><strong>${failedHistory.length} previous download${failedHistory.length===1?'':'s'} failed for this target</strong><span>NewzDeck blocked ${failedHistory.length===1?'that release':'those releases'} from being grabbed again. Choose a different post below.</span></div>${failedHistory.slice(0,4).map(x=>`<div class="release-failed-history-row"><b>${escapeHtml(x.title||'Failed release')}</b><span>${escapeHtml(x.indexer||'Unknown indexer')} • ${escapeHtml(x.reason||'Download/post failed')}</span></div>`).join('')}</div>`:'';
    $('releaseSearchBody').innerHTML=(d.errors||[]).map(x=>`<div class="release-indexer-error">${escapeHtml(x.indexer)}: ${escapeHtml(x.error)}</div>`).join('')+failedBanner+summary+(rows.length?`<div class="release-table"><div class="release-row header"><span>Release / decision</span><span>Quality</span><span>Size</span><span>Age</span><span>Score</span><span>Actions</span></div>${rows.map((r,i)=>{const age=r.published?Math.max(0,(Date.now()/1000-r.published)/86400):null;const decision=r.recommended?'RECOMMENDED':r.blacklisted?(r.blacklist_failed?'FAILED':'BLACKLISTED'):r.automatic_eligible?'ELIGIBLE':r.accepted?'MANUAL ONLY':'REJECTED';const components=(r.score_components||[]).map(c=>`<li><span>${escapeHtml(c.label)}</span><b class="${Number(c.score)>=0?'positive':'negative'}">${Number(c.score)>=0?'+':''}${Number(c.score)}</b></li>`).join('');const rejects=(r.rejections||[]).map(x=>`<li class="reject">${escapeHtml(x)}</li>`).join('');const why=`<details class="release-why"><summary>Why this release?</summary><div><ul>${components}</ul>${rejects?`<div class="release-rejections"><b>Rejected because</b><ul>${rejects}</ul></div>`:''}</div></details>`;return `<div class="release-row ${r.accepted?'accepted':'rejected'} ${r.recommended?'recommended':''}"><span><div class="release-title-line"><strong>${escapeHtml(r.title)}</strong><em class="release-decision ${decision.toLowerCase().replace(/\s+/g,'-')}">${decision}</em>${r.season_pack?'<em class="release-pack-badge">SEASON PACK</em>':''}</div><small>#${Number(r.rank||i+1)} • ${escapeHtml(r.indexer||'')} • ${escapeHtml((r.reasons||[]).slice(0,3).join(' • '))}</small>${why}</span><span>${escapeHtml(r.parsed?.quality||'Unknown')}<small>${escapeHtml([r.parsed?.codec,r.parsed?.hdr,r.parsed?.audio,r.parsed?.release_group].filter(Boolean).join(' • '))}</small></span><span>${r.size?formatBytes(r.size):'—'}</span><span>${age==null?'—':age<1?`${Math.max(1,Math.round(age*24))}h`:`${Math.round(age)}d`}</span><span><b class="release-score ${r.score>=0?'positive':'negative'}">${r.score>=0?'+':''}${r.score}</b>${r.effective_score!==r.score?`<small>effective ${r.effective_score}</small>`:''}</span><span class="release-actions"><button class="primary-btn compact" data-grab-release="${i}" ${r.accepted&&!r.blacklisted?'':'disabled'}>${r.season_pack?'Grab pack':'Grab'}</button><button class="secondary-btn compact" data-blacklist-release="${i}" ${r.blacklisted?'disabled':''}>${r.blacklisted?(r.blacklist_failed?'Failed':'Blocked'):'Blacklist'}</button></span></div>`}).join('')}</div>`:automationEmpty('⌕','No releases found',seasonPack?'No safe season packs were returned. You can still search individual episodes.':'Check your indexer configuration or try again later.'));
    document.querySelectorAll('[data-grab-release]').forEach(b=>b.onclick=()=>grabAutomationRelease(rows[Number(b.dataset.grabRelease)],b));document.querySelectorAll('[data-blacklist-release]').forEach(b=>b.onclick=()=>blacklistAutomationRelease(rows[Number(b.dataset.blacklistRelease)],b));
  }catch(e){$('releaseSearchBody').innerHTML=automationEmpty('!','Search failed',e.message)}
}
async function blacklistAutomationRelease(r,b){if(!confirm(`Blacklist this release for this Automation target?\n\n${r.title}`))return;const old=b.textContent;b.disabled=true;b.textContent='Blocking…';try{await api('/api/automation/blacklist/add',r);toast('Release blacklisted for this target.','success');const c=state.releaseSearchContext||{};await loadAutomation({quiet:true});await openReleaseSearch(c.itemId,c.season,c.episode)}catch(e){toast(e.message,'error');b.disabled=false;b.textContent=old}}
async function grabAutomationRelease(r,b){const old=b.textContent;b.disabled=true;b.textContent='Grabbing…';try{const d=await api('/api/automation/releases/grab',r,{timeoutMs:30000,timeoutMessage:'The indexer did not finish returning this NZB in time. Try the release again.'});const oneTime=!String(r.item_id||'')&&!!String(r.media_title||'');toast(oneTime?`${r.media_title} queued for one-time Smart Import. It will be renamed and moved without being added to Automation.`:`${d.collection_name||'Release'} added to the background download queue.`,'success');b.textContent='Queued';void loadDownloads();return}catch(e){const msg=friendlyTransportErrorMessage(e.message,'/api/automation/releases/grab');toast(msg,'error');const markedFailed=/marked FAILED for this target/i.test(String(msg||''));if(markedFailed&&state.releaseSearchContext?.itemId){const c={...state.releaseSearchContext};await loadAutomation({quiet:true});await openReleaseSearch(c.itemId,c.season,c.episode);return}b.disabled=false;b.textContent=old}}

async function addAutomationRoot(kind){const roots=[...automationRootsForKind(kind)],button=document.querySelector(`[data-add-root="${kind}"]`),old=button?.textContent||'';if(button){button.disabled=true;button.textContent='Opening folder picker…'}try{const r=await api('/api/automation/choose-folder',{kind,initial:roots.at(-1)||'',title:`Choose ${kind==='tv'?'TV':'movie'} library root`});if(r.cancelled)return;const folder=String(r.folder||'').trim();if(!folder)throw new Error('Windows did not return the selected folder.');await loadAutomation();renderAutomation();const count=automationRootsForKind(kind).length;if(r.added===false)toast('That root folder is already configured.');else toast(`Media root added • ${count} configured.`,'success')}catch(e){toast(`${e.message} You can also enter the full folder path below.`,'error')}finally{if(button?.isConnected){button.disabled=false;button.textContent=old}}}
async function addAutomationRootPath(kind){const input=document.querySelector(`[data-root-path="${kind}"]`),path=String(input?.value||'').trim();if(!path){input?.focus();toast('Enter a full folder path first.','error');return}const button=document.querySelector(`[data-add-root-path="${kind}"]`),old=button?.textContent||'';if(button){button.disabled=true;button.textContent='Adding…'}try{const r=await api('/api/automation/root/add',{kind,path});await loadAutomation();renderAutomation();const count=automationRootsForKind(kind).length;if(r.added===false)toast('That root folder is already configured.');else toast(`Media root added • ${count} configured.`,'success')}catch(e){toast(e.message,'error');if(input?.isConnected)input.focus()}finally{if(button?.isConnected){button.disabled=false;button.textContent=old}}}
async function removeAutomationRoot(kind,index){const roots=[...automationRootsForKind(kind)],removed=roots[index];if(!removed)return;const assigned=(state.automation?.library||[]).filter(x=>x.kind===kind&&String(x.root_folder||'').toLocaleLowerCase()===String(removed).toLocaleLowerCase()).length;if(assigned&&!confirm(`This root is assigned to ${assigned} library item${assigned===1?'':'s'}. Remove it anyway? Those items will use Automatic root until you assign another folder.`))return;roots.splice(index,1);try{await api('/api/automation/config/save',{[kind==='tv'?'tv_roots':'movie_roots']:roots});await loadAutomation();renderAutomation();toast('Media root removed.','success')}catch(e){toast(e.message,'error')}}


els.providerForm.onsubmit=async(e)=>{e.preventDefault();try{const d=await api('/api/providers/save',providerFormData());state.providerId=d.provider.id;await loadProviders();editProvider(d.provider.id);toast('Provider saved.','success');if(state.onboardingActive){closeProviderModal();showWelcomeStep('folder')}}catch(err){toast(err.message,'error')}};
$('testProviderBtn').onclick=async()=>{const box=els.providerTestResult;box.className='test-result';box.textContent='Testing secure NNTP connection…';try{const payload=providerFormData();if(payload.id&&!payload.password)payload.provider_id=payload.id;const d=await api('/api/providers/test',payload);box.innerHTML=`Connected successfully • <b>${d.latency_ms} ms</b><br>${escapeHtml(d.capabilities.slice(0,5).join(' • ')||'Server capabilities unavailable')}`;}catch(e){box.className='test-result error';box.textContent=e.message}};
$('deleteProviderBtn').onclick=async()=>{const id=$('providerId').value;if(!id)return;if(!confirm('Delete this provider profile?'))return;try{await api('/api/providers/delete',{id});if(state.providerId===id)state.providerId='';await loadProviders();newProvider();toast('Provider deleted.')}catch(e){toast(e.message,'error')}};


$('welcomeProviderBtn').onclick=()=>{state.onboardingActive=true;closeWelcome();openProviderModal();newProvider()};
$('welcomeLaterBtn').onclick=()=>{state.onboardingActive=false;closeWelcome()};
$('welcomeDefaultFolderBtn').onclick=()=>showWelcomeStep('ready');
$('welcomeChooseFolderBtn').onclick=async()=>{try{const r=await api('/api/settings/choose-download-folder',{});if(!r.cancelled){await loadDownloads();toast('Download folder updated.','success')}showWelcomeStep('ready')}catch(e){toast(e.message,'error')}};
$('welcomeStartBtn').onclick=async()=>{state.onboardingActive=false;closeWelcome();if(state.providerId)await loadGroups({refresh:true})};
$('welcomeModal').addEventListener('click',e=>{});
document.querySelectorAll('.sidebar .nav-item').forEach(b=>{if(b.classList.contains('active'))b.setAttribute('aria-current','page')});$('navBrowse').onclick=()=>setMainView('browse');$('navDiscover').onclick=()=>setMainView('discover');$('navDownloads').onclick=()=>setMainView('downloads');$('navDiagnostics').onclick=()=>setMainView('diagnostics');document.querySelectorAll('.sidebar [data-auto-tab]').forEach(b=>b.onclick=()=>setAutomationTab(b.dataset.autoTab));document.querySelectorAll('#automationTabs [data-auto-tab]').forEach(b=>b.onclick=()=>setAutomationTab(b.dataset.autoTab));document.querySelectorAll('#discoverTabs [data-discover-tab]').forEach(b=>b.onclick=()=>activateDiscoverTab(b.dataset.discoverTab));$('discoverSearchBtn').onclick=()=>{state.discoverPage=1;loadDiscover({refresh:true})};$('discoverSearch').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();state.discoverPage=1;loadDiscover({refresh:true})}};$('discoverApplyBtn').onclick=()=>{state.discoverPage=1;loadDiscover({refresh:true})};$('discoverRefreshBtn').onclick=()=>loadDiscover({refresh:true});$('discoverHideLibrary').onchange=()=>loadDiscover({refresh:false});$('discoverDetailClose').onclick=()=>$('discoverDetailModal').classList.add('hidden');$('discoverDetailModal').addEventListener('click',e=>{if(e.target===$('discoverDetailModal'))$('discoverDetailModal').classList.add('hidden')});
document.querySelectorAll('[data-download-filter]').forEach(b=>b.onclick=()=>{state.downloadFilter=b.dataset.downloadFilter;document.querySelectorAll('[data-download-filter]').forEach(x=>x.classList.toggle('active',x===b));renderDownloads();});if($('downloadHistorySearch'))$('downloadHistorySearch').oninput=()=>{state.downloadSearchTerm=$('downloadHistorySearch').value||'';renderDownloads()};
els.pauseDownloadsBtn.onclick=()=>downloadControl(state.downloadSnapshot.paused?'resume_all':'pause_all');if(els.hardStopDownloadsBtn)els.hardStopDownloadsBtn.onclick=()=>{const d=state.downloadSnapshot||{},c=d.counts||{};const active=Number(c.downloading||0)+Number(c.queued||0)+Number(c.retry_wait||0)+Number(c.cancelling||0)+Number(d.post_processing_active||0);if(!active){toast('There is no active queue work to stop.');return}if(confirm('Hard stop all downloads and post-processing? Completed article blocks will be preserved so cancelled downloads can be retried later.'))downloadControl('hard_stop_all')};els.clearCompletedBtn.onclick=()=>downloadControl('clear_completed');els.importNzbBtn.onclick=()=>els.nzbFileInput.click();els.nzbFileInput.onchange=()=>startNzbImport(els.nzbFileInput.files);if(els.downloadOrganization)els.downloadOrganization.onchange=()=>{state.downloadOrganization=els.downloadOrganization.value;saveUiSettings();toast('Download organization will apply to newly queued files.','success')};els.chooseDownloadsFolderBtn.onclick=async()=>{try{const r=await api('/api/settings/choose-download-folder',{});if(!r.cancelled){toast('Download folder updated.','success');await loadDownloads()}}catch(e){toast(e.message,'error')}};els.openDownloadsFolderBtn.onclick=async()=>{try{await api('/api/downloads/open-folder',{});}catch(e){toast(e.message,'error')}};
els.downloadMoveTopBtn.onclick=()=>downloadBatch('move_top');els.downloadMoveBottomBtn.onclick=()=>downloadBatch('move_bottom');els.downloadPauseSelectedBtn.onclick=()=>downloadBatch('pause');els.downloadResumeSelectedBtn.onclick=()=>downloadBatch('resume');els.downloadRetrySelectedBtn.onclick=()=>downloadBatch('retry');els.downloadCancelSelectedBtn.onclick=()=>downloadBatch('cancel');els.downloadRemoveSelectedBtn.onclick=()=>downloadBatch('remove');els.downloadClearSelectionBtn.onclick=()=>{state.selectedDownloads.clear();state.downloadSelectionAnchor='';renderDownloads()};els.downloadPrioritySelect.onchange=()=>downloadBatch('priority',els.downloadPrioritySelect.value);
$('refreshDiagnosticsBtn').onclick=loadDiagnostics;$('probeProvidersBtn').onclick=probeProviders;$('copyDiagnosticsBtn').onclick=copyDiagnostics;$('clearDiagnosticsBtn').onclick=async()=>{try{await api('/api/diagnostics/clear',{});await loadDiagnostics()}catch(e){toast(e.message,'error')}};
els.articlesList.addEventListener('scroll',()=>{if((state.selectedGroup)&&els.selectVisibleBtn)els.selectVisibleBtn.disabled=viewportSelectableArticles().length===0;if(state.selectedGroup){clearTimeout(state.groupStateSaveTimer);state.groupStateSaveTimer=setTimeout(()=>captureCurrentGroupState(),500)}},{passive:true});
els.nzbImportCloseBtn.onclick=()=>closeNzbPreview(true);els.nzbImportCancelBtn.onclick=()=>closeNzbPreview(true);els.nzbImportQueueBtn.onclick=queueCurrentNzb;els.nzbSelectAllBtn.onclick=()=>{els.nzbImportFiles.querySelectorAll('input[type="checkbox"]').forEach(c=>c.checked=true);updateNzbSelectionSummary()};els.nzbSelectNoneBtn.onclick=()=>{els.nzbImportFiles.querySelectorAll('input[type="checkbox"]').forEach(c=>c.checked=false);updateNzbSelectionSummary()};els.nzbSelectRecommendedBtn.onclick=()=>{const files=state.currentNzbPreview?.files||[];els.nzbImportFiles.querySelectorAll('input[type="checkbox"]').forEach(c=>{const f=files.find(x=>Number(x.index)===Number(c.dataset.index));c.checked=f?.default_selected!==false});updateNzbSelectionSummary()};els.archivePasswordCloseBtn.onclick=closeArchivePassword;els.archivePasswordCancelBtn.onclick=closeArchivePassword;els.archivePasswordSubmitBtn.onclick=submitArchivePassword;els.archivePasswordInput.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();submitArchivePassword()}};
$('automationSetupBtn').onclick=openAutomationSetup;$('automationIndexersBtn').onclick=openAutomationIndexers;$('automationScanBtn').onclick=()=>scanAutomationLibrary();$('automationAddBtn').onclick=openAutomationAdd;$('automationAddClose').onclick=closeAutomationAdd;$('automationAddKind').onchange=()=>{refreshAutomationAddRootOptions();refreshAutomationAddMonitoringOptions()};$('automationAddMonitor').onchange=()=>{const help=$('automationAddMonitorHelp');if(help)help.textContent=automationMonitoringHelp($('automationAddKind').value,$('automationAddMonitor').value)};$('automationMetadataSearchBtn').onclick=searchAutomationMetadata;$('automationMetadataQuery').onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();searchAutomationMetadata()}};$('automationManualAddBtn').onclick=()=>addAutomationMedia();$('automationItemClose').onclick=()=>$('automationItemModal').classList.add('hidden');$('releaseSearchClose').onclick=()=>$('releaseSearchModal').classList.add('hidden');$('qualityProfileClose').onclick=()=>$('qualityProfileModal').classList.add('hidden');$('qualityProfileQualities').oninput=()=>refreshQualityCutoff($('qualityProfileCutoff').value);$('qualityProfileSave').onclick=saveQualityProfile;$('qualityProfileDelete').onclick=deleteQualityProfile;$('indexerModalClose').onclick=()=>$('indexerModal').classList.add('hidden');$('indexerSave').onclick=saveIndexer;$('indexerTest').onclick=testIndexer;$('indexerDelete').onclick=deleteIndexer;['automationAddModal','automationItemModal','releaseSearchModal','qualityProfileModal','indexerModal'].forEach(id=>$(id)?.addEventListener('click',e=>{if(e.target===$(id))$(id).classList.add('hidden')}));
document.addEventListener('dragover',e=>{const files=[...(e.dataTransfer?.items||[])];if(files.some(x=>x.kind==='file'&&String(x.type||'').toLowerCase().includes('xml'))||[...(e.dataTransfer?.files||[])].some(f=>f.name?.toLowerCase().endsWith('.nzb'))){e.preventDefault();e.dataTransfer.dropEffect='copy'}});document.addEventListener('drop',e=>{const files=[...(e.dataTransfer?.files||[])].filter(f=>f.name?.toLowerCase().endsWith('.nzb'));if(files.length){e.preventDefault();startNzbImport(files)}});window.addEventListener('beforeunload',()=>captureCurrentGroupState());
document.addEventListener('keydown',handleKeyboardShortcuts);

async function ensureBackendVersion(){
  let h;try{const r=await fetch('/api/health',{cache:'no-store'});if(!r.ok)return true;h=await r.json()}catch(_e){return true}
  if(!h?.version||String(h.version)===UI_VERSION)return true;
  if(!h.service_mode){
    const reloadKey=`newzdeck-ui-reload-${String(h.version)}`;
    if(sessionStorage.getItem(reloadKey)!=='1'){
      sessionStorage.setItem(reloadKey,'1');
      location.replace(`/?ui=${encodeURIComponent(String(h.version))}&reload=${Date.now()}`);
      return false;
    }
    throw new Error(`NewzDeck UI v${UI_VERSION} is connected to backend v${h.version}. The UI cache could not refresh automatically. Fully close the NewzDeck window and launch this build again.`);
  }
  state.serviceTransition='restart';showServiceTransitionOverlay('stop');const o=$('serviceTransitionOverlay');o.querySelector('h2').textContent='Finishing NewzDeck update…';o.querySelector('p').textContent='Restarting the background service to load the installed backend.';$('serviceReconnectBtn').disabled=true;
  try{await fetch('/api/service/control',{method:'POST',headers:{'Content-Type':'application/json'},body:'{"action":"restart"}',cache:'no-store'})}catch(_e){}
  for(let i=0;i<60;i++){await new Promise(r=>setTimeout(r,750));try{const r=await fetch('/api/health?sync='+Date.now(),{cache:'no-store'});if(r.ok&&(await r.json())?.version===UI_VERSION){location.reload();return false}}catch(_e){}}
  return false;
}

async function ensureDesktopTaskbarIdentity(){
  try{
    const h=await fetch('/api/health',{cache:'no-store'}).then(r=>r.json());
    if(h?.platform!=='win32')return;
    await fetch('/api/app/taskbar-identify',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',cache:'no-store'});
  }catch(_e){}
}

async function maybeOfferBackgroundService(){
  try{
    const health=await api('/api/health');if(health.platform!=='win32'||health.service_mode)return;
    const service=await api('/api/service/status');
    if(!service.installed&&localStorage.getItem('newzdeckBackgroundOfferV200')!=='shown'){
      localStorage.setItem('newzdeckBackgroundOfferV200','shown');
      setTimeout(()=>openSettingsModal('background'),700);
    }
  }catch(_e){}
}

function scheduleNextDownloadPoll(delay=null){
  if(downloadPollTimer)clearTimeout(downloadPollTimer);
  const visible=state.activeView==='downloads'&&!document.hidden;
  const ms=delay==null?(visible?250:1000):delay;
  downloadPollTimer=setTimeout(runDownloadLivePoll,ms);
}
async function runDownloadLivePoll(){
  if(state.serviceTransition){scheduleNextDownloadPoll();return;}
  if(downloadPollInFlight){scheduleNextDownloadPoll(100);return;}
  downloadPollInFlight=true;
  try{await loadDownloads({render:true,livePatch:state.activeView==='downloads',quiet:true});}finally{downloadPollInFlight=false;scheduleNextDownloadPoll();}
}
function startDownloadLivePolling(){
  document.addEventListener('visibilitychange',()=>scheduleNextDownloadPoll(document.hidden?750:0));
  scheduleNextDownloadPoll(250);
}

async function ensureAuthoritativeRuntime(){
  try{
    const d=await api('/api/runtime/authoritative',null,{timeoutMs:3500,timeoutMessage:'NewzDeck could not determine the authoritative background runtime.'});
    const target=String(d?.url||'').replace(/\/$/,'');
    const here=window.location.origin.replace(/\/$/,'');
    if(target && target!==here){
      const next=target+(window.location.pathname||'/');
      window.location.replace(next);
      return false;
    }
  }catch(e){ console.warn('Authoritative runtime check failed',e); }
  return true;
}

(async function initializeApp(){
  if(!(await ensureBackendVersion()))return;
  if(!(await ensureAuthoritativeRuntime()))return;
  ensureDesktopTaskbarIdentity();
  // Prime Automation sidebar state independently of provider/newsgroup startup.
  // The immediate call plus two bounded warm-up refreshes handles a service that
  // is still restoring its media library when the desktop UI first connects.
  primeAutomationSidebarCounts();
  await loadUiSettings();
  await loadDownloads();
  const desiredTab=state.browserTabs.find(t=>t.id===state.activeBrowserTabId)||state.browserTabs[0]||null;
  if(desiredTab?.provider_id)localStorage.setItem('providerId',desiredTab.provider_id);
  await loadProviders();startTrackedGroupRefresh();
  setInterval(()=>{if(state.activeView==='automation')loadAutomation({quiet:true,render:false,background:true})},10000);
  renderBrowserTabs();updateMutedPostersButton();updateSelectionBar();
  const tab=state.browserTabs.find(t=>t.id===state.activeBrowserTabId)||state.browserTabs.find(t=>t.provider_id===state.providerId)||null;
  if(tab&&tab.provider_id===state.providerId){try{await loadGroups();await selectGroup(tab.group,{tabId:tab.id,fromTab:true})}catch(e){toast(`Could not restore ${tab.group}: ${e.message}`,'error')}}
  maybeOfferBackgroundService();
  setTimeout(async()=>{const d=await checkOnlineUpdates(false,{quiet:true});if(d?.update_available&&!sessionStorage.getItem('newzdeckUpdateNotice'+d.latest_version)){sessionStorage.setItem('newzdeckUpdateNotice'+d.latest_version,'1');toast(`NewzDeck v${d.latest_version} is available. Open About & Updates to install it.`,'success')}},4500);
})().catch(e=>toast(e.message,'error'));
startDownloadLivePolling();setInterval(()=>{if(state.activeView==='diagnostics')loadDiagnostics()},3000);

(async function initDesktopHeartbeat(){
  // The desktop backend must not depend on one perfectly-timed startup probe.
  // Keep probing until the local server is ready, then maintain the lease.
  for(let attempt=0;attempt<300;attempt++){
    try{
      const r=await fetch('/api/health',{cache:'no-store'});
      if(r.ok){
        const health=await r.json();
        if(!health?.desktop_mode)return;
        const beat=()=>fetch('/api/app/heartbeat',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}',cache:'no-store'}).catch(()=>{});
        beat();
        setInterval(beat,3000);
        // Browsers can throttle timers while Windows sleeps or while the app is
        // hidden. Renew the lease immediately when the desktop becomes active.
        window.addEventListener('focus',beat);
        window.addEventListener('pageshow',beat);
        document.addEventListener('visibilitychange',()=>{if(!document.hidden)beat()});
        return;
      }
    }catch(_e){}
    await new Promise(r=>setTimeout(r,1000));
  }
})();
