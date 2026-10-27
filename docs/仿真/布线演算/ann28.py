import json, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, FancyArrowPatch
plt.rcParams['font.sans-serif']=['WenQuanYi Zen Hei','Noto Sans CJK SC','DejaVu Sans']
import logging; logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
C=json.load(open('lay28.json'))
col={'LT_VIN':'#d62728','DCBUS':'#ff9896','LT_SW':'#ff9900','PGND':'#1f77b4','GND':'#2ca02c','LT_SHUNT_P':'#9467bd','VCC_OUT':'#8c564b','LT_TG':'#e377c2','LT_BG':'#17becf'}
x0,x1,y0,y1=50,128,20,95
fig,axs=plt.subplots(1,2,figsize=(24,12))
for side,ax in enumerate(axs):
    ax.add_patch(Rectangle((0,0),128,95,fill=False,ec='k',lw=1.5))
    for h in [[124.5,91.5],[64,52.5],[100,88],[93,3.5]]: ax.add_patch(Circle(h,1.6,fc='w',ec='k'))
    for c in C:
        if not(x0-12<c['x']<x1+12 and y0-12<c['y']<y1+12): continue
        mine=(c['b']==side); bx,by,bw,bh=c['bb']
        ax.add_patch(Rectangle((bx,by),bw,bh,fill=False,ec='k' if mine else '#dddddd',lw=0.6 if mine else 0.3,zorder=2))
        for p in c['p']:
            x,y,w,h,net,num,th,ly=p
            if not mine and not th: continue
            ax.add_patch(Rectangle((x,y),w,h,fc=col.get(net,'#999999'),ec='k',lw=0.2,alpha=0.85 if mine else 0.35,zorder=3))
        if mine and bw*bh>1 and x0<c['x']<x1 and y0<c['y']<y1: ax.text(c['x'],c['y'],c['r'],clip_on=True,fontsize=6.5,ha='center',va='center',zorder=6,fontweight='bold')
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.grid(True,lw=0.25)
A,B=axs
A.set_title('顶层：问题与建议',fontsize=14); B.set_title('底层（从上透视）：40 A 通道',fontsize=14)
# --- top annotations
A.add_patch(Rectangle((88.2,63.9),1.9,10.5,fc='none',ec='red',lw=2.5,zorder=8))
A.annotate('③ 右列栅极组 R49/R53/R61\n把 Q7/Q10 到 L8 的顶层 SW 全挡住\n（HS 栅极脚天生在 SW 这一排，挪不走）',(89,69),(90,86.5),fontsize=10,color='red',bbox=dict(fc='white',ec='none',alpha=0.85),arrowprops=dict(arrowstyle='->',color='red'),zorder=9)
A.add_patch(Rectangle((70.95,78.2),3.27,4.7,fc='red',alpha=0.25,ec='red',lw=1.5,zorder=8))
A.annotate('④ R42 → 漏极的 VIN 顶层只有约 2.8 mm 缺口\n（底层 x 65–73 有约 7 mm 可并联）',(72.6,80.5),(51,89),fontsize=10,color='#b00',bbox=dict(fc='white',ec='none',alpha=0.85),arrowprops=dict(arrowstyle='->',color='#b00'),zorder=9)
for i in range(3):
    xl=62.0+10.5*i
    A.add_patch(Rectangle((xl,72.7),5.0,5.2,fill=False,ec='purple',ls='--',lw=1.6,zorder=7))
    A.add_patch(Rectangle((xl,65.5),5.0,5.0,fill=False,ec='purple',ls='--',lw=1.6,zorder=7))
A.text(51,21,'紫虚线 = 按新位置应有的凸台（上管 y 72.7–77.9，下管 y 65.5–70.5，列距 10.5 mm）',fontsize=9,color='purple',bbox=dict(fc='white',ec='none',alpha=0.85))
A.annotate('① R67（NTC）在板外 x 175.7',(127.5,62.6),(98,56),fontsize=10,color='red',bbox=dict(fc='white',ec='none',alpha=0.85),arrowprops=dict(arrowstyle='->',color='red'),zorder=9)
for xg in (69.0,79.6):
    A.add_patch(Rectangle((xg,63.0),3.4,10.8,fc='#e377c2',alpha=0.18,ec='none',zorder=1))
A.text(97.5,64,'粉色条：顶层列间隙空着（约 3.5 mm），\nTG / SW 成对从这里上去；\nTG、BG 的横向分配走 L3',fontsize=9,color='#a0306a',bbox=dict(fc='white',ec='none',alpha=0.85))
A.annotate('⑦ R212 离 CN14.1 只 0.24 mm',(116.9,33.25),(88,23),fontsize=9,color='#b00',bbox=dict(fc='white',ec='none',alpha=0.85),arrowprops=dict(arrowstyle='->',color='#b00'),zorder=9)
# --- bottom annotations
for r in ['C106','C107','C108','R71','C94']:
    c=[c for c in C if c['r']==r][0]; bx,by,bw,bh=c['bb']
    B.add_patch(Rectangle((bx-0.2,by-0.2),bw+0.4,bh+0.4,fill=False,ec='red',lw=2.5,zorder=8))
sw=Polygon([(62.3,63.9),(97,63.9),(97,71.6),(109,71.6),(109,76.2),(96.9,76.2),(92.4,72.4),(62.3,72.4)],closed=True,fc='orange',alpha=0.22,ec='darkorange',lw=2,ls='--',zorder=4)
B.add_patch(sw)
B.annotate('② SW 40 A 只能走底层：三列下管铜岛\n连成一条（y 约 63.7–72.3）到 L8 第 1 脚。\n现在被 C106–C108、R71/C94（红框）\n卡到约 3.4–4.7 mm',(80,66),(75.5,90),fontsize=9.5,color='#c05000',bbox=dict(fc='white',ec='none',alpha=0.85),arrowprops=dict(arrowstyle='->',color='#c05000'),zorder=9)
pg=Polygon([(114.4,32.4),(122,32.4),(122,49),(108.2,49),(108.2,53.6),(121,53.6),(121,63.4),(62,63.4),(62,60.3),(89,60.3),(89,54),(97,54),(97,43),(100,33)],closed=True,fc='#1f77b4',alpha=0.15,ec='#1f77b4',lw=2,ls='--',zorder=4)
B.add_patch(pg)
B.annotate('⑤ PGND 回流通道：CN14.1 → R56 / L8 正下方 → 下管源极。\n回流紧贴正向电流（L8 → R56 → CN14），回路面积最小',(104,45),(52,24),fontsize=10,color='#1f4f8f',bbox=dict(fc='white',ec='none',alpha=0.85),arrowprops=dict(arrowstyle='->',color='#1f4f8f'),zorder=9)
plt.tight_layout(); plt.savefig('/home/user/hengliu/docs/仿真/布线演算/布局核对_20261027b.png',dpi=105)
