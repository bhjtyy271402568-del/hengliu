"""辅助板前端（防反接 + LM5069）和放行电路的建议摆放：生成新坐标、查重叠 / 间距 / 禁布，导出 json。
坐标 y 向上（和嘉立创一致），单位 mm。用法：python3 aux_place_plan.py aux_cur.json 输出.json
封装尺寸按 aux_cur.json 里同料号焊盘取（0805 / 1206 / SOD-123 / SOT-23 / SMC / 2512）。"""
import json, sys, itertools
cur = json.load(open(sys.argv[1])); C = {c['r']: c for c in cur['c']}

def two(cx, cy, d, w, h, nets, ang):   # 两脚件：ang=0 横放 1 脚在左；90 竖放 1 脚在下；180 横放 1 脚在右；270 竖放 1 脚在上
    import math
    dx, dy = {0: (-d, 0), 90: (0, -d), 180: (d, 0), 270: (0, d)}[ang]
    if ang in (90, 270): w, h = h, w
    p1 = [cx + dx - w / 2, cy + dy - h / 2, w, h, nets[0], '1']
    p2 = [cx - dx - w / 2, cy - dy - h / 2, w, h, nets[1], '2']
    return [p1, p2]
def sot(cx, cy, pins, side, pw=1.0, ph=0.65, dx=1.0, sp=0.95):
    # pins = {'1':net,'2':net,'3':net}；side='L'：1、2 脚在左列（1 下 2 上），3 脚在右；'R' 反之；'Lr'：左列 1 上 2 下
    s = -1 if side.startswith('L') else 1
    y1, y2 = (cy - sp, cy + sp) if not side.endswith('r') else (cy + sp, cy - sp)
    P = [[cx + s * dx - pw / 2, y1 - ph / 2, pw, ph, pins['1'], '1'], [cx + s * dx - pw / 2, y2 - ph / 2, pw, ph, pins['2'], '2'],
         [cx - s * dx - pw / 2, cy - ph / 2, pw, ph, pins['3'], '3']]
    return P

NEW = {}   # 位号: dict(b=底层?, pads, body=[x0,y0,x1,y1])
def put(r, pads, body, b=0): NEW[r] = dict(r=r, b=b, p=pads, body=body)
N = lambda r, k: {p[5]: p[4] for p in C[r]['p']}[k]
# ---- 前端 ----
put('D1', two(18.6, 41.0, 3.4, 3.0, 3.8, [N('D1', '1'), N('D1', '2')], 90), [15.7, 37.5, 21.5, 44.5])
put('D2', two(20.6, 22.55, 1.63, 0.91, 1.22, [N('D2', '1'), N('D2', '2')], 270), [20.0, 21.4, 21.2, 23.7])   # 1 脚 BAT_PROT 在上
put('C1', two(22.55, 22.55, 1.59, 1.49, 1.73, [N('C1', '1'), N('C1', '2')], 270), [21.75, 20.9, 23.35, 24.2])
put('R1', two(17.6, 18.0, 1.0, 1.13, 1.38, [N('R1', '1'), N('R1', '2')], 90), [16.9, 16.7, 18.3, 19.3], b=1)       # 底层：1 脚 GND 在下
put('R2', two(28.0, 21.0, 3.1, 2.0, 3.3, [N('R2', '1'), N('R2', '2')], 0), [24.8, 19.4, 31.2, 22.6])
put('C2', two(28.4, 24.75, 1.59, 1.49, 1.73, [N('C2', '1'), N('C2', '2')], 0), [26.8, 23.95, 30.0, 25.55])
U = C['U1']; dy = -1.0                                        # U1 原方向，整体下移 1 mm
put('U1', [[p[0], p[1] + dy] + p[2:] for p in U['p']], [23.5, 11.0, 26.5, 14.0])
put('R3', two(22.5, 18.05, 1.0, 1.13, 1.38, [N('R3', '1'), N('R3', '2')], 90), [21.8, 16.8, 23.2, 19.3])          # 下 UVLO 上 BAT_PROT
put('R5', two(20.7, 18.05, 1.0, 1.13, 1.38, [N('R5', '1'), N('R5', '2')], 90), [20.0, 16.8, 21.4, 19.3])          # 下 OVLO 上 BAT_PROT
put('R4', two(22.5, 18.05, 1.0, 1.13, 1.38, [N('R4', '1'), N('R4', '2')], 270), [21.8, 16.8, 23.2, 19.3], b=1)   # 底层，正对 R3：下 UVLO 上 GND
put('R6', two(20.7, 18.05, 1.0, 1.13, 1.38, [N('R6', '1'), N('R6', '2')], 270), [20.0, 16.8, 21.4, 19.3], b=1)
put('C4', two(21.9, 7.6, 1.59, 1.49, 1.73, [N('C4', '1'), N('C4', '2')], 270), [21.1, 5.9, 22.7, 9.3])             # 上 TIMER 下 GND
put('R7', two(23.8, 7.0, 1.0, 1.13, 1.38, [N('R7', '1'), N('R7', '2')], 90), [23.1, 5.7, 24.5, 8.3])                # 上 PWR 下 GND
# ---- 放行电路 ----
put('R8', two(49.4, 14.0, 1.0, 1.13, 1.38, [N('R8', '1'), N('R8', '2')], 90), [48.7, 12.7, 50.1, 15.3])            # 下 基极 上 AUX_IN
put('R9', two(49.4, 10.0, 1.0, 1.13, 1.38, [N('R9', '2'), N('R9', '1')], 90), [48.7, 8.7, 50.1, 11.3])            # 下 PGD 上 基极
put('Q3', sot(52.0, 13.0, {k: N('Q3', k) for k in '123'}, 'L', 1.25, 0.7), [51.3, 11.5, 52.7, 14.5])
put('R10', two(53.0, 9.8, 1.0, 1.13, 1.38, [N('R10', '2'), N('R10', '1')], 90), [52.3, 8.5, 53.7, 11.1])          # 下 Q4 基极 上 Q3 集电极
put('Q4', sot(54.0, 6.3, {k: N('Q4', k) for k in '123'}, 'Lr', 1.0, 0.65), [53.3, 4.8, 54.7, 7.8])               # 左列 1 基极上、2 发射极下
put('R11', two(51.4, 6.8, 1.0, 1.13, 1.38, [N('R11', '1'), N('R11', '2')], 90), [50.7, 5.5, 52.1, 8.1])            # 下 GND 上 Q4 基极
put('D3', sot(56.2, 10.5, {k: N('D3', k) for k in '123'}, 'R', 1.07, 0.6, 1.23), [55.5, 9.0, 56.9, 12.0])        # 右列 1 下(CTRL_P) 2 上(CTRL_N)，3 阴极在左

moved = set(NEW)
others = [c for r, c in C.items() if r not in moved]
def rect(p): return (p[0], p[1], p[0] + p[2], p[1] + p[3])
def gap(a, b):
    dx = max(b[0] - a[2], a[0] - b[2], 0); dy = max(b[1] - a[3], a[1] - b[3], 0)
    return (dx * dx + dy * dy) ** .5 if (dx or dy) else -min(a[2] - b[0], b[2] - a[0], a[3] - b[1], b[3] - a[1])
bad = []
pads = [(r, NEW[r]['b'], rect(p), p[4]) for r in NEW for p in NEW[r]['p']]
pads += [(c['r'], c['b'], rect(p), p[4]) for c in others for p in c['p'] if c['r'] not in ('U2', 'U3', 'J1', 'J2', 'J3', 'J4', 'C5', 'C6', 'C7', 'C9', 'C11', 'C12', 'C14', 'C15', 'C18')] \
      + [(c['r'], 2, rect(p), p[4]) for c in others for p in c['p'] if c['r'] in ('U2', 'U3', 'J1', 'J2', 'J3', 'J4', 'C5', 'C6', 'C7', 'C9', 'C11', 'C12', 'C14', 'C15', 'C18')]   # 插件焊盘两面都有
for (ra, la, a, na), (rb, lb, b, nb) in itertools.combinations(pads, 2):
    if ra == rb or (la != lb and 2 not in (la, lb)) or na == nb: continue
    g = gap(a, b)
    if g < 0.25: bad.append(f'焊盘间距 {ra}.{na} ↔ {rb}.{nb}: {g:.2f} mm')
bodies = [(r, NEW[r]['b'], tuple(NEW[r]['body'])) for r in NEW]
for c in others:
    bb = c['bb']; bodies.append((c['r'], 2 if c['r'] in ('U2', 'U3', 'J1', 'C5', 'C6', 'C7', 'C9') else c['b'], (bb[0], bb[1], bb[0] + bb[2], bb[1] + bb[3])))
for (ra, la, a), (rb, lb, b) in itertools.combinations(bodies, 2):
    if ra == rb or (la != lb and 2 not in (la, lb)): continue
    if ra not in moved and rb not in moved: continue
    g = gap(a, b)
    if g < 0.2: bad.append(f'本体 {ra} ↔ {rb}: {g:.2f} mm')
for r in NEW:
    x0, y0, x1, y1 = NEW[r]['body']
    for hx, hy, hr in cur['keep']:
        dx = max(x0 - hx, 0, hx - x1); dy = max(y0 - hy, 0, hy - y1)
        if (dx * dx + dy * dy) ** .5 < hr: bad.append(f'{r} 进了安装孔禁布 ({hx},{hy})')
    if x0 < 0.5 or y0 < 0.5: bad.append(f'{r} 离板边太近')
    if x1 > 60: bad.append(f'{r} 越过一次侧边界 x 60')
print('\n'.join(bad) if bad else '没有重叠或间距问题')
json.dump({'new': NEW}, open(sys.argv[2], 'w'), ensure_ascii=False, indent=0)
