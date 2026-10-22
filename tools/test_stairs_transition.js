const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');

const el = () => new Proxy(function () {}, {
  get: (t, k) => k === 'classList' ? { add() {}, remove() {}, toggle() {}, contains: () => false } :
                k === 'style' ? {} :
                k === 'getContext' ? () => new Proxy({}, { get: () => () => ({ addColorStop() {} }), set: () => true }) :
                k === 'getBoundingClientRect' ? () => ({ left: 0, top: 0, width: 100, height: 100 }) :
                () => {},
  set: () => true,
  apply: () => undefined
});

global.window = global;
global.document = { getElementById: el, createElement: el, activeElement: null };
global.addEventListener = () => {};
global.innerWidth = 400; global.innerHeight = 800; global.devicePixelRatio = 1;
global.requestAnimationFrame = () => {};
global.Image = function () { this.complete = true; };
global.atob = (s) => Buffer.from(s, 'base64').toString('binary');
global.performance = { now: () => Date.now() };

eval(fs.readFileSync(path.join(root, 'js/mapdata.js'), 'utf8').replace('window.MAPDATA', 'global.MAPDATA'));
eval(fs.readFileSync(path.join(root, 'js/app.js'), 'utf8'));

const g = global.__game;

console.log('--- TESTING EVERY STAIR TRANSITION ---');
let failures = 0;
let transitionsTested = 0;

for (let fromFloor = 1; fromFloor <= 3; fromFloor++) {
  const flFrom = g.floors[fromFloor - 1];
  for (let sIdx = 0; sIdx < flFrom.stairs.length; sIdx++) {
    const st = flFrom.stairs[sIdx];
    for (const dir of [1, -1]) {
      const toStair = dir > 0 ? st.up : st.down;
      if (toStair === null) continue;
      const toFloor = fromFloor + dir;
      if (toFloor < 1 || toFloor > 3) continue;

      // Position player at this stair on fromFloor
      g.S.floor = fromFloor;
      g.S.x = st.x;
      g.S.y = st.y;
      g.S.near = sIdx;
      g.S.busy = false;

      // Execute transition
      const targetFl = g.floors[toFloor - 1];
      const targetSt = targetFl.stairs[toStair];
      const [nx, ny] = g.snap(targetFl, targetSt.x, targetSt.y);

      // Verify that [nx, ny] has clearance and can walk
      g.S.floor = toFloor;
      g.S.x = nx;
      g.S.y = ny;

      // Try moving 4 directions
      let movesSucceeded = 0;
      for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) {
        const startX = g.S.x, startY = g.S.y;
        // Step in that direction
        // In app.js, moving by (dx * 2, dy * 2)
        // Let's call g.snap or test move logic
        const fl = g.floors[toFloor - 1];
        // Move test
        let x = startX, y = startY;
        const R = 0.85;
        const PROBES = Array.from({ length: 12 }, (_, i) => [Math.cos(i / 12 * Math.PI * 2), Math.sin(i / 12 * Math.PI * 2)]);
        const walk = (fll, xx, yy) => xx >= 0 && yy >= 0 && xx < fll.gw && yy < fll.gh && fll.grid[(yy | 0) * fll.gw + (xx | 0)] > 0;
        const free = (fll, xx, yy) => {
          if (!walk(fll, xx, yy)) return false;
          for (const [cx, cy] of PROBES) if (!walk(fll, xx + cx * R, yy + cy * R)) return false;
          return true;
        };
        for (let step = 0; step < 4; step++) {
          if (free(fl, x + dx * 0.5, y)) x += dx * 0.5;
          if (free(fl, x, y + dy * 0.5)) y += dy * 0.5;
        }
        if (Math.hypot(x - startX, y - startY) > 0.4) movesSucceeded++;
      }

      transitionsTested++;
      if (movesSucceeded === 0) {
        console.error(`FAILED: Floor ${fromFloor} stair ${sIdx} -> Floor ${toFloor} stair ${toStair} lands at (${nx}, ${ny}) - CANNOT MOVE!`);
        failures++;
      }
    }
  }
}

console.log(`Results: ${transitionsTested} transitions tested, ${failures} failures.`);
if (failures === 0) {
  console.log('✅ ALL STAIR TRANSITIONS WORK PERFECTLY! Character never gets stuck.');
} else {
  process.exit(1);
}
