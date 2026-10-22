import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse

for fl, pg in ((2, 18), (3, 19)):
    img, m, w1, inside, box = analyse(fl, pg)
    lab, n = ndi.label(inside)
    sizes = ndi.sum(inside, lab, range(1, n + 1))
    top_ids = np.argsort(sizes)[::-1][:6] + 1
    print(f"\n=== Floor {fl} Top Components ===")
    for tid in top_ids:
        print(f"  Component {tid}: size = {sizes[tid - 1]}")
    
    # Check distances between top 1 and top 2, 3, etc.
    c1 = (lab == top_ids[0])
    for tid in top_ids[1:]:
        c2 = (lab == tid)
        # distance between c1 and c2
        dist_map = ndi.distance_transform_edt(~c1)
        min_d = dist_map[c2].min()
        y, x = np.where(c2 & (dist_map == min_d))
        print(f"  Dist between Comp {top_ids[0]} and Comp {tid}: {min_d:.2f} at ({x[0]}, {y[0]})")
