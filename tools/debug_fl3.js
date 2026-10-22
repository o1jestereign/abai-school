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
const z305 = fl3.zones.find(z => z.name === '305 кабинет');
const zLib = fl3.zones.find(z => z.name === 'Кітапхана');
console.log('305 кабинет:', z305);
console.log('Кітапхана:', zLib);

// Test field on Floor 3 from each stair
fl3.stairs.forEach((st, i) => {
  const f = g.dijkstraField(fl3, st.x, st.y);
  const d305 = f[z305.cy * fl3.gw + z305.cx];
  const dLib = f[zLib.cy * fl3.gw + zLib.cx];
  console.log(`Stair ${i} (${st.x}, ${st.y}): to 305 = ${d305}, to Lib = ${dLib}`);
});
