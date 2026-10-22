import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse, ROOT

img, m, w1, inside, box = analyse(1, 17)
# Where is the bridge? The bridge connects x < 185 to x > 185
ys, xs = np.where(inside[:, 175:215])
if len(ys):
    print("Bridge y range:", ys.min(), ys.max())
    print("Bridge unique y:", np.unique(ys))
else:
    print("No inside found between x=175 and 215!")
