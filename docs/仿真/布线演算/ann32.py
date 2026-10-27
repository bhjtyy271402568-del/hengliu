import json, matplotlib, logging; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
plt.rcParams['font.sans-serif']=['WenQuanYi Zen Hei','DejaVu Sans']
C=json.load(open('lay32.json'))
col={'VCC_BAT':'#e6550d','GND_BAT':'#636363','DCBUS':'#ff9896','PGND':'#1f77b4','LT_VIN':'#d62728'}
bb=dict(fc='white',ec='none',alpha=0.9)
fig,axs=plt.subplots(1,2,figsize=(22,9.5))
for side,ax in enumerate(axs):
    for c in C:
        if not(10<c['x']<75 and 50<c['y']<100): continue
        mine=c['b']==side; bx,by,bw,bh=c['bb']
        ax.add_patch(Rectangle((bx,by),bw,bh,fill=False,ec='k' if mine else '#dddddd',lw=0.6 if mine else 0.3,zorder=2))
        for p in c['p']:
            if not mine and not p[6]: continue
            ax.add_patch(Rectangle((p[0],p[1]),p[2],p[3],fc=col.get(p[4],'#aaaaaa'),ec='k',lw=0.2,alpha=0.85 if mine else 0.3,zorder=3))
        if mine and 18<c['x']<66 and 56<c['y']<96: ax.text(c['x'],c['y'],c['r'],fontsize=7,ha='center',va='center',fontweight='bold',zorder=6)
    for h in [(34.5,91.5)]: ax.add_patch(Circle(h,1.6,fc='w',ec='k',zorder=5))
    ax.plot([0,128,128,0,0],[0,0,95,95,0],'k',lw=1.5)
    ax.set_xlim(18,66); ax.set_ylim(56,96); ax.set_aspect('equal'); ax.grid(True,lw=0.25)
for ax,f,t,c in [(axs[0],'neck_top.json','顶层最窄处约 10.0 mm（在 CN3 出口）','red'),(axs[1],'neck_bot.json','底层最窄处约 13.8 mm（在 CN3 出口）','red')]:
    pts=json.load(open(f))['pts']; ax.scatter([p[0] for p in pts],[p[1] for p in pts],s=8,c=c,zorder=8)
    ax.text(19,93.5,t,fontsize=12,color=c,bbox=bb,zorder=9)
pts=json.load(open('neck_q12.json'))['pts']; axs[0].scatter([p[0] for p in pts],[p[1] for p in pts],s=8,c='purple',zorder=8)
axs[0].text(19,57.5,'紫点：Q1 → Q2 之间（半电流约 23 A）约 5.7 mm',fontsize=11,color='purple',bbox=bb,zorder=9)
axs[1].text(19,57.5,'底层电流要在 Q1 / Q2 源极脚旁打一排过孔上到顶层',fontsize=11,color='#a33a00',bbox=bb,zorder=9)
axs[0].set_title('电池正极（VCC_BAT）通路：顶层',fontsize=14); axs[1].set_title('底层（从上透视）',fontsize=14)
plt.tight_layout(); plt.savefig('/home/user/hengliu/docs/仿真/布线演算/输入通路宽度_20261028.png',dpi=100)
