'use strict';
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const path=require('path');
const code=fs.readFileSync(path.join(__dirname,'../../src/app/static/app.js'),'utf8');
const begin=code.indexOf('// v3.7.32: POST acknowledges work; polling observes the SAME operation.');
const end=code.indexOf('async function addAutomationRoot(',begin);
assert(begin>0&&end>begin,'production Grab functions found');
const source=code.slice(begin,end).replace('const manualGrabDelay = ms => new Promise(resolve=>setTimeout(resolve,ms));','const manualGrabDelay = ms => Promise.resolve();');
async function scenario(status,timeout=false){
  const log=[],requests=[],id='a'.repeat(32),button={disabled:false,textContent:'Grab',isConnected:true};
  const context={console,crypto:{randomUUID:()=> 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'},
    api:async (url,body,opts)=>{
      requests.push({url,body,opts});
      if(url==='/api/automation/releases/grab'){
        assert(body.async_grab===true&&body.client_request_id===id);
        if(timeout){const e=new Error('ack timeout');e.code='ui-timeout';throw e;}
        return {request_id:id,job_id:'z'.repeat(32),status:'queued'};
      }
      if(url.startsWith('/api/automation/releases/grab/status?request_id='))
        return {status,...(status==='accepted'?{pending_engine_handoff:true}:{}),message:'Backend result'};
      throw new Error('bad route '+url);
    },
    toast:(message,type)=>log.push({message,type}),loadDownloads:()=>Promise.resolve(),encodeURIComponent,
    state:{releaseSearchContext:{}},document:{},setTimeout};
  vm.createContext(context);vm.runInContext(source,context);
  await context.grabAutomationRelease({item_id:'movie1',title:'Sinners.2025'},button);
  assert.strictEqual(requests.filter(x=>x.url==='/api/automation/releases/grab').length,1,'no duplicate POST');
  assert(requests.some(x=>x.url.includes('grab/status?request_id=')),'poll by stable client ID');
  return {button,log,requests};
}
(async()=>{
  let x=await scenario('accepted');assert(x.log.some(x=>x.type==='success'));assert.strictEqual(x.button.textContent,'Pending SAB');
  for(const val of ['already_queued','reservation_only','suppressed']){
    x=await scenario(val);assert(x.log.some(x=>x.type==='warning'));assert(!x.log.some(x=>x.type==='success'));
    assert.strictEqual(x.button.disabled,false);
  }
  x=await scenario('failed');assert(x.log.some(x=>x.type==='error'));assert.strictEqual(x.button.textContent,'Grab');
  x=await scenario('accepted',true);assert.strictEqual(x.requests.filter(z=>z.url==='/api/automation/releases/grab').length,1);
  assert(x.log.some(z=>z.type==='success'));
  assert(!code.includes("api('/api/automation/releases/grab',r,{timeoutMs:30000"),'old blocking UI Grab removed');
  console.log('PASS: asynchronous UI status polling, accurate success/duplicate/reservation/failure toasts, stable request identity and no retry after POST timeout');
})().catch(err=>{console.error(err);process.exit(1)});
