import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse

img, m, w1, inside, box = analyse(1, 17)
clr = ndi.distance_transform_cdt(inside, metric='chessboard')
ok = clr >= 2
lab, n = ndi.label(ok, structure=np.ones((3, 3)))
l_main = lab[208, 339]
print("Component ID at player start (339, 208):", l_main)
l_elem = lab[193, 141]
print("Component ID at elementary stair (141, 193):", l_elem)
# Find path or where it breaks between x=141 and 339
for x in range(141, 340):
    ys = np.where(lab[:, x] == l_elem)[0]
    if len(ys) == 0:
        print(f"Broken at x={x}! No l_elem found.")
        print(f"Values at col x={x}:", np.unique(lab[:, x]))
        print(f"Values at col x-1={x-1}:", np.unique(lab[:, x-1]))
        break
