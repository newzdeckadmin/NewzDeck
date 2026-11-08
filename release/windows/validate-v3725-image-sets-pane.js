// Regression: use the real updateBrowseModeControls() body from the reviewed app.js.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const text=fs.readFileSync(path.resolve(__dirname,'../../src/app/static/app.js'),'utf8');
const start=text.indexOf('function updateBrowseModeControls(){');
const end=text.indexOf('function updateGroupRelatedButton(){',start);
assert(start>=0&&end>start,'Missing production browse layout function');
const fn=text.slice(start,end);
function classList(initial=[]){const flags=new Set(initial);return{toggle:(name,on)=>{if(on)flags.add(name);else flags.delete(name)},remove:name=>flags.delete(name),contains:name=>flags.has(name)}}
function element(initial=[]){return{classList:classList(initial),attrs:{},setAttribute(name,value){this.attrs[name]=value}}}
function controls(){return Object.fromEntries(['articleViewToggle','binaryViewToggle','binaryPackagesBtn','rawPostsBtn','galleryViewBtn','listViewBtn'].map(k=>[k,element()]))}
let total=0;
for(const kind of ['images','videos','media','all']){
 for(const enabled of [false,true]){
  const view=element(),side=element(['open']),els=controls();
  view.querySelector=sel=>sel==='.preview-pane'?side:null;
  const sandbox={
   state:{groupRelatedMedia:enabled,groupBinarySets:true},
   els,
   $:id=>id==='browseView'?view:null,
   isAllPostsMode:()=>kind==='all',effectiveViewMode:()=>kind==='all'?'list':'gallery',
   document:{querySelector:()=>null},syncBinaryMinSizeToolbar:()=>{},updateGroupRelatedButton:()=>{}
  };
  vm.runInNewContext(fn+'; updateBrowseModeControls();',sandbox);
  const hidden=kind==='all'||!enabled;
  assert.equal(view.classList.contains('all-posts-wide'),hidden,`Incorrect grid: ${kind}, sets=${enabled}`);
  assert.equal(side.attrs['aria-hidden'],String(hidden),`Incorrect accessibility: ${kind}, sets=${enabled}`);
  assert.equal(side.classList.contains('open'),!hidden,`Unexpected pane open state: ${kind}, sets=${enabled}`);
  assert.equal(els.articleViewToggle.classList.contains('hidden'),kind==='all','Media controls changed');
  assert.equal(els.binaryViewToggle.classList.contains('hidden'),kind!=='all','All Posts controls changed');
  total++;
 }
}
// Simulate OFF->ON->OFF on one persistent pane; toggling must restore layout.
const view=element(),side=element(['open']),els=controls();view.querySelector=()=>side;
const sandbox={state:{groupRelatedMedia:false,groupBinarySets:true},els,$:()=>view,isAllPostsMode:()=>false,effectiveViewMode:()=> 'gallery',document:{querySelector:()=>null},syncBinaryMinSizeToolbar:()=>{},updateGroupRelatedButton:()=>{}};
const ctx=vm.createContext(sandbox);
vm.runInContext(fn+'; updateBrowseModeControls();',ctx);
assert(view.classList.contains('all-posts-wide'));
sandbox.state.groupRelatedMedia=true;
vm.runInContext('updateBrowseModeControls()',ctx);
assert(!view.classList.contains('all-posts-wide'));
assert.equal(side.attrs['aria-hidden'],'false');
sandbox.state.groupRelatedMedia=false;
vm.runInContext('updateBrowseModeControls()',ctx);
assert(view.classList.contains('all-posts-wide'));
// The shared full-width class must actually remove the visual column.
const styles=fs.readFileSync(path.resolve(__dirname,'../../src/app/static/styles.css'),'utf8');
assert(/\.workspace\.all-posts-wide\{grid-template-columns:[^}]+\}/.test(styles),'The full-width browser style is missing');
assert(/\.workspace\.all-posts-wide\s+\.preview-pane\{display:none!important\}/.test(styles),'The side pane must be hidden by the full-width layout');
console.log(`PASS: ${total} browse mode combinations, live OFF/ON/OFF, and existing CSS full-width rules`);
