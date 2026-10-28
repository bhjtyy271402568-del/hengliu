# 换流回路（布线第 ① 步）细节图：顶层 / 底层 / L2 / 截面
# 用法：在 lay32.json 所在目录运行 python3 loop33.py
import json, matplotlib, logging; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, FancyArrowPatch
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
plt.rcParams['font.sans-serif'] = ['WenQuanYi Zen Hei', 'DejaVu Sans']
C = json.load(open('lay32.json'))
NC = {'LT_VIN': '#d62728', 'PGND': '#1f77b4', 'LT_SW': '#ff9900', 'GND': '#2ca02c', 'DCBUS': '#e377c2'}
X0, X1, Y0, Y1 = 53.5, 99, 57.5, 95
bb = dict(fc='white', ec='none', alpha=0.9)

# ---------- 建议的过孔位置（计算：避开异网焊盘，间隙 ≥ 0.3 mm） ----------
cap_top = []          # 顶层电容 PGND
for x in (61.9, 62.7): cap_top.append((x, 87.0))            # C113 焊盘内（下面是底层 C117 的 PGND）
cap_top += [(63.9, 86.8), (63.9, 87.7)]                      # C113 与 C71 之间
cap_top.append((67.15, 87.2))                                # C71 右半（左半下面是底层 C117 的 VIN）
for x in (74.7, 75.5, 77.9, 78.7, 79.85, 81.3, 82.1, 82.95, 84.5, 85.35, 86.3, 87.8, 89.5):
    cap_top.append((x, 86.95))                               # 顶 / 底电容 PGND 焊盘重叠处
for x in [74.5 + i for i in range(17)]:              # 73.5 会落进 R42 旁的 VIN 铜（10-28 顶层铜版）
    cap_top.append((x, 88.75))                               # 焊盘上方一排
left = [(57.4, 73.0), (57.4, 74.1), (58.0, 70.6), (58.45, 79.0)]   # C69 / C70 / C63
bot_cap = [(69.75, 78.7), (70.75, 78.7), (80.3, 78.7), (81.2, 78.7), (90.8, 78.7), (91.7, 78.7),  # C106-108
           (58.0, 80.5), (58.0, 81.5), (58.0, 76.7), (58.0, 77.7),                                 # C115 / C118
           (93.0, 86.7), (94.1, 86.7), (96.2, 82.0), (97.3, 82.0)]                                 # C109 / C112
strip = []
for y in (62.6, 63.6, 64.6, 65.6):
    for x in (61.0, 62.0, 63.0, 64.0, 65.0): strip.append((x, y))
    for x in (71.5, 72.5, 73.5, 74.5, 75.5): strip.append((x, y))
    for x in (82.0, 83.0, 84.0, 85.0, 86.0): strip.append((x, y))
    if y < 64: strip += [(87.0, y), (88.0, y)]
windows = [(67.2, 71.0), (77.7, 81.5)]

def board(ax, side, title):
    for c in C:
        bx, by, bw, bh = c['bb']
        if bx + bw < X0 or bx > X1 or by + bh < Y0 or by > Y1: continue
        mine = c['b'] == side
        ax.add_patch(Rectangle((bx, by), bw, bh, fill=False, ec='#777' if mine else '#e6e6e6', lw=0.6 if mine else 0.3, zorder=3))
        for p in c['p']:
            if not mine and not p[6]: continue
            col = NC.get(p[4], '#9e9e9e')
            ax.add_patch(Rectangle((p[0], p[1]), p[2], p[3], fc=col if mine else '#f2f2f2', alpha=0.55 if mine else 1, ec='#555', lw=0.25, zorder=4))
        if mine and X0 < c['x'] < X1 and Y0 < c['y'] < Y1 and c['r'][0] in 'CQR':
            ax.text(c['x'], c['y'], c['r'], fontsize=7, ha='center', va='center', color='#222', zorder=6)
    ax.set_xlim(X0, X1); ax.set_ylim(Y0, Y1); ax.set_aspect('equal'); ax.grid(True, lw=0.2)
    ax.set_title(title, fontsize=15)

def vias(ax, pts, c='#1f77b4'):
    for (x, y) in pts:
        ax.add_patch(Circle((x, y), 0.3, fc=c, ec='k', lw=0.4, zorder=8))
        ax.add_patch(Circle((x, y), 0.15, fc='white', ec='none', zorder=9))

def poly(ax, xy, c, a=0.18, ls='-', z=2, lw=1.2):
    ax.add_patch(Polygon(xy, closed=True, fc=c, alpha=a, ec=c, lw=lw, ls=ls, zorder=z))

def box(ax, x0, y0, x1, y1, c, a=0.18, ls='-', z=2, lw=1.2):
    poly(ax, [(x0, y0), (x1, y0), (x1, y1), (x0, y1)], c, a, ls, z, lw)

def tag(ax, x, y, t, c, fs=9.5):
    ax.text(x, y, t, fontsize=fs, color=c, bbox=dict(fc='white', ec=c, boxstyle='round,pad=0.25', alpha=0.95), zorder=12)

fig, axs = plt.subplots(2, 2, figsize=(24, 21))
A, B, L, S = axs[0, 0], axs[0, 1], axs[1, 0], axs[1, 1]

# ---------- 顶层 ----------
board(A, 0, '顶层（L1）：换流回路要铺的铜和过孔')
box(A, 60.4, 82.5, 90.2, 85.0, '#d62728', 0.15)              # 电容 VIN 排 ↔ 上管漏极
box(A, 67.7, 85.0, 74.2, 88.3, '#d62728', 0.15)              # R42 下来的 VIN 通道
box(A, 60.05, 69.2, 61.9, 82.5, '#d62728', 0.12)             # 左侧 C69 / C70 / C63 的 VIN（离 C63 PGND、Q6 SW 脚各 ≥ 0.3）
box(A, 60.4, 86.3, 67.7, 88.05, '#1f77b4', 0.2)               # 左 PGND 条（上面是 R42 的 DCBUS 焊盘）
box(A, 74.2, 86.3, 90.2, 89.3, '#1f77b4', 0.2)                # 右 PGND 条
# 源极 PGND 条：上沿 66.1（离 R72 的 SW 焊盘、下管栅极脚 ≥ 0.3），向上伸指头接源极脚，避开下拉电阻的栅极端
sp = [(60.0, 62.1), (88.6, 62.1), (88.6, 66.1)]
for x0 in (82.95, 72.45, 61.95):                               # 从右往左：每列 [栅极端缺口] + [源极指头]
    g = x0 + 4.25                                              # 下拉电阻栅极端焊盘左沿（R62 / R58 / R60）
    sp += [(g + 1.11, 66.1), (g + 1.11, 64.75), (g - 0.3, 64.75), (g - 0.3, 66.1),
           (x0 + 3.5, 66.1), (x0 + 3.5, 67.5), (x0 + 0.4, 67.5), (x0 + 0.4, 66.1)]
sp += [(60.0, 66.1)]
poly(A, sp, '#1f77b4', 0.2)
vias(A, cap_top + left + strip)
for (a, b) in windows:
    A.add_patch(Rectangle((a, 61.9), b - a, 4.4, fill=False, ec='k', ls='--', lw=1.6, zorder=10))
tag(A, 66.3, 59.0, '两个窗口不打孔：④ 的 TG / BG 在 L3 从这里上去', 'k', 9)
A.add_patch(FancyArrowPatch((76.2, 84.2), (76.2, 66.9), arrowstyle='-|>', mutation_scale=22, color='#c00000', lw=3, zorder=11))
tag(A, 91.2, 79.5, '去路（顶层）：\n电容 VIN → 上管 → SW\n→ 下管 → 源极', '#c00000', 9.5)
tag(A, 91.2, 89.8, 'PGND 条：焊盘内 + 上方一排孔\n→ 穿到 L2', '#1f77b4', 9)
tag(A, 54.0, 92.2, 'C71 左半正下方是底层 C117 的 VIN，\n孔只能打在右半 / C113 之间', '#8c2d04', 8.5)
tag(A, 89.5, 61.2, '源极 PGND 条：4 行 × 每列约 20 孔，孔距 1 mm', '#1f77b4', 9)
tag(A, 68.0, 85.4, 'R42 → 漏极 VIN 通道\n（PGND 在这里断开）', '#c00000', 8)

# ---------- 底层 ----------
board(B, 1, '底层（L4，从上透视）：底层电容就近接到 VIN 岛和 L2')
for i in range(3):
    xl = 62.0 + 10.5 * i
    box(B, xl - 1, 76.9, xl + 6, 84.1, '#d62728', 0.13)       # 上管 VIN 铜岛（凸台 + 1 mm）
box(B, 62.3, 67.9, 97, 77.5, '#ff9900', 0.12, '--')            # SW 带（② 步）
box(B, 60.9, 60.9, 88.6, 66.2, '#1f77b4', 0.2)                 # 底层源极 PGND 条（离 R67 焊盘 ≥ 0.3）
vias(B, strip + bot_cap + cap_top + left)
B.add_patch(Rectangle((73.3, 66.0), 3.5, 1.6, fill=False, ec='#8c2d04', lw=1.6, ls='--', zorder=10))
tag(B, 60.5, 58.6, 'Q8 下方有底层 R67（NTC，GND）：这里的孔 y ≤ 66.0', '#8c2d04', 9)
tag(B, 91.0, 72.5, 'SW 带（② 步）', '#c06000', 9)
tag(B, 54.0, 92.6, '底层电容的 VIN 直接贴着\n上管 VIN 铜岛（经上管散热孔到漏极）\n→ 电容排不需要 VIN 过孔', '#c00000', 8.5)
tag(B, 82.0, 88.6, '底层 PGND 焊盘：和顶层重叠处\n同一个孔连三层', '#1f77b4', 9)
tag(B, 66.0, 79.8, 'C106-108：PGND 孔\n打在间隙里', '#1f77b4', 8)

# ---------- L2 ----------
L.set_title('L2：整块 PGND，回流从“列间隙”这几条路走回电容', fontsize=15)
box(L, X0, Y0, X1, Y1, '#1f77b4', 0.22, z=1)
L.add_patch(Rectangle((66.0, Y0), 27.0, 62.0 - Y0, fc='white', ec='none', zorder=1))
poly(L, [(66.5, Y0), (92.5, Y0), (92.5, 61.5), (66.5, 61.5)], '#2ca02c', 0.25, z=1)
L.plot([66.5, 92.5], [63.6, 63.6], color='#2ca02c', ls='--', lw=1.5, zorder=5)
L.text(67, 59.3, 'U9 GND 岛（上边从 63.6 收到 61.5，留 0.5 mm 缝）', fontsize=9.5, color='#1a6b1a', zorder=6)
L.text(84, 63.9, '旧边界 63.6', fontsize=8, color='#2ca02c', zorder=6)
for c in C:
    if c['b'] != 0: continue
    for p in c['p']:
        if c['r'] in ('Q6', 'Q5', 'Q7') and p[2] > 4:
            L.add_patch(Rectangle((p[0], p[1]), p[2], p[3], fc='white', ec='#d62728', lw=1, hatch='..', zorder=3))
        if c['r'] in ('Q9', 'Q8', 'Q10') and p[2] > 4:
            L.add_patch(Rectangle((p[0], p[1]), p[2], p[3], fc='white', ec='#ff9900', lw=1, hatch='..', zorder=3))
vias(L, cap_top + left + strip + bot_cap)
for x in (59.0, 69.6, 80.1, 91.5):
    L.add_patch(FancyArrowPatch((x, 66.8), (x, 85.6), arrowstyle='-|>', mutation_scale=20, color='#0b4f9c', lw=2.6, ls='--', zorder=11))
L.add_patch(Rectangle((74.2, 83.2), 16, 1.8, fill=False, ec='#c00000', lw=2, ls=':', zorder=10))
tag(L, 58.8, 92.5, '白色网格 = 上管 / 下管焊盘里的散热孔在 L2 上挖的洞\n（VIN / SW 孔穿过 PGND 层要隔离）', '#444', 8.5)
tag(L, 76.0, 90.6, '红点框：电容 VIN 排下面不要打 VIN 孔，\n否则在 L2 上挖出一条横缝，回流要绕', '#c00000', 8.5)
tag(L, 54.2, 75.8, '回流\n高速路', '#0b4f9c', 9)
L.set_xlim(X0, X1); L.set_ylim(Y0, Y1); L.set_aspect('equal'); L.grid(True, lw=0.2)

# ---------- 截面 ----------
S.set_title('截面示意（不按比例）：回流离去路越近，回路电感越小', fontsize=15)
S.set_xlim(0, 100); S.set_ylim(-4, 64); S.axis('off')
def stack(y0, title):
    S.text(0, y0 + 27, title, fontsize=12, fontweight='bold')
    lay = [('L1 顶层', y0 + 22), ('L2 PGND', y0 + 18), ('L3 信号', y0 + 6), ('L4 底层', y0 + 2)]
    for n, y in lay:
        S.add_patch(Rectangle((14, y - 0.4), 74, 0.8, fc='#c87533', ec='none'))
        S.text(1, y - 0.5, n, fontsize=9.5)
    S.text(89, y0 + 19.5, '0.21 mm', fontsize=9); S.text(89, y0 + 11.5, '1.1 mm 芯板', fontsize=9); S.text(89, y0 + 3.6, '0.21 mm', fontsize=9)
    S.add_patch(Rectangle((18, y0 + 22.4), 7, 2.4, fc='#888', ec='k')); S.text(18.6, y0 + 23.1, '电容', fontsize=8.5, color='w')
    S.add_patch(Rectangle((46, y0 + 22.4), 20, 3.2, fc='#555', ec='k')); S.text(48, y0 + 23.5, '上管 → SW → 下管', fontsize=8.5, color='w')
    return lay
l1 = stack(32, '好：回流走 L2（紧贴顶层）')
S.annotate('', (66, 56.4), (25, 56.4), arrowprops=dict(arrowstyle='-|>', color='#c00000', lw=2.5))
S.plot([67, 67], [54.4, 50], color='#1f77b4', lw=4); S.plot([22, 22], [54.4, 50], color='#1f77b4', lw=4)
S.annotate('', (22, 50), (67, 50), arrowprops=dict(arrowstyle='-|>', color='#1f77b4', lw=2.5, ls='--'))
S.text(28, 46.2, '回路高度 ≈ 0.28 mm → 约 0.2–0.4 nH；过孔 L1→L2 每个约 0.13 nH', fontsize=10, color='#0b4f9c', bbox=bb)
l2 = stack(0, '差：L2 被挖断，回流只能绕到底层')
S.annotate('', (66, 24.4), (25, 24.4), arrowprops=dict(arrowstyle='-|>', color='#c00000', lw=2.5))
S.plot([67, 67], [22.4, 2], color='#1f77b4', lw=4); S.plot([22, 22], [22.4, 2], color='#1f77b4', lw=4)
S.annotate('', (22, 2), (67, 2), arrowprops=dict(arrowstyle='-|>', color='#1f77b4', lw=2.5, ls='--'))
S.add_patch(Rectangle((35, 17.4), 18, 1.2, fc='white', ec='none'))
S.text(36, 15.4, 'L2 断口', fontsize=9, color='#c00000')
S.text(14, -3.5, '回路高度 ≈ 1.7 mm → 约 1.2–2.4 nH；过孔穿到底层每个约 1.4 nH', fontsize=10, color='#c00000', bbox=bb)
plt.tight_layout()
plt.savefig('/home/user/hengliu/docs/仿真/布线演算/换流回路细节_20261028.png', dpi=80)
print(len(cap_top), len(left), len(strip), len(bot_cap))
