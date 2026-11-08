'use strict';
// Exercise production function bodies against a DOM stub. No browser/network is used.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.resolve(__dirname,'../..');
const text=fs.readFileSync(path.join(root,'src/app/static/app.js'),'utf8');
function body(name){const start=text.indexOf('function '+name+'(');assert(start>=0,name);let i=text.indexOf('{',start),depth=0,quoted=null,escape=false,template=false;
  // Function slices used in this test contain no template substitutions nesting braces
  // in a manner that needs a tokenizer. Match by the next function declaration.
  const end=text.indexOf('\nfunction ',start+9);return text.slice(start,end<0?undefined:end);
}
assert(text.includes('let downloadBulkQueueActive = 0;'));
assert(text.includes('downloadLastFullAttemptAt=now;'));
assert(text.includes("api('/api/downloads/pulse',null,{timeoutMs:1200"));
assert(text.includes('if(submittedBatches%3===0)await new Promise(resolve=>setTimeout(resolve,0))'));
assert(text.includes("api('/api/diagnostics/ping',null,{timeoutMs:1200})"));
assert(text.includes('UI event-loop lag: last='));
const view={id:'SAB-1',expected_bytes:1000,downloaded_bytes:100,speed_bps:1,eta_seconds:0,status:'downloading',collection_id:'SAB-1'};
const pkg={id:'SAB-1',job_ids:['SAB-1'],expected_bytes:1000,downloaded_bytes:100};
function cell(){return {textContent:'old',style:{width:'5%'}}}
const row={dataset:{id:'SAB-1'},querySelector(sel){if(sel.includes('.download-progress-fill'))return this.fill;if(sel==='.download-meta > b')return this.meta;return null},querySelectorAll(sel){if(sel==='.download-progress-cell > small > span')return this.spans;return []},fill:cell(),meta:cell(),spans:[cell(),cell()]};
const panel={dataset:{packageId:'SAB-1'},querySelector(sel){if(sel.includes('.download-progress-fill'))return this.fill;if(sel==='.package-progress small > span')return this.label;return null},fill:cell(),label:cell()};
const dl={querySelectorAll(sel){return sel.includes('.download-row')?[row]:sel.includes('.download-package')?[panel]:[]}};
let context={Date,document:{hidden:false},state:{activeView:'downloads',downloadSnapshot:{jobs:[view],collections:[pkg]}},els:{downloadsList:dl},downloadLastFreshPulseAt:0,formatBytes:n=>String(n)+'B',formatEta:n=>n+'s',formatSpeed:n=>String(n)+'B/s'};
vm.createContext(context);
vm.runInContext(body('applyDownloadPulse'),context);
assert.strictEqual(context.applyDownloadPulse({fresh:false,jobs:[{id:'SAB-1',percent:90}]}),false);
assert.strictEqual(view.downloaded_bytes,100);
assert.strictEqual(context.applyDownloadPulse({fresh:true,jobs:[{id:'SAB-1',percent:50,total_bytes:1000,remaining_bytes:500,speed_bps:256,eta_seconds:5}]}),true);
assert.strictEqual(view.downloaded_bytes,500);
assert.strictEqual(row.fill.style.width,'50%');
assert.strictEqual(panel.fill.style.width,'50%');
assert(row.spans[0].textContent.includes('50%'));
assert(panel.label.textContent.includes('500B'));
context.applyDownloadPulse({fresh:true,jobs:[{id:'SAB-1',percent:10,total_bytes:1000,remaining_bytes:900,speed_bps:0,eta_seconds:0}]});
assert.strictEqual(view.downloaded_bytes,500,'fresh pulses must not rewind already observed progress');
assert.strictEqual(row.fill.style.width,'50%');
console.log('PASS: pulse UI updates existing row/package progress without DOM rebuild and rejects stale/rewind samples');
