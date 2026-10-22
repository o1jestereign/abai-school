import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_plans import build, ROOT
from analyse import save_rgb

for floor, page in ((1, 17), (3, 19)):
    img, m, box = build(page, floor)
    for it in (0, 1):
        w = m if it == 0 else ndi.binary_closing(np.pad(m, 3), structure=np.ones((3, 3)), iterations=it)[3:-3, 3:-3] | m
        free = ~w
        lab, n = ndi.label(free)
        outs = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
        inside = free & ~np.isin(lab, list(outs))
        clr = ndi.distance_transform_cdt(inside, metric='chessboard')
        l2, n2 = ndi.label(clr >= 2, structure=np.ones((3, 3)))
        sz = sorted(ndi.sum(clr >= 2, l2, range(1, n2 + 1)).astype(int), reverse=True)
        print(floor, 'closing', it, 'inside', int(inside.sum()), 'comps', n2, sz[:6])
