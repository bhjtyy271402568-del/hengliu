"""10-30 规整版（46a44fa67e30）终审标注图，坐标 y 向上（和嘉立创一致）。
用法：python3 review60_fig.py geo.pkl lay.pkl 输出.png
geo.pkl 由 review50_geo.py 生成（第 4 个参数传 Codex 快照，补上 U2 的封装）；lay.pkl 由 Gerber 渲染得到（每层铜 + 阻焊 / 丝印）。"""
import pickle, sys, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from shapely.geometry import box
plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'
G = pickle.load(open(sys.argv[1], 'rb')); LAY = pickle.load(open(sys.argv[2], 'rb')); CU = G['CU']

def draw(ax, geom, c, a=1.0, clip=None):
    if clip is not None: geom = geom.intersection(clip)
    for p in getattr(geom, 'geoms', [geom]):
        if p.is_empty or p.geom_type != 'Polygon': continue
        x, y = p.exterior.xy; ax.fill(x, y, color=c, lw=0, alpha=a)
        for i in p.interiors: x, y = i.xy; ax.fill(x, y, color='white', lw=0)

def win(ax, x0, y0, x1, y1, title):
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.set_title(title, fontsize=12)

fig, axs = plt.subplots(2, 3, figsize=(21, 13))

# 1 TG / SW 过孔孔距
ax = axs[0, 0]; b = box(79.5, 55, 83.5, 59.5)
draw(ax, LAY[16], '#cccccc', 1, b)
for n, c in (('LT_TG', '#d62728'), ('LT_SW', '#1f77b4')): draw(ax, CU[(16, n)], c, .7, b)
for v in G['vias']:
    if b.contains(box(v['x'] - .01, v['y'] - .01, v['x'] + .01, v['y'] + .01)):
        ax.add_patch(Circle((v['x'], v['y']), v['d'] / 2, fc='white', ec='k', lw=1))
ax.annotate('', xy=(81.45, 57.275), xytext=(81.8, 57.925), arrowprops=dict(arrowstyle='<->', lw=1.5))
ax.text(80.0, 58.6, '孔边到孔边 0.48 mm\n（嘉立创异网孔距要求 0.5 mm）', fontsize=11)
win(ax, 79.5, 55, 83.5, 59.5, '① L3：TG 孔（红）和 SW 孔（蓝）孔距略小\n把 SW 孔挪开 0.05 mm 即可')

# 2 母线电容只有 1 个地孔
ax = axs[0, 1]; b = box(36, 53, 56, 75)
draw(ax, CU[(2, 'PGND')], '#2ca02c', .5, b); draw(ax, CU[(2, 'DCBUS')], '#ff7f0e', .5, b)
one = {'C9', 'C10', 'C14', 'C15', 'C16', 'C17', 'C18'}
for c in G['C']:
    if c['b'] and c['r'] in one | {'C11', 'C12', 'C13', 'C19'}:
        bb = c['bb']; ax.add_patch(Rectangle((bb[0], bb[1]), bb[2], bb[3], fill=False, ec='r' if c['r'] in one else 'k', lw=2))
        ax.text(c['x'], c['y'], c['r'], ha='center', va='center', fontsize=9)
for v in G['vias']:
    if v['net'] == 'PGND' and b.buffer(-.1).contains(box(v['x'], v['y'], v['x'] + .01, v['y'] + .01)):
        ax.add_patch(Circle((v['x'], v['y']), .3, fc='k'))
win(ax, 36, 53, 56, 75, '② 底层母线电容：红框 7 只的地焊盘只有 1 个孔（黑点）\n绿 = PGND，橙 = DCBUS；每只补 1 孔，约少 1 nH')

# 3 角孔
ax = axs[0, 2]; x, y = 93, 3.5; b = box(x - 5, y - 4, x + 5, y + 5)
draw(ax, LAY[1], '#c87533', .55, b); draw(ax, LAY[2], '#3366cc', .35, b)
ax.add_patch(Circle((x, y), 1.6, fc='white', ec='k', lw=2))
ax.add_patch(Circle((x, y), 1.81, fill=False, ec='k', ls=':', lw=1.5))
ax.add_patch(Circle((x, y), 3.25, fill=False, ec='r', ls='--', lw=2))
ax.text(x - 4.7, y + 4.4, '四层都是 PGND（(3.5, 3.5) 是 GND）\n铜离孔边 0.21 mm\n红虚线 = 建议禁铜 Ø6.5', fontsize=11, va='top')
win(ax, x - 5, y - 4, x + 5, y + 5, '③ 角孔 (93, 3.5)：VCC_OUT 已不在孔边\n只要用尼龙柱就没事；金属柱会把 GND / PGND 经机壳多连一处')

# 4 凸台区阻焊
ax = axs[1, 0]; b = box(60, 65, 90, 84.5)
draw(ax, LAY[2], '#9db7e6', 1, b); draw(ax, LAY['bsm'], '#f2c200', 1, b); draw(ax, LAY['bso'], '#000000', 1, b)
for r in ('Q5', 'Q6', 'Q7', 'Q8', 'Q9', 'Q10'):
    ps = [p['g'] for p in G['pads'] if p['r'] == r]
    x0 = min(p.bounds[0] for p in ps); x1 = max(p.bounds[2] for p in ps)
    y0 = min(p.bounds[1] for p in ps); y1 = max(p.bounds[3] for p in ps)
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec='r', lw=2))
win(ax, 60, 65, 90, 84.5, '④ 底层：红框 = 管子焊盘投影（凸台接触区）\n黄 = 阻焊开窗，只占 32–39%；黑 = 丝印\n要整块开窗就在出 Gerber 前画阻焊区')

# 5 PWM 压在 ISMON 正下方
ax = axs[1, 1]; b = box(50, 40, 70, 52)
draw(ax, LAY[16], '#dddddd', 1, b)
for t in G['tracks']:
    if t['net'] == 'PWM' and t['L'] == 2: ax.plot([t['x0'], t['x1']], [t['y0'], t['y1']], color='#d62728', lw=3)
    if t['net'] == 'SHUCHUDIANLIUJIANCE' and t['L'] == 16: ax.plot([t['x0'], t['x1']], [t['y0'], t['y1']], color='#1f77b4', lw=3, ls='--')
ax.text(50.5, 40.4, '红 = PWM（底层 y 49.41）\n蓝虚线 = ISMON 读回（L3 y 49.20）\n上下只隔 0.21 mm 介质，并行约 6.5 mm', fontsize=11)
win(ax, 50, 40, 70, 52, '⑤ 走廊里 PWM 和 ISMON 上下叠着走\nPWM 只在启停时翻转、ISMON 端有 10 k + 100 nF，影响小\n有空就把 PWM 挪 0.5 mm')

# 6 散热器下的底层器件
ax = axs[1, 2]; b = box(25, 38, 110, 96)
draw(ax, LAY[2], '#e0e8f5', 1, b)
ax.add_patch(Rectangle((27, 50), 80, 45, fill=False, ec='k', lw=2, ls='--'))
for c in G['C']:
    bb = c['bb']
    if c['b'] and box(*bb[:2], bb[0] + bb[2], bb[1] + bb[3]).intersects(box(27, 50, 107, 95)):
        tall = c['r'].startswith('C') and bb[2] > 2.4 and bb[3] > 2.4
        ax.add_patch(Rectangle((bb[0], bb[1]), bb[2], bb[3], fc='#d62728' if tall else '#7f7f7f', alpha=.8))
ax.text(28, 47, '虚线 = 散热器底座（x 27–107，y 50–95）\n红 = 1210 电容（高 2.5 mm），灰 = 其他底层件\n共 51 只：凸台高度 / 底座避让槽按 2.5 mm + 余量定', fontsize=11, va='top')
win(ax, 25, 38, 110, 96, '⑥ 散热器投影下的底层器件（机械定版时核对）')

plt.tight_layout(); plt.savefig(sys.argv[3], dpi=70)
print('saved', sys.argv[3])
