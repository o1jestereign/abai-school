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
console.log('fl3.gw:', fl3.gw, 'fl3.gh:', fl3.gh);
fl3.stairs.forEach((st, i) => {
  const idx = st.y * fl3.gw + st.x;
  console.log(`Stair ${i}: (${st.x}, ${st.y}) clr = ${fl3.clr[idx]}`);
});
const z305 = fl3.zones.find(z => z.name === '305 кабинет');
console.log('z305 cx, cy:', z305.cx, z305.cy, 'clr:', fl3.clr[z305.cy * fl3.gw + z305.cx]);
