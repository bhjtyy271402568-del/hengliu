"""辅助板（两层）Gerber 连通 / 短路 / 异网间距 / 收缩连通（窄颈）检查。
用法：/usr/bin/python3 aux_conn.py snap.pkl lay.pkl [收缩量 mm]"""
import sys, pickle, itertools, collections
from shapely.geometry import Point
from shapely.strtree import STRtree
S = pickle.load(open(sys.argv[1], 'rb')); L = pickle.load(open(sys.argv[2], 'rb')); E = float(sys.argv[3]) if len(sys.argv) > 3 else 0
def parts(g): return list(getattr(g, 'geoms', [g]))
def run(e):
    isl = []   # (layer, poly)
    for lay in (1, 2):
        g = L[lay].buffer(-e) if e else L[lay]
        for q in parts(g):
            if q.area > 1e-4: isl.append((lay, q))
    tree = {lay: STRtree([q for l, q in isl if l == lay]) for lay in (1, 2)}
    idx = {lay: [i for i, (l, q) in enumerate(isl) if l == lay] for lay in (1, 2)}
    par = list(range(len(isl)))
    def f(i):
        while par[i] != i: par[i] = par[par[i]]; i = par[i]
        return i
    def hit(lay, pt):
        return [idx[lay][j] for j in tree[lay].query(pt) if isl[idx[lay][j]][1].intersects(pt)]
    owners = collections.defaultdict(set)   # 岛 -> 网络
    padhits = {}
    for p in S['pads']:
        name = f"{p['ref']}.{p['num']}"
        lays = (1, 2) if p['layer'] == 12 else (p['layer'],)
        hs = []
        for lay in lays:
            c = p['g'].representative_point() if not p['hole'] else Point(p['x'], p['y']).buffer(p['hole'] / 2 + 0.05)
            hs += hit(lay, c)
        if p['layer'] == 12 and not p['plated']: continue
        for h in hs: owners[h].add(p['net'] or '(空)'); 
        padhits[name] = (p['net'], hs)
        if p['layer'] == 12 and p['plated'] and len(hs) > 1:
            for h in hs[1:]: par[f(h)] = f(hs[0])
    for v in S['vias']:
        pt = Point(v['x'], v['y']).buffer(v['h'] / 2 + 0.05)
        hs = hit(1, pt) + hit(2, pt)
        for h in hs: owners[h].add(v['net'])
        if len(hs) < 2: print('过孔没有两层都接上', v)
        for h in hs[1:]: par[f(h)] = f(hs[0])
    grp = collections.defaultdict(set)
    for i in range(len(isl)): grp[f(i)].update(owners[i])
    shorts = [g for g in grp.values() if len(g - {'(空)'}) > 1]
    netgrp = collections.defaultdict(set)
    for name, (net, hs) in padhits.items():
        if not net: continue
        if not hs: print('焊盘没碰到铜', name, net); continue
        netgrp[net].add(f(hs[0]))
    opens = {n: len(g) for n, g in netgrp.items() if len(g) > 1}
    return isl, shorts, opens, owners, f, padhits
isl, shorts, opens, owners, f, padhits = run(0)
print('岛', len(isl), '短路', shorts, '断开', opens)
nets_of = {i: owners[i] for i in range(len(isl))}
# 异网最小间距（同层）
res = []
for lay in (1, 2):
    I = [i for i, (l, q) in enumerate(isl) if l == lay]
    for a, b in itertools.combinations(I, 2):
        na, nb = nets_of[a] - {'(空)'}, nets_of[b] - {'(空)'}
        if not na or not nb or na & nb: continue
        dd = isl[a][1].distance(isl[b][1])
        if dd < 0.3: res.append((round(dd, 3), lay, sorted(na), sorted(nb)))
print('异网间距 < 0.3 mm：', sorted(res)[:20])
for e in (0.075, 0.1):
    _, sh, op, *_ = run(e)
    print(f'收缩 {e} mm：断开', op)
