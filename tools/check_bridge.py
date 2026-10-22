import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse, save_rgb, ROOT
from extract_plans import CELL

img, m, w1, inside, box = analyse(1, 17)
# bridge region is around y=180..220, x=170..240
print("box:", box)
bridge_m = m[180:230, 170:230]
print("bridge wall shape:", bridge_m.shape)
# print ASCII of bridge
for row in bridge_m[::2]:
    print(''.join('#' if c else '.' for c in row[::2]))
