import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse

img, m, w1, inside, box = analyse(1, 17)
# Let's inspect along y=183..190, x=175..220
print("inside slice:")
for y in range(183, 192):
    print(f"y={y}: " + "".join(str(min(9, int(c))) if c else '.' for c in inside[y, 170:220]))
clr = ndi.distance_transform_cdt(inside, metric='chessboard')
print("\nclr slice:")
for y in range(183, 192):
    print(f"y={y}: " + "".join(str(min(9, int(c))) if c else '.' for c in clr[y, 170:220]))
