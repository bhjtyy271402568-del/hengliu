"""恒流源板四层布线演算。

层：0 = L1 顶层，1 = L3 内层 2（信号），2 = L4 底层；L2 是地平面（GND / PGND 分区），不走线。
大电流网络不走线，按“焊盘周围铺铜”的方式生成铺铜区（L1、L4），其他网络不能穿过别人的铺铜区。
大电流网络上的小焊盘（检测、分压、滤波）当作“尾巴”走线接回铺铜区；开尔文线必须接到指定电阻焊盘。
用法：python3 -I router4.py placement.json out.json
"""
import json, sys, math, heapq
import numpy as np
from scipy import ndimage

RES = 0.2
BW, BH = 128.0, 95.0
W, H = int(BW / RES) + 1, int(BH / RES) + 1
NL = 3
LAYER_COST = (1.0, 1.15, 1.6)   # L1 / L3 / L4
VIA_R, VIA_COST = 0.3, 2.5 / RES
POUR_VIA_COST = 6.0 / RES
POWER_COMPS = {'Q1','Q2','Q4','Q5','Q6','Q7','Q8','Q9','Q10','L8','R42','R56','CN3','CN14','D2','D11','D12'}
POWER = ['VCC_BAT', 'GND_BAT', 'DCBUS', 'LT_VIN', 'LT_SW', 'VCC_OUT', 'LT_SHUNT_P', 'PGND']
GROUNDS = {'GND', 'PGND'}
KELVIN = {  # 尾巴焊盘 → 必须接到的焊盘
    ('R66', 'LT_SHUNT_P'): 'R56', ('R69', 'VCC_OUT'): 'R56',
    ('U201', 'LT_SHUNT_P'): 'R56', ('U201', 'VCC_OUT'): 'R56',
    ('R43', 'DCBUS'): 'R42', ('R44', 'LT_VIN'): 'R42',
}
WIDTH = {'LT_TG': .6, 'LT_BG': .6, 'LT_INTVCC': .6, '$1N2974': .6, '12V': .5, '5V': .5, 'VCC': .4, 'AVCC': .4}
GATE_NETS = {'$1N2965', '$1N2970', '$1N3014', '$1N2967', '$1N2972', '$1N3016'}


def cells(x0, y0, x1, y1):
    # 格点中心落在矩形内才算（避免把 0.65 mm 间距的引脚涂成一片）
    i0, i1 = int(math.ceil(x0 / RES - 0.5)), int(math.floor(x1 / RES + 0.5))
    j0, j1 = int(math.ceil(y0 / RES - 0.5)), int(math.floor(y1 / RES + 0.5))
    if i1 < i0: i0 = i1 = int(round((x0 + x1) / 2 / RES))
    if j1 < j0: j0 = j1 = int(round((y0 + y1) / 2 / RES))
    return max(0, i0), min(W - 1, i1), max(0, j0), min(H - 1, j1)


def disk(r):
    k = int(math.ceil(r / RES))
    yy, xx = np.ogrid[-k:k + 1, -k:k + 1]
    return (xx * xx + yy * yy) <= (r / RES) ** 2


class Board:
    def __init__(self, pl, geom):
        self.pl = pl
        self.keep = np.zeros((NL, H, W), bool)
        e = int(0.5 / RES)
        for l in range(NL):
            self.keep[l, :e, :] = self.keep[l, -e:, :] = self.keep[l, :, :e] = self.keep[l, :, -e:] = True
        yy, xx = np.mgrid[0:H, 0:W] * RES
        for cx, cy, r in pl.get('keep', []):
            self.keep[:, (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r] = True
        for cx, cy, d in pl.get('holes', []):
            self.keep[:, (xx - cx) ** 2 + (yy - cy) ** 2 <= (d / 2 + 0.5) ** 2] = True
        self.pads = []
        for c in pl['c']:
            for p in c['p']:
                x, y, w, h, net, num, th = p
                layers = (0, 1, 2) if th else ((2,) if c['b'] else (0,))
                self.pads.append(dict(ref=c['r'], num=num, net=net, x=x, y=y, w=w, h=h, layers=layers, th=th,
                                      cells=cells(x, y, x + w, y + h), cx=x + w / 2, cy=y + h / 2))
        nets = sorted({p['net'] for p in self.pads if p['net']})
        self.nid = {n: i for i, n in enumerate(nets)}
        self.nets = nets
        self.cu = np.full((NL, H, W), -1, np.int16)
        for p in self.pads:
            i0, i1, j0, j1 = p['cells']
            v = self.nid.get(p['net'], -2)
            for l in p['layers']:
                self.cu[l, j0:j1 + 1, i0:i1 + 1] = v
        self.geom = geom
        self.make_pours()
        self.routes, self.vias, self.notes = {}, [], []

    # ---------- 铺铜区 ----------
    def is_pour_pad(self, p):
        return p['net'] in POWER and (p['w'] * p['h'] >= 2.0 or p['th'] and p['w'] >= 2.0 or p['ref'] in POWER_COMPS)

    def make_pours(self):
        terr = np.full((NL, H, W), -1, np.int16)
        dist = np.full((NL, H, W), np.inf)
        contacts = {'Q5': 'LT_VIN', 'Q6': 'LT_VIN', 'Q7': 'LT_VIN', 'Q8': 'LT_SW', 'Q9': 'LT_SW', 'Q10': 'LT_SW',
                    'Q1': 'DCBUS', 'Q2': 'DCBUS', 'Q4': 'GND_BAT'}
        self.pour_pads = [p for p in self.pads if self.is_pour_pad(p)]
        for net in POWER:
            if net not in self.nid:
                continue
            nid = self.nid[net]
            for l in (0, 2):
                m = np.zeros((H, W), bool)
                for p in self.pour_pads:
                    if p['net'] == net and l in p['layers']:
                        i0, i1, j0, j1 = p['cells']
                        m[j0:j1 + 1, i0:i1 + 1] = True
                if l == 2:
                    for k in self.geom['contacts']:
                        if contacts.get(k['ref']) == net:
                            x, y, w, h = k['xywh']
                            i0, i1, j0, j1 = cells(x, y, x + w, y + h)
                            m[j0:j1 + 1, i0:i1 + 1] = True
                if not m.any():
                    continue
                d = ndimage.distance_transform_edt(~m) * RES
                t = d <= 2.5
                t = ndimage.binary_closing(t, structure=disk(2.0), iterations=1)
                better = t & (d < dist[l])
                terr[l][better] = nid
                dist[l][better] = d[better]
        # 不同网络铺铜区之间留 0.3 mm
        for l in (0, 2):
            for nid in np.unique(terr[l]):
                if nid < 0:
                    continue
                m = terr[l] == nid
                other = (terr[l] >= 0) & ~m
                d = ndimage.distance_transform_edt(~other) * RES
                terr[l][m & (d < 0.3)] = -1
        terr[self.keep] = -1
        self.terr = terr

    # ---------- 布线 ----------
    def free(self, nid, half, clr, near=None):
        out = np.zeros((NL, H, W), bool)
        for l in range(NL):
            other = ((self.cu[l] != -1) & (self.cu[l] != nid)) | ((self.terr[l] >= 0) & (self.terr[l] != nid))
            if near is not None and l != 1:
                # 自己焊盘附近允许穿铺铜区出线
                other = ((self.cu[l] != -1) & (self.cu[l] != nid)) | ((self.terr[l] >= 0) & (self.terr[l] != nid) & ~near)
            d = ndimage.distance_transform_edt(~other) * RES
            out[l] = (d >= half + clr) & ~self.keep[l] | (self.cu[l] == nid) | (self.terr[l] == nid)
        return out

    def astar(self, nid, half, tree, target_mask, tlayers, bbox, near):
        clr = 0.2 if half <= 0.2 else 0.25
        fr = self.free(nid, half, clr, near)
        frn = self.free(nid, 0.06, 0.127, near)   # 细间距引脚旁收窄到 0.12 mm 线、0.127 mm 间距
        fr = fr | (frn & near[None])
        vf = np.zeros((NL, H, W), bool)
        for l in range(NL):
            other = (self.cu[l] != -1) & (self.cu[l] != nid)
            d = ndimage.distance_transform_edt(~other) * RES
            vf[l] = (d >= VIA_R + 0.2) & ~self.keep[l]
        via_ok = vf.all(axis=0)
        in_pour = ((self.terr >= 0) & (self.terr != nid)).any(axis=0)
        ys, xs = np.nonzero(target_mask)
        tx, ty = xs.mean(), ys.mean()
        i0, i1, j0, j1 = bbox
        heap, dist, seen, prev = [], {}, set(), {}
        for l in range(NL):
            js, is_ = np.nonzero(tree[l][j0:j1 + 1, i0:i1 + 1])
            for j, i in zip(js + j0, is_ + i0):
                k = (l, j, i)
                if target_mask[j, i] and l in tlayers:
                    return [k]
                dist[k] = 0.0
                heapq.heappush(heap, (math.hypot(i - tx, j - ty), 0.0, k, None))
        steps = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
        while heap:
            f, g, k, pk = heapq.heappop(heap)
            if k in seen:
                continue
            seen.add(k); prev[k] = pk
            l, j, i = k
            if target_mask[j, i] and l in tlayers:
                path = []
                while k is not None:
                    path.append(k); k = prev[k]
                return path[::-1]
            for di, dj, s in steps:
                ni, nj = i + di, j + dj
                if ni < i0 or ni > i1 or nj < j0 or nj > j1 or not fr[l, nj, ni]:
                    continue
                nk = (l, nj, ni); ng = g + s * LAYER_COST[l]
                if ng < dist.get(nk, 1e18):
                    dist[nk] = ng
                    heapq.heappush(heap, (ng + math.hypot(ni - tx, nj - ty), ng, nk, k))
            if via_ok[j, i]:
                for nl in range(NL):
                    if nl == l:
                        continue
                    nk = (nl, j, i); ng = g + (POUR_VIA_COST if in_pour[j, i] else VIA_COST)
                    if ng < dist.get(nk, 1e18):
                        dist[nk] = ng
                        heapq.heappush(heap, (ng + math.hypot(i - tx, j - ty), ng, nk, k))
        return None

    def paint(self, nid, half, path, near):
        for l in range(NL):
            for hw, sel in ((half, False), (min(half, 0.06), True)):
                m = np.zeros((H, W), bool)
                for (pl, j, i) in path:
                    if pl == l and bool(near[j, i]) == sel:
                        m[j, i] = True
                if m.any():
                    d = ndimage.distance_transform_edt(~m) * RES
                    self.cu[l][(d <= hw) & (self.cu[l] == -1)] = nid
        for a, b in zip(path, path[1:]):
            if a[0] != b[0]:
                cut = bool(((self.terr[:, a[1], a[2]] >= 0) & (self.terr[:, a[1], a[2]] != nid)).any())
                self.vias.append((round(a[2] * RES, 2), round(a[1] * RES, 2), self.nets[nid], cut))
                k = int(VIA_R / RES)
                sl = (slice(max(0, a[1] - k), a[1] + k + 1), slice(max(0, a[2] - k), a[2] + k + 1))
                for l in range(NL):
                    sub = self.cu[l][sl]
                    sub[sub == -1] = nid

    def pad_mask(self, p):
        m = np.zeros((H, W), bool)
        i0, i1, j0, j1 = p['cells']
        m[j0:j1 + 1, i0:i1 + 1] = True
        return m

    def connect(self, net, pads_seq, half, root=None):
        """root：起始铜（铺铜区或指定焊盘）；pads_seq：要依次连上的焊盘。"""
        nid = self.nid[net]
        tree = np.zeros((NL, H, W), bool)
        segs, fails = [], []
        if root is not None:
            tree |= root
        todo = list(pads_seq)
        if not tree.any():
            p0 = todo.pop(0)
            for l in p0['layers']:
                tree[l] |= self.pad_mask(p0)
        while todo:
            ys, xs = np.nonzero(tree.any(axis=0))
            best = min(todo, key=lambda p: np.min(np.hypot(xs * RES - p['cx'], ys * RES - p['cy'])) if len(xs) else 0)
            todo.remove(best)
            tm = self.pad_mask(best)
            near = np.zeros((H, W), bool)
            mm = int(1.2 / RES)
            for q in [best] + [q for q in self.pads if q['net'] == net and min(q['w'], q['h']) < 1.0]:
                i0, i1, j0, j1 = q['cells']
                near[max(0, j0 - mm):j1 + mm + 1, max(0, i0 - mm):i1 + mm + 1] = True
            path = None
            for m in (8, 25, 200):
                d = ndimage.distance_transform_edt(~tree.any(axis=0)) * RES
                jj, ii = int(best['cy'] / RES), int(best['cx'] / RES)
                # 只在树里离目标最近的那一片附近搜索，避免大铺铜区全图展开
                sub = tree.any(axis=0)
                ys, xs = np.nonzero(sub)
                dd = np.hypot(xs * RES - best['cx'], ys * RES - best['cy'])
                sel = dd <= dd.min() + m
                x0, x1 = xs[sel].min() * RES, xs[sel].max() * RES
                y0, y1 = ys[sel].min() * RES, ys[sel].max() * RES
                bb = cells(min(x0, best['x']) - m, min(y0, best['y']) - m, max(x1, best['x'] + best['w']) + m, max(y1, best['y'] + best['h']) + m)
                tr = tree.copy()
                tr[:, :bb[2], :] = False; tr[:, bb[3] + 1:, :] = False; tr[:, :, :bb[0]] = False; tr[:, :, bb[1] + 1:] = False
                # 限制源点数量：只保留离目标最近的 400 个树格
                if tr.sum() > 400:
                    ls, js, is_ = np.nonzero(tr)
                    dd = np.hypot(is_ * RES - best['cx'], js * RES - best['cy'])
                    keep = np.argsort(dd)[:400]
                    tr[:] = False
                    tr[ls[keep], js[keep], is_[keep]] = True
                path = self.astar(nid, half, tr, tm, best['layers'], bb, near)
                if path:
                    break
            if path is None:
                fails.append(f"{best['ref']}.{best['num']}")
            else:
                self.paint(nid, half, path, near)
                segs.append(path)
                for (l, j, i) in path:
                    tree[l, j, i] = True
            for l in best['layers']:
                tree[l] |= tm
        r = self.routes.setdefault(net, dict(w=2 * half, segs=[], fails=[]))
        r['segs'] += segs; r['fails'] += fails

    def ground_fanout(self):
        self.no_via = []
        for g in ('GND', 'PGND'):
            if g not in self.nid:
                continue
            nid = self.nid[g]
            for p in [q for q in self.pads if q['net'] == g and not q['th']]:
                l0 = p['layers'][0]
                if g == 'PGND' and self.terr[l0, int(p['cy'] / RES), int(p['cx'] / RES)] == nid:
                    continue
                ok = np.ones((H, W), bool)
                i0, i1, j0, j1 = p['cells']
                k = int(2.0 / RES)
                sl = (slice(max(0, j0 - k), j1 + k + 1), slice(max(0, i0 - k), i1 + k + 1))
                for l in range(NL):
                    sub_cu = self.cu[l][sl]
                    other = (sub_cu != -1) & (sub_cu != nid)
                    if l != 1:
                        other |= (self.terr[l][sl] >= 0) & (self.terr[l][sl] != nid)
                    d = ndimage.distance_transform_edt(~other) * RES
                    ok_l = (d >= VIA_R + 0.2) & ~self.keep[l][sl]
                    ok = ok[sl] & ok_l if ok.shape != ok_l.shape else ok & ok_l
                js, is_ = np.nonzero(ok)
                if not len(js):
                    self.no_via.append(f"{p['ref']}.{p['num']}({g})")
                    continue
                cj, ci = (j0 + j1) / 2 - sl[0].start, (i0 + i1) / 2 - sl[1].start
                n = np.argmin((js - cj) ** 2 + (is_ - ci) ** 2)
                vj, vi = js[n] + sl[0].start, is_[n] + sl[1].start
                kk = int(VIA_R / RES)
                for l in range(NL):
                    sub = self.cu[l][vj - kk:vj + kk + 1, vi - kk:vi + kk + 1]
                    sub[sub == -1] = nid
                self.vias.append((round(vi * RES, 2), round(vj * RES, 2), g, False))

    def run(self, order=None):
        # 1) 大电流网络的尾巴
        for net in POWER:
            if net not in self.nid or net in GROUNDS:
                continue
            nid = self.nid[net]
            tails = [p for p in self.pads if p['net'] == net and not self.is_pour_pad(p)]
            pour = (self.terr == nid)
            for p in tails:
                if pour[list(p['layers'])[0], int(p['cy'] / RES), int(p['cx'] / RES)]:
                    continue
                tgt = KELVIN.get((p['ref'], net))
                if tgt:
                    rp = [q for q in self.pads if q['ref'] == tgt and q['net'] == net][0]
                    root = np.zeros((NL, H, W), bool)
                    for l in rp['layers']:
                        root[l] |= self.pad_mask(rp)
                    self.connect(net, [p], 0.15, root)
                else:
                    self.connect(net, [p], 0.2, pour)
        # 2) 信号
        sig = [n for n in self.nets if n not in POWER and n not in GROUNDS and sum(p['net'] == n for p in self.pads) >= 2]
        def span(n):
            ps = [p for p in self.pads if p['net'] == n]
            return max(p['cx'] for p in ps) - min(p['cx'] for p in ps) + max(p['cy'] for p in ps) - min(p['cy'] for p in ps)
        def wid(n):
            return 0.6 if n in GATE_NETS else WIDTH.get(n, 0.2)
        sig.sort(key=lambda n: (-wid(n), span(n)))
        if order:
            sig.sort(key=lambda n: order.index(n) if n in order else 999)
        for n in sig:
            ps = [p for p in self.pads if p['net'] == n]
            ps.sort(key=lambda p: -p['w'] * p['h'])
            self.connect(n, ps, wid(n) / 2)
        # 3) 最后给 GND / PGND 小焊盘打地过孔
        self.ground_fanout()

    # ---------- 地 ----------
    def ground_check(self):
        """GND / PGND 的小焊盘要能在 1.5 mm 内打过孔到 L2；L2 按焊盘归属分 GND / PGND 两区。"""
        gp = [p for p in self.pads if p['net'] in GROUNDS]
        res = dict(no_via=list(getattr(self, 'no_via', [])), wrong_side=[])
        vf = {}
        for g in GROUNDS:
            if g not in self.nid:
                continue
            nid = self.nid[g]
            ok = np.ones((H, W), bool)
            for l in range(NL):
                other = ((self.cu[l] != -1) & (self.cu[l] != nid)) | ((self.terr[l] >= 0) & (self.terr[l] != nid))
                d = ndimage.distance_transform_edt(~other) * RES
                ok &= (d >= VIA_R + 0.2) & ~self.keep[l]
            vf[g] = ok
        # L2 分区：按最近的地焊盘
        mg = np.zeros((H, W), bool); mp = np.zeros((H, W), bool)
        for p in gp:
            (mg if p['net'] == 'GND' else mp)[p['cells'][2]:p['cells'][3] + 1, p['cells'][0]:p['cells'][1] + 1] = True
        dg = ndimage.distance_transform_edt(~mg); dp = ndimage.distance_transform_edt(~mp)
        self.l2 = np.where(dg < dp, 0, 1)   # 0 = GND，1 = PGND
        return res

    def crossings(self):
        """L1 / L3 走线跨 L2 的 GND / PGND 分界（参考平面换了）。"""
        out = {}
        for n, r in self.routes.items():
            c = 0
            for path in r['segs']:
                for a, b in zip(path, path[1:]):
                    if a[0] == b[0] and a[0] in (0, 1) and self.l2[a[1], a[2]] != self.l2[b[1], b[2]]:
                        c += 1
            if c:
                out[n] = c
        return out

    def report(self):
        nets = {}
        for n, r in self.routes.items():
            L = [0.0] * NL; nv = 0
            for path in r['segs']:
                for a, b in zip(path, path[1:]):
                    if a[0] != b[0]:
                        nv += 1
                    else:
                        L[a[0]] += math.hypot(a[1] - b[1], a[2] - b[2]) * RES
            nets[n] = dict(w=r['w'], L=[round(x, 1) for x in L], vias=nv, fails=r['fails'])
        g = self.ground_check()
        return dict(nets=nets, vias=len(self.vias), ground=g, cross=self.crossings(),
                    pour_area={self.nets[i]: [round(float((self.terr[l] == i).sum() * RES * RES), 0) for l in (0, 2)] for i in np.unique(self.terr) if i >= 0})


def solve(pl, geom, passes=2):
    best, order = None, None
    for k in range(passes):
        b = Board(pl, geom)
        b.run(order)
        nf = sum(len(r['fails']) for r in b.routes.values())
        print(f'  第 {k + 1} 轮：布不通 {nf}', flush=True)
        if best is None or nf < best[0]:
            best = (nf, b)
        if nf == 0:
            break
        failed = [n for n, r in b.routes.items() if r['fails']]
        order = failed + [n for n in b.routes if n not in failed]
    return best[1]


if __name__ == '__main__':
    pl = json.load(open(sys.argv[1])); geom = json.load(open(sys.argv[3])) if len(sys.argv) > 3 else json.load(open('geom.json'))
    b = solve(pl, geom)
    rep = b.report()
    rep['paths'] = {n: [[[p[0], round(p[2] * RES, 2), round(p[1] * RES, 2)] for p in s] for s in r['segs']] for n, r in b.routes.items()}
    rep['via_xy'] = b.vias
    np.save(sys.argv[2].replace('.json', '_terr.npy'), b.terr)
    np.save(sys.argv[2].replace('.json', '_l2.npy'), b.l2)
    json.dump(rep, open(sys.argv[2], 'w'), ensure_ascii=False)
    tot = [sum(v['L'][l] for v in rep['nets'].values()) for l in range(NL)]
    print(f"走线 L1 {tot[0]:.0f} / L3 {tot[1]:.0f} / L4 {tot[2]:.0f} mm，过孔 {rep['vias']}")
    for n, v in rep['nets'].items():
        if v['fails']:
            print('  布不通', n, v['fails'])
    print('跨地分区', rep['cross'])
    print('打不了地过孔', rep['ground']['no_via'])
