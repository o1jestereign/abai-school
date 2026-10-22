import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse

for floor, page in ((1, 17), (2, 18), (3, 19)):
    img, m, w1, inside, box = analyse(floor, page)
    # Get walk after carved
    lab, n = ndi.label(inside)
    sizes = ndi.sum(inside, lab, range(1, n + 1))
    max_lab = sizes.argmax() + 1
    print(f"Floor {floor}: largest component size = {sizes.max()}")
    
    # Check each stair in STAIRS_SRC
    from build_data import STAIRS_SRC, CELL, nearest_walkable
    sc, pts = STAIRS_SRC[floor]
    x0, y0 = box[2], box[0]
    clr = ndi.distance_transform_cdt(inside, metric='chessboard')
    for i, (px, py) in enumerate(pts):
        sx, sy = nearest_walkable(inside, (px * sc - x0) / CELL, (py * sc - y0) / CELL, clr)
        st_lab = lab[sy, sx]
        sz = sizes[st_lab - 1] if st_lab > 0 else 0
        in_main = (st_lab == max_lab)
        print(f"  stair {i} at ({sx}, {sy}): comp size = {sz}, in_main = {in_main}")
