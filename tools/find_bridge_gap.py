import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse

img, m, w1, inside, box = analyse(1, 17)
# On floor 1, elementary wing is x <= 180. Main building is x >= 210.
# The bridge is between x=175 and 215. Let's find rows where y has inside pixels in elementary and main
lab, n = ndi.label(inside)
sizes = ndi.sum(inside, lab, range(1, n + 1))
s_elem = lab[:, :160]
elem_id = np.argmax(np.bincount(s_elem[s_elem > 0]))
print("elem_id:", elem_id, "size:", sizes[elem_id - 1])

s_main = lab[:, 220:]
main_id = np.argmax(np.bincount(s_main[s_main > 0]))
print("main_id:", main_id, "size:", sizes[main_id - 1])

# Check where elem_id and main_id get closest:
ys_e, xs_e = np.where(lab == elem_id)
ys_m, xs_m = np.where(lab == main_id)
# find pair with minimum distance
cand_e = [(y, x) for y, x in zip(ys_e, xs_e) if x > 150]
cand_m = [(y, x) for y, x in zip(ys_m, xs_m) if x < 230]
min_d = 1e9
best_pair = None
for ye, xe in cand_e:
    for ym, xm in cand_m:
        d = (ye - ym)**2 + (xe - xm)**2
        if d < min_d:
            min_d = d
            best_pair = ((ye, xe), (ym, xm))

print("Closest pair between elem and main:", best_pair, "dist:", min_d**0.5)
