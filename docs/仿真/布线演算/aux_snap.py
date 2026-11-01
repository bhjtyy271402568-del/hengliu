"""从 Codex 审核快照（audit-before.json，单位 mil）提取辅助板焊盘 / 过孔 / 导线 / 器件，转成 mm、y 向上的 shapely 几何。
用法：/usr/bin/python3 aux_snap.py audit-before.json snap.pkl"""
import sys, json, math, pickle
from shapely.geometry import Point, box, LineString, Polygon
from shapely import affinity
M = 0.0254
d = json.load(open(sys.argv[1]))
SGN = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0     # y 方向：1 = 快照已是 y 向上
def P(x, y): return x * M, SGN * y * M
cid = {c['primitiveId']: c for c in d['components']}
pads = []
for p in d['pads']:
    comp = None
    for k, c in cid.items():
        if p['primitiveId'].startswith(k) and len(p['primitiveId']) > len(k): comp = c; break
    x, y = P(p['x'], p['y']); sh = p['pad']; rot = p.get('rotation', 0) or 0
    if abs(rot) < 7: rot = math.degrees(rot)       # 有的记录是弧度
    if sh[0] in ('RECT', 'OVAL', 'ELLIPSE'):
        w, h = sh[1] * M, sh[2] * M
        if sh[0] == 'RECT': g = box(-w / 2, -h / 2, w / 2, h / 2)
        elif sh[0] == 'ELLIPSE': g = affinity.scale(Point(0, 0).buffer(1, 32), w / 2, h / 2)
        else: g = (LineString([(-(w - h) / 2, 0), ((w - h) / 2, 0)]).buffer(h / 2, 16) if w >= h else LineString([(0, -(h - w) / 2), (0, (h - w) / 2)]).buffer(w / 2, 16))
        g = affinity.rotate(g, SGN * rot, origin=(0, 0)); g = affinity.translate(g, x, y)
    elif sh[0] == 'POLYGON':
        q = [v for v in sh[1] if isinstance(v, (int, float))]
        g = Polygon([P(a, b) for a, b in zip(q[0::2], q[1::2])])
        if not g.is_valid: g = g.buffer(0)
    else: print('pad shape?', sh[0]); continue
    pads.append(dict(ref=comp['designator'] if comp else '', num=p.get('padNumber'), net=p.get('net') or '', layer=p['layer'], g=g,
                     hole=(p['hole'][1] * M if (p.get('hole') and p['layer'] == 12) else 0), plated=p.get('metallization'), x=x, y=y))
vias = [dict(net=v['net'], x=P(v['x'], v['y'])[0], y=P(v['x'], v['y'])[1], d=v['diameter'] * M, h=v['holeDiameter'] * M) for v in d['vias']]
lines = []
for l in d['lines']:
    a = P(l['startX'], l['startY']); b = P(l['endX'], l['endY'])
    lines.append(dict(net=l['net'], layer=l['layer'], a=a, b=b, w=l['lineWidth'] * M))
comps = [dict(ref=c['designator'], layer=c['layer'], x=P(c['x'], c['y'])[0], y=P(c['x'], c['y'])[1], rot=c['rotation'],
              part=(c.get('component') or {}).get('name'), fp=(c.get('footprint') or {}).get('name')) for c in d['components']]
pickle.dump(dict(pads=pads, vias=vias, lines=lines, comps=comps, pours=d['pours'], regions=d['regions']), open(sys.argv[2], 'wb'))
print(len(pads), 'pads', len(vias), 'vias', len(lines), 'lines', len(comps), 'comps')
