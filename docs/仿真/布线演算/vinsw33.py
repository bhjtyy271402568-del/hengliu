# 顶层 LT_VIN / LT_SW 铜（10-28 版，指纹 176f88e42e56）：按铜区轮廓减异网焊盘 0.3 mm 近似填充，标出窄颈和电流
# 用法：在草稿区运行（需要 z33/load.py、z33/p.epro2、r27/lay32.json）
import sys, json, matplotlib, logging; matplotlib.use('Agg')
sys.path.insert(0, 'z33'); from load import load
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon as MP, FancyArrowPatch
from shapely.geometry import Polygon, box
from shapely.ops import unary_union
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
d = load('z33/p.epro2')['9a0fbfd22df79247']['recs']
P = {}
for h, r in d:
    if h['type'] == 'POUR' and r['netName'] in ('LT_VIN', 'LT_SW'):
        n = [v for v in r['path'][0] if not isinstance(v, str)]
        P[r['netName']] = Polygon([(n[i] * 0.0254, n[i + 1] * 0.0254) for i in range(0, len(n), 2)])
C = json.load(open('r27/lay32.json'))
def obst(net):
    return unary_union([box(p[0], p[1], p[0] + p[2], p[1] + p[3]) for c in C for p in c['p'] if (c['b'] == 0 or p[6]) and p[4] != net]).buffer(0.3, join_style=2)
F = {n: P[n].difference(obst(n)) for n in P}
F['LT_VIN'] = F['LT_VIN'].difference(P['LT_SW'].buffer(0.3, join_style=2))
NC = {'LT_VIN': '#d62728', 'PGND': '#1f77b4', 'LT_SW': '#e69500', 'DCBUS': '#9467bd'}
fig, ax = plt.subplots(figsize=(17, 11))
for net, g in F.items():
    for poly in getattr(g, 'geoms', [g]):
        ax.add_patch(MP(list(poly.exterior.coords), closed=True, fc=NC[net], alpha=0.22, ec=NC[net], lw=1))
for c in C:
    if c['b'] != 0: continue
    for p in c['p']:
        if 54 < p[0] < 112 and 63 < p[1] < 95:
            ax.add_patch(Rectangle((p[0], p[1]), p[2], p[3], fc=NC.get(p[4], '#999'), alpha=0.6, ec='#444', lw=0.3))
    if 55 < c['x'] < 111 and 64 < c['y'] < 95 and c['r'][0] in 'CQRL':
        ax.text(c['x'], c['y'], c['r'], fontsize=7.5, ha='center', va='center')
def mark(x0, y0, x1, y1, t, c, tx, ty):
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec=c, lw=2.2, ls='--', zorder=9))
    ax.annotate(t, ((x0 + x1) / 2, (y0 + y1) / 2), (tx, ty), fontsize=10, color=c, zorder=10,
                bbox=dict(fc='white', ec=c, boxstyle='round,pad=0.3'), arrowprops=dict(arrowstyle='->', color=c, lw=1.4))
mark(60.1, 74.95, 61.85, 78.0, 'C69 / C70 窄颈：约 1.75 mm（轮廓允许值）\n死胡同：只过电容自己的纹波，约 0.3 A rms\n2 oz 1–1.75 mm 能过约 4–6 A（温升 10 °C）→ 不是问题', '#2a7a2a', 40.5, 62.0)
mark(68.0, 85.7, 73.9, 88.1, 'VIN 窄颈 5.9 mm × 约 2.4 mm 长\n直流最大约 46 A（输入限流上限）\n→ 要底层并联 + 过孔', '#c00000', 76.0, 91.5)
mark(77.4, 69.85, 83.15, 74.45, 'SW 跨列 4.6 mm\n第 2→3 列之间约 27 A，第 1→2 列约 13 A\n→ 靠底层 SW 带分担', '#b06000', 84.0, 60.2)
mark(90.15, 69.85, 109.6, 76.5, 'SW → L8：顶层 6.65 mm，全部 40 A\n+ 底层 SW 带并联', '#b06000', 95.0, 79.5)
ax.plot([73.5], [88.75], 'x', color='k', ms=12, mew=2.5, zorder=11)
ax.annotate('原计划的 PGND 孔 (73.5, 88.75) 落进 VIN 铜，删掉\n（上方一排改从 x 74.5 开始）', (73.5, 88.75), (52.5, 93.0), fontsize=9.5,
            bbox=dict(fc='white', ec='k', boxstyle='round,pad=0.3'), arrowprops=dict(arrowstyle='->'), zorder=10)
for (a, b, t) in [((70.0, 92.0), (71.5, 86.2), ''), ((71.5, 85.0), (75.0, 82.0), '')]:
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=18, color='#c00000', lw=2.2, zorder=10))
ax.add_patch(FancyArrowPatch((64.5, 72.0), (107, 73.2), arrowstyle='-|>', mutation_scale=20, color='#b06000', lw=2.2, zorder=10, connectionstyle='arc3,rad=-0.05'))
ax.text(56.0, 66.0, '箭头 = 直流电流的路；电容支路不过直流', fontsize=10)
ax.set_xlim(54, 112); ax.set_ylim(58.5, 95); ax.set_aspect('equal'); ax.grid(True, lw=0.2)
ax.set_title('顶层 LT_VIN（红）/ LT_SW（橙）：哪里窄、过多少电流', fontsize=15)
plt.tight_layout(); plt.savefig('/home/user/hengliu/docs/仿真/布线演算/顶层VIN_SW核对_20261028.png', dpi=90)
