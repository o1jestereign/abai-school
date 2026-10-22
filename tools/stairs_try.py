import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_plans import process, ROOT, CELL
from analyse import save_rgb

for floor, page in ((1, 17), (2, 18), (3, 19)):
    img, mask, red, (y0, y1, x0, x1) = process(page, floor)
    mc = mask[y0:y1, x0:x1].astype(float)
    d = ndi.uniform_filter(mc, 26)
    for thr in (0.40,):
        lab, n = ndi.label(d > thr)
        cs = ndi.center_of_mass(d > thr, lab, range(1, n + 1))
        sz = ndi.sum(d > thr, lab, range(1, n + 1))
        pts = [(round(c[1] / CELL), round(c[0] / CELL), int(s)) for c, s in zip(cs, sz) if s > 80]
        print(floor, thr, len(pts), pts)
