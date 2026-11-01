"""辅助板 Gerber 铜层 + 位号查看图（y 向上）。用法：/usr/bin/python3 aux_view.py snap.pkl lay.pkl 输出.png x0 y0 x1 y1 [层 1/2/both]"""
import sys, pickle, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MP, Circle
plt.rcParams['font.family'] = 'WenQuanYi Zen Hei'
S = pickle.load(open(sys.argv[1], 'rb')); L = pickle.load(open(sys.argv[2], 'rb'))
x0, y0, x1, y1 = map(float, sys.argv[4:8]); which = sys.argv[8] if len(sys.argv) > 8 else 'both'
fig, ax = plt.subplots(figsize=(max(8, (x1 - x0) / 4), max(6, (y1 - y0) / 4)))
def draw(g, fc, a, ec='none'):
    for q in getattr(g, 'geoms', [g]):
        if q.is_empty: continue
        ax.add_patch(MP(list(q.exterior.coords), closed=True, fc=fc, ec=ec, alpha=a, lw=.4))
        for h in q.interiors: ax.add_patch(MP(list(h.coords), closed=True, fc='white', ec='none', alpha=1))
if which in ('2', 'both'): draw(L[2], '#3b7dd8', .45 if which == 'both' else .8)
if which in ('1', 'both'): draw(L[1], '#d84b3b', .55 if which == 'both' else .8)
for v in S['vias']: ax.add_patch(Circle((v['x'], v['y']), v['h'] / 2, fc='k'))
for p in S['pads']:
    c = p['g'].centroid
    if x0 <= c.x <= x1 and y0 <= c.y <= y1 and p['ref']:
        ax.text(c.x, c.y, f"{p['ref']}.{p['num']}\n{p['net']}", fontsize=5.5, ha='center', va='center', color='k')
ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect('equal'); ax.grid(True, lw=.3)
ax.set_title(f'红 = 顶层，蓝 = 底层（{which}），黑点 = 过孔；y 向上')
fig.savefig(sys.argv[3], dpi=110, bbox_inches='tight')
