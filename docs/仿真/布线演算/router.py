"""两层板网格布线演算：A* 迷宫布线 + 地铺铜连通检查。

用法：python3 -I router.py placement.json out.json
placement.json 的格式和 pagedata.json 里 'aux' 一样（c: 器件列表, keep: 禁布圆）。
"""
import json, sys, math, heapq
import numpy as np
from scipy import ndimage

RES = 0.25           # 网格 mm
CLR = 0.30           # 间距 mm
VIA_R = 0.45         # 过孔焊盘半径 mm（0.4 孔 / 0.9 盘）
VIA_COST = 3.0 / RES # 一个过孔折合 3 mm 走线
BOT_MUL = 2.0        # 非地网络走底层的代价倍数（底层留给地）
BW, BH = 128.0, 95.0
W, H = int(BW / RES) + 1, int(BH / RES) + 1

GROUNDS = {'AUX_GND', 'BAT_GND'}
WIDTH = {  # 1 oz 铜，按 IPC-2221 外层温升 20 °C 粗选
    'AUX_IN': 2.0, 'BAT_PROT': 2.0, '$1N661': 2.0, '$1N667': 2.0,
    'P15_RAW': 2.5, 'GALVO_P15': 2.0, 'GALVO_N15': 2.0, 'N15_RAW': 2.0, 'CARD_P15': 1.5,
}
SIDE = {'BAT_GND': (0, 58), 'AUX_GND': (66, 128)}


def cells(x0, y0, x1, y1):
    i0, i1 = max(0, int(math.floor(x0 / RES))), min(W - 1, int(math.ceil(x1 / RES)))
    j0, j1 = max(0, int(math.floor(y0 / RES))), min(H - 1, int(math.ceil(y1 / RES)))
    return i0, i1, j0, j1


def load(pl):
    keep = np.zeros((H, W), bool)
    # 隔离带
    i0, i1, _, _ = cells(58, 0, 66, 0)
    keep[:, i0:i1 + 1] = True
    # 板边 0.5 mm
    e = int(0.5 / RES)
    keep[:e, :] = keep[-e:, :] = True
    keep[:, :e] = keep[:, -e:] = True
    yy, xx = np.mgrid[0:H, 0:W] * RES
    for cx, cy, r in pl.get('keep', []):
        keep |= (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r
    pads = []
    for c in pl['c']:
        for p in c['p']:
            x, y, w, h, net, num, th = p
            layers = (0, 1) if th else ((1,) if c['b'] else (0,))
            pads.append(dict(ref=c['r'], num=num, net=net, x=x, y=y, w=w, h=h, layers=layers, th=th))
    return keep, pads


class Board:
    def __init__(self, pl):
        self.keep, self.pads = load(pl)
        nets = sorted({p['net'] for p in self.pads if p['net']})
        self.nid = {n: i for i, n in enumerate(nets)}
        self.nets = nets
        self.cu = [np.full((H, W), -1, np.int16) for _ in range(2)]
        for p in self.pads:
            i0, i1, j0, j1 = cells(p['x'], p['y'], p['x'] + p['w'], p['y'] + p['h'])
            v = self.nid.get(p['net'], -2)  # 无网络焊盘也算障碍
            for l in p['layers']:
                self.cu[l][j0:j1 + 1, i0:i1 + 1] = v
            p['cells'] = (i0, i1, j0, j1)
        self.routes = {}
        self.vias = []

    def free(self, nid, half, clr=CLR):
        """每层：离其他网络铜 ≥ half + clr 的格子。"""
        out = []
        for l in range(2):
            other = (self.cu[l] != -1) & (self.cu[l] != nid)
            d = ndimage.distance_transform_edt(~other) * RES
            out.append((d >= half + clr) & ~self.keep | (self.cu[l] == nid))
        return out

    def astar(self, nid, half, target, bbox, tree):
        clr = CLR if half > 0.3 else 0.2
        fr = self.free(nid, half, clr)
        via_ok = self.free(nid, VIA_R, clr)
        via_ok = via_ok[0] & via_ok[1]
        # 宽线进小焊盘：焊盘 2.5 mm 内允许收窄到 0.25 mm（neck-down）
        self.near = np.zeros((H, W), bool)
        if half > 0.2:
            frn = self.free(nid, 0.125, 0.2)
            a, b, c, d = target['cells']
            m = int(2.5 / RES)
            self.near[max(0, c - m):d + m + 1, max(0, a - m):b + m + 1] = True
            for q in self.pads:   # 已连上的小焊盘附近也允许收窄
                if q['net'] == self.nets[nid] and tree[q['layers'][0]][q['cells'][2], q['cells'][0]] and min(q['w'], q['h']) < 2 * half:
                    a, b, c, d = q['cells']
                    self.near[max(0, c - m):d + m + 1, max(0, a - m):b + m + 1] = True
            fr = [fr[l] | (frn[l] & self.near) for l in range(2)]
        tx, ty = (target['cells'][0] + target['cells'][1]) / 2, (target['cells'][2] + target['cells'][3]) / 2
        i0, i1, j0, j1 = bbox
        tgt = np.zeros((H, W), bool)
        a, b, c, d = target['cells']
        tgt[c:d + 1, a:b + 1] = True
        dist = {}
        heap = []
        for l in range(2):
            js, is_ = np.nonzero(tree[l][j0:j1 + 1, i0:i1 + 1])
            for j, i in zip(js + j0, is_ + i0):
                if tgt[j, i] and l in target['layers']:
                    continue
                k = (l, j, i)
                dist[k] = 0.0
                heapq.heappush(heap, (math.hypot(i - tx, j - ty), 0.0, k, None))
        prev = {}
        mul = (1.0, BOT_MUL)
        steps = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
        seen = set()
        while heap:
            f, g, k, pk = heapq.heappop(heap)
            if k in seen:
                continue
            seen.add(k)
            prev[k] = pk
            l, j, i = k
            if tgt[j, i] and l in target['layers']:
                path = []
                while k is not None:
                    path.append(k)
                    k = prev[k]
                return path[::-1]
            for di, dj, s in steps:
                ni, nj = i + di, j + dj
                if ni < i0 or ni > i1 or nj < j0 or nj > j1 or not fr[l][nj, ni]:
                    continue
                nk = (l, nj, ni)
                ng = g + s * mul[l]
                if ng < dist.get(nk, 1e18):
                    dist[nk] = ng
                    heapq.heappush(heap, (ng + math.hypot(ni - tx, nj - ty), ng, nk, k))
            if via_ok[j, i]:
                nk = (1 - l, j, i)
                ng = g + VIA_COST
                if ng < dist.get(nk, 1e18):
                    dist[nk] = ng
                    heapq.heappush(heap, (ng + math.hypot(i - tx, j - ty), ng, nk, k))
        return None

    def paint(self, nid, half, path):
        near = getattr(self, 'near', np.zeros((H, W), bool))
        for l in range(2):
            for hw, sel in ((half, lambda j, i: not near[j, i]), (min(half, 0.125), lambda j, i: near[j, i])):
                m = np.zeros((H, W), bool)
                for (pl, j, i) in path:
                    if pl == l and sel(j, i):
                        m[j, i] = True
                if m.any():
                    d = ndimage.distance_transform_edt(~m) * RES
                    self.cu[l][(d <= hw) & (self.cu[l] == -1)] = nid
        for a, b in zip(path, path[1:]):
            if a[0] != b[0]:
                self.vias.append((a[2] * RES, a[1] * RES, self.nets[nid]))
                yy, xx = np.ogrid[0:H, 0:W]
                disk = (xx - a[2]) ** 2 + (yy - a[1]) ** 2 <= (VIA_R / RES) ** 2
                for l in range(2):
                    self.cu[l][disk & (self.cu[l] == -1)] = nid

    def route_net(self, net):
        nid = self.nid[net]
        w = WIDTH.get(net, 0.25)
        pads = [p for p in self.pads if p['net'] == net]
        # 从最大的焊盘（通常是模块脚或接口）开始
        pads.sort(key=lambda p: -p['w'] * p['h'])
        done = [pads[0]]
        todo = pads[1:]
        tree = [np.zeros((H, W), bool) for _ in range(2)]
        def addpad(p):
            i0, i1, j0, j1 = p['cells']
            for l in p['layers']:
                tree[l][j0:j1 + 1, i0:i1 + 1] = True
        addpad(pads[0])
        segs, fails = [], []
        while todo:
            best = min(((math.hypot(p['x'] - q['x'], p['y'] - q['y']), p) for p in todo for q in done), key=lambda t: t[0])[1]
            todo.remove(best)
            xs = [q['x'] for q in done] + [best['x']]
            ys = [q['y'] for q in done] + [best['y']]
            path = None
            for m in (12, 30, 200):
                bb = cells(min(xs) - m, min(ys) - m, max(xs) + m, max(ys) + m)
                path = self.astar(nid, w / 2, best, bb, tree)
                if path:
                    break
            if path is None:
                fails.append(f"{best['ref']}.{best['num']}")
            else:
                self.paint(nid, w / 2, path)
                segs.append(path)
                for (l, j, i) in path:
                    tree[l][j, i] = True
                addpad(best)
            done.append(best)
        self.routes[net] = dict(w=w, segs=segs, fails=fails)

    def run(self, order=None):
        nets = [n for n in self.nets if n not in GROUNDS and sum(p['net'] == n for p in self.pads) >= 2]
        def span(n):
            ps = [p for p in self.pads if p['net'] == n]
            return max(ps, key=lambda p: p['x'])['x'] - min(ps, key=lambda p: p['x'])['x'] + \
                max(ps, key=lambda p: p['y'])['y'] - min(ps, key=lambda p: p['y'])['y']
        nets.sort(key=lambda n: (-WIDTH.get(n, 0.25), span(n)))
        if order:
            nets.sort(key=lambda n: order.index(n) if n in order else 999)
        for n in nets:
            self.route_net(n)

    def pours(self):
        """地铺铜：每层在本侧、离其他网络铜 ≥ CLR 的地方铺；上下层重叠处可打过孔缝合。"""
        res = {}
        for g in GROUNDS:
            if g not in self.nid:
                continue
            gid = self.nid[g]
            x0, x1 = SIDE[g]
            reg = np.zeros((H, W), bool)
            reg[:, int(x0 / RES):int(x1 / RES) + 1] = True
            lab, n = [], []
            area = []
            for l in range(2):
                other = (self.cu[l] != -1) & (self.cu[l] != gid)
                d = ndimage.distance_transform_edt(~other) * RES
                m = (d >= CLR + RES * 0.5) & reg & ~self.keep | (self.cu[l] == gid)
                lb, k = ndimage.label(m)
                lab.append(lb); n.append(k); area.append(m)
            # 并查集：上下层重叠 ≥ 过孔大小的连通块合并
            par = {}
            def f(a):
                par.setdefault(a, a)
                while par[a] != a:
                    par[a] = par[par[a]]; a = par[a]
                return a
            ov = area[0] & area[1]
            er = ndimage.binary_erosion(ov, iterations=int(VIA_R / RES) + 1)
            pairs = set(zip(lab[0][er].tolist(), lab[1][er].tolist()))
            for a, b in pairs:
                par[f((0, a))] = f((1, b))
            groups = {}
            for p in self.pads:
                if p['net'] != g:
                    continue
                i0, i1, j0, j1 = p['cells']
                roots = set()
                for l in p['layers']:
                    v = lab[l][j0:j1 + 1, i0:i1 + 1]
                    for k in np.unique(v[v > 0]):
                        roots.add(f((l, int(k))))
                # 顶层贴片地焊盘：旁边能打过孔到底层
                key = min(roots) if roots else ('孤立', p['ref'])
                groups.setdefault(key, []).append(f"{p['ref']}.{p['num']}")
            res[g] = dict(groups=sorted(groups.values(), key=len, reverse=True),
                          bot_fill=float(area[1][reg].mean()), top_fill=float(area[0][reg].mean()))
        return res

    def report(self):
        out = {'nets': {}, 'vias': len(self.vias)}
        for n, r in self.routes.items():
            L = [0.0, 0.0]
            nv = 0
            for path in r['segs']:
                for a, b in zip(path, path[1:]):
                    if a[0] != b[0]:
                        nv += 1
                    else:
                        L[a[0]] += math.hypot(a[1] - b[1], a[2] - b[2]) * RES
            out['nets'][n] = dict(w=r['w'], top=round(L[0], 1), bot=round(L[1], 1), vias=nv, fails=r['fails'])
        out['pours'] = self.pours()
        return out


def solve(pl, passes=3):
    best, order = None, None
    for k in range(passes):
        b = Board(pl)
        b.run(order)
        nf = sum(len(r['fails']) for r in b.routes.values())
        if best is None or nf < best[0]:
            best = (nf, b)
        if nf == 0:
            break
        failed = [n for n, r in b.routes.items() if r['fails']]
        order = failed + [n for n in b.routes if n not in failed]
    return best[1]


if __name__ == '__main__':
    pl = json.load(open(sys.argv[1]))
    b = solve(pl)
    rep = b.report()
    rep['paths'] = {n: [[[p[0], round(p[2] * RES, 2), round(p[1] * RES, 2)] for p in s] for s in r['segs']] for n, r in b.routes.items()}
    rep['via_xy'] = b.vias
    json.dump(rep, open(sys.argv[2], 'w'), ensure_ascii=False)
    tot = sum(v['top'] + v['bot'] for v in rep['nets'].values())
    bot = sum(v['bot'] for v in rep['nets'].values())
    print(f"总长 {tot:.0f} mm，底层 {bot:.0f} mm，过孔 {rep['vias']}")
    for n, v in sorted(rep['nets'].items(), key=lambda t: -(t[1]['top'] + t[1]['bot'])):
        print(f"  {n:12s} w{v['w']:<4} 顶 {v['top']:6.1f} 底 {v['bot']:6.1f} 孔 {v['vias']} {'失败 ' + ','.join(v['fails']) if v['fails'] else ''}")
    for g, v in rep['pours'].items():
        print(g, f"顶层铺铜率 {v['top_fill']:.2f} 底层 {v['bot_fill']:.2f}", '连通组：', [len(x) for x in v['groups']])
        for grp in v['groups'][1:]:
            print('   没连上主地：', grp)
