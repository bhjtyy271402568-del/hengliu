"""画辅助板前端 + 放行电路的建议摆放和走线通道（y 向上）。用法：python3 aux_place_fig.py aux_cur.json new.json 输出.png"""
import json, sys, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'
cur = json.load(open(sys.argv[1])); NEW = json.load(open(sys.argv[2]))['new']
C = {c['r']: c for c in cur['c']}
COL = {'$1N661': '#d62728', 'BAT_PROT': '#ff7f0e', '$1N667': '#a6a600', 'AUX_IN': '#e377c2', 'BAT_GND': '#7f7f7f',
       'CTRL_P': '#1f77b4', 'CTRL_N': '#17becf', 'HS_PGD': '#2ca02c', '$1N669': '#9467bd', '$1N665': '#8c564b',
       '$1N673': '#bcbd22', '$1N676': '#6b8e23', '$1N682': '#999999', '$1N684': '#999999'}
POLY = {  # 铜皮示意（顶层）
 '$1N661': [(2.5, 18.9), (12.5, 18.9), (12.5, 30.0), (15.6, 30.0), (15.6, 35.6), (20.6, 35.6), (20.6, 39.6), (11.8, 39.9), (11.8, 31.5), (2.5, 31.5)],
 'BAT_PROT': [(15.5, 22.8), (15.5, 27.3), (27.6, 27.3), (27.6, 23.0), (25.9, 23.0), (25.9, 19.35), (23.9, 19.35), (23.9, 22.8)],
 '$1N667': [(29.9, 16.4), (37.4, 16.4), (37.4, 22.7), (29.9, 22.7)],
 'AUX_IN': [(42.3, 13.2), (46.3, 13.2), (46.3, 18.0), (41.6, 28.6), (30.0, 28.6), (30.0, 87.0), (34.5, 87.0), (34.5, 28.6), (37.2, 28.6), (37.2, 24.0), (38.4, 22.8), (38.4, 17.3), (42.3, 15.2)],
 '$1N665': [(19.5, 20.1), (23.3, 20.1), (23.3, 21.8), (19.5, 21.8)],
}
LINES = [  # 走线示意：(网络, 点列, 线型, 说明)
 ('BAT_PROT', [(23.9, 19.3), (20.0, 19.3)], '-', ''),
 ('BAT_PROT', [(25.75, 19.35), (25.75, 16.4), (25.5, 15.3)], '--', 'VIN'),
 ('$1N667', [(30.1, 19.6), (27.4, 16.3), (26.0, 15.3)], '--', 'SENSE'),
 ('$1N673', [(25.0, 15.3), (25.0, 17.0), (23.2, 17.0)], '-', ''),
 ('$1N676', [(24.5, 15.3), (24.5, 16.1), (20.7, 16.1), (20.7, 16.5)], '-', ''),
 ('BAT_GND', [(24.0, 15.3), (24.0, 15.5), (23.0, 15.5)], '-', ''),
 ('$1N682', [(24.0, 9.7), (24.0, 9.3), (22.6, 9.3)], '-', ''),
 ('$1N684', [(24.5, 9.7), (24.5, 8.1)], '-', ''),
 ('HS_PGD', [(25.0, 9.7), (25.0, 3.6), (48.0, 3.6), (48.0, 9.0), (48.7, 9.0)], '-', 'PGD'),
 ('AUX_IN', [(25.5, 9.7), (25.5, 4.4), (47.0, 4.4), (47.0, 14.0), (46.3, 14.0)], '-', 'OUT'),
 ('$1N669', [(26.0, 9.7), (26.0, 5.2), (39.8, 5.2), (39.8, 9.0), (42.3, 9.0)], '-', 'GATE'),
 ('AUX_IN', [(46.3, 14.6), (49.4, 15.0), (51.0, 13.95)], '-', ''),
 ('$1N688', [(49.4, 10.6), (49.4, 13.4)], '-', ''), ('$1N688', [(49.4, 12.4), (51.0, 12.05)], '-', ''),
 ('$1N690', [(53.0, 13.0), (53.0, 10.8)], '-', ''), ('$1N691', [(53.0, 8.8), (53.0, 7.25)], '-', ''), ('$1N691', [(51.4, 7.6), (53.0, 7.25)], '-', ''),
 ('$1N696', [(55.0, 6.3), (55.0, 10.5)], '-', ''),
 ('CTRL_N', [(57.43, 11.45), (57.43, 41.6), (40.6, 41.6)], '-', 'CTRL_N'),
 ('CTRL_P', [(57.43, 9.55), (58.6, 9.55), (58.6, 71.5), (37.9, 71.5)], '-', 'CTRL_P'),
 ('$1N665', [(18.5, 20.3), (19.5, 20.6)], '-', ''),
 ('AUX_IN', [(28.0, 31.46), (30.0, 31.46)], '-', ''), ('AUX_IN', [(26.54, 61.0), (30.0, 61.0)], '-', ''), ('AUX_IN', [(26.54, 73.0), (30.0, 73.0)], '-', ''),
 ('AUX_IN', [(26.54, 85.0), (30.0, 85.0)], '-', ''), ('AUX_IN', [(34.5, 79.1), (35.3, 79.1)], '-', ''),
]
VIAS = [(30.0, 25.6, 'g'), (21.9, 5.0, 'g'), (23.8, 5.0, 'g'), (53.0, 4.3, 'g'), (51.4, 5.0, 'g'), (22.7, 15.5, 'g'),
        (23.7, 17.0, 's'), (20.7, 15.6, 's'), (18.5, 20.3, 's')]
SEC = {'U2', 'U3', 'J1', 'C5', 'C6', 'C7', 'C9', 'Q1', 'Q2', 'C3', 'C8', 'C10', 'R12', 'R13', 'C11', 'C14'}

def pad(ax, p, alpha=.9, hatch=None):
    ax.add_patch(Rectangle((p[0], p[1]), p[2], p[3], fc=COL.get(p[4], '#cccccc'), ec='k' if hatch else 'none', lw=.4, alpha=alpha, hatch=hatch))
def scene(ax, box, title, labels=True, lw=1.6):
    x0, y0, x1, y1 = box
    ax.add_patch(Rectangle((0, 0), 128, 95, fill=False, ec='k', lw=1.5))
    ax.axvspan(60, 68, color='#f3e5f5', zorder=0)
    for hx, hy, hr in cur['keep']: ax.add_patch(Circle((hx, hy), hr, fc='#eeeeee', ec='#999999', ls=':'))
    for k, pts in POLY.items(): ax.add_patch(Polygon(pts, closed=True, fc=COL[k], alpha=.22, ec=COL[k], lw=.8))
    for r, c in C.items():
        if r in NEW: continue
        bb = c['bb']
        if not (bb[0] < x1 and bb[0] + bb[2] > x0 and bb[1] < y1 and bb[1] + bb[3] > y0): continue
        big = r in ('U2', 'U3')
        ax.add_patch(Rectangle((bb[0], bb[1]), bb[2], bb[3], fill=False, ec='#555555' if big else '#aaaaaa', lw=1 if big else .6, ls='--' if (big or c['b']) else '-'))
        for p in c['p']: pad(ax, p, .55 if c['b'] else .8)
        if labels and not big: ax.text(bb[0] + bb[2] / 2, bb[1] + bb[3] + .3, r + ('（底）' if c['b'] else ''), ha='center', fontsize=7, color='#666666', clip_on=True)
    for r, n in NEW.items():
        b = n['body']; bot = n['b'] == 1
        ax.add_patch(Rectangle((b[0], b[1]), b[2] - b[0], b[3] - b[1], fill=False, ec='#0f6d8f', lw=1.3, ls='--' if bot else '-'))
        for p in n['p']: pad(ax, p, .5 if bot else .95, '////' if bot else None)
        if labels: ax.text((b[0] + b[2]) / 2, b[3] + .25, r + ('（底）' if bot else ''), ha='center', va='bottom', fontsize=8, color='#0f6d8f', weight='bold', clip_on=True)
    for net, pts, ls, lab in LINES:
        xs, ys = zip(*pts); ax.plot(xs, ys, color=COL.get(net, '#333333'), lw=lw, ls=ls, solid_capstyle='round')
    for x, y, t in VIAS: ax.add_patch(Circle((x, y), .3, fc='k' if t == 'g' else 'white', ec='k', lw=.8, zorder=5))
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.set_title(title, fontsize=12)

fig = plt.figure(figsize=(26, 15))
ax = fig.add_axes([0.02, 0.05, 0.36, 0.88])
scene(ax, (0, 0, 66, 95), '① 整体：功率沿底边一条线，U1 在功率路径外侧（靠板边），放行电路在 Q2 右边\n粉 = AUX_IN 母线（走模块输入脚左侧），蓝 / 青 = 两根 CTRL（走模块输入脚右侧，在模块下面）', labels=False, lw=2)
for r, (x, y) in {'J1': (8, 49), 'D1': (18.6, 46), 'Q1': (7, 32.5), 'R2': (28, 23.2), 'U1': (25, 15.6), 'Q2': (35, 17.8), 'U3': (50, 33), 'U2': (50, 85), '放行': (53, 19.5), 'C9': (28, 40), 'C5–C7': (24, 92)}.items():
    ax.text(x, y, r, fontsize=11, weight='bold', ha='center')
ax.text(61, 50, '一次侧铜\n到此为止\n（x ≤ 60，\n示意）', fontsize=10, color='#7b1fa2')
ax.text(31, 60, 'AUX_IN\n母线', fontsize=10, color='#c2185b')
ax.text(58.9, 30, 'CTRL_N', fontsize=9, color='#17becf', rotation=90); ax.text(59.1, 58, 'CTRL_P', fontsize=9, color='#1f77b4', rotation=90)
ax2 = fig.add_axes([0.40, 0.33, 0.36, 0.62])
scene(ax2, (13.5, 1.5, 40.5, 29.5), '② LM5069 周围（放大）：每个小件贴着自己的脚')
notes = [((15.6, 28.3), 'BAT_PROT（橙）：Q1 源极 → 横条 → R2 输入焊盘；D2、C1 上端、C2 都接在这条上'),
         ((14.0, 13.2), 'R3 / R5 上端从 R2 输入焊盘左下角\n引一根细线取 BAT_PROT（0.7 mA）\nR4 / R6 在背面，正对 R3 / R5'),
         ((26.6, 18.7), 'VIN / SENSE 虚线 = 开尔文'),
         ((26.5, 2.0), 'PGD / OUT / GATE 从板边下方走过 Q2 散热焊盘'),
         ((30.5, 11.0), 'Q2 散热焊盘 = 漏极')]
for (x, y), t in notes: ax2.text(x, y, t, fontsize=9, va='top')
ax3 = fig.add_axes([0.40, 0.04, 0.36, 0.27])
scene(ax3, (43.5, 1.5, 61.5, 19.5), '③ 放行电路（放大）：链条一字排开，PGD 从左下进，两根 CTRL 从右上出')
ax3.text(44, 18.6, 'R8 上端 = Q3 发射极 = AUX_IN，就近从 Q2 源极焊盘右端取', fontsize=9)
axl = fig.add_axes([0.78, 0.04, 0.21, 0.91]); axl.axis('off')
txt = ['图例', '实心焊盘 = 顶层；斜线焊盘 / 虚线框 = 底层', '蓝色粗框 = 这次要挪的件；灰色 = 不动的件', '黑点 = 地过孔；白点 = 信号过孔', '淡色块 = 铜皮示意（顶层）', '',
       '颜色（网络）', '红  电池正（J1 → Q1 漏极）', '橙  BAT_PROT（Q1 源极 → R2）', '黄绿  R2 → Q2 漏极', '粉  AUX_IN（Q2 源极之后）', '紫  GATE', '棕  Q1 栅极', '绿  PGD', '蓝 / 青  CTRL_P / CTRL_N', '灰  BAT_GND', '',
       '要点', '1. D1 竖放紧贴 J1', '2. D2、C1 竖跨在 Q1 栅极脚和 BAT_PROT 横条之间', '3. R1 放背面，栅极过孔下去，另一端直接落在地平面', '4. R2 右移约 3 mm：输入焊盘内侧刚好对着 U1 第 2 脚，',
       '    VIN 直线下来，不和 3、4、5 脚的出线交叉', '5. U1 下移 1 mm，给 3、4、5 脚出线留 2 mm', '6. 出线高度：5 脚地 15.5 → 过孔；OVLO 16.1；UVLO 17.0', '7. C4、R7 在 U1 下方贴 6、7 脚，地各打一孔',
       '8. PGD 3.6 / OUT 4.4 / GATE 5.2 三根平行线从板边走', '9. OUT 绕到栅极焊盘外侧接源极，不交叉', '10. 放行电路 x 48–59，离二次侧铜 ≥ 9 mm', '11. D3 两个阳极脚：上 = CTRL_N，下 = CTRL_P，',
       '     CTRL_N 在左、先拐；CTRL_P 在右、后拐，不交叉', '', '坐标 y 向上（和嘉立创一致），单位 mm', '图上的线只是通道示意，线宽、间距以 DRC 为准']
for i, t in enumerate(txt): axl.text(0, 1 - i * 0.027, t, fontsize=10.5 if t in ('图例', '颜色（网络）', '要点') else 9.5, weight='bold' if t in ('图例', '颜色（网络）', '要点') else 'normal', transform=axl.transAxes, va='top')
fig.savefig(sys.argv[3], dpi=72); print('saved')

# ---- 第 4 个参数：标全位号的放大图 ----
if len(sys.argv) > 4:
    fig = plt.figure(figsize=(25, 19))
    ax = fig.add_axes([0.03, 0.04, 0.95, 0.9])
    scene(ax, (0, 0, 62, 47), '辅助板前端 + 放行电路：全部位号（y 向上，单位 mm；蓝框 = 要挪的件，斜线 / 虚框 = 背面件，灰 = 不动的件）', labels=False, lw=2.2)
    B = dict(boxstyle='round,pad=0.2', fc='white', ec='#0f6d8f', lw=1, alpha=.92)
    G = dict(boxstyle='round,pad=0.2', fc='white', ec='#888888', lw=1, alpha=.92)
    A = dict(arrowstyle='-', color='#0f6d8f', lw=1.2)
    AG = dict(arrowstyle='-', color='#888888', lw=1.2)
    LAB = [  # 文字, 文字位置, 指向点, 是否挪动的件
     ('J1 电池接口', (2.0, 45.5), (8.0, 42.0), 0), ('D1 TVS', (23.5, 43.5), (18.6, 41.0), 1),
     ('Q1 防反接 P 管', (3.0, 33.0), (7.5, 27.0), 0),
     ('D2', (18.2, 25.6), (20.6, 23.0), 1), ('C1', (24.4, 25.6), (22.55, 23.0), 1),
     ('C2', (31.4, 25.8), (29.6, 24.75), 1), ('R2  8 mΩ', (27.0, 18.2), (28.0, 20.5), 1),
     ('R1（底）', (11.4, 17.0), (17.2, 18.0), 1),
     ('R5（顶）/ R6（底）  OVLO', (6.0, 15.0), (20.7, 17.6), 1), ('R3（顶）/ R4（底）  UVLO', (6.0, 13.2), (22.5, 17.2), 1),
     ('U1  LM5069', (16.6, 11.6), (24.0, 12.5), 1),
     ('C4  TIMER', (14.6, 7.4), (21.4, 7.6), 1), ('R7  PWR', (18.5, 2.0), (23.8, 6.4), 1),
     ('Q2 热插拔 N 管', (30.3, 15.2), (33.7, 13.5), 0),
     ('C3（底）', (42.6, 20.8), (46.0, 14.8), 0), ('C9', (24.6, 41.0), (28.0, 36.0), 0), ('C10（底）', (31.5, 30.6), (38.3, 28.9), 0),
     ('R8', (45.2, 17.4), (49.4, 14.6), 1), ('R9', (45.0, 11.2), (49.4, 10.0), 1), ('Q3', (51.2, 17.4), (52.0, 13.6), 1),
     ('R10', (53.4, 15.6), (53.0, 10.4), 1), ('R11', (49.6, 1.0), (51.4, 6.0), 1), ('Q4', (56.0, 3.0), (54.2, 5.8), 1),
     ('D3', (58.6, 14.0), (56.6, 11.0), 1),
     ('U3 第 3 脚 +Vin', (41.6, 25.4), (39.6, 26.4), 0), ('U3 第 2 脚 -Vin', (41.6, 31.2), (39.6, 31.5), 0), ('U3 第 1 脚 CTRL', (41.6, 43.6), (39.6, 41.6), 0),
    ]
    for t, xy, p, mv in LAB:
        ax.annotate(t, p, xytext=xy, fontsize=13, weight='bold', color='#0f6d8f' if mv else '#555555', bbox=B if mv else G,
                    arrowprops=A if mv else AG, zorder=8)
    PIN = [('D', (7.5, 24.0)), ('G', (18.0, 20.2)), ('S', (18.0, 28.0)),                     # Q1
           ('D（漏极，散热焊盘）', (33.7, 11.0)), ('G', (45.6, 7.6)), ('S', (45.4, 15.9))]       # Q2
    for t, (x, y) in PIN: ax.text(x, y, t, fontsize=11, ha='center', va='center', color='#333333', weight='bold', zorder=8)
    U = NEW['U1']['p']
    for p in U:
        cx, cy = p[0] + p[2] / 2, p[1] + p[3] / 2
        ax.text(cx, cy + (0.95 if cy > 12.5 else -0.95), p[5], fontsize=8.5, ha='center', va='center', color='#0f6d8f', zorder=9)
    ax.text(26.6, 16.4, '1 SENSE  2 VIN  3 UVLO  4 OVLO  5 GND（从右往左）', fontsize=9, color='#0f6d8f', zorder=9)
    ax.text(7.0, 10.3, '6 TIMER  7 PWR  8 PGD  9 OUT  10 GATE（从左往右）', fontsize=9, color='#0f6d8f', zorder=9)
    for t, (x, y) in [('BAT_PROT', (20.0, 27.8)), ('AUX_IN', (35.0, 40.0)), ('PGD', (36.0, 2.7)), ('OUT', (36.0, 4.45)), ('GATE', (36.0, 5.9)),
                      ('CTRL_N', (57.7, 30.0)), ('CTRL_P', (58.9, 22.0))]:
        ax.text(x, y, t, fontsize=10, color='#444444', style='italic', zorder=9, rotation=90 if t.startswith('CTRL') else 0)
    fig.savefig(sys.argv[4], dpi=70); print('saved', sys.argv[4])
