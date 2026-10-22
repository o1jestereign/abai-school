"""Analyse wall grids: seal dashes, flood outside, label zones, detect stairs. Debug images + analysis dict."""
import os, sys, json
import numpy as np, fitz
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_plans import build, ROOT, CELL

def save_rgb(a, path):
    a = np.ascontiguousarray(a.astype(np.uint8))
    fitz.Pixmap(fitz.csRGB, a.shape[1], a.shape[0], a.tobytes(), False).save(path)

def analyse(floor, page, door_box=13):
    img, m, box = build(page, floor)
    gh, gw = m.shape
    st = np.ones((3, 3), bool)
    w1 = ndi.binary_closing(np.pad(m, 3), structure=st, iterations=1)[3:-3, 3:-3] | m
    free = ~w1
    lab, n = ndi.label(free)
    outside_ids = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    outside = np.isin(lab, list(outside_ids))
    inside = free & ~outside
    # clean tiny speckles
    lab2, n2 = ndi.label(inside)
    sizes = ndi.sum(inside, lab2, range(1, n2 + 1))
    inside = np.isin(lab2, [i + 1 for i, s in enumerate(sizes) if s >= 6])
    # stair candidates: pixel density
    return img, m, w1, inside, box

if __name__ == '__main__':
    for floor, page in ((1, 17), (2, 18), (3, 19)):
        img, m, w1, inside, box = analyse(floor, page)
        # door-sealed labelling
        pad = 8
        w2 = ndi.binary_closing(np.pad(w1, pad), structure=np.ones((13, 13), bool))[pad:-pad, pad:-pad] | w1
        zone = inside & ~w2
        lab, n = ndi.label(zone)
        rgb = np.full(m.shape + (3,), 255, np.uint8)
        rng = np.random.RandomState(1)
        cols = rng.randint(90, 250, (n + 1, 3))
        rgb[zone] = cols[lab[zone]]
        rgb[inside & ~zone] = (255, 255, 200)
        rgb[w1] = (20, 20, 20)
        sizes = ndi.sum(zone, lab, range(1, n + 1))
        print(floor, 'zones', n, 'inside cells', inside.sum(), 'big', sorted(sizes.astype(int))[-8:])
        rgb = np.kron(rgb, np.ones((2, 2, 1), np.uint8))
        save_rgb(rgb, os.path.join(ROOT, 'tools', f'zones_{floor}.png'))
