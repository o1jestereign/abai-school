import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse

for floor, page in ((1, 17), (2, 18), (3, 19)):
    img, m, w1, inside, box = analyse(floor, page)
    # If we carve doorways between any pocket and the adjacent corridor:
    # Any small component (size < 200) that is within 3 cells of a large component (size >= 1000)
    # can be connected by clearing the wall between them!
    lab, n = ndi.label(inside)
    sizes = ndi.sum(inside, lab, range(1, n + 1))
    big = np.isin(lab, [i + 1 for i, s in enumerate(sizes) if s >= 1000])
    
    # Bridge for floor 1:
    if floor == 1:
        # carve bridge corridor around y=183..187, x=170..215
        inside[183:186, 170:215] = True
        w1[183:186, 170:215] = False
    
    # Dilate big and small to find doorways
    dil_big = ndi.binary_dilation(big, structure=np.ones((5, 5)))
    for i, s in enumerate(sizes):
        if 5 <= s < 1000:
            small_mask = (lab == i + 1)
            # if small touches dil_big
            overlap = small_mask & dil_big
            if overlap.any():
                # find closest point from small to big
                cy, cx = ndi.center_of_mass(small_mask)
                yy, xx = np.mgrid[0:inside.shape[0], 0:inside.shape[1]]
                d = (xx - cx)**2 + (yy - cy)**2 <= 4.0**2
                # Carve only if it connects to big
                if (d & big).any():
                    inside |= d
                    w1 &= ~d
    
    # Re-check components
    lab2, n2 = ndi.label(inside)
    sizes2 = sorted(ndi.sum(inside, lab2, range(1, n2 + 1)).astype(int), reverse=True)
    print(f"Floor {floor} after connection: top 5 components:", sizes2[:5])
