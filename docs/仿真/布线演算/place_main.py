import json, math, itertools
cur = json.load(open('main_cur.json'))
geom = json.load(open('geom.json'))
C = {c['r']: c for c in cur['c']}
C['L8']['bb'] = [round(C['L8']['x'] - 17.85, 2), round(C['L8']['y'] - 18, 2), 35.7, 36.0]
LOG = []

def tfm(c, nx, ny, rot):
    cx, cy = c['x'], c['y']; a = math.radians(rot)
    def tf(x, y):
        dx, dy = x - cx, y - cy
        return nx + dx * math.cos(a) - dy * math.sin(a), ny + dx * math.sin(a) + dy * math.cos(a)
    def rect(x, y, w, h):
        pts = [tf(x, y), tf(x + w, y), tf(x, y + h), tf(x + w, y + h)]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        return [round(min(xs), 3), round(min(ys), 3), round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3)]
    return dict(c, x=nx, y=ny, bb=rect(*c['bb']), p=[rect(*p[:4]) + p[4:] for p in c['p']])

def side(c):
    return {1} if c['b'] else {0}

def ok(n, ignore=()):
    x, y, w, h = n['bb']
    if x < 0.6 or y < 0.6 or x + w > 127.4 or y + h > 94.4:
        return False
    for p in n['p']:
        if p[0] < .6 or p[1] < .6 or p[0] + p[2] > 127.4 or p[1] + p[3] > 94.4:
            return False
    th = any(p[6] for p in n['p'])
    mysides = {0, 1} if th else side(n)
    for o in C.values():
        if o['r'] == n['r'] or o['r'] in ignore:
            continue
        osides = {0, 1} if any(p[6] for p in o['p']) else side(o)
        # 本体（同面）
        if side(o) & mysides or side(n) & osides:
            ox, oy, ow, oh = o['bb']
            if side(o) == side(n) and min(x + w, ox + ow) - max(x, ox) > 0.05 and min(y + h, oy + oh) - max(y, oy) > 0.05:
                return False
        # 焊盘间距 ≥ 0.4
        for p in n['p']:
            pl = {0, 1} if p[6] else side(n)
            for q in o['p']:
                ql = {0, 1} if q[6] else side(o)
                if not pl & ql:
                    continue
                dx = max(q[0] - (p[0] + p[2]), p[0] - (q[0] + q[2]), 0)
                dy = max(q[1] - (p[1] + p[3]), p[1] - (q[1] + q[3]), 0)
                if math.hypot(dx, dy) < 0.4 and not (p[4] and p[4] == q[4]):
                    return False
            # 其他器件本体压在我的焊盘上
            ox, oy, ow, oh = o['bb']
            if side(o) & pl and min(p[0] + p[2], ox + ow) - max(p[0], ox) > 0 and min(p[1] + p[3], oy + oh) - max(p[1], oy) > 0:
                return False
    # 散热器凸台和安装孔
    for k in geom['contacts']:
        if 1 in mysides:
            kx, ky, kw, kh = k['xywh']
            if min(x + w, kx + kw) - max(x, kx) > -0.3 and min(y + h, ky + kh) - max(y, ky) > -0.3:
                return False
    for hx, hy, r in cur['keep'] + [[h[0], h[1], h[2] / 2 + 1] for h in cur['holes']]:
        dx = max(x - hx, 0, hx - (x + w)); dy = max(y - hy, 0, hy - (y + h))
        if math.hypot(dx, dy) < r:
            return False
    return True

def place(ref, tx, ty, rots=(0, 90, 180, 270), bottom=None, why='', rmax=12, ignore=()):
    c = C[ref]
    best = None
    for r in rots:
        for b in ([c['b']] if bottom is None else [bottom]):
            base = dict(c, b=b)
            if b != c['b']:   # 换面：镜像
                base = dict(base, p=[[2 * c['x'] - p[0] - p[2]] + p[1:] for p in c['p']], bb=[2 * c['x'] - c['bb'][0] - c['bb'][2]] + c['bb'][1:])
            for k in range(0, int(rmax / .25) + 1):
                for ang in range(0, 360, 15 if k else 360):
                    nx = tx + k * .25 * math.cos(math.radians(ang)); ny = ty + k * .25 * math.sin(math.radians(ang))
                    n = tfm(base, round(nx, 2), round(ny, 2), r)
                    if ok(n, ignore):
                        d = k * .25
                        if best is None or d < best[0] - 1e-9:
                            best = (d, n, r)
                        break
                if best and best[0] <= k * .25:
                    break
    if best is None:
        LOG.append((ref, None, why)); return False
    old = (c['x'], c['y'], c['b']); C[ref] = best[1]
    LOG.append((ref, [round(old[0], 1), round(old[1], 1), '底' if old[2] else '顶'], [best[1]['x'], best[1]['y'], '底' if best[1]['b'] else '顶'], best[2], why))
    return True

def pad(ref, num):
    p = [q for q in C[ref]['p'] if q[5] == str(num)][0]
    return p[0] + p[2] / 2, p[1] + p[3] / 2

if __name__ == '__main__':
    u3 = pad('U9', 3)
    place('C64', u3[0] - 2.5, u3[1] + 2.5, why='LT3763 VIN 脚就近 4.7 µF（手册）')
    for ref, x in (('CN11', 94.5), ('CN15', 97.5), ('CN18', 100.5)):
        place(ref, x, 47.0, rots=(0,), why='测试点挪到 U9 右下（不挡 MCU 方向的走线），去掉穿过管子区的长线')
    place('CN12', 94.5, 50.5, rots=(0,), why='ISMON 测试点放到 R46 旁')
    place('R12', C['C87']['x'], C['C87']['y'], bottom=True, why='CTRL1 分压上电阻挪到 U9 旁（底层，C87 正下方），长线由 DAC 直接驱动')
    r15 = C['R15']
    place('R24', r15['x'] + 2.5, r15['y'], why='FAULT 上拉电阻挪到 MCU 端，给 U9 左侧让出过孔通道')
    # U9 左侧出线环：左列小电容整体左移约 1 mm，留出过孔位置
    for ref in ('R50', 'R44', 'R43', 'R45', 'R64'):
        place(ref, C[ref]['x'] - 1.0, C[ref]['y'], rots=(0, 90, 180, 270), why='U9 左侧外圈器件左移，给出线和过孔让位', rmax=1.5)
    for ref in ('C81', 'C82', 'C78', 'C83', 'C89'):
        place(ref, C[ref]['x'] - 1.0, C[ref]['y'], rots=(0, 90, 180, 270), why='U9 左侧内圈电容左移约 1 mm，留 2.5 mm 出线环', rmax=1.5)
    p1 = pad('U201', 1)
    place('C203', p1[0] - 1.6, p1[1], why='INA310 VS 旁路贴脚')
    place('C105', C['C105']['x'] - 1.0, C['C105']['y'] + 0.8, why='离 CN14.1 PGND 焊盘拉开到 ≥ 0.4 mm')
    # L8 上移 1.6 mm，R56 竖放在 L8 第 2 脚和 CN14 第 2 脚之间
    l8 = C['L8']; old8 = (l8['x'], l8['y'])
    C['L8'] = tfm(l8, l8['x'], l8['y'] + 1.6, 0)
    if ok(C['L8']):
        LOG.append(('L8', [round(old8[0], 1), round(old8[1], 1), '顶'], [C['L8']['x'], round(C['L8']['y'], 2), '顶'], 0, '上移 1.6 mm，给竖放的 R56 让出 12.3 mm'))
    else:
        C['L8'] = l8; LOG.append(('L8', None, '上移失败'))
    r = C['R56']; cx, cy = 108.0, 38.3
    nets = {q[5]: q[4] for q in r['p']}
    newr = dict(r, x=cx, y=cy, bb=[cx - 2.6, cy - 5.0, 5.2, 10.0],
                p=[[cx - 2.75, cy - 4.5 - 1.65, 5.5, 3.3, nets['2'], '2', 0], [cx - 2.75, cy + 4.5 - 1.65, 5.5, 3.3, nets['1'], '1', 0]])
    oldr = (r['x'], r['y'])
    save = C.pop('R212')
    C['R56'] = newr
    if ok(newr):
        LOG.append(('R56', [round(oldr[0], 1), round(oldr[1], 1), '顶'], [cx, cy, '顶'], 90, '−160° 改竖放：L8 → R56 → CN14 一条直线，开尔文从焊盘内侧引出'))
    else:
        C['R56'] = r; LOG.append(('R56', None, '竖放仍放不下'))
    C['R212'] = save
    place('R212', 102.5, 38.3, rots=(90, 270), why='并联修调电阻跟着 R56 走（默认不焊）', rmax=6)
    for i, ref in enumerate(['C9', 'C10', 'C11', 'C12', 'C13', 'C14', 'C15', 'C16']):
        place(ref, 40 + (i % 4) * 4.5, 64 + (i // 4) * 3.5, bottom=True, why='DCBUS 电容从控制区挪到母线旁（底层）', rmax=14)
    out = dict(cur); out['c'] = list(C.values())
    json.dump(out, open('main_new.json', 'w'))
    for l in LOG: print(l)
