"""10-30 四层补铜版（3f423d36ddb0）窄接头放大图：Gerber 实际铜（y 向上），红圈 = 走线端头只擦到焊盘 / 过孔的位置。
用法：python3 review70_necks.py geo.pkl lay.pkl 输出.png（lay.pkl 由 review60_gerber.py 生成）"""
import pickle, sys, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
from shapely.geometry import box
plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'
G = pickle.load(open(sys.argv[1], 'rb')); LAY = pickle.load(open(sys.argv[2], 'rb'))
LN = {1: '顶层', 2: '底层', 15: 'L2', 16: 'L3'}
cases = [  # 层, 接头坐标, 标题
    (2, (50.27, 71.42), '$1N493 → R5.2（过压切断）\n颈部约 0.04–0.08 mm'),
    (2, (85.28, 56.40), 'OCP_CLAMP_BASE → R213.2（过流拉 PWM）\n约 0.10 mm'),
    (1, (90.05, 38.48), '$1N3097 → U201.5（INA310 RESET）\n约 0.10 mm'),
    (2, (50.70, 69.38), '$1N493 → U1.1 / R3.1（过压尺子）\n约 0.12 / 0.15 mm'),
    (1, (23.18, 22.88), 'VCC → U2.64（MCU 供电）\n约 0.12 mm'),
    (2, (81.80, 53.20), '$1N2941 → 过孔（ISMON 读回）\n约 0.12 mm'),
    (2, (53.03, 50.75), 'DCBUS 过孔 → R216.2（LM5164 供电）\n约 0.12–0.15 mm，本轮孔焊盘 0.7→0.6 后变窄'),
    (1, (73.4, 82.2), 'Q5 焊盘内 LT_VIN 孔：两排间距 0.55 mm\n孔壁只剩 0.27 mm（本轮新出现，14 对）'),
]
fig, axs = plt.subplots(2, 4, figsize=(22, 11))
for ax, (L, (x, y), title) in zip(axs.ravel(), cases):
    r = 1.6 if 'Q5' not in title else 1.4
    W = box(x - r, y - r, x + r, y + r)
    g = LAY[L].intersection(W)
    for p in getattr(g, 'geoms', [g]):
        if p.is_empty or p.geom_type != 'Polygon': continue
        xs, ys = p.exterior.xy; ax.fill(xs, ys, color='#c87533' if L == 1 else '#3366cc', alpha=.75, lw=0)
        for i in p.interiors: xs, ys = i.xy; ax.fill(xs, ys, color='white', lw=0)
    for v in G['vias']:
        if W.contains(box(v['x'] - .01, v['y'] - .01, v['x'] + .01, v['y'] + .01)):
            ax.add_patch(Circle((v['x'], v['y']), v['d'] / 2, fc='white', ec='k', lw=.8))
    if 'Q5' not in title: ax.add_patch(Circle((x, y), 0.25, fill=False, ec='r', lw=2.5))
    ax.set_xlim(x - r, x + r); ax.set_ylim(y - r, y + r); ax.set_aspect('equal')
    ax.set_title(LN[L] + '：' + title, fontsize=11)
fig.suptitle('10-30 四层补铜版：走线端头只擦到焊盘边 / 角的接头（Gerber 实际铜，y 向上）。改法：端点移到焊盘中心，或伸进焊盘 ≥ 线宽', fontsize=14)
plt.tight_layout(rect=(0, 0, 1, .95)); plt.savefig(sys.argv[3], dpi=70); print('saved')
