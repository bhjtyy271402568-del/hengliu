"""辅助电源板前端（防反接 + LM5069 + 放行）布局规划图，坐标 y 向上（和嘉立创一致），单位 mm。
用法：python3 aux_front_plan.py aux_cur.json 输出.png（aux_cur.json = 10-27 版辅助板器件和焊盘）"""
import json, sys, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch
plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'
d = json.load(open(sys.argv[1])); C = {c['r']: c for c in d['c']}
FRONT = {'J1','D1','Q1','R1','D2','C1','R2','C2','U1','Q2','C3','C4','R3','R4','R5','R6','R7',
         'R8','R9','R10','R11','Q3','Q4','D3','C5','C6','C7','C8','C9','C10','U2','U3'}
CHAIN = {'R8','R9','R10','R11','Q3','Q4','D3'}
NETC = {'$1N661':'#d62728','BAT_PROT':'#ff7f0e','$1N667':'#bcbd22','AUX_IN':'#e377c2','BAT_GND':'#7f7f7f',
        'CTRL_P':'#1f77b4','CTRL_N':'#17becf','HS_PGD':'#2ca02c','$1N669':'#9467bd'}

def base(ax, title, moved=()):
    ax.add_patch(Rectangle((0, 0), 95, 95, fill=False, ec='k', lw=1.5))
    ax.add_patch(Rectangle((58, 0), 8, 95, fc='#f3e5f5', ec='none'))
    ax.text(62, 93, '隔离带\n（示意）', ha='center', va='top', fontsize=9, color='#7b1fa2')
    for x, y, r in d['keep']:
        if x < 95: ax.add_patch(Circle((x, y), r, fc='#eeeeee', ec='#999999', ls=':'))
    for r, c in C.items():
        if r not in FRONT or r in moved: continue
        bb = c['bb']; big = r in ('U2', 'U3')
        ax.add_patch(Rectangle((bb[0], bb[1]), bb[2], bb[3], fill=False, ec='#555555' if big else '#999999',
                               lw=1.2 if big else .7, ls='--' if big else '-'))
        for p in c['p']:
            ax.add_patch(Rectangle((p[0], p[1]), p[2], p[3], fc=NETC.get(p[4], '#cccccc'), ec='none', alpha=.85))
        if big: ax.text(bb[0] + bb[2] / 2 + 8, bb[1] + bb[3] / 2, r + ('\nURF 15 V' if r == 'U2' else '\nURB -15 V'),
                        ha='center', va='center', fontsize=11, color='#555555')
        elif r[0] in 'JQUDR' or r in ('C2', 'C9'):
            ax.text(bb[0] + bb[2] / 2, bb[1] + bb[3] + .3, r, ha='center', va='bottom', fontsize=7)
    ax.set_xlim(-1, 96); ax.set_ylim(-1, 96); ax.set_aspect('equal'); ax.set_title(title, fontsize=12)

def path(ax, pts, c, lw, ls='-', z=3):
    xs, ys = zip(*pts); ax.plot(xs, ys, color=c, lw=lw, ls=ls, solid_capstyle='round', zorder=z, alpha=.8)

def X(ax, x, y):
    ax.plot([x], [y], marker='X', ms=14, color='r', mec='k', zorder=6)

fig, axs = plt.subplots(1, 3, figsize=(31, 11.5))
# ---------- A：现状 ----------
ax = axs[0]; base(ax, 'A 现在（10-27）：U1 在功率路径外侧（靠板边）\n红 X = 顶层信号必须跨过 5 A 铜的地方')
POWER = [(13.1, 38.5), (7.5, 30), (7.5, 24), (17.5, 26.5), (21.9, 20), (28.1, 20), (33.7, 11.5), (44.3, 14), (39.1, 26.4)]
path(ax, POWER, '#d62728', 9)
TRUNK = [(39.1, 26.4), (34, 30), (32, 50), (28, 58), (26.5, 61), (26.5, 85), (36.6, 79.1)]
path(ax, TRUNK, '#e377c2', 7)
path(ax, [(25, 11.2), (25, 9), (21, 9), (21, 30), (18, 41)], '#2ca02c', 2.5, '--')
X(ax, 21, 23)
path(ax, [(29.2, 45.0), (39.1, 41.6)], '#17becf', 2.5, '--'); X(ax, 32.8, 43.6)
path(ax, [(29.2, 47.0), (31, 55), (33, 66), (36.6, 71.5)], '#1f77b4', 2.5, '--'); X(ax, 29.6, 56)
path(ax, [(26, 11.2), (27, 4.5), (41, 4.5), (44.3, 9)], '#9467bd', 2.5)
ax.text(30, 2.2, 'GATE 约 18 mm（绕过散热焊盘）', fontsize=9, color='#9467bd')
ax.text(13, 55.5, 'D1 离 J1 约 12 mm', fontsize=9, color='#d62728')
ax.text(1, 11, 'D2 / C1 离 Q1\n栅源脚 6–10 mm', fontsize=9)
ax.text(1.5, 70, '粗红 = 电池 → Q1 → R2 → Q2\n粉 = AUX_IN 母线（走模块输入脚左侧）\n绿虚 = PGD；蓝虚 = 两路 CTRL',
        fontsize=10, va='top')
# ---------- B：建议 ----------
ax = axs[1]; moved = {'D1', 'D2', 'C1', 'R1'} | CHAIN
base(ax, 'B 建议：功率走底边一条线，信号分到两侧的通道\n放行电路挪到 Q2 右边，CTRL 从模块输入脚右侧上去', moved)
path(ax, POWER, '#d62728', 9); path(ax, TRUNK, '#e377c2', 7)
def blk(x, y, w, h, t, c='#2ca02c'):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.3', fc=c, alpha=.18, ec=c, lw=1.5))
    ax.text(x + w / 2, y + h / 2, t, ha='center', va='center', fontsize=9)
blk(15.6, 37.5, 5.9, 6.9, 'D1\n紧贴\nJ1', '#d62728')
blk(19.8, 21.0, 2.6, 5.8, 'D2\nC1', '#9467bd'); blk(8.0, 14.5, 4.0, 3.5, 'R1', '#9467bd')
blk(48.5, 3.5, 8.5, 14.5, '放行\nQ3 Q4 D3\nR8–R11')
path(ax, [(25, 11.2), (25, 2.6), (51.5, 2.6), (51.5, 3.3)], '#2ca02c', 2.5, '--')
path(ax, [(54, 18), (49, 30), (49, 41.6), (40.6, 41.6)], '#17becf', 2.5, '--')
path(ax, [(55.5, 18), (51, 30), (51, 71.5), (37.9, 71.5)], '#1f77b4', 2.5, '--')
path(ax, [(48.5, 12), (46.3, 14)], '#e377c2', 3)
ax.text(44, 19.5, 'R8、Q3 发射极就近接\nQ2 源极的 AUX_IN', fontsize=8.5, va='bottom', ha='right')
ax.text(52.5, 50, 'CTRL 走模块\n肚子下（一次侧，\n离隔离带 ≥ 7 mm）', fontsize=9, color='#1f77b4')
ax.text(25.5, 1.0, 'PGD 从 C4 / R7 下面、Q2 散热焊盘下方绕出', fontsize=8.5, color='#2ca02c')
ax.text(1.5, 70, '没有一根顶层信号线跨过功率铜，\n底层可以整块铺 BAT_GND，\n电流去路和回路上下重合', fontsize=10, va='top')
# ---------- C：U1 周围放大 ----------
ax = axs[2]; ax.set_xlim(11, 54); ax.set_ylim(-1, 31); ax.set_aspect('equal')
ax.set_title('C U1 周围放大：小件贴着自己的脚；小信号地先汇到 5 脚，再一个孔下地', fontsize=12)
for r in ('R2', 'Q2', 'U1', 'C2', 'C3', 'C4', 'R3', 'R4', 'R5', 'R6', 'R7'):
    c = C[r]; bb = c['bb']
    ax.add_patch(Rectangle((bb[0], bb[1]), bb[2], bb[3], fill=False, ec='#888888', lw=.8))
    for p in c['p']:
        ax.add_patch(Rectangle((p[0], p[1]), p[2], p[3], fc=NETC.get(p[4], '#cccccc'), ec='none', alpha=.85))
    if r != 'U1': ax.text(bb[0] + bb[2] / 2, bb[1] + bb[3] + .2, r, ha='center', va='bottom', fontsize=9)
PIN = {1: 'SENSE', 2: 'VIN', 3: 'UVLO', 4: 'OVLO', 5: 'GND', 6: 'TIMER', 7: 'PWR', 8: 'PGD', 9: 'OUT', 10: 'GATE'}
for p in C['U1']['p']:
    n = int(p[5]); x = p[0] + p[2] / 2; y = p[1] + p[3] / 2
    ax.text(x, y + (0.7 if y > 13 else -0.7), f'{n} {PIN[n]}', rotation=90, fontsize=7,
            ha='center', va='bottom' if y > 13 else 'top')
path(ax, [(22.9, 18.4), (25.5, 16.4)], '#000000', 1.5); path(ax, [(27.1, 18.4), (26.0, 16.4)], '#000000', 1.5)
ax.text(30, 22.5, '① R2 开尔文：从两个焊盘内侧边（靠电阻体）\n引出，成对走到 1、2 脚，不碰铺铜', fontsize=9.5, va='bottom')
ax.text(12, 30, '② C2 贴 R2 输入焊盘：手册要求 VIN 旁路电容靠近检流电阻，\n不放在 VIN 脚上（短路关断瞬间防 VIN–SENSE 被 LC 拉开）', fontsize=9.5, va='top')
ax.plot([24.0, 24.0, 21.0, 19.0, 15.0, 15.0], [15.8, 17.6, 17.6, 7.0, 4.0, 4.0], color='#7f7f7f', lw=2, ls=':')
ax.plot([24.0, 24.0, 28.0], [5.4, 4.0, 6.0], color='#7f7f7f', lw=2, ls=':')
ax.add_patch(Circle((21.0, 17.6), .45, fc='k')); ax.text(15.5, 18.5, '唯一地孔', fontsize=9)
ax.text(12, 26.0, '③ 灰点线：R4、R6、R7、C4 的地\n先汇到 5 脚，再一孔到 BAT_GND', fontsize=9.5, va='top')
path(ax, [(26, 11.2), (26.6, 6.0), (40.0, 6.0), (40.0, 9.0), (42.3, 9.0)], '#9467bd', 2.2)
path(ax, [(25.5, 11.2), (25.8, 4.6), (47.5, 4.6), (47.5, 14.0), (46.3, 14.0)], '#e377c2', 1.4)
path(ax, [(25.0, 11.2), (25.0, 2.6), (51.5, 2.6)], '#2ca02c', 1.6, '--')
ax.text(30, 6.6, '④ GATE（紫）', fontsize=9, color='#9467bd')
ax.text(48.2, 9.0, 'OUT（粉）绕到\n栅极焊盘外侧\n接源极，不交叉', fontsize=8.5, color='#c2185b', va='center')
ax.text(30.5, 0.4, '⑤ PGD（绿虚）贴板边出去，到右边放行电路', fontsize=9, color='#2ca02c')
plt.tight_layout(); plt.savefig(sys.argv[2], dpi=75); print('saved')
