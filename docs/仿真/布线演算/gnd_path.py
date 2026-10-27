import json, sys, math, heapq
import numpy as np
from scipy import ndimage
sys.path.insert(0, '.')
import router as R
def geo(b, net, pairs):
    gid = b.nid[net]; x0, x1 = R.SIDE[net]
    m = []
    for l in range(2):
        other = (b.cu[l] != -1) & (b.cu[l] != gid)
        d = ndimage.distance_transform_edt(~other) * R.RES
        reg = np.zeros((R.H, R.W), bool); reg[:, int(x0 / R.RES):int(x1 / R.RES) + 1] = True
        m.append((d >= R.CLR) & reg & ~b.keep | (b.cu[l] == gid))
    pads = {f"{p['ref']}.{p['num']}": p for p in b.pads}
    out = {}
    for a, z in pairs:
        pa, pz = pads[a], pads[z]
        src = (int((pa['y'] + pa['h'] / 2) / R.RES), int((pa['x'] + pa['w'] / 2) / R.RES))
        dst = (int((pz['y'] + pz['h'] / 2) / R.RES), int((pz['x'] + pz['w'] / 2) / R.RES))
        # 双层 Dijkstra，过孔缝合代价 1 mm
        dist = {}; h = []
        for l in pa['layers']:
            dist[(l,) + src] = 0; heapq.heappush(h, (0, (l,) + src))
        best = None
        while h:
            g, k = heapq.heappop(h)
            if g > dist.get(k, 1e9): continue
            l, j, i = k
            if (j, i) == dst and l in pz['layers']:
                best = g; break
            for dj, di, s in ((1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)):
                nj, ni = j + dj, i + di
                if 0 <= nj < R.H and 0 <= ni < R.W and m[l][nj, ni]:
                    nk = (l, nj, ni); ng = g + s * R.RES
                    if ng < dist.get(nk, 1e9): dist[nk] = ng; heapq.heappush(h, (ng, nk))
            if m[1 - l][j, i]:
                nk = (1 - l, j, i); ng = g + 1.0
                if ng < dist.get(nk, 1e9): dist[nk] = ng; heapq.heappush(h, (ng, nk))
        out[f'{a}→{z}'] = round(best, 1) if best else None
    return out
for f in sys.argv[1:]:
    b = R.solve(json.load(open(f)))
    print(f, geo(b, 'AUX_GND', [('J2.2', 'U2.4'), ('J3.2', 'U3.4'), ('J4.2', 'U2.4'), ('J2.2', 'U3.4')]))
