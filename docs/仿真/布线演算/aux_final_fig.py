"""辅助板终审标注图：辅助板两层铜（淡）+ 恒流源板高器件投影（L8 等）+ 问题编号。y 向上。
用法：/usr/bin/python3 aux_final_fig.py snap.pkl lay.pkl 输出.png"""
import sys, pickle, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Rectangle, Circle
plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'
S = pickle.load(open(sys.argv[1], 'rb')); L = pickle.load(open(sys.argv[2], 'rb'))
fig, ax = plt.subplots(figsize=(20, 15))
for lay, col, a in ((2, '#9cb8e0', .5), (1, '#e8a59a', .5)):
    for q in getattr(L[lay], 'geoms', [L[lay]]):
        ax.add_patch(MP(list(q.exterior.coords), fc=col, ec='none', alpha=a))
        for h in q.interiors: ax.add_patch(MP(list(h.coords), fc='white', ec='none'))
ax.add_patch(Rectangle((0, 0), 128, 95, fill=False, ec='k', lw=1.5))
# 恒流源板（下层）高器件投影：L8 CPCF3535 35 × 35 mm、高 34.2 mm；C97 / C99 Ø10 × 16.5
ax.add_patch(Rectangle((108.86 - 17.5, 62.6 - 17.5), 35, 35, fill=False, ec='#6a1b9a', lw=2.5, ls='--'))
ax.text(110, 46.5, '下层恒流源板 L8 投影\n高 34.2 mm，到辅助板底面只剩约 5.8 mm', color='#6a1b9a', fontsize=12, weight='bold')
for x, y in ((81, 36), (81, 24)):
    ax.add_patch(Circle((x, y), 5, fill=False, ec='#6a1b9a', lw=1.5, ls='--'))
ax.text(70.5, 17.0, '下层 C97 / C99\nØ10 × 16.5', color='#6a1b9a', fontsize=10)
# 底面高器件
for ref, (cx, cy), col in (('D4', (94.76, 67.88), '#c62828'), ('D5', (89.5, 29.27), '#ef6c00')):
    ax.add_patch(Rectangle((cx - 2.25, cy - 5), 4.5, 10, fc=col, alpha=.75, ec='k'))
ax.annotate('① D4 立式 TO-220 装在底面，向下伸出约 15–18 mm，\n正好压在 L8 上方（重叠约 10 mm）→ 必须改', (94.8, 72.9), xytext=(60, 90), fontsize=13, color='#c62828', weight='bold',
            arrowprops=dict(arrowstyle='->', color='#c62828', lw=2))
ax.annotate('D5 同样立式装在底面：不在 L8 上方，\n离下层 C97 / C99 约 1.3 mm（水平），能装，建议和 D4 一起改', (89.5, 24.3), xytext=(52, 6), fontsize=11, color='#ef6c00',
            arrowprops=dict(arrowstyle='->', color='#ef6c00', lw=1.5))
ax.annotate('② U1 LM5069（0.5 mm 脚距，脚间 0.20 mm）\n在 2 oz 铜上刚到嘉立创下限 → 下单前过 DFM', (23.5, 21.3), xytext=(2, 6), fontsize=11, color='#1565c0',
            arrowprops=dict(arrowstyle='->', color='#1565c0', lw=1.5))
ax.annotate('③ U2 散热片朝上，不在两板夹层的风道里', (62, 90), xytext=(40, 93.3), fontsize=11, color='#2e7d32')
ax.annotate('J2 / J4 插针、C11 / C12 / C18 引脚也在 L8 上方：剪脚 ≤ 2 mm', (122.5, 64), xytext=(84, 2.5), fontsize=10.5, color='#6a1b9a',
            arrowprops=dict(arrowstyle='->', color='#6a1b9a', lw=1))
ax.annotate('唯一一个 0.305 / 0.61 mm 过孔', (29.97, 24.04), xytext=(30, 45), fontsize=10, color='#555555', arrowprops=dict(arrowstyle='->', color='#555555'))
ax.annotate('C22 / C23 经底层接到第 7 脚（Sense+），\n可改接第 8 脚', (82, 73.5), xytext=(64, 80.5), fontsize=10, color='#555555', arrowprops=dict(arrowstyle='->', color='#555555'))
ax.axvspan(57.5, 66.5, color='#fff3e0', zorder=0); ax.text(58, 50, '隔离带\n9.0 mm\n两层\n无铜', fontsize=11, color='#e65100')
for v in S['vias']: ax.add_patch(Circle((v['x'], v['y']), v['h'] / 2 + .1, fc='k'))
ax.set_xlim(-1, 129); ax.set_ylim(-1, 96); ax.set_aspect('equal'); ax.grid(True, lw=.3)
ax.set_title('辅助电源板终审（5a4c1c977e82）：红 = 顶层铜，蓝 = 底层铜，紫虚线 = 下层恒流源板高器件投影；y 向上，mm', fontsize=13)
fig.savefig(sys.argv[3], dpi=75, bbox_inches='tight'); print('saved')
