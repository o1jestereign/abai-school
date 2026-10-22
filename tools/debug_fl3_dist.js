const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const el = () => new Proxy(function () {}, { get: (t, k) => k === 'classList' ? { add() {}, remove() {}, toggle() {}, contains: () => false } : k === 'style' ? {} : k === 'getContext' ? () => new Proxy({}, { get: () => () => ({ addColorStop() {} }) , set: () => true }) : k === 'getBoundingClientRect' ? () => ({ left: 0, top: 0, width: 100, height: 100 }) : (k === 'appendChild' || k === 'addEventListener' || k === 'setPointerCapture') ? () => {} : undefined, set: () => true, apply: () => undefined });
global.window = global; global.document = { getElementById: el, createElement: el };
global.addEventListener = () => {}; global.innerWidth = 400; global.innerHeight = 800; global.devicePixelRatio = 1;
global.requestAnimationFrame = () => {}; global.Image = function () { this.complete = true; };
global.atob = (s) => Buffer.from(s, 'base64').toString('binary');
global.performance = { now: () => Date.now() };
eval(fs.readFileSync(path.join(root, 'js/mapdata.js'), 'utf8').replace('window.MAPDATA', 'global.MAPDATA'));
eval(fs.readFileSync(path.join(root, 'js/app.js'), 'utf8'));

const g = global.__game;
const fl3 = g.floors[2];
const f = g.dijkstraField(fl3, 144, 215);
const idx = 180 * fl3.gw + 173;
console.log('Distance from Stair 1 (144, 215) to 305 (173, 180):', f[idx]);
let finiteCount = 0;
for (let i = 0; i < f.length; i++) if (isFinite(f[i])) finiteCount++;
console.log('Finite cells reached from (144, 215):', finiteCount);

const fStair2 = g.dijkstraField(fl3, 258, 97);
let finite2 = 0;
for (let i = 0; i < fStair2.length; i++) if (isFinite(fStair2[i])) finite2++;
console.log('Finite cells reached from Stair 2 (258, 97):', finite2);
const zLib = fl3.zones.find(z => z.name === 'Кітапхана');
console.log('Distance from Stair 2 to Lib (279, 126):', fStair2[zLib.cy * fl3.gw + zLib.cx]);
