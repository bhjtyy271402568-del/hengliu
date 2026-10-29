"""在 Codex 10-29 1638 版上做优化（复核文件第 24 节）。输入 epro2，输出 epro2。只改恒流源板 PCB 9a0fbfd22df79247。"""
import sys, json, zipfile, random
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
SRC, DST = sys.argv[1], sys.argv[2]
M = 0.0254
zin = zipfile.ZipFile(SRC)
name = [n for n in zin.namelist() if n.endswith('.epru')][0]
lines = zin.read(name).decode().split('\n')
# PCB 文档行范围
start = end = None
for i, l in enumerate(lines):
    if l.startswith('{"type":"DOCHEAD"'):
        b = json.loads(l.split('||', 1)[1].rstrip('|'))
        if start is not None and end is None: end = i
        if b.get('uuid') == '9a0fbfd22df79247': start = i
assert start is not None and end is not None
maxt = 0
for l in lines:
    try: maxt = max(maxt, json.loads(l.split('||', 1)[0]).get('ticket', 0))
    except Exception: pass
tick = [maxt]
def nt():
    tick[0] += 1; return tick[0]
def parse(i):
    h, b = lines[i].split('||', 1)
    b = b[:-1] if b.endswith('|') else b
    return json.loads(h), (json.loads(b) if b else {})
def dump(h, b): return json.dumps(h, ensure_ascii=False, separators=(',', ':')) + '||' + json.dumps(b, ensure_ascii=False, separators=(',', ':')) + '|'
def ring_mm(path):
    q = [v for v in path[0] if not isinstance(v, str)]
    return Polygon([(q[k]*M, q[k+1]*M) for k in range(0, len(q), 2)])
def path_mil(poly):
    poly = poly.buffer(0)
    assert poly.geom_type == 'Polygon' and len(poly.interiors) == 0, poly.geom_type
    c = list(poly.exterior.coords)
    out = [round(c[0][0]/M, 4), round(c[0][1]/M, 4), 'L']
    for x, y in c[1:]: out += [round(x/M, 4), round(y/M, 4)]
    return [out]
def rid(): return '%016x' % random.getrandbits(64)
random.seed(20261029)
recs = {}
for i in range(start+1, end):
    if '||' not in lines[i]: continue
    h, b = parse(i)
    if h['type'] in ('POUR', 'FILL'):
        recs[(h['type'], b.get('name') if h['type'] == 'POUR' else h['id'])] = i
log = []
def setrec(i, h, b, why):
    h['ticket'] = nt(); lines[i] = dump(h, b); log.append(why)
# ---- 1. 顶层信号地区：POUR6（顶层 PGND）切掉信号地区，新增顶层 GND 铺铜
i11 = recs[('POUR', 'POUR11')]; _, b11 = parse(i11)
zone = ring_mm(b11['path'])                       # L2/L3 信号地区（含控制区）
i3 = recs[('POUR', 'POUR3')]; _, b3 = parse(i3)
ctrl_top = ring_mm(b3['path'])
i6 = recs[('POUR', 'POUR6')]; h6, b6 = parse(i6)
p6 = ring_mm(b6['path']).difference(zone)
if p6.geom_type == 'MultiPolygon':
    p6 = max(p6.geoms, key=lambda g: g.area)
b6['path'] = path_mil(p6)
setrec(i6, h6, b6, 'POUR6 顶层 PGND：去掉信号地区（U9 / U201 / R12 周围约 %.0f mm²）' % zone.difference(ctrl_top).area)
newg = zone.difference(box(-1, -1, 53.6, 45.1))
if newg.geom_type == 'MultiPolygon': newg = max(newg.geoms, key=lambda g: g.area)
bN = dict(b3); bN['name'] = 'CONTROL_GND_TOP'; bN['order'] = 41; bN['path'] = path_mil(newg)
hN = {'type': 'POUR', 'ticket': nt(), 'id': rid()}
lines.insert(end, dump(hN, bN)); end += 1
log.append('新增 CONTROL_GND_TOP：顶层 GND，范围 = L2/L3 信号地区去掉控制区（%.0f mm²）' % newg.area)
# ---- 2. 地桥接移到 U9 西南、源极条北边
fills = [k for k in recs if k[0] == 'FILL']
assert len(fills) == 1
iF = recs[fills[0]]; hF, bF = parse(iF)
assert bF.get('isBridgingCopper')
x0, x1, y0, y1 = 66.0, 69.2, 59.2, 62.9
old = bF['path'][0]
bF['path'] = [['R', round(x0/M, 4), round(y1/M, 4), round((x1-x0)/M, 4), round((y1-y0)/M, 4), 0, 0]]
setrec(iF, hF, bF, '地桥接（isBridgingCopper）从 U9 北侧 (78.6–79.6, 50.4–53.2) 移到 (%.1f–%.1f, %.1f–%.1f)，跨在信号地区和源极 PGND 条之间' % (x0, x1, y0, y1))
# 两个 GND 过孔，复制一个现有 0.3/0.6 GND 过孔的字段
tmpl = None
for i in range(start+1, end):
    if '"type":"VIA"' in lines[i][:40]:
        h, b = parse(i)
        if b.get('netName') == 'GND' and abs(b['holeDiameter']*M-0.3) < 0.01 and abs(b['viaDiameter']*M-0.6) < 0.01: tmpl = b; break
assert tmpl
for (x, y) in [(66.5, 59.8), (66.5, 60.8)]:
    b = dict(tmpl); b['centerX'] = round(x/M, 4); b['centerY'] = round(y/M, 4)
    lines.insert(end, dump({'type': 'VIA', 'ticket': nt(), 'id': rid()}, b)); end += 1
log.append('桥接处加 2 个 GND 过孔 (66.5, 59.8)、(66.5, 60.8)，0.3 / 0.6 mm，接 L2 / L3 信号地')
# ---- 3. L2 分界在 BG 主干下北移：x 71.0–93.1 的边界 62.08 → 61.0
cut = unary_union([box(71.0, 61.0, 87.3, 62.3), box(87.3, 60.0, 93.1, 62.3)])
i2 = recs[('POUR', 'POWER_PGND_L2')]; h2, b2 = parse(i2)
pg2 = ring_mm(b2['path'])
pg2n = pg2.union(cut.intersection(zone.buffer(0.5)))
b2['path'] = path_mil(pg2n)
setrec(i2, h2, b2, 'L2 PGND 轮廓：x 71.0–87.3 向北扩到 y 61.0（BG 主干 y 61.85 正下方变成 PGND），x 87.3–93.1 扩到 y 60.0（右下角 PGND 过孔排接上 L2）')
h11, b11 = parse(i11)
z2 = zone.difference(cut)
b11['path'] = path_mil(z2)
setrec(i11, h11, b11, 'L2 GND（POUR11）轮廓：南边界 x 71.0–87.3 由 62.08 → 61.0，x 87.3–93.1 → 60.0')
# ---- 4. SW → L8 末段加宽
iT = recs[('POUR', 'POWER_LT_SW_TOP')]; hT, bT = parse(iT)
sw = ring_mm(bT['path']).union(Polygon([(90.3, 76.3), (90.3, 77.6), (92.3, 77.6), (92.3, 80.6), (109.6, 80.6), (109.6, 76.3)]))
bT['path'] = path_mil(sw)
setrec(iT, hT, bT, '顶层 SW（POWER_LT_SW_TOP）：x 90.3–109.6 上沿 76.5 → 80.6（R49 和 C108 孔处让开）')
iB = recs[('POUR', 'ST01_LT_SW_BOTTOM')]; hB, bB = parse(iB)
swb = ring_mm(bB['path']).union(Polygon([(92.8, 76.8), (92.8, 80.6), (110.2, 80.6), (110.2, 76.8)]))
bB['path'] = path_mil(swb)
setrec(iB, hB, bB, '底层 SW（ST01_LT_SW_BOTTOM）：x 92.8–110.2 上沿 77.0 → 80.6（C108 处让开）')
# PCB 文档头 ticket 也更新
hD, bD = parse(start); hD['ticket'] = nt(); lines[start] = dump(hD, bD)
zout = zipfile.ZipFile(DST, 'w', zipfile.ZIP_DEFLATED)
for it in zin.infolist():
    data = zin.read(it.filename)
    if it.filename == name: data = '\n'.join(lines).encode()
    zout.writestr(it, data, compress_type=zipfile.ZIP_DEFLATED)
zout.close()
print('\n'.join(log)); print('max ticket', tick[0])
