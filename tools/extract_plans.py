"""Extract floor plans (PDF pages 17-19 = Қосымша №5-7) and build collision grids.
Outputs: assets/floor{n}.png (clean plan) and tools/grid_debug_{n}.png
"""
import sys, os, json
import numpy as np, fitz
from scipy import ndimage as ndi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PDF = os.path.join(ROOT, 'Абай школа.pdf')
DPI = 150
CELL = 4  # px per grid cell at DPI

def render(n):
    d = fitz.open(PDF)
    pix = d[n - 1].get_pixmap(dpi=DPI)
    img = np.frombuffer(pix.samples, np.uint8).reshape(pix.h, pix.w, pix.n)[:, :, :3]
    return img.copy()

def process(page, floor):
    img = render(page)
    h, w = img.shape[:2]
    r, g, b = [img[:, :, i].astype(int) for i in range(3)]
    nonwhite = (r + g + b) < 690
    red = (r > 190) & (g < 90) & (b < 90)
    # remove frame/legend/title: keep only region of the drawing
    mask = nonwhite & ~red
    mask[: int(h * 0.07)] = False       # title
    mask[int(h * 0.88):] = False       # legend
    mask[:, : int(w * 0.04)] = False
    mask[:, int(w * 0.97):] = False
    # floor caption text ("N-қабат") sits above the drawing
    cap = {1: (1470, 1600, 160, 215), 2: (1630, 1740, 135, 175), 3: (1515, 1625, 175, 215)}[floor]
    mask[cap[2]:cap[3], cap[0]:cap[1]] = False
    # drop small blobs (text)
    lab, nl = ndi.label(mask, structure=np.ones((3, 3)))
    sizes = ndi.sum(mask, lab, range(1, nl + 1))
    keep = np.zeros(nl + 1, bool); keep[1:] = sizes > 150
    mask = keep[lab]
    ys, xs = np.where(mask)
    y0, y1, x0, x1 = ys.min() - 20, ys.max() + 20, xs.min() - 20, xs.max() + 20
    return img, mask, red, (y0, y1, x0, x1)

def build(page, floor):
    img, mask, red, (y0, y1, x0, x1) = process(page, floor)
    mask_c = mask[y0:y1, x0:x1]; img_c = img[y0:y1, x0:x1]
    H, W = mask_c.shape
    gh, gw = H // CELL, W // CELL
    # a cell is wall when >=6/16 of its pixels are wall (an 'any' rule would eat the door gaps)
    m = mask_c[: gh * CELL, : gw * CELL].reshape(gh, CELL, gw, CELL).sum(axis=(1, 3)) >= 6
    return img_c, m, (y0, y1, x0, x1)

if __name__ == '__main__':
    os.makedirs(os.path.join(ROOT, 'assets'), exist_ok=True)
    for floor, page in ((1, 17), (2, 18), (3, 19)):
        img_c, m, box = build(page, floor)
        a = np.ascontiguousarray((~m * 255).astype(np.uint8))
        pm = fitz.Pixmap(fitz.csGRAY, a.shape[1], a.shape[0], a.tobytes(), False)
        pm.save(os.path.join(ROOT, 'tools', f'wall_{floor}.png'))
        print(floor, m.shape, box)
