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
for (let y = 210; y <= 220; y++) {
  let s = '';
  for (let x = 140; x <= 150; x++) {
    const d = f[y * fl3.gw + x];
    const c = fl3.clr[y * fl3.gw + x];
    s += (isFinite(d) ? '*' : '.') + c + ' ';
  }
  console.log(`y=${y}: ${s}`);
}
