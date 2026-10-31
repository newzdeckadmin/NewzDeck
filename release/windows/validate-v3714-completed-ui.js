'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict'),path=require('node:path');
const app=fs.readFileSync(path.join(__dirname,'../../src/app/static/app.js'),'utf8');
const html=fs.readFileSync(path.join(__dirname,'../../src/app/static/index.html'),'utf8');
assert(html.includes('id="removeAllCompletedBtn"')&&html.includes('id="removeAllFailedBtn"'));
assert(app.includes("if($('removeAllCompletedBtn'))$('removeAllCompletedBtn').onclick=()=>removeAllCompletedDownloads()"));
assert(app.includes('updateRemoveAllFailedButton(allJobs);updateRemoveAllCompletedButton(d)'));
const section=app.slice(app.indexOf('function completedHistoryCount('),app.indexOf('function updateRemoveAllFailedButton('));
assert(section.includes("action:'clear_completed'")&&!section.includes("action:'remove'"));
function setup({confirm=true,count=153,scope='completed',filter='completed',fail=false}={}){
 const btn={textContent:'',disabled:false,hidden:true,classList:{toggle(c,b){if(c==='hidden')btn.hidden=b}}};
 const state={downloadFilter:filter,downloadSnapshot:{view:{scope,total:count},counts:{completed:count},jobs:[]},removingAllCompleted:false,downloadHistoryOffset:100,downloadHistoryLimit:50,downloadHistoryLoaded:[{id:'1'}]};
 const events=[],dialogs=[],ctx={state,console,window:{confirm(s){dialogs.push(s);return confirm}},$:(id)=>id==='removeAllCompletedBtn'?btn:null,api:async(p,body,opts)=>{events.push({p,body,opts});if(fail)throw Error('test error');return {}},loadDownloads:async()=>{events.push({p:'refresh'});return {jobs:[],view:{scope:'completed',total:0}}},toast:(msg,kind)=>events.push({msg,kind})};
 vm.runInNewContext(section,ctx);
 return {ctx,state,btn,events,dialogs};
}
(async()=>{
 let t=setup();t.ctx.updateRemoveAllCompletedButton();assert.equal(t.btn.hidden,false);assert.match(t.btn.textContent,/153/);
 await t.ctx.removeAllCompletedDownloads();assert.equal(t.events[0].body.action,'clear_completed');assert.equal(t.events[0].body.ids,null);assert.equal(t.events[0].opts.timeoutMs,90000);assert.equal(t.state.downloadHistoryOffset,0);assert.equal(t.state.downloadHistoryLoaded.length,0);assert.match(t.dialogs[0],/NOT be deleted/);assert.match(t.dialogs[0],/all Completed history pages/);assert.equal(t.state.removingAllCompleted,false);
 t=setup({confirm:false});await t.ctx.removeAllCompletedDownloads();assert.equal(t.events.length,0);
 t=setup({count:0});await t.ctx.removeAllCompletedDownloads();assert.equal(t.events.length,0);assert.equal(t.btn.hidden,true);
 t=setup({filter:'failed'});await t.ctx.removeAllCompletedDownloads();assert.equal(t.events.length,0);
 t=setup({fail:true});await t.ctx.removeAllCompletedDownloads();assert.equal(t.state.removingAllCompleted,false);assert(t.events.some(x=>x.kind==='error'));
 console.log('validate-v3714-completed-ui.js: PASS (visibility, total count, confirm/cancel, one server action, all pages refresh, failures)');
})().catch(e=>{console.error(e);process.exit(1)});
