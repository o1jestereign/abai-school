import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse, ROOT

for floor, page in ((1, 17), (2, 18), (3, 19)):
    img, m, w1, inside, box = analyse(floor, page)
    pad = 8
    w2 = ndi.binary_closing(np.pad(w1, pad), structure=np.ones((13, 13), bool))[pad:-pad, pad:-pad] | w1
    zone = inside & ~w2
    lab, n = ndi.label(zone)
    main = inside.copy(); main[:, :185] = False
    ys, xs = np.where(main)
    bx0, bx1, by0, by1 = xs.min(), xs.max(), ys.min(), ys.max()
    print('floor', floor, 'shape', m.shape, 'box', box, 'main bbox', bx0, bx1, by0, by1)
    for i in range(1, n + 1):
        a = (lab == i).sum()
        if a > 700:
            yy, xx = np.where(lab == i)
            cx, cy = xx.mean(), yy.mean()
            print('  big', i, a, 'c', int(cx), int(cy), 'f', round((cx - bx0) / (bx1 - bx0), 2), round((cy - by0) / (by1 - by0), 2))
