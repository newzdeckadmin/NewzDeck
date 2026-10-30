const fs=require('fs'),vm=require('vm');
const file=process.argv[2]||'src/app/static/app.js';const s=fs.readFileSync(file,'utf8');
const a=s.indexOf('function mediaSetNormalizeBase('),b=s.indexOf('function resetMediaSetIndex()',a);
if(a<0||b<a)throw Error('could not isolate pure classifier');
const context={articleGroup: a=>a.group||'alt.test'};vm.createContext(context);vm.runInContext(s.slice(a,b),context);
const aitem=(filename,subject='',from='Alice <alice@example.com>',group='alt.test',kind='image')=>({subject,from,group,media:{filename,kind}});
const key=(f,s='',from,group,kind)=>context.mediaSetKey(aitem(f,s,from,group,kind));
const groups=[
 ['Vacation001.jpg','Vacation002.jpg','Vacation003.jpg'],
 ['Vacation_001.jpg','Vacation (002).jpg','Vacation [003].jpg'],
 ['Vacation [01/25].jpg','Vacation_02_of_25.jpg','Vacation-3of25.jpg'],
 ['Mountain Drive - Page 01.jpg','Mountain Drive page002.jpg','Mountain Drive-page003.jpg'],
 ['01 - Vacation.jpg','[02] Vacation.jpg','#03_Vacation.jpg'],
 ['Trip to Rome - photo 007.jpg','Trip.to.Rome-img008.jpg','Trip_to_Rome image 009.jpg'],
];
for(const g of groups){const k=g.map(x=>key(x));if(!k[0]||new Set(k).size!==1)throw Error('expected set: '+JSON.stringify(g)+' => '+JSON.stringify(k));}
const subjects=['My Beach Album [01/20] "IMG_0001.jpg" yEnc','My Beach Album (02/20) "IMG_0002.jpg" yEnc','My Beach Album 03 of 20 "IMG_0003.jpg" yEnc'];
const sKeys=subjects.map((s,i)=>key('IMG_000'+(i+1)+'.jpg',s));
if(!sKeys[0]||new Set(sKeys).size!==1)throw Error('subject generic camera cases '+JSON.stringify(sKeys));
const numKeys=subjects.map((s,i)=>key('0'+(i+1)+'.jpg',s));
if(!numKeys[0]||new Set(numKeys).size!==1 || numKeys[0]!==sKeys[0])throw Error('subject numeric fallback '+JSON.stringify(numKeys));
if(key('IMG_0001.jpg','Other Trip [01/20] "IMG_0001.jpg" yEnc')===sKeys[0])throw Error('different albums merged');
for(const file of ['Vacation2024.jpg','Vacation_2024.jpg','2024 - Vacation.jpg','Vacation.jpg'])if(key(file))throw Error('false positive '+file);
if(key('Vacation_001.jpg','', 'Bob <bob@example.com>')===key('Vacation_002.jpg'))throw Error('sender isolation failed');
if(key('Vacation_001.jpg','', 'Alice <alice@example.com>','alt.other')===key('Vacation_002.jpg'))throw Error('group isolation failed');
if(key('Vacation_001.jpg','', 'Alice <alice@example.com>','alt.test','video')===key('Vacation_002.jpg'))throw Error('kind isolation failed');
const uiChecks=[
 "state.groupRelatedMedia?appendContinuousGroupedGallery(previousKeys):appendContinuousGallery(previousKeys)",
 "if(state.groupRelatedMedia){renderGroupedGallery(items);return}",
 "grouped=(!isAllPostsMode()&&state.groupRelatedMedia)?buildMediaSets(items):null",
 "els.groupRelatedBtn.textContent=active?'▦ Image Sets: ON':'▦ Image Sets: OFF'",
 "resetMediaSetIndex();recalculatePreviewConcurrency();updateGroupRelatedButton();saveUiSettings();renderArticles({preserveScroll:false})",
 'group_related_media:state.groupRelatedMedia',
 ];
for(const q of uiChecks)if(!s.includes(q))throw Error('missing toggle behavior '+q);
console.log('Image Sets v3.7.8 classifier and ON/OFF browser paths: PASS');
