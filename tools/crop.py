import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_plans import process, ROOT
from analyse import save_rgb
img, mask, red, bb = process(19, 3)
y0, y1, x0, x1 = 700, 1100, 1000, 1500   # page px at 150dpi (left wing, floor 3)
crop = img[y0:y1, x0:x1].copy()
save_rgb(np.kron(crop, np.ones((2, 2, 1), np.uint8)), os.path.join(ROOT, 'tools', 'crop3.png'))
