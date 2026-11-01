"""每个网络（或“网络:焊盘1,焊盘2”只看这几只焊盘之间）的最窄颈：把该网铜（两层 + 过孔 + 通孔焊盘）逐步收缩，焊盘全部仍连通的最大收缩量 e，颈宽约 2e。
用法：/usr/bin/python3 aux_neck.py snap.pkl lay.pkl 网络..."""
import sys, pickle, collections
from shapely.geometry import Point
S = pickle.load(open(sys.argv[1], 'rb')); L = pickle.load(open(sys.argv[2], 'rb'))
def parts(g): return list(getattr(g, 'geoms', [g]))
def netcopper(net):
    pads = [p for p in S['pads'] if p['net'] == net]
    out = {}
    for lay in (1, 2):
        keep = []
        for q in parts(L[lay]):
            if any(q.intersects(p['g'].representative_point()) for p in pads if p['layer'] in (lay, 12)) or \
               any(q.contains(Point(v['x'], v['y'])) for v in S['vias'] if v['net'] == net): keep.append(q)
        out[lay] = keep
    return pads, out
def connected(net, pads, cu, e):
    isl = [(lay, g) for lay in (1, 2) for q in cu[lay] for g in parts(q.buffer(-e)) if not g.is_empty]
    par = list(range(len(isl)))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    def hits(lay, geom): return [i for i, (l, g) in enumerate(isl) if l == lay and g.intersects(geom)]
    for v in S['vias']:
        if v['net'] != net: continue
        h = hits(1, Point(v['x'], v['y']).buffer(v['h'] / 2 + .05)) + hits(2, Point(v['x'], v['y']).buffer(v['h'] / 2 + .05))
        for k in h[1:]: par[f(k)] = f(h[0])
    first = []
    for p in pads:
        if p['layer'] == 12:
            pt = Point(p['x'], p['y']).buffer(p['hole'] / 2 + .05); h = hits(1, pt) + hits(2, pt)
            for k in h[1:]: par[f(k)] = f(h[0])
        else:
            h = hits(p['layer'], p['g'].centroid.buffer(0.05))
        if not h: return False, p
        first.append(h[0])
    return len({f(i) for i in first}) == 1, None
for arg in sys.argv[3:]:
    net, _, want = arg.partition(':')
    pads, cu = netcopper(net)
    if want: pads = [p for p in pads if f"{p['ref']}.{p['num']}" in want.split(',')]
    lo, hi = 0.0, 3.0
    for _ in range(14):
        m = (lo + hi) / 2; ok, _ = connected(net, pads, cu, m)
        lo, hi = (m, hi) if ok else (lo, m)
    _, bad = connected(net, pads, cu, hi)
    print(f'{arg}: 颈宽约 {2 * lo:.2f} mm（先断开的焊盘 {bad["ref"]}.{bad["num"] if bad else ""}）' if bad else f'{arg}: 颈宽约 {2 * lo:.2f} mm')
