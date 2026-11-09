// Tests against the actual rendered application source, not a copy of UI snippets.
const fs = require('fs'), assert=require('assert');
const js=fs.readFileSync('src/app/static/app.js','utf8');
const open=js.slice(js.indexOf('async function openAutomationItem('),js.indexOf('async function ',js.indexOf('async function openAutomationItem(')+8));
const health=js.slice(js.indexOf('function renderAutomationHealth()'),js.indexOf('async function retryAutomationImport('));
for(const token of ['item.metadata_refreshed_at','item.metadata_refresh_error','Last successful refresh',"item.kind==='movie'",'Awaiting verified home-release metadata','Digital / Physical policy'])assert(open.includes(token),'Movie and TV detail missing: '+token);
for(const token of ['h.metadata?.updated','h.metadata?.attempted','h.metadata?.pending_retry','h.metadata?.status'])assert(health.includes(token),'Automation Health missing: '+token);
assert(js.includes("api('/api/downloads/pulse'"),'v3.7.27 progress feed changed unexpectedly');
assert(js.includes("browseView?.classList.toggle('all-posts-wide',hideRelatedPane)"),'Image Sets full-width layout changed unexpectedly');
console.log('PASS: movie/TV verified metadata timestamps, per-title errors, awaiting-home date and Automation Health progress are visible; Downloads and Image Sets preserved');
