import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse

img, m, w1, inside, box = analyse(1, 17)
clr = ndi.distance_transform_cdt(inside, metric='chessboard')
print("clr around 141, 193:")
for y in range(188, 198):
    print(f"y={y}:", clr[y, 136:146])
