import json, sys, heapq
import numpy as np
sys.path.insert(0, '.')
import router as R
def along(b, net, a, z):
    nid = b.nid[net]; m = [b.cu[l] == nid for l in range(2)]
    pads = {f"{p['ref']}.{p['num']}": p for p in b.pads}
    pa, pz = pads[a], pads[z]
    i0,i1,j0,j1 = pz['cells']
    src = [(l, j, i) for l in pa['layers'] for j in range(pa['cells'][2], pa['cells'][3]+1) for i in range(pa['cells'][0], pa['cells'][1]+1) if m[l][j, i]]
    dist = {k: 0 for k in src}; h = [(0, k) for k in src]; heapq.heapify(h)
    while h:
        g, k = heapq.heappop(h)
        if g > dist[k]: continue
        l, j, i = k
        if j0 <= j <= j1 and i0 <= i <= i1 and l in pz['layers']: return round(g, 1)
        for dj, di, s in ((1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,1.414),(1,-1,1.414),(-1,1,1.414),(-1,-1,1.414)):
            nj, ni = j+dj, i+di
            if 0<=nj<R.H and 0<=ni<R.W and m[l][nj, ni]:
                nk=(l,nj,ni); ng=g+s*R.RES
                if ng < dist.get(nk,1e9): dist[nk]=ng; heapq.heappush(h,(ng,nk))
        if m[1-l][j,i]:
            nk=(1-l,j,i); ng=g+0.5
            if ng < dist.get(nk,1e9): dist[nk]=ng; heapq.heappush(h,(ng,nk))
    return None
for f in sys.argv[1:]:
    b = R.solve(json.load(open(f)))
    r = {}
    for net, a, z in [('P15_RAW','U2.8','L1.1'),('P15_RAW','U2.8','L3.1'),('GALVO_P15','L1.2','J2.1'),('GALVO_P15','L1.2','J3.1'),
                      ('N15_RAW','U3.5','L2.1'),('GALVO_N15','L2.2','J2.3'),('GALVO_N15','L2.2','J3.3'),('CARD_P15','L3.2','J4.1'),('AUX_IN','Q2.3','U2.1'),('AUX_IN','Q2.3','U3.3'),('$1N669','U1.10','Q2.1'),('AUX_IN','U1.9','Q2.3')]:
        r[f'{a}→{z}'] = along(b, net, a, z)
    print(f, r)
