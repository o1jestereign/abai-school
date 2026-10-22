import os, sys
import numpy as np
from scipy import ndimage as ndi
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyse import analyse, save_rgb, ROOT

for floor, page in ((1, 17), (2, 18), (3, 19)):
    img, m, w1, inside, box = analyse(floor, page)
    for name, walk in (('inside', inside),):
        clr = ndi.distance_transform_cdt(walk, metric='chessboard')
        for need in (1, 2, 3):
            lab, n = ndi.label(clr >= need, structure=np.ones((3, 3)))
            sizes = sorted(ndi.sum(clr >= need, lab, range(1, n + 1)).astype(int), reverse=True)
            print(floor, 'clr>=', need, 'comps', n, sizes[:8], 'total', int((clr >= need).sum()))
    lab, n = ndi.label(inside >= 1)
    # picture of components for clr>=2
    clr = ndi.distance_transform_cdt(inside, metric='chessboard')
    lab, n = ndi.label(clr >= 2, structure=np.ones((3, 3)))
    sizes = ndi.sum(clr >= 2, lab, range(1, n + 1))
    rng = np.random.RandomState(3)
    cols = rng.randint(60, 255, (n + 1, 3)); cols[0] = 0
    rgb = cols[lab]
    big = np.argsort(sizes)[::-1][:1] + 1
    rgb[np.isin(lab, big)] = (255, 255, 255)
    rgb[w1] = (80, 80, 80)
    save_rgb(np.kron(rgb, np.ones((2, 2, 1), np.uint8)), os.path.join(ROOT, 'tools', f'conn_{floor}.png'))
