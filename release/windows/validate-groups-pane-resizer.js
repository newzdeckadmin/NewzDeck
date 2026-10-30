const fs = require('fs');
const vm = require('vm');

function fail(message) {
  console.error('validate-groups-pane-resizer.js: ' + message);
  process.exit(1);
}

const app = fs.readFileSync('src/app/static/app.js', 'utf8');
const html = fs.readFileSync('src/app/static/index.html', 'utf8');
const css = fs.readFileSync('src/app/static/styles.css', 'utf8');

const start = app.indexOf("const GROUPS_PANE_WIDTH_KEY");
const end = app.indexOf("const THEME_IDS", start);
if (start < 0 || end < 0 || end <= start) fail('Could not isolate pure Newsgroups-pane sizing helpers.');

const helperSource = app.slice(start, end);
if (/\bdocument\b|\bwindow\b|applyTheme\s*\(/.test(helperSource)) {
  fail('Pure sizing-helper slice unexpectedly includes browser initialization code.');
}

const context = {};
vm.createContext(context);
vm.runInContext(helperSource, context);

const bounds = context.groupsPaneWidthBounds;
const clamp = context.clampGroupsPaneWidth;
if (typeof bounds !== 'function' || typeof clamp !== 'function') fail('Sizing helper functions were not defined.');

let b = bounds(1250, 1440);
if (b.min !== 240 || b.max !== 460) fail(`Desktop bounds changed unexpectedly: ${JSON.stringify(b)}`);
if (clamp(999, 1250, 1440) !== 460) fail('Desktop clamp did not preserve Articles/Related Media space.');
if (clamp(200, 1250, 1440) !== 240) fail('Minimum width clamp failed.');

b = bounds(980, 1100);
if (b.max !== 560) fail(`Two-pane compact maximum should be 560, got ${b.max}.`);
if (clamp(500, 980, 1100) !== 500) fail('Valid compact width was incorrectly changed.');

b = bounds(736, 800);
if (b.max !== 376) fail(`Narrow maximum should be 376, got ${b.max}.`);
if (clamp(600, 736, 800) !== 376) fail('Narrow viewport clamp failed.');

b = bounds(2000, 1920);
if (b.max !== 640) fail(`Hard maximum should remain 640, got ${b.max}.`);

for (const marker of [
  'id="groupsPaneResizer"',
  'role="separator"',
  'aria-orientation="vertical"',
  'tabindex="0"',
]) if (!html.includes(marker)) fail(`HTML splitter marker missing: ${marker}`);

for (const marker of [
  '.groups-pane-resizer{',
  'cursor:col-resize',
  'body.groups-pane-resizing',
  '--groups-pane-width',
  'grid-template-columns:var(--groups-pane-width)',
]) if (!css.includes(marker)) fail(`CSS splitter marker missing: ${marker}`);

for (const marker of [
  'function initGroupsPaneResizer()',
  "localStorage.setItem(GROUPS_PANE_WIDTH_KEY",
  "handle.addEventListener('pointerdown'",
  "handle.addEventListener('pointermove'",
  "handle.addEventListener('dblclick'",
  "e.key==='ArrowLeft'||e.key==='ArrowRight'",
  "initGroupsPaneResizer();",
]) if (!app.includes(marker)) fail(`JS splitter marker missing: ${marker}`);

console.log('validate-groups-pane-resizer.js: PASS');
