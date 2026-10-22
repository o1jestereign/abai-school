const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const el = () => new Proxy(function () {}, { get: (t, k) => k === 'classList' ? { add() {}, remove() {}, toggle() {}, contains: () => false } : k === 'style' ? {} : k === 'getContext' ? () => new Proxy({}, { get: () => () => ({ addColorStop() {} }) , set: () => true }) : k === 'getBoundingClientRect' ? () => ({ left: 0, top: 0, width: 100, height: 100 }) : (k === 'appendChild' || k === 'addEventListener' || k === 'setPointerCapture') ? () => {} : undefined, set: () => true, apply: () => undefined });
global.window = global; global.document = { getElementById: el, createElement: el, activeElement: null };
global.addEventListener = () => {}; global.innerWidth = 400; global.innerHeight = 800; global.devicePixelRatio = 1;
global.requestAnimationFrame = () => {}; global.Image = function () { this.complete = true; };
global.atob = (s) => Buffer.from(s, 'base64').toString('binary');
global.performance = { now: () => Date.now() };
eval(fs.readFileSync(path.join(root, 'js/mapdata.js'), 'utf8').replace('window.MAPDATA', 'global.MAPDATA'));
eval(fs.readFileSync(path.join(root, 'js/app.js'), 'utf8'));
const g = global.__game;
const z = (f, n) => g.floors[f - 1].zones.find((q) => q.name === n);
console.log('start', g.S.floor, g.S.x, g.S.y);
let t0 = Date.now();
const fl = g.floors[0];
const f = g.dijkstraField(fl, g.S.x, g.S.y);
let fin = 0; for (const v of f) if (isFinite(v)) fin++;
console.log('field ms', Date.now() - t0, 'finite cells', fin, 'clr@start', fl.clr[g.S.y * fl.gw + g.S.x]);
const destinations = [
  [1, 'Асхана'],
  [1, 'Актовый зал'],
  [1, 'Орталық вестибюль / Гардероб'],
  [1, '105 кабинет'],
  [2, 'Спорт залы (Үлкен зал)'],
  [2, 'Мұғалімдер залы (Учительская)'],
  [2, '204 кабинет'],
  [2, 'Ұлдар дәретханасы 2.1'],
  [3, 'Кітапхана және оқу залы'],
  [3, 'IT зертханасы және бағдарламалау'],
  [3, '305 кабинет'],
  [3, 'Қыздар дәретханасы 3.2']
];
for (const [fo, n] of destinations) {
  t0 = Date.now();
  const zone = z(fo, n);
  if (!zone) { console.error('Zone not found:', n, 'on floor', fo); continue; }
  const r = g.planRoute(1, g.S.x, g.S.y, { floor: fo, x: zone.cx, y: zone.cy });
  console.log(n, fo, r ? r.segs.map((s) => `${s.floor}:${s.pts.length}${s.endsAtStair ? '->' + s.toFloor : ''}`).join(' | ') + ' cost ' + Math.round(r.cost) : 'NO ROUTE', Date.now() - t0, 'ms');
}
const s0 = g.floors[2].stairs[0];
const r = g.planRoute(3, s0.x, s0.y, { floor: 1, x: z(1, 'Негізгі кіреберіс').cx, y: z(1, 'Негізгі кіреберіс').cy });
console.log('3->1', r && r.segs.map((s) => `${s.floor}:${s.pts.length}->${s.toFloor}`).join(' | '));
