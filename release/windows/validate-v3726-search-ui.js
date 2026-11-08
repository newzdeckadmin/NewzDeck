// Exercise the real search polling function with a mocked UI/API. No network calls.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const src=fs.readFileSync(path.resolve(__dirname,'../../src/app/static/app.js'),'utf8');
const start=src.indexOf('function startEntireGroupSearchPolling(){');
const end=src.indexOf('async function cancelEntireGroupSearch(){',start);
assert(start>0&&end>start,'Production search poll function missing');
const code=src.slice(start,end);
async function exercise({mode=true,page=1,selected='',scroll=0,headers=10,previous=0}){
 let calls=0,timerClears=0;
 const state={groupSearchJob:{id:'abc123',status:'scanning',match_headers:previous},groupSearchPollTimer:null,
              searchMode:mode,articlePage:page,selectedArticleKey:selected,
              groupSearchLiveRefreshAt:0,groupSearchLiveRefreshCount:0,groupSearchLiveRefreshPending:false};
 const els={articlesList:{scrollTop:scroll}};
 const sandbox={state,els,Date,Number,
   api:async()=>({search:{id:'abc123',status:'scanning',match_headers:headers,match_posts:headers,
                  total_headers:1000,scanned_headers:100,percent:10}}),
   renderEntireGroupSearchStatus:()=>{},renderSearchModeSummary:()=>{},
   loadEntireGroupSearchResults:async(num,options)=>{assert.equal(num,1);assert.equal(options.silent,true);calls++},
   setInterval:()=>42,clearInterval:()=>{timerClears++},toast:()=>{throw Error('Unexpected toast')}
 };
 vm.runInNewContext(code+'; startEntireGroupSearchPolling();',sandbox);
 await new Promise(resolve=>setTimeout(resolve,1));
 return {calls,state,timerClears};
}
(async()=>{
 let t=await exercise({});assert.equal(t.calls,1,'Live first-page results did not refresh');
 for(const args of [{mode:false},{page:3},{selected:'article-3'},{scroll:400},{headers:0}]){
  t=await exercise(args);assert.equal(t.calls,0,`Should not repaint during reading/scrolled/unchanged: ${JSON.stringify(args)}`);
 }
 assert(src.includes('const lanes=Number(job.workers||1)'),'Active parallel worker telemetry missing from search UI');
 assert(src.includes('if(!silent)setArticleLoading(true)'),'Silent refresh must not block the browsing UI');
 console.log('PASS: search live progress, throttled first-page refresh and user-selection protection');
})().catch(err=>{console.error(err);process.exit(1)});
