# -*- coding: utf-8 -*-
"""Builds assets/floorN.png and js/mapdata.js from 'Абай школа.pdf' (pages 17-19 = Қосымша №5-7)."""
import os, sys, json, base64
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse, save_rgb, ROOT
from extract_plans import CELL

FLOORS = ((1, 17), (2, 18), (3, 19))

# stair icons read from the drawings (px of the 130-dpi render). Floor 1 was viewed downscaled (1820 wide).
S1 = 1.3636  # 1820-wide view -> 150dpi px
S2 = 150 / 130
STAIRS_SRC = {
    1: (S1, [(231, 750), (526, 750), (836, 458), (836, 708), (914, 808), (958, 1082), (978, 497), (1237, 497),
             (1195, 252), (1030, 683), (1182, 678), (1107, 722), (1107, 508), (1377, 458), (1377, 708),
             (1375, 230), (1300, 808), (1254, 1082)]),
    2: (S2, [(262, 917), (610, 917), (1103, 538), (1205, 997), (1280, 595), (1617, 595), (1457, 603), (1353, 830),
             (1547, 825), (1450, 885), (1558, 288), (1800, 248), (1800, 543), (1700, 997), (1258, 1355), (1638, 1358)]),
    3: (S2, [(265, 818), (613, 818), (1000, 425), (1187, 480), (1533, 480), (1718, 125), (1720, 428), (1105, 895),
             (1616, 895), (1360, 782), (1163, 1258), (1558, 1258)]),
}
EXITS_SRC = {1: (S1, [(1108, 808, 'Негізгі кіреберіс', 'Негізгі кіреберістесіз'),
                       (385, 803, 'Бастауыш блогы кіреберісі', 'Бастауыш блогының кіреберісіндесіз')])}

# type -> (fill colour, locative)
COL = {'room': (24, 40, 74), 'corridor': (16, 30, 56), 'hall': (22, 52, 92), 'restroom': (58, 38, 104),
       'stairs': (8, 96, 118), 'exit': (6, 110, 80), 'cafe': (92, 60, 30), 'assembly': (86, 34, 80),
       'library': (30, 76, 90), 'gym': (20, 76, 60)}

def name_big(floor, fx, fy):
    t = {
        1: [((0.18, 0.10), ('Кітапхана', 'library', 'Кітапханадасыз')),
            ((0.54, 0.21), ('Актовый зал', 'assembly', 'Актовый залдасыз')),
            ((0.55, 0.46), ('Орталық зал', 'hall', 'Орталық залдасыз')),
            ((0.55, 0.62), ('Асхана', 'cafe', 'Асханадасыз'))],
        2: [((0.08, 0.11), ('Информатика залы', 'hall', 'Информатика залындасыз')),
            ((0.44, 0.19), ('Конференц-зал', 'hall', 'Конференц-залдасыз')),
            ((0.59, 0.24), ('Оқу залы', 'hall', 'Оқу залындасыз')),
            ((0.23, 0.51), ('Лекция залы (сол)', 'hall', 'Лекция залындасыз')),
            ((0.77, 0.51), ('Лекция залы (оң)', 'hall', 'Лекция залындасыз')),
            ((0.50, 0.49), ('Орталық атриум', 'hall', 'Орталық атриумдасыз')),
            ((0.50, 0.84), ('Спорт залы', 'gym', 'Спорт залындасыз'))],
        3: [((0.22, 0.47), ('Кітапхана', 'library', 'Кітапханадасыз')),
            ((0.77, 0.47), ('Компьютер залы', 'hall', 'Компьютер залындасыз')),
            ((0.50, 0.45), ('Орталық зал', 'hall', 'Орталық залдасыз')),
            ((0.50, 0.79), ('Үлкен спорт залы', 'gym', 'Үлкен спорт залындасыз'))],
    }[floor]
    best = min(t, key=lambda e: (e[0][0] - fx) ** 2 + (e[0][1] - fy) ** 2)
    if (best[0][0] - fx) ** 2 + (best[0][1] - fy) ** 2 < 0.02:
        return best[1]
    return None

def nearest_walkable(walk, x, y, clr=None):
    h, w = walk.shape
    lab, n = ndi.label(walk)
    sizes = ndi.sum(walk, lab, range(1, n + 1))
    if n > 0:
        valid_labs = set(np.where(sizes >= 500)[0] + 1)
        if not valid_labs:
            valid_labs = {sizes.argmax() + 1}
        ok = np.isin(lab, list(valid_labs))
    else:
        ok = walk.copy()
    if clr is not None:
        ok &= (clr >= 1)
    x, y = int(round(x)), int(round(y))
    for r in range(0, 80):
        y0, y1, x0, x1 = max(0, y - r), min(h, y + r + 1), max(0, x - r), min(w, x + r + 1)
        sub = ok[y0:y1, x0:x1]
        if sub.any():
            yy, xx = np.where(sub)
            d = (yy + y0 - y) ** 2 + (xx + x0 - x) ** 2
            k = d.argmin()
            return int(xx[k] + x0), int(yy[k] + y0)
    return x, y

def stair_matrix(walk, clr, stairs):
    """All-pairs walking cost between stairs on one floor (same cost model as the JS router)."""
    from scipy.sparse import coo_matrix
    from scipy.sparse.csgraph import dijkstra
    h, w = walk.shape
    ok = clr >= 1
    idx = np.full((h, w), -1, np.int64)
    idx[ok] = np.arange(ok.sum())
    sc = np.where(clr >= 6, 1.0, 1 + (6 - clr) * 1.2)
    rows, cols, vals = [], [], []
    for dx, dy, c in ((1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.4142), (1, -1, 1.4142), (-1, 1, 1.4142), (-1, -1, 1.4142)):
        ys, xs = np.mgrid[max(0, -dy):h - max(0, dy), max(0, -dx):w - max(0, dx)]
        a = ok[ys, xs] & ok[ys + dy, xs + dx]
        if dx and dy:
            a &= ok[ys, xs + dx] & ok[ys + dy, xs]
        ys, xs = ys[a], xs[a]
        rows.append(idx[ys, xs]); cols.append(idx[ys + dy, xs + dx]); vals.append(c * sc[ys + dy, xs + dx])
    n = int(ok.sum())
    g = coo_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(n, n)).tocsr()
    src = [int(idx[s['y'], s['x']]) for s in stairs]
    d = dijkstra(g, directed=True, indices=src)
    out = []
    for i in range(len(stairs)):
        out.append([(-1 if not np.isfinite(d[i][j]) else int(round(d[i][j]))) for j in src])
    return out

def link(A, B, thr=45):
    """for each stair in A choose counterpart in B after best translation search."""
    out = [None] * len(A)
    for grp in (lambda p: p[0] < 185, lambda p: p[0] >= 185):
        ia = [i for i, p in enumerate(A) if grp(p)]
        ib = [i for i, p in enumerate(B) if grp(p)]
        if not ia or not ib:
            continue
        best, bt = -1, (0, 0)
        for i in ia:
            for j in ib:
                t = (B[j][0] - A[i][0], B[j][1] - A[i][1])
                c = 0
                for k in ia:
                    q = (A[k][0] + t[0], A[k][1] + t[1])
                    if min((q[0] - B[l][0]) ** 2 + (q[1] - B[l][1]) ** 2 for l in ib) < 100:
                        c += 1
                if c > best:
                    best, bt = c, t
        for i in ia:
            q = (A[i][0] + bt[0], A[i][1] + bt[1])
            j = min(ib, key=lambda l: (q[0] - B[l][0]) ** 2 + (q[1] - B[l][1]) ** 2)
            if ((q[0] - B[j][0]) ** 2 + (q[1] - B[j][1]) ** 2) ** .5 < thr:
                out[i] = j
    return out

def build_floor(floor, page):
    img, m, w1, inside, box = analyse(floor, page)
    y0, y1, x0, x1 = [int(v) for v in box]
    gh, gw = m.shape
    pad = 8
    w2 = ndi.binary_closing(np.pad(w1, pad), structure=np.ones((7, 7), bool))[pad:-pad, pad:-pad] | w1
    zmask = inside & ~w2
    lab, n = ndi.label(zmask)
    # --- doors: narrow plugs (gaps sealed by the closing) that join two different spaces get widened
    plug = inside & w2
    pl, pn = ndi.label(plug, structure=np.ones((3, 3)))
    yy0, xx0 = np.mgrid[0:gh, 0:gw]
    carved = np.zeros_like(inside)
    carve_pts = []
    for k in range(1, pn + 1):
        P = pl == k
        a = int(P.sum())
        if a < 3 or a > 160:
            continue
        near = ndi.binary_dilation(P, structure=np.ones((3, 3)), iterations=3)
        labs = set(np.unique(lab[near & zmask])) - {0}
        if len(labs) < 2:
            continue
        cy_, cx_ = ndi.center_of_mass(P)
        d = (xx0 - cx_) ** 2 + (yy0 - cy_) ** 2 <= 3.3 ** 2
        carved |= d
        carve_pts.append((cx_, cy_))
    # only carve through wall cells that touch the enclosed interior
    carved &= ndi.binary_dilation(inside, structure=np.ones((3, 3)), iterations=4)
    keep_outside = ~ndi.binary_dilation(~(inside | w1), structure=np.ones((3, 3)), iterations=1)  # never open to the exterior
    carved &= keep_outside | inside
    if floor == 1:
        # bridge connecting elementary wing and main building corridor
        inside[183:188, 170:233] = True
        w1[183:188, 170:233] = False
    # ensure any room/pocket within 5 cells of a major component is punctured
    lab_c, n_c = ndi.label(inside)
    sz_c = ndi.sum(inside, lab_c, range(1, n_c + 1))
    main_comps = np.isin(lab_c, [i + 1 for i, s in enumerate(sz_c) if s >= 500])
    dil_main = ndi.binary_dilation(main_comps, structure=np.ones((9, 9)))
    for i, s in enumerate(sz_c):
        if 4 <= s < 500:
            sub = (lab_c == i + 1)
            if (sub & dil_main).any():
                dist_to_main = ndi.distance_transform_edt(~main_comps)
                sub_dists = np.where(sub, dist_to_main, 1e9)
                ymin, xmin = np.unravel_index(sub_dists.argmin(), sub_dists.shape)
                if sub_dists[ymin, xmin] <= 6:
                    yy_m, xx_m = np.mgrid[0:gh, 0:gw]
                    circle = (xx_m - xmin)**2 + (yy_m - ymin)**2 <= 4.2**2
                    inside |= (circle & keep_outside)
                    w1 &= ~(circle & keep_outside)
    walk = inside.copy()
    clr = ndi.distance_transform_cdt(walk, metric='chessboard')
    _l, _n = ndi.label(clr >= 2, structure=np.ones((3, 3)))
    _s = sorted(ndi.sum(clr >= 2, _l, range(1, _n + 1)).astype(int), reverse=True)
    print('  walkable comps (clr>=2):', _n, _s[:8], 'total', int((clr >= 2).sum()))
    # corridor-like components (long & thin) are not rooms
    edt = ndi.distance_transform_edt(zmask)
    maxd = ndi.maximum(edt, lab, range(1, n + 1))
    corridor_ids = {i + 1 for i in range(n) if maxd[i] <= 7.5 and (lab == i + 1).sum() >= 250}
    main = inside.copy(); main[:, :185] = False
    ys, xs = np.where(main)
    bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
    frac = lambda cx, cy: ((cx - bx0) / (bx1 - bx0), (cy - by0) / (by1 - by0))

    # stairs
    sc, pts = STAIRS_SRC[floor]
    stairs = []
    for i, (px, py) in enumerate(pts):
        sx, sy = nearest_walkable(walk, (px * sc - x0) / CELL, (py * sc - y0) / CELL, clr)
        stairs.append({'id': i, 'x': sx, 'y': sy})

    zid = np.zeros((gh, gw), np.uint16)   # 0 = wall
    zones = []
    def add_zone(name, typ, at, cells_mask, num=None):
        zones.append({'id': len(zones) + 1, 'name': name, 'type': typ, 'at': at, 'num': num})
        zid[cells_mask & (zid == 0) & walk] = len(zones)
        return zones[-1]

    # stair & exit discs (claim first)
    yy, xx = np.mgrid[0:gh, 0:gw]
    for s in stairs:
        z = add_zone(f'Баспалдақ {s["id"] + 1}', 'stairs', 'Баспалдақ алаңындасыз',
                     ((xx - s['x']) ** 2 + (yy - s['y']) ** 2) <= 36)
        s['zone'] = z['id']
    exits = []
    if floor in EXITS_SRC:
        sc2, ex = EXITS_SRC[floor]
        for (px, py, nm, at) in ex:
            ex_x, ex_y = nearest_walkable(walk, (px * sc2 - x0) / CELL, (py * sc2 - y0) / CELL - 3)
            z = add_zone(nm, 'exit', at, ((xx - ex_x) ** 2 + (yy - ex_y) ** 2) <= 49)
            z['cx'], z['cy'] = ex_x, ex_y
            exits.append(z)

    # room components
    comps = []
    for i in range(1, n + 1):
        mk = lab == i
        a = int(mk.sum())
        if a < 30 or i in corridor_ids:
            continue
        cy_, cx_ = ndi.center_of_mass(mk)
        comps.append((i, a, cx_, cy_))
    # restrooms: small comps nearest to a stair
    smalls = [c for c in comps if 30 <= c[1] <= 600 and c[2] >= 185]
    toilets = set()
    for s in stairs:
        cand = [c for c in smalls if c[0] not in toilets and ((c[2] - s['x']) ** 2 + (c[3] - s['y']) ** 2) ** .5 < 40]
        if cand and len(toilets) < 5:
            toilets.add(min(cand, key=lambda c: (c[2] - s['x']) ** 2 + (c[3] - s['y']) ** 2)[0])
    def zone_order(c):
        i, a, cx_, cy_ = c
        fx, fy = frac(cx_, cy_)
        wing = 0 if cx_ < 185 else (1 if fx < 0.3 else (3 if fx > 0.7 else 2))
        return (wing, int(cy_ // 40), cx_)
    num = 0
    tcount = 0
    for c in sorted(comps, key=zone_order):
        i, a, cx_, cy_ = c
        mk = lab == i
        fx, fy = frac(cx_, cy_)
        if i in toilets:
            tcount += 1
            z = add_zone(f'Дәретхана {floor}.{tcount}', 'restroom', 'Дәретханадасыз', mk)
        elif a >= 700 and cx_ >= 185 and name_big(floor, fx, fy):
            nm, ty, at = name_big(floor, fx, fy)
            z = add_zone(nm, ty, at, mk)
        else:
            num += 1
            z = add_zone(f'{floor}{num:02d} кабинет', 'room', f'{floor}{num:02d}-ші кабинеттесіз', mk, floor * 100 + num)
        dist = ndi.distance_transform_edt(mk)
        yy_, xx_ = np.unravel_index(dist.argmax(), dist.shape)
        z['cx'], z['cy'] = int(xx_), int(yy_)

    # corridor regions (everything else walkable)
    def region(cx_, cy_):
        if cx_ < 185:
            return 'Бастауыш блогы коридоры'
        if floor == 1 and cx_ < 212 and cy_ > 150:
            return 'Бастауыш блогын жалғайтын көпір'
        fx, fy = frac(cx_, cy_)
        if fx < 0.3:
            return 'Сол қанат коридоры'
        if fx > 0.7:
            return 'Оң қанат коридоры'
        if fy < 0.3:
            return 'Солтүстік коридор'
        if fy > 0.64:
            return 'Негізгі коридор'
        return 'Орталық холл'
    rest = walk & (zid == 0)
    names = {}
    ry, rx = np.where(rest)
    for yv, xv in zip(ry, rx):
        nm = region(xv, yv)
        if nm not in names:
            names[nm] = add_zone(nm, 'corridor', {'Орталық холл': 'Орталық холлдасыз'}.get(nm, nm.replace('коридоры', 'коридорындасыз').replace('коридор', 'коридордасыз').replace('көпір', 'көпірдесіз')), np.zeros_like(walk))['id']
        zid[yv, xv] = names[nm]
    for nm, idx in names.items():
        mk = zid == idx
        dist = ndi.distance_transform_edt(mk)
        yy_, xx_ = np.unravel_index(dist.argmax(), dist.shape)
        zones[idx - 1]['cx'], zones[idx - 1]['cy'] = int(xx_), int(yy_)
    for z in zones:
        if 'cx' not in z:
            mk = zid == z['id']
            if mk.any():
                dist = ndi.distance_transform_edt(mk)
                yy_, xx_ = np.unravel_index(dist.argmax(), dist.shape)
                z['cx'], z['cy'] = int(xx_), int(yy_)
            else:
                z['cx'], z['cy'] = 0, 0
    for s in stairs:
        z = zones[s['zone'] - 1]
        z['cx'], z['cy'] = s['x'], s['y']
    assert len(zones) < 255, len(zones)

    # ---- background image
    H, W = gh * CELL, gw * CELL
    from extract_plans import process
    _, mask, red, bb = process(page, floor)
    wall_px = mask[bb[0]:bb[1], bb[2]:bb[3]][:H, :W]
    wall_px = np.pad(wall_px, ((0, H - wall_px.shape[0]), (0, W - wall_px.shape[1])))
    wall_px = ndi.binary_closing(wall_px, structure=np.ones((5, 5), bool)) | wall_px
    wall_px &= ~np.kron(carved, np.ones((CELL, CELL), bool))
    tmap = {z['id']: COL.get(z['type'], COL['room']) for z in zones}
    rgb = np.zeros((gh, gw, 3), np.uint8); rgb[:] = (9, 15, 30)
    rng = np.random.RandomState(floor)
    for z in zones:
        mk = zid == z['id']
        c = np.array(tmap[z['id']]) + (rng.randint(-5, 6, 3) if z['type'] in ('room',) else 0)
        rgb[mk] = np.clip(c, 0, 255)
    rgb = np.kron(rgb, np.ones((CELL, CELL, 1), np.uint8)).astype(np.float32)
    glow = ndi.gaussian_filter(wall_px.astype(np.float32), 2.5)
    rgb += glow[..., None] * np.array([20, 120, 160], np.float32) * 1.3
    core = wall_px[..., None]
    rgb = np.where(core, np.array([84, 214, 255], np.float32), rgb)
    save_rgb(np.clip(rgb, 0, 255), os.path.join(ROOT, 'assets', f'floor{floor}.png'))

    # outside darkening is implicit. Output
    grid = base64.b64encode(zid.astype(np.uint8).tobytes()).decode()
    return {'floor': floor, 'gw': gw, 'gh': gh, 'grid': grid, 'zones': zones, 'stairs': stairs,
            'dm': stair_matrix(walk, clr, stairs), 'img': f'assets/floor{floor}.png'}

if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'assets'), exist_ok=True)
    os.makedirs(os.path.join(ROOT, 'js'), exist_ok=True)
    fl = [build_floor(f, p) for f, p in FLOORS]
    for a, b in ((0, 1), (1, 2)):
        A = [(s['x'], s['y']) for s in fl[a]['stairs']]
        B = [(s['x'], s['y']) for s in fl[b]['stairs']]
        up = link(A, B); down = link(B, A)
        for i, j in enumerate(up):
            fl[a]['stairs'][i]['up'] = j
        for i, j in enumerate(down):
            fl[b]['stairs'][i]['down'] = j
    for f in fl:
        for s in f['stairs']:
            s.setdefault('up', None); s.setdefault('down', None)
            s['up'] = s['up']; s['down'] = s['down']
    data = {'cell': CELL, 'floors': fl}
    with open(os.path.join(ROOT, 'js', 'mapdata.js'), 'w', encoding='utf-8') as fh:
        fh.write('window.MAPDATA = ' + json.dumps(data, ensure_ascii=False) + ';\n')
    for f in fl:
        print('floor', f['floor'], f['gw'], f['gh'], 'zones', len(f['zones']), 'stairs', [(s['id'], s['up'], s['down']) for s in f['stairs']])
        print('  ', [z['name'] for z in f['zones'] if z['type'] != 'stairs'][:80])
