const fs = require('fs');
const vm = require('vm');

function fail(message) {
  console.error('validate-media-set-key.js: ' + message);
  process.exit(1);
}

const source = fs.readFileSync('src/app/static/app.js', 'utf8');
const start = source.indexOf('function mediaSetNormalizeBase');
const end = source.indexOf('function resetMediaSetIndex', start);
if (start < 0 || end < 0 || end <= start) fail('Could not locate media-set helper block in app.js.');

const context = { articleGroup: a => a.group || 'alt.test' };
vm.createContext(context);
vm.runInContext(source.slice(start, end), context);

const make = (filename, from='Alice <poster@example.com>', group='alt.test', kind='image', subject='') => ({
  group, from, subject, media: { filename, kind }
});
const key = (...args) => context.mediaSetKey(make(...args));

const positiveGroups = [
  ['Vacation_001.jpg', 'Vacation_002.jpg', 'Vacation_003.jpg'],
  ['Vacation001.jpg', 'Vacation002.jpg', 'Vacation003.jpg'],
  ['Vacation(01).jpg', 'Vacation(02).jpg', 'Vacation(03).jpg'],
  ['Vacation [01].jpg', 'Vacation [02].jpg', 'Vacation [03].jpg'],
  ['Vacation_01_of_25.jpg', 'Vacation-2of25.jpg', 'Vacation 03 of 25.jpg'],
  ['Vacation [01/25].jpg', 'Vacation (02 of 25).jpg', 'Vacation {03/25}.jpg'],
  ['Family-Trip_001.jpg', 'Family.Trip (002).jpg', 'Family Trip [003].jpg'],
  ['Vacation - Image 007.jpg', 'Vacation_img008.jpg', 'Vacation photo 009.jpg'],
  ['VacationImage007.jpg', 'VacationImg008.jpg', 'VacationPhoto009.jpg'],
];

for (const files of positiveGroups) {
  const keys = files.map(f => key(f));
  if (!keys[0] || new Set(keys).size !== 1) {
    fail('Expected one set key for: ' + files.join(' | ') + ' -> ' + keys.join(' | '));
  }
}

const senderA = key('Vacation_001.jpg', 'Alice <poster@example.com>');
const senderB = key('Vacation_002.jpg', '"Alice Smith" <poster@example.com>');
if (!senderA || senderA !== senderB) fail('Canonical poster identity did not merge display-name variants.');

const subjectA = context.mediaSetKey(make('001.jpg', 'Alice <poster@example.com>', 'alt.test', 'image', 'My Set [1/20] "001.jpg" yEnc'));
const subjectB = context.mediaSetKey(make('002.jpg', 'Alice <poster@example.com>', 'alt.test', 'image', 'My Set [2/20] "002.jpg" yEnc'));
if (!subjectA || subjectA !== subjectB) fail('Subject index/total fallback did not group numeric-only filenames.');

if (key('Vacation_2024.jpg') || key('Vacation2024.jpg')) fail('Bare year-like suffix was incorrectly treated as sequence evidence.');
if (key('Vacation.jpg')) fail('Unsequenced filename was incorrectly grouped.');
if (key('Vacation_001.jpg', 'Bob <other@example.com>') === senderA) fail('Different posters were merged.');
if (key('Vacation_001.jpg', 'Alice <poster@example.com>', 'alt.other') === senderA) fail('Different newsgroups were merged.');
if (key('Vacation_001.jpg', 'Alice <poster@example.com>', 'alt.test', 'video') === senderA) fail('Different media kinds were merged.');

console.log('validate-media-set-key.js: PASS');
