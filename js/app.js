/* Абай мектебі — 2D Indoor Navigation / Digital Twin */
(() => {
'use strict';
const D = window.MAPDATA;
const $ = (id) => document.getElementById(id);
const canvas = $('map'), ctx = canvas.getContext('2d');
const METERS_PER_CELL = 0.16;

/* ============ MAP DATA ============ */
const floors = D.floors.map((f) => {
  const bin = atob(f.grid);
  const grid = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) grid[i] = bin.charCodeAt(i);
  const o = { ...f, grid, img: new Image() };
  o.img.src = f.img;
  o.clr = clearance(grid, f.gw, f.gh);
  o.fields = new Map();
  return o;
});
const ZICON = { restroom: '🚻', stairs: '🪜', assembly: '🎭', cafe: '🍽️', exit: '🚪', library: '📚', gym: '🏀' };

function clearance(grid, w, h) { // chessboard distance to nearest wall
  const d = new Uint8Array(w * h);
  const INF = 250;
  for (let i = 0; i < d.length; i++) d[i] = grid[i] ? INF : 0;
  for (let y = 0; y < h; y++) for (let x = 0; x < w; x++) {
    const i = y * w + x; if (!d[i]) continue;
    let m = d[i];
    if (x > 0) m = Math.min(m, d[i - 1] + 1);
    if (y > 0) { m = Math.min(m, d[i - w] + 1); if (x > 0) m = Math.min(m, d[i - w - 1] + 1); if (x < w - 1) m = Math.min(m, d[i - w + 1] + 1); }
    d[i] = m;
  }
  for (let y = h - 1; y >= 0; y--) for (let x = w - 1; x >= 0; x--) {
    const i = y * w + x; if (!d[i]) continue;
    let m = d[i];
    if (x < w - 1) m = Math.min(m, d[i + 1] + 1);
    if (y < h - 1) { m = Math.min(m, d[i + w] + 1); if (x < w - 1) m = Math.min(m, d[i + w + 1] + 1); if (x > 0) m = Math.min(m, d[i + w - 1] + 1); }
    d[i] = m;
  }
  return d;
}

/* ============ STATE ============ */
/* ============ COLLISION / MOVEMENT ============ */
const R = 0.8; // player collision radius (cells, ~0.5m diameter, cleanly passes through 3-cell doors)
const PROBES = Array.from({ length: 16 }, (_, i) => [Math.cos(i / 16 * Math.PI * 2), Math.sin(i / 16 * Math.PI * 2)]);
const S = {
  floor: 1, x: 0, y: 0, ang: -Math.PI / 2, tAng: -Math.PI / 2,
  cam: { x: 0, y: 0, zoom: 4.2, follow: true },
  input: { x: 0, y: 0 }, keys: {},
  route: null, target: null, lastRouteAt: 0, lastRoutePos: { x: -99, y: -99, f: 0 },
  zoneId: 0, near: null, t: 0, busy: false,
};
const F = () => floors[S.floor - 1];
const zoneAt = (f, x, y) => { const fl = floors[f - 1]; const v = fl.grid[(y | 0) * fl.gw + (x | 0)]; return v ? fl.zones[v - 1] : null; };
const walk = (fl, x, y) => x >= 0 && y >= 0 && x < fl.gw && y < fl.gh && fl.grid[(y | 0) * fl.gw + (x | 0)] > 0;

function free(fl, x, y) {
  if (!walk(fl, x, y)) return false;
  for (const [cx, cy] of PROBES) if (!walk(fl, x + cx * R, y + cy * R)) return false;
  return true;
}

function snap(fl, x, y) {
  x = Math.round(x); y = Math.round(y);
  for (const minClr of [3, 2, 1]) {
    let best = null, bd = 1e9;
    for (let r = 0; r < 50; r++) {
      for (let yy = y - r; yy <= y + r; yy++) for (let xx = x - r; xx <= x + r; xx++) {
        if (Math.max(Math.abs(xx - x), Math.abs(yy - y)) !== r) continue;
        if (xx < 0 || yy < 0 || xx >= fl.gw || yy >= fl.gh) continue;
        if (fl.clr[yy * fl.gw + xx] >= minClr && free(fl, xx, yy)) {
          const d = (xx - x) ** 2 + (yy - y) ** 2;
          if (d < bd) { bd = d; best = [xx, yy]; }
        }
      }
      if (best) return best;
    }
  }
  return [x, y];
}

function move(dx, dy) {
  const fl = F();
  const steps = Math.max(1, Math.ceil(Math.hypot(dx, dy) / 0.35));
  const sx = dx / steps, sy = dy / steps;
  for (let i = 0; i < steps; i++) {
    if (free(fl, S.x + sx, S.y)) S.x += sx;           // slide along walls: axes resolved separately
    if (free(fl, S.x, S.y + sy)) S.y += sy;
  }
}

/* ============ PATHFINDING ============ */
class Heap { // binary min-heap on typed arrays (fast, no per-push allocation)
  constructor(cap = 1 << 16) { this.k = new Float64Array(cap); this.v = new Int32Array(cap); this.n = 0; }
  push(key, val) { if (this.n === this.k.length) { const k = new Float64Array(this.n * 2), v = new Int32Array(this.n * 2); k.set(this.k); v.set(this.v); this.k = k; this.v = v; }
    const k = this.k, v = this.v; let i = this.n++;
    while (i > 0) { const p = (i - 1) >> 1; if (k[p] <= key) break; k[i] = k[p]; v[i] = v[p]; i = p; } k[i] = key; v[i] = val; }
  pop() { const k = this.k, v = this.v; this.pk = k[0]; this.pv = v[0]; const n = --this.n; const lk = k[n], lv = v[n];
    if (n) { let i = 0; for (;;) { let c = 2 * i + 1; if (c >= n) break; if (c + 1 < n && k[c + 1] < k[c]) c++; if (k[c] >= lk) break; k[i] = k[c]; v[i] = v[c]; i = c; } k[i] = lk; v[i] = lv; } }
  get size() { return this.n; }
}
const N8 = [[1, 0, 1], [-1, 0, 1], [0, 1, 1], [0, -1, 1], [1, 1, 1.4142], [1, -1, 1.4142], [-1, 1, 1.4142], [-1, -1, 1.4142]];
const OK_CLR = 1;
function costMap(fl) { // per-cell step cost: cells hugging walls are pricier so routes stay mid-corridor
  if (fl.cost) return fl.cost; const c = new Float32Array(fl.clr.length);
  for (let i = 0; i < c.length; i++) { const d = fl.clr[i]; c[i] = d >= 6 ? 1 : 1 + (6 - d) * 1.2; } return (fl.cost = c);
}
const DX = N8.map((n) => n[0]), DY = N8.map((n) => n[1]), DC = N8.map((n) => n[2]);
function dijkstraField(fl, sx, sy, stops) {
  const { gw, gh, clr } = fl; const cm = costMap(fl);
  const dist = new Float32Array(gw * gh).fill(Infinity);
  const h = new Heap(); const s = sy * gw + sx; dist[s] = 0; h.push(0, s);
  let remaining = 0; const want = stops ? new Set(stops) : null; if (want) remaining = want.size;
  while (h.size) {
    h.pop(); const d = h.pk, i = h.pv; if (d > dist[i]) continue;
    if (want && want.has(i)) { want.delete(i); if (--remaining === 0) break; }
    const x = i % gw, y = (i / gw) | 0;
    for (let k = 0; k < 8; k++) {
      const dx = DX[k], dy = DY[k]; const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= gw || ny >= gh) continue;
      const j = ny * gw + nx; if (clr[j] < OK_CLR) continue;
      if (dx && dy && (clr[y * gw + nx] < OK_CLR || clr[ny * gw + x] < OK_CLR)) continue;
      const nd = d + DC[k] * cm[j];
      if (nd < dist[j]) { dist[j] = nd; h.push(dist[j], j); }
    }
  }
  return dist;
}
function descend(fl, dist, tx, ty) { // follow gradient from target back to field source
  const { gw, gh } = fl; const pts = [[tx, ty]]; let x = tx, y = ty, guard = 20000;
  while (dist[y * gw + x] > 0 && guard-- > 0) {
    let bx = x, by = y, bd = dist[y * gw + x];
    for (const [dx, dy] of N8) { const nx = x + dx, ny = y + dy; if (nx < 0 || ny < 0 || nx >= gw || ny >= gh) continue;
      if (dx && dy && (fl.clr[y * gw + nx] < OK_CLR || fl.clr[ny * gw + x] < OK_CLR)) continue;
      const d = dist[ny * gw + nx]; if (d < bd) { bd = d; bx = nx; by = ny; } }
    if (bx === x && by === y) break; x = bx; y = by; pts.push([x, y]);
  }
  return pts.reverse();
}
function los(fl, a, b) {
  const n = Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) * 1.5);
  for (let i = 0; i <= n; i++) { const t = i / n; const x = Math.round(a[0] + (b[0] - a[0]) * t), y = Math.round(a[1] + (b[1] - a[1]) * t);
    if (fl.clr[y * fl.gw + x] < 1) return false; }
  return true;
}
function simplify(fl, pts) {
  if (pts.length < 3) return pts; const out = [pts[0]]; let i = 0;
  while (i < pts.length - 1) { let j = pts.length - 1; while (j > i + 1 && !los(fl, pts[i], pts[j])) j--; out.push(pts[j]); i = j; }
  return out;
}

/* Multi-floor routing.
   - one Dijkstra field from the player (current floor)
   - one Dijkstra field from the target (target floor)
   - stair<->stair costs inside a floor come precomputed (floor.dm, built from the same grid by tools/build_data.py)
   - stair links between floors cost a fixed penalty. Only the first leg is drawn; after changing floors the route is re-planned. */
const STAIR_PENALTY = 14;
function planRoute(floor, px, py, tgt) {
  const flS = floors[floor - 1], flT = floors[tgt.floor - 1];
  const [sx, sy] = snap(flS, px, py), [tx, ty] = snap(flT, tgt.x, tgt.y);
  const stairCell = (f, i) => { const fl = floors[f - 1]; const st = fl.stairs[i]; return st.y * fl.gw + st.x; };
  const fieldS = dijkstraField(flS, sx, sy, flS.stairs.map((_, i) => stairCell(floor, i)).concat(floor === tgt.floor ? [ty * flS.gw + tx] : []));
  if (floor === tgt.floor) { const d = fieldS[ty * flS.gw + tx]; if (isFinite(d)) return { segs: [{ floor, pts: simplify(flS, descend(flS, fieldS, tx, ty)), endsAtStair: false, toFloor: null }], cost: d }; }
  const fieldT = dijkstraField(flT, tx, ty, flT.stairs.map((_, i) => stairCell(tgt.floor, i)));
  // Dijkstra over stair nodes
  const ids = []; floors.forEach((fl, fi) => fl.stairs.forEach((_, i) => ids.push([fi + 1, i])));
  const key = (f, i) => floors.slice(0, f - 1).reduce((a, fl) => a + fl.stairs.length, 0) + i;
  const dist = new Float64Array(ids.length).fill(Infinity), prev = new Int32Array(ids.length).fill(-1), done = new Uint8Array(ids.length);
  flS.stairs.forEach((_, i) => { const d = fieldS[stairCell(floor, i)]; if (isFinite(d)) dist[key(floor, i)] = d; });
  let bestEnd = -1, bestCost = Infinity;
  for (;;) {
    let u = -1, ud = Infinity; for (let n = 0; n < ids.length; n++) if (!done[n] && dist[n] < ud) { ud = dist[n]; u = n; }
    if (u < 0) break; done[u] = 1; const [f, i] = ids[u]; const fl = floors[f - 1], st = fl.stairs[i];
    if (f === tgt.floor) { const dt = fieldT[stairCell(f, i)]; if (isFinite(dt) && ud + dt < bestCost) { bestCost = ud + dt; bestEnd = u; } }
    fl.dm[i].forEach((c, j) => { if (c < 0 || j === i) return; const v = key(f, j); if (ud + c < dist[v]) { dist[v] = ud + c; prev[v] = u; } });
    if (st.up !== null && f < 3) { const v = key(f + 1, st.up); if (ud + STAIR_PENALTY < dist[v]) { dist[v] = ud + STAIR_PENALTY; prev[v] = u; } }
    if (st.down !== null && f > 1) { const v = key(f - 1, st.down); if (ud + STAIR_PENALTY < dist[v]) { dist[v] = ud + STAIR_PENALTY; prev[v] = u; } }
    if (ud > bestCost) break;
  }
  if (bestEnd < 0) return null;
  const chain = []; for (let n = bestEnd; n >= 0; n = prev[n]) chain.unshift(ids[n]);
  // first stair on the player's floor that the chain leaves through (walk to it directly)
  let k = 0; while (k + 1 < chain.length && chain[k + 1][0] === floor && chain[k][0] === floor) k++;
  const [sf, si] = chain[k]; const st = floors[sf - 1].stairs[si];
  const nextFloor = chain[k + 1] ? chain[k + 1][0] : tgt.floor;
  const pts = simplify(flS, descend(flS, fieldS, st.x, st.y));
  return { segs: [{ floor, pts, endsAtStair: true, toFloor: nextFloor, stairIdx: si }], cost: bestCost + STAIR_PENALTY * Math.abs(tgt.floor - floor) };
}
function segLen(pts) { let L = 0; const cum = [0]; for (let i = 1; i < pts.length; i++) { L += Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]); cum.push(L); } return { L, cum }; }

function setTarget(t) {
  S.target = t; S.lastRouteAt = 0; S.lastRoutePos = { x: -99, y: -99, f: 0 };
  refreshRoute(true);
}
function clearRoute() { S.target = null; S.route = null; $('route-card').classList.add('hidden'); $('hint').classList.add('hidden'); updateStairsUI(true); }
/* index of the path segment closest to (x,y) and the distance to it */
function nearestSeg(pts, x, y) {
  let bi = 0, bd = Infinity;
  for (let i = 0; i < pts.length - 1; i++) {
    const [ax, ay] = pts[i], [bx, by] = pts[i + 1]; const dx = bx - ax, dy = by - ay; const l2 = dx * dx + dy * dy || 1;
    const t = Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / l2)); const d = Math.hypot(ax + dx * t - x, ay + dy * t - y);
    if (d < bd) { bd = d; bi = i; }
  }
  return { i: bi, d: bd };
}
function refreshRoute(force) {
  if (!S.target) return;
  const now = performance.now();
  if (!force) {
    const seg = S.route && S.route.segs[0];
    const onPath = seg && seg.floor === S.floor && nearestSeg(seg.pts, S.x, S.y).d < 6;
    if (onPath && now - S.lastRouteAt < 4000) return;   // cheap: keep following the existing path
    if (now - S.lastRouteAt < 400) return;
  }
  S.lastRouteAt = now;
  const r = planRoute(S.floor, S.x, S.y, S.target);
  if (!r) { S.route = null; showToast('Маршрут табылмады 😕'); S.target = null; $('route-card').classList.add('hidden'); return; }
  S.route = r; const seg = r.segs[0]; seg.m = segLen(seg.pts);
  $('route-card').classList.remove('hidden');
  $('route-title').textContent = '➜ ' + S.target.label;
  const crossing = seg.endsAtStair;
  $('route-sub').textContent = `${Math.round(r.cost * METERS_PER_CELL)} м шамамен · ${S.target.floor}-қабат`;
  const hint = $('hint');
  if (crossing) {
    const word = seg.toFloor > S.floor ? 'көтеріліңіз' : 'түсіңіз';
    hint.textContent = `Алдымен жақын маңдағы баспалдақпен ${S.target.floor}-қабатқа ${word} 🪜`;
    hint.classList.remove('hidden');
  } else hint.classList.add('hidden');
  updateStairsUI(true);
}

/* ============ UI: BANNER, STAIRS, TOAST ============ */
let lastBanner = '';
function updateBanner() {
  const z = zoneAt(S.floor, S.x, S.y);
  S.zoneId = z ? z.id : 0;
  const txt = `📍 Сіз қазір: ${z ? z.at : 'Белгісіз аймақтасыз'} (${S.floor}-қабат)`;
  if (txt !== lastBanner) { $('location-text').textContent = txt; lastBanner = txt; }
}
function nearStair() {
  const fl = F(); let best = null, bd = 11;
  fl.stairs.forEach((s, i) => { const d = Math.hypot(s.x - S.x, s.y - S.y); if (d < bd) { bd = d; best = i; } });
  return best;
}
let stairKey = '';
function updateStairsUI(force) {
  const i = nearStair(); const fl = F(); const st = i === null ? null : fl.stairs[i];
  const canUp = st && st.up !== null && S.floor < 3, canDown = st && st.down !== null && S.floor > 1;
  const seg = S.route && S.route.segs[0];
  const key = `${S.floor}|${i}|${canUp}|${canDown}|${seg ? seg.toFloor : ''}`;
  if (key === stairKey && !force) return; stairKey = key;
  S.near = i;
  const p = $('stairs-panel');
  if (i === null || (!canUp && !canDown)) { p.classList.add('hidden'); return; }
  p.classList.remove('hidden');
  const up = $('btn-up'), dn = $('btn-down');
  up.classList.toggle('hidden', !canUp); dn.classList.toggle('hidden', !canDown);
  up.textContent = `🔼 Жоғарғы қабатқа шығу (${S.floor + 1} қабат)`;
  dn.textContent = `🔽 Төменгі қабатқа түсу (${S.floor - 1} қабат)`;
  const rec = seg && seg.endsAtStair ? seg.toFloor : null;
  if (rec && rec > S.floor) up.textContent = `🔼 ${S.floor + 1}-қабатқа шығу`;
  if (rec && rec < S.floor) dn.textContent = `🔽 ${S.floor - 1}-қабатқа түсу`;
  up.classList.toggle('rec', !!rec && rec > S.floor);
  dn.classList.toggle('rec', !!rec && rec < S.floor);
}
let toastT;
function showToast(msg, ms = 2400) { const t = $('toast'); t.textContent = msg; t.classList.remove('hidden'); clearTimeout(toastT); toastT = setTimeout(() => t.classList.add('hidden'), ms); }

function changeFloor(dir) {
  if (S.busy || S.near === null) return;
  const fl = F(); const st = fl.stairs[S.near]; const to = dir > 0 ? st.up : st.down; if (to === null) return;
  const nf = S.floor + dir; S.busy = true;
  S.keys = {}; S.input.x = 0; S.input.y = 0;
  if (document.activeElement && typeof document.activeElement.blur === 'function') document.activeElement.blur();
  $('fade-text').textContent = `${nf}-ҚАБАТ`; $('fade').classList.add('on');
  setTimeout(() => {
    try {
      S.floor = nf; const ns = floors[nf - 1].stairs[to]; const [x, y] = snap(floors[nf - 1], ns.x, ns.y);
      S.x = x; S.y = y; S.cam.x = x; S.cam.y = y; updateFloorChip();
      refreshRoute(true); updateBanner(); updateStairsUI(true);
    } catch (err) {
      console.error('Stair change error:', err);
    } finally {
      setTimeout(() => {
        $('fade').classList.remove('on');
        S.busy = false;
        S.keys = {}; S.input.x = 0; S.input.y = 0;
      }, 280);
    }
  }, 420);
}
function updateFloorChip() {
  for (let f = 1; f <= 3; f++) {
    const b = $(`fbtn-${f}`);
    if (b) b.classList.toggle('active', f === S.floor);
  }
}
[1, 2, 3].forEach((f) => {
  const b = $(`fbtn-${f}`);
  if (b) {
    b.onclick = () => {
      if (S.floor === f) {
        S.cam.x = S.x; S.cam.y = S.y; S.cam.follow = true;
        return;
      }
      const hall = findZone(f, 'Орталық холл') || floors[f - 1].zones[0];
      const tx = hall ? hall.cx : floors[f - 1].gw / 2;
      const ty = hall ? hall.cy : floors[f - 1].gh / 2;
      teleport(f, tx, ty, `${f}-қабатқа ауыстыңыз`);
    };
  }
});
$('btn-up').onclick = () => changeFloor(1);
$('btn-down').onclick = () => changeFloor(-1);

/* ============ SEARCH ============ */
const norm = (s) => s.toLowerCase().replace(/ё/g, 'е').replace(/[ә]/g, 'а').replace(/[іı]/g, 'и').replace(/[ңн]/g, 'н').replace(/[ғг]/g, 'г').replace(/[қк]/g, 'к').replace(/[өо]/g, 'о').replace(/[үұу]/g, 'у').replace(/һ/g, 'х').replace(/-ші/g, '').replace(/[^a-zа-я0-9 ]/g, ' ').replace(/\s+/g, ' ').trim();
const ENTRIES = [];
floors.forEach((fl) => fl.zones.forEach((z) => {
  if (z.type === 'stairs') return;
  ENTRIES.push({ floor: fl.floor, zone: z, name: z.name, key: norm(z.name + ' ' + (z.type === 'restroom' ? 'дәретхана туалет wc' : z.type === 'cafe' ? 'столовая асхана' : z.type === 'room' ? 'кабинет сынып' : '')), icon: ZICON[z.type] || (z.type === 'room' ? '🚪' : z.type === 'corridor' ? '🧭' : '🏛️') });
}));
const sInput = $('search-input'), sRes = $('search-results');
function searchList(q) {
  const nq = norm(q); const toks = nq.split(' ').filter(Boolean);
  let out = [];
  if (!toks.length) {
    out = ENTRIES.filter((e) => e.zone.type !== 'room' && e.zone.type !== 'corridor').slice(0, 30);
  } else {
    out = ENTRIES.filter((e) => toks.every((t) => e.key.includes(t)));
    if (/^[0-9]+$/.test(nq)) out.sort((a, b) => (a.zone.num == nq ? -1 : 0) - (b.zone.num == nq ? -1 : 0));
  }
  out.sort((a, b) => (a.floor === S.floor ? 0 : 1) - (b.floor === S.floor ? 0 : 1));
  const extra = [];
  if (!toks.length || 'дәретхана туалет wc'.split(' ').some((w) => norm(w).startsWith(toks[0] || '~')) ) extra.push({ nearest: 'restroom', name: 'Ең жақын дәретхана', icon: '🚻', floor: 0 });
  return [...extra, ...out].slice(0, 40);
}
let sActive = -1, sCur = [];
let isTouchScrolling = false, touchStartY = 0, touchStartX = 0;

sRes.addEventListener('touchstart', (ev) => {
  if (ev.touches.length > 0) {
    touchStartX = ev.touches[0].clientX;
    touchStartY = ev.touches[0].clientY;
    isTouchScrolling = false;
  }
}, { passive: true });

sRes.addEventListener('touchmove', (ev) => {
  if (ev.touches.length > 0) {
    const dx = Math.abs(ev.touches[0].clientX - touchStartX);
    const dy = Math.abs(ev.touches[0].clientY - touchStartY);
    if (dy > 6 || dx > 6) isTouchScrolling = true;
  }
}, { passive: true });

function renderResults() {
  sCur = searchList(sInput.value); sActive = -1; sRes.innerHTML = '';
  if (!sCur.length) sRes.innerHTML = '<li class="empty">Ештеңе табылмады</li>';
  sCur.forEach((e) => {
    const li = document.createElement('li');
    li.innerHTML = `<span class="r-ico">${e.icon}</span><span class="r-name">${e.name}</span>` + (e.floor ? `<span class="r-floor ${e.floor === S.floor ? 'here' : ''}">${e.floor}-қабат</span>` : '<span class="r-floor here">жақын</span>');
    li.addEventListener('click', (ev) => { ev.preventDefault(); pick(e); });
    li.addEventListener('touchend', (ev) => {
      if (isTouchScrolling) return; // Do not select if user was scrolling!
      ev.preventDefault();
      pick(e);
    });
    sRes.appendChild(li);
  });
  sRes.classList.remove('hidden');
}
function nearestOfType(type) {
  let best = null, bd = 1e9;
  ENTRIES.filter((e) => e.zone.type === type).forEach((e) => { const d = Math.abs(e.floor - S.floor) * 400 + (e.floor === S.floor ? Math.hypot(e.zone.cx - S.x, e.zone.cy - S.y) : 0); if (d < bd) { bd = d; best = e; } });
  return best;
}
function pick(e) {
  if (e.nearest) e = nearestOfType(e.nearest);
  sInput.value = e.name; sRes.classList.add('hidden'); sInput.blur(); $('search-clear').classList.remove('hidden');
  setTarget({ floor: e.floor, x: e.zone.cx, y: e.zone.cy, label: `${e.name} (${e.floor}-қабат)`, name: e.name });
}
sInput.addEventListener('focus', renderResults);
sInput.addEventListener('input', () => { renderResults(); $('search-clear').classList.toggle('hidden', !sInput.value); });
sInput.addEventListener('keydown', (ev) => {
  if (ev.key === 'ArrowDown' || ev.key === 'ArrowUp') { ev.preventDefault(); sActive = (sActive + (ev.key === 'ArrowDown' ? 1 : -1) + sCur.length) % sCur.length;
    [...sRes.children].forEach((c, i) => c.classList.toggle('active', i === sActive)); }
  else if (ev.key === 'Enter') { const e = sCur[Math.max(0, sActive)]; if (e) pick(e); }
  ev.stopPropagation();
});

// Dismiss search only when tapping outside of search box
document.addEventListener('pointerdown', (ev) => {
  const box = $('search-box');
  if (box && !box.contains(ev.target)) {
    sRes.classList.add('hidden');
  }
});

$('search-clear').onclick = () => { sInput.value = ''; $('search-clear').classList.add('hidden'); clearRoute(); sInput.focus(); };
$('route-cancel').onclick = () => { sInput.value = ''; $('search-clear').classList.add('hidden'); clearRoute(); };

/* ============ TELEPORT / QR ============ */
function teleport(floor, x, y, label) {
  const fl = floors[floor - 1]; const [sx, sy] = snap(fl, x, y);
  S.floor = floor; S.x = sx; S.y = sy; S.cam.x = sx; S.cam.y = sy; S.cam.follow = true;
  S.keys = {}; S.input.x = 0; S.input.y = 0;
  updateFloorChip(); updateBanner(); updateStairsUI(true); if (S.target) refreshRoute(true);
  if (label) showToast('⚡ ' + label);
}
function findZone(floor, name) { const fl = floors[floor - 1]; const n = norm(name); return fl.zones.find((z) => z.name === name) || fl.zones.find((z) => norm(z.name) === n || norm(z.name).includes(n)); }
const PRESETS = [
  ['Негізгі кіреберіс (1-қабат)', 1, 'Негізгі кіреберіс'],
  ['Орталық вестибюль / Гардероб', 1, 'Орталық вестибюль / Гардероб'],
  ['Актовый зал (1-қабат)', 1, 'Актовый зал'],
  ['Асхана (Батыс қанат)', 1, 'Асхана'],
  ['105 кабинет', 1, '105 кабинет'],
  ['Спорт залы (2-қабат)', 2, 'Спорт залы (Үлкен зал)'],
  ['Мұғалімдер залы (2-қабат)', 2, 'Мұғалімдер залы (Учительская)'],
  ['204 кабинет', 2, '204 кабинет'],
  ['Кітапхана және оқу залы (3-қабат)', 3, 'Кітапхана және оқу залы'],
  ['IT зертханасы (3-қабат)', 3, 'IT зертханасы және бағдарламалау'],
  ['Робототехника және STEM (3-қабат)', 3, 'Робототехника және STEM орталығы'],
  ['305 кабинет', 3, '305 кабинет'],
];
PRESETS.forEach(([label, f, name]) => { const b = document.createElement('button'); b.textContent = '📍 ' + label;
  b.onclick = () => { const z = findZone(f, name); if (z) { teleport(f, z.cx, z.cy, label); closeQR(); } }; $('sim-list').appendChild(b); });
function handleSpotName(spot) {
  if (!spot) return false;
  const ALIASES = {
    'entrance': { floor: 1, name: 'Орталық вестибюль / Гардероб', label: 'Басты кіреберіс' },
    'kireberis': { floor: 1, name: 'Орталық вестибюль / Гардероб', label: 'Басты кіреберіс' },
    'vestibule': { floor: 1, name: 'Орталық вестибюль / Гардероб', label: 'Орталық вестибюль' },
    'cafe': { floor: 1, name: 'Асхана', label: 'Мектеп асханасы' },
    'canteen': { floor: 1, name: 'Асхана', label: 'Мектеп асханасы' },
    'asxana': { floor: 1, name: 'Асхана', label: 'Мектеп асханасы' },
    'ashana': { floor: 1, name: 'Асхана', label: 'Мектеп асханасы' },
    'assembly': { floor: 1, name: 'Актовый зал', label: 'Актовый зал' },
    'aktovyi': { floor: 1, name: 'Актовый зал', label: 'Актовый зал' },
    'akt': { floor: 1, name: 'Актовый зал', label: 'Актовый зал' },
    'gym': { floor: 2, name: 'Спорт залы (Үлкен зал)', label: 'Спорт залы' },
    'sport': { floor: 2, name: 'Спорт залы (Үлкен зал)', label: 'Спорт залы' },
    'sportzal': { floor: 2, name: 'Спорт залы (Үлкен зал)', label: 'Спорт залы' },
    'library': { floor: 3, name: 'Кітапхана және оқу залы', label: 'Кітапхана' },
    'kitapxana': { floor: 3, name: 'Кітапхана және оқу залы', label: 'Кітапхана' }
  };

  const key = String(spot).toLowerCase().trim();
  if (ALIASES[key]) {
    const a = ALIASES[key];
    const z = findZone(a.floor, a.name);
    if (z) {
      teleport(a.floor, z.cx, z.cy, `${a.label} (${a.floor}-қабат)`);
      return true;
    }
  }

  // Search by zone name or room number
  for (let f = 1; f <= 3; f++) {
    const z = findZone(f, spot);
    if (z) {
      teleport(f, z.cx, z.cy, `${z.name} (${f}-қабат)`);
      return true;
    }
  }
  return false;
}

function handleQR(text) {
  if (!text) return false;
  text = String(text).trim();

  // 1. If scanned text is a full URL (e.g. https://abai-school.vercel.app/?spot=cafe)
  if (text.includes('?') || text.includes('#') || text.startsWith('http')) {
    try {
      const url = new URL(text, window.location.origin);
      const spot = url.searchParams.get('spot') || url.searchParams.get('start') || url.searchParams.get('room') || url.searchParams.get('qr') || url.hash.replace('#', '');
      const to = url.searchParams.get('to') || url.searchParams.get('target');
      if (spot && handleSpotName(spot)) {
        if (to) {
          setTimeout(() => {
            for (let f = 1; f <= 3; f++) {
              const dest = findZone(f, to);
              if (dest) { setTarget(f, dest); break; }
            }
          }, 600);
        }
        return true;
      }
    } catch (e) {
      const m = text.match(/[?&](?:spot|start|room)=([^&#]+)/);
      if (m && handleSpotName(decodeURIComponent(m[1]))) return true;
    }
  }

  // 2. If it is JSON
  let obj = null;
  try { obj = JSON.parse(text); } catch (e) {}
  if (obj && typeof obj === 'object') {
    const floor = Number(obj.floor) || S.floor;
    if (obj.room) {
      const z = findZone(floor, String(obj.room));
      if (z) { teleport(floor, z.cx, z.cy, `${obj.room} (${floor}-қабат)`); return true; }
    } else if (obj.x != null && obj.y != null) {
      teleport(floor, Number(obj.x), Number(obj.y), `${floor}-қабат · QR орны`);
      return true;
    }
  }

  // 3. Fallback: plain spot name or classroom number
  return handleSpotName(text);
}

let qrScanner = null;
let isScanning = false;

async function stopCamera() {
  if (qrScanner && isScanning) {
    try {
      await qrScanner.stop();
    } catch (e) {}
  }
  isScanning = false;
  const btn = $('qr-start');
  if (btn) {
    btn.textContent = 'Камераны қосу';
    btn.style.background = '';
    btn.style.color = '';
    btn.disabled = false;
  }
}

async function closeQR() {
  await stopCamera();
  $('qr-modal').classList.add('hidden');
}

$('qr-btn').onclick = () => {
  $('qr-modal').classList.remove('hidden');
  $('qr-status').textContent = 'Камераны іске қосу үшін батырманы басыңыз';
};
$('qr-close').onclick = closeQR;
$('qr-modal').addEventListener('pointerdown', (e) => {
  if (e.target.id === 'qr-modal') closeQR();
});

$('qr-start').onclick = async () => {
  const statusEl = $('qr-status');
  const btnStart = $('qr-start');

  if (isScanning) {
    await stopCamera();
    statusEl.textContent = 'Камера тоқтатылды';
    return;
  }

  if (!window.Html5Qrcode) {
    statusEl.textContent = '⚠️ Сканер кітапханасы табылмады. Төмендегі жылдам тест нүктелерін басыңыз.';
    return;
  }

  statusEl.textContent = '⏳ Камера қосылуда, рұқсат беріңіз…';
  btnStart.textContent = 'Қосылуда…';
  btnStart.disabled = true;

  try {
    if (!qrScanner) {
      qrScanner = new Html5Qrcode('qr-reader');
    }

    const config = {
      fps: 15,
      qrbox: (viewfinderWidth, viewfinderHeight) => {
        const edge = Math.min(viewfinderWidth, viewfinderHeight);
        const size = Math.floor(edge * 0.75);
        return { width: Math.max(160, Math.min(size, 260)), height: Math.max(160, Math.min(size, 260)) };
      },
      aspectRatio: 1.0
    };

    const onScanSuccess = (decodedText) => {
      if (navigator.vibrate) try { navigator.vibrate(80); } catch (e) {}
      if (handleQR(decodedText)) {
        closeQR();
      } else {
        statusEl.innerHTML = `⚠️ Белгісіз QR: <span style="font-size:11px">${decodedText.slice(0, 45)}</span>`;
      }
    };

    // Camera selection strategy: environment (back camera) with progressive fallbacks
    try {
      await qrScanner.start({ facingMode: { exact: "environment" } }, config, onScanSuccess, () => {});
    } catch (e1) {
      try {
        await qrScanner.start({ facingMode: "environment" }, config, onScanSuccess, () => {});
      } catch (e2) {
        try {
          const cameras = await Html5Qrcode.getCameras();
          if (cameras && cameras.length > 0) {
            // Pick last camera (usually back/environment camera on phones)
            const camId = cameras[cameras.length - 1].id;
            await qrScanner.start(camId, config, onScanSuccess, () => {});
          } else {
            await qrScanner.start({}, config, onScanSuccess, () => {});
          }
        } catch (e3) {
          // Final fallback to user facing camera
          await qrScanner.start({ facingMode: "user" }, config, onScanSuccess, () => {});
        }
      }
    }

    isScanning = true;
    statusEl.innerHTML = '🟢 Камера қосылды! QR-кодты шаршыға көрсетіңіз';
    btnStart.textContent = '⏹ Камераны өшіру';
    btnStart.style.background = 'linear-gradient(135deg, #ef4444, #dc2626)';
    btnStart.style.color = '#fff';
    btnStart.disabled = false;

  } catch (err) {
    console.error('Camera error:', err);
    statusEl.innerHTML = `⚠️ Камера ашылмады (${err.message || 'Рұқсат берілмеді'}). Төмендегі тест нүктелерін басыңыз.`;
    btnStart.textContent = 'Қайта қосып көру';
    btnStart.style.background = '';
    btnStart.style.color = '';
    btnStart.disabled = false;
    isScanning = false;
  }
};

/* ============ INPUT: JOYSTICK, KEYS, CAMERA ============ */
const joy = $('joystick'), knob = $('joy-knob'); let joyId = null;
function joyMove(e) { const r = joy.getBoundingClientRect(); let dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
  const max = r.width / 2 - 14, len = Math.hypot(dx, dy); const k = len > max ? max / len : 1; dx *= k; dy *= k;
  knob.style.transform = `translate(${dx}px,${dy}px)`; const m = Math.min(1, len / max); const dead = m < 0.12 ? 0 : m; S.input.x = (dx / max) * (dead ? 1 : 0) ; S.input.y = (dy / max) * (dead ? 1 : 0); }
joy.addEventListener('pointerdown', (e) => { joyId = e.pointerId; joy.setPointerCapture(joyId); knob.classList.add('drag'); joyMove(e); S.cam.follow = true; });
joy.addEventListener('pointermove', (e) => { if (e.pointerId === joyId) joyMove(e); });
const joyEnd = (e) => { if (e.pointerId !== joyId) return; joyId = null; knob.classList.remove('drag'); knob.style.transform = ''; S.input.x = S.input.y = 0; };
joy.addEventListener('pointerup', joyEnd); joy.addEventListener('pointercancel', joyEnd);
addEventListener('keydown', (e) => { if (document.activeElement === sInput) return; S.keys[e.key.toLowerCase()] = true; if (e.key.startsWith('Arrow')) e.preventDefault(); if (e.key === 'e' || e.key === 'Enter') { const u = !$('btn-up').classList.contains('hidden'); const d = !$('btn-down').classList.contains('hidden'); if ($('stairs-panel').classList.contains('hidden')) return; if (u && (!d || $('btn-up').classList.contains('rec'))) changeFloor(1); else if (d) changeFloor(-1); } });
addEventListener('keyup', (e) => { S.keys[e.key.toLowerCase()] = false; });
function keyVec() { const k = S.keys; const x = (k['d'] || k['arrowright'] || k['в'] ? 1 : 0) - (k['a'] || k['arrowleft'] || k['ф'] ? 1 : 0);
  const y = (k['s'] || k['arrowdown'] || k['ы'] ? 1 : 0) - (k['w'] || k['arrowup'] || k['ц'] ? 1 : 0); const l = Math.hypot(x, y) || 1; return [x / l, y / l]; }

const zoomBy = (f) => { S.cam.zoom = Math.max(1.6, Math.min(12, S.cam.zoom * f)); };
$('zoom-in').onclick = () => zoomBy(1.25); $('zoom-out').onclick = () => zoomBy(0.8);
$('recenter').onclick = () => { S.cam.follow = true; };
canvas.addEventListener('wheel', (e) => { e.preventDefault(); zoomBy(e.deltaY < 0 ? 1.1 : 0.9); }, { passive: false });
const ptrs = new Map(); let pinch0 = 0, zoom0 = 1;
canvas.addEventListener('pointerdown', (e) => { canvas.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, [e.clientX, e.clientY]); if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; pinch0 = Math.hypot(a[0] - b[0], a[1] - b[1]); zoom0 = S.cam.zoom; } });
canvas.addEventListener('pointermove', (e) => { if (!ptrs.has(e.pointerId)) return; const prev = ptrs.get(e.pointerId); ptrs.set(e.pointerId, [e.clientX, e.clientY]);
  if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; S.cam.zoom = Math.max(1.6, Math.min(12, zoom0 * Math.hypot(a[0] - b[0], a[1] - b[1]) / pinch0)); }
  else if (ptrs.size === 1) { S.cam.follow = false; S.cam.x -= (e.clientX - prev[0]) / S.cam.zoom; S.cam.y -= (e.clientY - prev[1]) / S.cam.zoom; } });
const ptrEnd = (e) => { ptrs.delete(e.pointerId); }; canvas.addEventListener('pointerup', ptrEnd); canvas.addEventListener('pointercancel', ptrEnd);

/* ============ RENDER ============ */
let W = 0, H = 0, DPR = 1;
function resize() { DPR = Math.min(2, devicePixelRatio || 1); W = innerWidth; H = innerHeight; canvas.width = W * DPR; canvas.height = H * DPR; }
addEventListener('resize', resize); resize();

function drawRoute(z, t) {
  const seg = S.route && S.route.segs[0]; if (!seg || seg.floor !== S.floor) return;
  const pts = seg.pts; if (pts.length < 2) return;
  // trim passed part
  const ns = nearestSeg(pts, S.x, S.y);
  const full = [[S.x, S.y], ...pts.slice(ns.i + 1)]; seg.m = segLen(full);
  ctx.save(); ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  const path = () => { ctx.beginPath(); full.forEach((p, i) => i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])); };
  path(); ctx.strokeStyle = 'rgba(52,211,153,.22)'; ctx.lineWidth = 7 / z * 1.5 + 2.6; ctx.shadowColor = '#34d399'; ctx.shadowBlur = 22; ctx.stroke();
  ctx.shadowBlur = 14; path(); ctx.strokeStyle = '#6ee7b7'; ctx.lineWidth = Math.max(1.0, 2.6 / z * 2); ctx.setLineDash([Math.max(.8, 3 / z * 2), Math.max(1.4, 5 / z * 2)]); ctx.lineDashOffset = -t * 14; ctx.stroke();
  ctx.setLineDash([]); ctx.shadowBlur = 8;
  // chevrons
  const { L, cum } = seg.m; const sp = 14; const off = (t * 9) % sp; ctx.fillStyle = '#ecfeff'; const cs = Math.max(1.5, 5 / z * 1.6);
  for (let d = off; d < L; d += sp) { let i = 1; while (i < cum.length - 1 && cum[i] < d) i++; const a = full[i - 1], b = full[i]; const k = (d - cum[i - 1]) / ((cum[i] - cum[i - 1]) || 1);
    const x = a[0] + (b[0] - a[0]) * k, y = a[1] + (b[1] - a[1]) * k; const an = Math.atan2(b[1] - a[1], b[0] - a[0]);
    ctx.save(); ctx.translate(x, y); ctx.rotate(an); ctx.globalAlpha = .9; ctx.beginPath(); ctx.moveTo(cs, 0); ctx.lineTo(-cs * .7, -cs * .8); ctx.lineTo(-cs * .25, 0); ctx.lineTo(-cs * .7, cs * .8); ctx.closePath(); ctx.fill(); ctx.restore(); }
  ctx.restore();
  const end = pts[pts.length - 1]; const pulse = (Math.sin(t * 4) + 1) / 2;
  ctx.save(); ctx.translate(end[0], end[1]);
  ctx.beginPath(); ctx.arc(0, 0, 3 + pulse * 3.2, 0, 7); ctx.fillStyle = `rgba(250,204,21,${.35 - pulse * .2})`; ctx.fill();
  ctx.beginPath(); ctx.arc(0, 0, 2.4, 0, 7); ctx.fillStyle = seg.endsAtStair ? '#a78bfa' : '#facc15'; ctx.shadowColor = ctx.fillStyle; ctx.shadowBlur = 16; ctx.fill(); ctx.shadowBlur = 0;
  ctx.font = `${Math.max(14, 5 * z) / z}px sans-serif`; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(seg.endsAtStair ? '🪜' : '📍', 0, -6.5); ctx.restore();
}
function drawLabels(fl, z) {
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  for (const zn of fl.zones) {
    if (!zn.cx && !zn.cy) continue;
    if (zn.type === 'stairs') { const s = Math.max(15, 4.2 * z) / z; ctx.font = `${s}px sans-serif`; ctx.fillStyle = '#fff'; ctx.fillText('🪜', zn.cx, zn.cy); continue; }
    if (zn.type === 'restroom') { ctx.font = `${Math.max(14, 3.8 * z) / z}px sans-serif`; ctx.fillText('🚻', zn.cx, zn.cy); continue; }
    if (zn.type === 'exit') { ctx.font = `${Math.max(16, 4.6 * z) / z}px sans-serif`; ctx.fillText('🚪', zn.cx, zn.cy - 2); ctx.font = `700 ${Math.max(10, 2.6 * z) / z}px Outfit,sans-serif`; ctx.fillStyle = '#6ee7b7'; ctx.fillText(zn.name, zn.cx, zn.cy + 4); continue; }
    if (zn.type === 'room') { if (z < 2.6) continue; ctx.font = `600 ${Math.max(9, 2.5 * z) / z}px Outfit,sans-serif`; ctx.fillStyle = 'rgba(226,244,255,.92)'; ctx.fillText(zn.num, zn.cx, zn.cy); continue; }
    if (zn.type === 'corridor') { if (z < 3.6) continue; ctx.font = `500 ${Math.max(9, 2.1 * z) / z}px Inter,sans-serif`; ctx.fillStyle = 'rgba(148,210,235,.55)'; ctx.fillText(zn.name, zn.cx, zn.cy); continue; }
    const ic = ZICON[zn.type]; const fs = Math.max(12, 3.2 * z) / z;
    if (ic) { ctx.font = `${fs * 1.9}px sans-serif`; ctx.fillStyle = '#fff'; ctx.fillText(ic, zn.cx, zn.cy - fs * 1.1); }
    ctx.font = `700 ${fs}px Outfit,sans-serif`; ctx.fillStyle = '#e0f2fe'; ctx.shadowColor = '#000'; ctx.shadowBlur = 4; ctx.fillText(zn.name, zn.cx, zn.cy + (ic ? fs * .6 : 0)); ctx.shadowBlur = 0;
  }
}
function drawPlayer(z, t) {
  const rr = Math.max(R * z, 9) / z;
  ctx.save(); ctx.translate(S.x, S.y);
  for (let k = 0; k < 2; k++) { const p = ((t * .8 + k * .5) % 1); ctx.beginPath(); ctx.arc(0, 0, rr * (1 + p * 3.2), 0, 7); ctx.strokeStyle = `rgba(34,211,238,${.55 * (1 - p)})`; ctx.lineWidth = 2 / z * 1.4; ctx.stroke(); }
  const g = ctx.createRadialGradient(0, 0, 0, 0, 0, rr * 2.2); g.addColorStop(0, 'rgba(34,211,238,.55)'); g.addColorStop(1, 'rgba(34,211,238,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.arc(0, 0, rr * 2.2, 0, 7); ctx.fill();
  ctx.rotate(S.ang + Math.PI / 2);
  ctx.shadowColor = '#22d3ee'; ctx.shadowBlur = 16;
  ctx.beginPath(); ctx.moveTo(0, -rr * 1.9); ctx.lineTo(rr * .85, -rr * .95); ctx.lineTo(-rr * .85, -rr * .95); ctx.closePath(); ctx.fillStyle = '#ecfeff'; ctx.fill(); // direction arrow
  ctx.shadowBlur = 12; ctx.beginPath(); ctx.arc(0, 0, rr, 0, 7); const bg = ctx.createRadialGradient(-rr * .3, -rr * .3, 0, 0, 0, rr); bg.addColorStop(0, '#a5f3fc'); bg.addColorStop(.6, '#22d3ee'); bg.addColorStop(1, '#0891b2'); ctx.fillStyle = bg; ctx.fill();
  ctx.lineWidth = 1.4 / z * 1.4; ctx.strokeStyle = '#fff'; ctx.stroke(); ctx.shadowBlur = 0;
  ctx.beginPath(); ctx.arc(0, -rr * .22, rr * .32, 0, 7); ctx.fillStyle = '#0e7490'; ctx.fill();
  ctx.restore();
}
let last = performance.now();
function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000); last = now; S.t += dt;
  const fl = F();
  // input
  let [kx, ky] = keyVec(); let ix = S.input.x + kx, iy = S.input.y + ky; const m = Math.hypot(ix, iy);
  if (m > 0.05 && !S.busy) { if (m > 1) { ix /= m; iy /= m; } const sp = 24; const ox = S.x, oy = S.y; move(ix * sp * dt, iy * sp * dt);
    if (Math.hypot(S.x - ox, S.y - oy) > 0.01) S.tAng = Math.atan2(iy, ix); else S.tAng = Math.atan2(iy, ix);
    S.cam.follow = S.cam.follow || false; }
  let da = S.tAng - S.ang; da = Math.atan2(Math.sin(da), Math.cos(da)); S.ang += da * Math.min(1, dt * 14);
  if (S.cam.follow) { const k = Math.min(1, dt * 6); S.cam.x += (S.x - S.cam.x) * k; S.cam.y += (S.y - S.cam.y) * k; }
  updateBanner(); updateStairsUI();
  if (S.target) { refreshRoute(false);
    if (S.target.floor === S.floor && Math.hypot(S.x - S.target.x, S.y - S.target.y) < 5) { showToast(`🎉 Сіз жеттіңіз: ${S.target.name}`, 3000); clearRoute(); $('search-input').value = ''; $('search-clear').classList.add('hidden'); } }
  // draw
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0); ctx.clearRect(0, 0, W, H);
  const z = S.cam.zoom;
  ctx.save(); ctx.translate(W / 2 - S.cam.x * z, H / 2 - S.cam.y * z); ctx.scale(z, z);
  ctx.imageSmoothingQuality = 'high';
  if (fl.img.complete) ctx.drawImage(fl.img, 0, 0, fl.gw, fl.gh);
  drawLabels(fl, z); drawRoute(z, S.t); drawPlayer(z, S.t);
  ctx.restore();
  requestAnimationFrame(frame);
}

/* ============ URL QUERY / QR PARAMETER INITIALIZATION ============ */
function initStartLocation() {
  const params = new URLSearchParams(window.location.search);
  const hash = (window.location.hash || '').replace('#', '').trim();
  const spot = params.get('spot') || params.get('start') || params.get('qr') || params.get('room') || hash;
  const to = params.get('to') || params.get('target');

  const ALIASES = {
    'entrance': { floor: 1, name: 'Орталық вестибюль / Гардероб', label: 'Басты кіреберіс' },
    'kireberis': { floor: 1, name: 'Орталық вестибюль / Гардероб', label: 'Басты кіреберіс' },
    'vestibule': { floor: 1, name: 'Орталық вестибюль / Гардероб', label: 'Орталық вестибюль' },
    'cafe': { floor: 1, name: 'Асхана', label: 'Асхана' },
    'canteen': { floor: 1, name: 'Асхана', label: 'Асхана' },
    'asxana': { floor: 1, name: 'Асхана', label: 'Асхана' },
    'ashana': { floor: 1, name: 'Асхана', label: 'Асхана' },
    'assembly': { floor: 1, name: 'Актовый зал', label: 'Актовый зал' },
    'aktovyi': { floor: 1, name: 'Актовый зал', label: 'Актовый зал' },
    'akt': { floor: 1, name: 'Актовый зал', label: 'Актовый зал' },
    'gym': { floor: 2, name: 'Спорт залы (Үлкен зал)', label: 'Спорт залы' },
    'sport': { floor: 2, name: 'Спорт залы (Үлкен зал)', label: 'Спорт залы' },
    'sportzal': { floor: 2, name: 'Спорт залы (Үлкен зал)', label: 'Спорт залы' },
    'library': { floor: 3, name: 'Кітапхана және оқу залы', label: 'Кітапхана' },
    'kitapxana': { floor: 3, name: 'Кітапхана және оқу залы', label: 'Кітапхана' }
  };

  let targetFloor = 1;
  let targetX = 0, targetY = 0;
  let locationLabel = '';

  if (spot) {
    const key = spot.toLowerCase().trim();
    if (ALIASES[key]) {
      const a = ALIASES[key];
      const z = findZone(a.floor, a.name);
      if (z) {
        targetFloor = a.floor;
        targetX = z.cx;
        targetY = z.cy;
        locationLabel = a.label;
      }
    } else {
      for (let f = 1; f <= 3; f++) {
        const z = findZone(f, spot);
        if (z) {
          targetFloor = f;
          targetX = z.cx;
          targetY = z.cy;
          locationLabel = z.name;
          break;
        }
      }
    }
  }

  if (!targetX && !targetY) {
    const defaultZone = findZone(1, 'Негізгі кіреберіс') || findZone(1, 'Орталық вестибюль / Гардероб');
    targetFloor = 1;
    targetX = defaultZone.cx;
    targetY = defaultZone.cy - 6;
  }

  S.floor = targetFloor;
  const [sx, sy] = snap(floors[targetFloor - 1], targetX, targetY);
  S.x = S.cam.x = sx;
  S.y = S.cam.y = sy;
  S.cam.zoom = 4.2;
  S.cam.follow = true;

  updateFloorChip();
  updateBanner();
  updateStairsUI(true);

  if (locationLabel) {
    setTimeout(() => {
      showToast(`📍 QR оқылды! Сіздің орныңыз: ${locationLabel} (${targetFloor}-қабат)`, 4500);
    }, 500);
  }

  if (to) {
    setTimeout(() => {
      let dest = null;
      for (let f = 1; f <= 3 && !dest; f++) {
        dest = findZone(f, to);
        if (dest) {
          setTarget(f, dest);
          showToast(`🎯 Бағыт: ${dest.name} (${f}-қабат)`, 3500);
        }
      }
    }, 800);
  }
}

initStartLocation();
requestAnimationFrame(frame);


window.__game = { S, floors, planRoute, teleport, setTarget, snap, pick, ENTRIES, changeFloor, dijkstraField, descend, simplify };
})();
