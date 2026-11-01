"""画辅助板二次侧（±15 V 输出 + 控制卡支路 + 接口）的建议摆放，标全位号（y 向上）。
用法：python3 aux_out_fig.py aux_cur.json out.json 输出.png"""
import json, sys, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'
cur = json.load(open(sys.argv[1])); D = json.load(open(sys.argv[2])); NEW, CU, VIAS = D['new'], D['cu'], D['vias']
C = {c['r']: c for c in cur['c']}
ELEC = {'C11', 'C12', 'C14', 'C15', 'C18'}
COL = {'P15_RAW': '#d62728', 'GALVO_P15': '#ff7f0e', 'CARD_P15': '#9467bd', '$1N777': '#c5b0d5', '$1N765': '#ffbb78',
       'N15_RAW': '#1f77b4', 'GALVO_N15': '#17becf', '$1N768': '#9edae5', 'AUX_GND': '#7f7f7f'}
fig = plt.figure(figsize=(25, 19))
ax = fig.add_axes([0.02, 0.03, 0.62, 0.92])
ax.add_patch(Rectangle((0, 0), 128, 95, fill=False, ec='k', lw=1.5))
for hx, hy, hr in cur['keep']: ax.add_patch(Circle((hx, hy), hr, fc='#eeeeee', ec='#999999', ls=':'))
for net, (x0, y0, x1, y1) in CU: ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=COL[net], alpha=.30, ec='none'))
def pad(p, bot):
    ax.add_patch(Rectangle((p[0], p[1]), p[2], p[3], fc=COL.get(p[4], '#cccccc'), alpha=.5 if bot else .95, ec='k' if bot else 'none', lw=.4, hatch='////' if bot else None))
for r, c in C.items():
    if r in NEW: continue
    bb = c['bb']
    if bb[0] + bb[2] < 66: continue
    big = r in ('U2', 'U3')
    ax.add_patch(Rectangle((bb[0], bb[1]), bb[2], bb[3], fill=False, ec='#555555' if big else '#aaaaaa', lw=1.2 if big else .7, ls='--' if (big or c['b']) else '-'))
    for p in c['p']: pad(p, c['b'] == 1)
for r, n in NEW.items():
    b = n['body']; bot = n['b'] == 1
    if r in ELEC: ax.add_patch(Circle(((b[0] + b[2]) / 2, (b[1] + b[3]) / 2), 4, fill=False, ec='#0f6d8f', lw=1.5))
    else: ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec='#0f6d8f', lw=1.5, ls='--' if bot else '-'))
    for p in n['p']: pad(p, bot)
for x, y in VIAS: ax.add_patch(Circle((x, y), .35, fc='k', ec='k', zorder=6))
B = dict(boxstyle='round,pad=0.2', fc='white', ec='#0f6d8f', lw=1, alpha=.93)
G = dict(boxstyle='round,pad=0.2', fc='white', ec='#888888', lw=1, alpha=.93)
LAB = [  # 文字, 文字位置, 指向点, 是否挪动
 ('J4 控制卡 15 V（从下边搬来）', (110.5, 96.4), (119.0, 86.8), 1), ('J2 振镜（下移 6.9 mm）', (91.0, 57.0), (117.6, 63.0), 1), ('J3 振镜（不动）', (98.5, 4.2), (119.5, 21.0), 0),
 ('D4 反向钳位', (86.0, 61.0), (95.0, 66.5), 1), ('C11 220 µF', (100.0, 64.5), (103.6, 68.6), 1), ('D6 TVS', (106.5, 64.5), (110.0, 69.5), 1),
 ('L1', (112.2, 85.2), (114.2, 82.2), 1), ('C13', (112.0, 73.0), (115.0, 70.0), 1), ('R12 0.22 Ω', (112.5, 53.0), (115.2, 59.0), 1), ('C12 220 µF', (103.0, 52.0), (107.0, 55.6), 1),
 ('L3', (90.0, 89.0), (95.0, 87.5), 1), ('R14 0.22 Ω', (90.0, 93.0), (101.0, 90.5), 1), ('C18 220 µF', (98.0, 96.4), (106.5, 93.0), 1), ('C19', (114.6, 92.6), (116.0, 88.6), 1),
 ('C22 1 µF（底，新增）', (70.0, 82.5), (83.0, 77.5), 1), ('C23 10 µF（底，新增）', (68.0, 70.0), (80.6, 75.5), 1),
 ('D5 反向钳位', (86.0, 52.0), (90.5, 46.5), 1), ('C14 220 µF', (95.5, 49.0), (99.0, 45.5), 1), ('D7 TVS', (106.0, 48.0), (107.5, 44.4), 1),
 ('L2', (113.5, 40.5), (112.5, 36.0), 1), ('R13 0.22 Ω', (100.0, 22.0), (108.6, 24.5), 1), ('C15 220 µF', (99.0, 12.0), (106.4, 14.6), 1), ('C16', (101.0, 29.5), (105.8, 28.2), 1),
 ('C20 / C21（底，不动）', (66.5, 19.0), (82.0, 27.5), 0),
 ('U2 第 8 脚 +Vo', (70.0, 88.0), (87.4, 79.6), 0), ('第 7 脚 Sense+', (70.0, 85.5), (87.0, 75.3), 0), ('U2 第 4 脚 0V', (70.0, 61.5), (87.0, 63.9), 0),
 ('第 5 脚 Sense-', (70.0, 66.0), (87.0, 67.7), 0),
 ('U3 第 5 脚 -15 V', (68.5, 40.0), (85.0, 34.5), 0), ('U3 第 4 脚 0V', (68.5, 11.5), (84.9, 23.0), 0),
]
for t, xy, p, mv in LAB:
    ax.annotate(t, p, xytext=xy, fontsize=12.5, weight='bold', color='#0f6d8f' if mv else '#555555', bbox=B if mv else G,
                arrowprops=dict(arrowstyle='-', color='#0f6d8f' if mv else '#888888', lw=1.1), zorder=8, annotation_clip=False)
for t, (x, y), col, rot in [('P15_RAW 横条', (89.0, 80.6), '#b71c1c', 0), ('N15_RAW 横条', (88.5, 33.4), '#0d47a1', 0),
                            ('CARD_P15', (104.5, 84.3), '#5e35b1', 0), ('GALVO_P15 内侧通道（在 J2 / J3 本体下）', (118.5, 36.0), '#e65100', 90),
                            ('GALVO_N15 外侧通道（贴板边）', (125.2, 40.0), '#006064', 90), ('GALVO_N15 从 J3 下面绕到板边', (114.6, 12.6), '#006064', 0)]:
    ax.text(x, y, t, fontsize=10.5, color=col, weight='bold', rotation=rot, zorder=9)
for r, pin in [('J2', ['+15', 'GND', '-15']), ('J3', ['+15', 'GND', '-15'])]:
    for p, t in zip(sorted(NEW.get(r, C[r])['p'], key=lambda p: p[5]), pin):
        ax.text(p[0] + p[2] + .25, p[1] + p[3] / 2, t, fontsize=8.5, va='center', color='k', zorder=9)
for p, t in zip(sorted(NEW['J4']['p'], key=lambda p: p[5]), ['+15', 'GND']):
    ax.text(p[0] + p[2] + .25, p[1] + p[3] / 2, t, fontsize=8.5, va='center', color='k', zorder=9)
ax.text(61, 92.8, 'U2（+15 V 模块）只画了输出侧', fontsize=10, color='#555555'); ax.text(61, 48.6, 'U3（-15 V 模块）', fontsize=10, color='#555555')
ax.set_xlim(60, 131); ax.set_ylim(0, 98); ax.set_aspect('equal')
ax.set_title('辅助板二次侧摆放建议（y 向上，mm）：蓝框 = 要挪 / 新增的件，斜线焊盘 = 背面，黑点 = 地过孔，淡色块 = 顶层铜皮示意', fontsize=13)
axl = fig.add_axes([0.66, 0.03, 0.33, 0.92]); axl.axis('off')
txt = ['颜色（网络）', '红  P15_RAW：U2 输出，滤波前', '橙  GALVO_P15：L1 之后，到两个振镜口', '紫  CARD_P15：L3 之后，到控制卡口',
       '蓝  N15_RAW：U3 输出，滤波前', '青  GALVO_N15：L2 之后，到两个振镜口', '灰  AUX_GND：底层整块地平面', '',
       '摆放思路', '1. 每路一条“脏”横条：模块输出脚 → 横条，', '    钳位二极管、TVS、大电解都挂在横条上，靠近模块', '2. 电感是分界：L1 / L2 / L3 之后才是“干净”的电，',
       '    干净的铜不再从模块脚旁边经过', '3. 地全走底层：通孔地脚（D4 / D5、电解负极、接口 GND）', '    直接落在地平面；贴片地焊盘旁打一个孔',
       '4. 两个振镜口都要 ±15 V，脚序 +15 / GND / -15 一样，', '    顺序排列必有一次交叉。办法：两条通道夹住接线柱那一列——', '    +15 走内侧（接口本体下面），-15 从 J3 下面绕到外侧（贴板边），',
       '    地脚是通孔，直接下到底层。全程不打信号过孔、不切地平面', '5. 控制卡口 J4 必须在最上面：它的 +15 只能从左边进，', '    放在 J2 / J3 之间会被 +15 内侧通道挡住；',
       '    J4 放上面又会碰右上角安装孔，所以 J2 下移 6.9 mm 让位', '6. C22 / C23 放背面、贴着 U2 第 8 脚，和 U3 的 C20 / C21 一样', '7. 第 7 脚 Sense+ 接第 8 脚、第 5 脚 Sense- 接第 4 脚，都在脚旁就近连',
       '', '线宽（1 oz 外层，温升 10 °C，计算）', '横条 6 mm，够 6 A 以上；+15 / -15 通道约 3.2 mm，', '约 5 A（只走 J3 那一路）；CARD 线 1.6 mm，约 3 A', '',
       '要你确认', '- J4 从下边搬到右边、J2 下移：机壳和线束能不能接受', '- C22 / C23 的位号以你图上的为准', '- 电解按 Ø8 估，以实际封装为准',
       '', '脚本：aux_out_plan.py（坐标 + 检查）、aux_out_fig.py（本图）', '检查：异网焊盘 ≥ 0.25 mm、铜皮示意 ≥ 0.4 mm、本体不重叠、', '不进安装孔禁布、全部在隔离带右侧']
for i, t in enumerate(txt):
    h = t in ('颜色（网络）', '摆放思路', '线宽（1 oz 外层，温升 10 °C，计算）', '要你确认')
    axl.text(0, 1 - i * 0.0262, t, fontsize=12 if h else 11, weight='bold' if h else 'normal', transform=axl.transAxes, va='top')
fig.savefig(sys.argv[3], dpi=68); print('saved')
