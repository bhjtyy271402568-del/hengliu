"""辅助板二次侧（±15 V 输出滤波 + 控制卡支路 + 三个接口）的建议摆放：生成新坐标、铜皮示意，查重叠 / 间距 / 禁布。
坐标 y 向上（和嘉立创一致），单位 mm。用法：python3 aux_out_plan.py aux_cur.json 输出.json
旋转 rot 按逆时针（0 / 90 / 180 / 270），绕器件原点转焊盘；电解电容本体按 Ø8 计（EEUFR1V221，以封装为准）。
C22 / C23 是 U2 输出新增的 1 µF + 10 µF（1206，位号以原理图为准）。"""
import json, sys, itertools, math
cur = json.load(open(sys.argv[1])); C = {c['r']: c for c in cur['c']}
ELEC = {'C11', 'C12', 'C14', 'C15', 'C18'}
THT = {'C11', 'C12', 'C14', 'C15', 'C18', 'D4', 'D5', 'J2', 'J3', 'J4', 'U2', 'U3'}

def rot(dx, dy, a):
    a = math.radians(a); return dx * math.cos(a) - dy * math.sin(a), dx * math.sin(a) + dy * math.cos(a)
def place(r, cx, cy, a=0):
    c = C[r]; ox, oy = c['x'], c['y']; P = []
    for p in c['p']:
        px, py = p[0] + p[2] / 2 - ox, p[1] + p[3] / 2 - oy
        nx, ny = rot(px, py, a); w, h = (p[3], p[2]) if a in (90, 270) else (p[2], p[3])
        P.append([round(cx + nx - w / 2, 3), round(cy + ny - h / 2, 3), w, h, p[4], p[5]])
    if r in ELEC: body = [cx - 4, cy - 4, cx + 4, cy + 4]
    else:
        bb = c['bb']; xs, ys = [], []
        for X in (bb[0], bb[0] + bb[2]):
            for Y in (bb[1], bb[1] + bb[3]):
                nx, ny = rot(X - ox, Y - oy, a); xs.append(cx + nx); ys.append(cy + ny)
        body = [min(xs), min(ys), max(xs), max(ys)]
    NEW[r] = dict(r=r, b=c['b'], p=P, body=[round(v, 3) for v in body], rot=a, x=cx, y=cy)
def c1206(r, cx, cy, top_net, bot_net, b=1):   # 竖放 1206：上焊盘 top_net
    w, h = 1.73, 1.49
    NEW[r] = dict(r=r, b=b, p=[[cx - w / 2, cy + 1.6 - h / 2, w, h, top_net, '1'], [cx - w / 2, cy - 1.6 - h / 2, w, h, bot_net, '2']],
                  body=[cx - .8, cy - 1.6, cx + .8, cy + 1.6], rot=0, x=cx, y=cy)

NEW = {}
# ---- 接口：都在右边，J4 最上、J2 下移 6.9 mm 让位，J3 不动 ----
place('J4', 122.4, 82.3, 90)      # 原来在下边；转 90° 后接线口朝右，1 脚 CARD_P15 在上
place('J2', 122.5, 69.1, 0)       # 原 y 76.0
# ---- +15 V：P15_RAW 横条 y 77–83 从 U2 第 8 脚往右；条下挂 D4 / C11 / D6，条右端 L1；条上挂控制卡支路 ----
place('D4', 96.33, 71.0, 270)     # 阴极（1 脚）在上，碰横条
place('C11', 103.6, 72.4, 0)      # 正极在上
place('D6', 111.0, 72.2, 270)     # 阴极在上
place('L1', 114.2, 79.5, 270)     # 1 脚 P15_RAW 在上（横条里），2 脚 GALVO_P15 在下
place('C13', 115.4, 69.0, 0)      # GALVO_P15 在上
place('R12', 115.2, 62.0, 0)      # GALVO_P15 在上
place('C12', 109.3, 58.9, 270)    # 正极（$1N765）朝右，对着 R12 下脚
place('L3', 97.0, 86.0, 0)        # 1 脚在左，往下接横条；2 脚 CARD_P15
place('R14', 102.0, 88.1, 270)    # CARD 脚在下
place('C18', 109.6, 90.3, 90)     # 正极（$1N777）在左
place('C19', 116.0, 87.0, 90)     # CARD 脚在下，压在 CARD 线上
c1206('C22', 83.0, 76.4, 'P15_RAW', 'AUX_GND')   # 背面，U2 第 8 脚左下
c1206('C23', 80.6, 76.4, 'P15_RAW', 'AUX_GND')
# ---- −15 V：N15_RAW 横条 y 31–37 从 U3 第 5 脚往右；条上挂 D5 / C14 / D7，条右端 L2；条下是滤波和出线 ----
place('D5', 91.5, 42.5, 270)      # 阳极（2 脚 N15_RAW）在下
place('C14', 100.0, 42.0, 180)    # 负极（N15_RAW）在下
place('D7', 107.5, 41.0, 270)     # 阳极（N15_RAW）在下
place('L2', 112.0, 33.5, 270)     # 1 脚 N15_RAW 在上，2 脚 GALVO_N15 在下
place('R13', 110.0, 25.5, 0)      # GALVO_N15 在上
place('C15', 110.0, 16.5, 180)    # 负极（$1N768）在上
place('C16', 106.5, 27.5, 180)    # GALVO_N15 在上

# ---- 顶层铜皮 / 走线示意（矩形并集，x0, y0, x1, y1） ----
CU = [
 ('P15_RAW', (85.9, 77.0, 111.3, 83.0)), ('P15_RAW', (111.3, 80.3, 115.3, 83.0)),          # 横条（L1 2 脚处让开）
 ('P15_RAW', (95.4, 74.4, 97.3, 77.0)), ('P15_RAW', (102.8, 74.8, 104.4, 77.0)),             # D4、C11 正极小桥
 ('P15_RAW', (93.8, 83.0, 95.8, 85.2)),                                                      # 上接 L3 1 脚
 ('P15_RAW', (86.4, 74.3, 88.4, 77.0)),                                                      # 第 7 脚（Sense+）就近接第 8 脚
 ('GALVO_P15', (113.6, 75.5, 120.8, 77.6)), ('GALVO_P15', (117.6, 22.0, 120.8, 77.6)),       # L1 → 内侧通道（J2 / J3 本体下）
 ('GALVO_P15', (120.8, 63.0, 121.5, 65.0)), ('GALVO_P15', (120.8, 22.0, 121.5, 23.8)),       # 接 J2.1、J3.1
 ('GALVO_P15', (116.2, 69.8, 117.6, 71.3)), ('GALVO_P15', (116.2, 64.4, 117.6, 65.7)),       # C13、R12 上脚
 ('$1N765', (111.4, 58.2, 115.4, 59.6)),                                                     # R12 下脚 → C12 正极
 ('CARD_P15', (98.4, 84.0, 121.5, 85.6)),                                                    # L3 → R14 → C19 → J4.1
 ('$1N777', (102.0, 90.0, 107.9, 91.3)),                                                     # R14 → C18 正极
 ('N15_RAW', (83.4, 31.0, 108.6, 37.0)), ('N15_RAW', (108.6, 34.6, 113.0, 37.0)),            # 横条
 ('N15_RAW', (90.6, 37.0, 92.4, 39.2)), ('N15_RAW', (99.2, 37.0, 100.8, 39.6)),              # D5、C14 小桥
 ('N15_RAW', (83.4, 37.0, 84.9, 38.0)),
 ('GALVO_N15', (106.0, 28.9, 113.0, 30.5)), ('GALVO_N15', (112.9, 29.3, 117.0, 31.3)),       # L2 2 脚 / R13 / C16
 ('GALVO_N15', (114.6, 15.5, 117.0, 31.3)), ('GALVO_N15', (114.6, 15.5, 127.5, 19.0)),       # 下行、从 J3 下面绕到板边
 ('GALVO_N15', (124.2, 15.5, 127.5, 75.4)), ('GALVO_N15', (123.5, 32.2, 124.2, 34.0)), ('GALVO_N15', (123.5, 73.3, 124.2, 75.1)),  # 外侧通道
 ('$1N768', (109.4, 18.0, 110.6, 22.6)),
]
VIAS = [(111.0, 66.3), (113.9, 67.4), (117.3, 89.2), (104.8, 25.9), (107.5, 46.7)]   # SMD 地焊盘旁的地过孔（通孔地脚直接落在底层地平面，不用另打）

# ---- 检查 ----
moved = set(NEW)
def rect(p): return (p[0], p[1], p[0] + p[2], p[1] + p[3])
def gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0); dy = max(b[1] - a[3], a[1] - b[3], 0)
    return (dx * dx + dy * dy) ** .5 if (dx or dy) else -min(a[2] - b[0], b[2] - a[0], a[3] - b[1], b[3] - a[1])
others = [c for r, c in C.items() if r not in moved]
pads = [(r, 2 if r in THT else n['b'], rect(p), p[4]) for r, n in NEW.items() for p in n['p']]
pads += [(c['r'], 2 if c['r'] in THT or c['r'] in ('C5', 'C6', 'C7', 'C9', 'J1') else c['b'], rect(p), p[4]) for c in others for p in c['p']]
bad = []
for (ra, la, a, na), (rb, lb, b, nb) in itertools.combinations(pads, 2):
    if ra == rb or (la != lb and 2 not in (la, lb)) or na == nb: continue
    if ra not in moved and rb not in moved: continue
    if gap(a, b) < 0.25: bad.append(f'焊盘间距 {ra}.{na} ↔ {rb}.{nb}: {gap(a, b):.2f}')
bodies = [(r, 0 if r in THT else n['b'], tuple(n['body'])) for r, n in NEW.items()]
bodies += [(c['r'], c['b'], (c['bb'][0], c['bb'][1], c['bb'][0] + c['bb'][2], c['bb'][1] + c['bb'][3])) for c in others if c['r'] not in ELEC]
for (ra, la, a), (rb, lb, b) in itertools.combinations(bodies, 2):
    if ra == rb or la != lb or (ra not in moved and rb not in moved): continue
    if ra in ELEC or rb in ELEC:     # 圆和矩形
        e, o = (a, b) if ra in ELEC else (b, a); cx, cy = (e[0] + e[2]) / 2, (e[1] + e[3]) / 2
        dx = max(o[0] - cx, 0, cx - o[2]); dy = max(o[1] - cy, 0, cy - o[3]); g = (dx * dx + dy * dy) ** .5 - 4
        if ra in ELEC and rb in ELEC: g = math.hypot(cx - (o[0] + o[2]) / 2, cy - (o[1] + o[3]) / 2) - 8
    else: g = gap(a, b)
    if g < 0.2: bad.append(f'本体 {ra} ↔ {rb}: {g:.2f}')
for r, n in NEW.items():
    x0, y0, x1, y1 = n['body']
    for hx, hy, hr in cur['keep']:
        dx = max(x0 - hx, 0, hx - x1); dy = max(y0 - hy, 0, hy - y1)
        if (dx * dx + dy * dy) ** .5 < hr: bad.append(f'{r} 进了安装孔禁布 ({hx},{hy})')
    if min(x0, y0) < 0.3 or x1 > 127.9 or y1 > 94.7: bad.append(f'{r} 离板边太近 {n["body"]}')
    if x0 < 68: bad.append(f'{r} 越过隔离带')
# 铜皮示意 vs 异网焊盘（顶层和通孔）
for net, cu in CU:
    for r, l, p, n in pads:
        if n == net or l == 1: continue
        g = gap(cu, p)
        if g < 0.4: bad.append(f'铜皮 {net} {cu} ↔ {r}.{n}: {g:.2f}')
    if cu[2] > 127.5 or cu[0] < 68: bad.append(f'铜皮出界 {net} {cu}')
for (na, a), (nb, b) in itertools.combinations(CU, 2):
    if na != nb and gap(a, b) < 0.4: bad.append(f'铜皮 {na} {a} ↔ {nb} {b}: {gap(a, b):.2f}')
# 铜皮要碰到本网络的焊盘（每个器件的该网焊盘至少碰一块铜，背面件和通孔地脚除外）
for r, n in NEW.items():
    for p in n['p']:
        if p[4] in ('AUX_GND',) or n['b'] == 1: continue
        if not any(net == p[4] and gap(cu, rect(p)) <= 0 for net, cu in CU): bad.append(f'没接上铜：{r}.{p[5]} {p[4]}')
for x, y in VIAS:
    v = (x - .3, y - .3, x + .3, y + .3)
    for r, l, p, n in pads:
        if n != 'AUX_GND' and l != 1 and gap(v, p) < 0.3: bad.append(f'过孔 ({x},{y}) ↔ {r}.{n}: {gap(v, p):.2f}')
    for net, cu in CU:
        if gap(v, cu) < 0.3: bad.append(f'过孔 ({x},{y}) ↔ 铜皮 {net}')
print('\n'.join(bad) if bad else '没有重叠、间距或连接问题')
json.dump({'new': NEW, 'cu': CU, 'vias': VIAS}, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
