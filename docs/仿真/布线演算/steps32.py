import json, matplotlib, logging; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon, FancyArrowPatch
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
plt.rcParams['font.sans-serif']=['WenQuanYi Zen Hei','DejaVu Sans']
C=json.load(open('lay32.json'))
bb=dict(fc='white',ec='none',alpha=0.9)
fig,axs=plt.subplots(1,2,figsize=(26,10.5))
for side,ax in enumerate(axs):
    for c in C:
        mine=c['b']==side; bx,by,bw,bh=c['bb']
        ax.add_patch(Rectangle((bx,by),bw,bh,fill=False,ec='#888' if mine else '#e3e3e3',lw=0.5 if mine else 0.3,zorder=2))
        for p in c['p']:
            if not mine and not p[6]: continue
            ax.add_patch(Rectangle((p[0],p[1]),p[2],p[3],fc='#bdbdbd' if mine else '#eeeeee',ec='#777',lw=0.2,zorder=3))
        if mine and bw*bh>25 and 15<c['x']<126 and 22<c['y']<95: ax.text(c['x'],c['y'],c['r'],fontsize=6.5,ha='center',va='center',color='#555',zorder=4)
    for h in [(34.5,91.5),(64,52.5),(100,88)]: ax.add_patch(Circle(h,1.6,fc='w',ec='k',zorder=5))
    ax.plot([0,128,128,0,0],[0,0,95,95,0],'k',lw=1.5)
    ax.set_xlim(15,128); ax.set_ylim(22,96); ax.set_aspect('equal'); ax.grid(True,lw=0.2)
def zone(ax,xy,c,a=0.3,ls='-'):
    ax.add_patch(Polygon(xy,closed=True,fc=c,alpha=a,ec=c,lw=1.6,ls=ls,zorder=6))
def tag(ax,x,y,t,c,fs=11):
    ax.text(x,y,t,fontsize=fs,color=c,fontweight='bold',bbox=dict(fc='white',ec=c,boxstyle='round,pad=0.25',alpha=0.95),zorder=10)
A,B=axs
A.set_title('顶层：各步骤的位置',fontsize=15); B.set_title('底层（从上透视）',fontsize=15)
# 1 commutation loop
zone(A,[(60.2,83.0),(90.3,83.0),(90.3,90.2),(60.2,90.2)],'#1f77b4',0.22)
zone(A,[(62.0,62.0),(88.4,62.0),(88.4,66.4),(62.0,66.4)],'#1f77b4',0.3)
tag(A,92,88,'① 电容 PGND 端打孔到 L2','#1f77b4',10)
tag(A,92,62.5,'① 下管源极过孔带','#1f77b4',10)
# 2 SW top
for x0 in (62.3,72.8,83.3):
    zone(A,[(x0,73.3),(x0+4.5,73.3),(x0+4.5,75.9),(x0,75.9)],'#ff9900',0.45)
zone(A,[(66.8,69.7),(72.8,69.7),(72.8,73.1),(66.8,73.1)],'#ff9900',0.35)
zone(A,[(77.3,69.7),(83.3,69.7),(83.3,73.1),(77.3,73.1)],'#ff9900',0.35)
zone(A,[(89.9,64.5),(97,64.5),(97,76.2),(89.9,76.2)],'#ff9900',0.35)
tag(A,98,79,'② SW 顶层','#c06000',10)
# 3 main path
zone(A,[(32.3,74.5),(58,74.5),(58,76.9),(32.3,76.9)],'#e6550d',0.3,'--')
zone(A,[(32.3,81.3),(44.5,81.3),(44.5,83.7),(32.3,83.7)],'#e6550d',0.3,'--')
tag(A,16,79.5,'③a 电池正极','#a33a00',10)
zone(A,[(59.0,88.4),(60.2,88.4),(60.2,93.9),(59.0,93.9)],'#e377c2',0.6)
tag(A,47,93.2,'③b DCBUS → R42','#a0306a',10)
zone(A,[(69.2,86.4),(73.5,86.4),(73.5,88.4),(69.2,88.4)],'#d62728',0.4)
tag(A,74,91.8,'③c R42 → 漏极','#d62728',10)
zone(A,[(105.4,44.2),(121,44.2),(121,49),(105.4,49)],'#9467bd',0.4)
tag(A,112,46.2,'③d L8 → R56','#6a3d9a',10)
tag(A,99,29,'③e R56 → CN14','#8c564b',10)
# 4 gate
for x0 in (69.0,79.6):
    zone(A,[(x0,58),(x0+3.4,58),(x0+3.4,74),(x0,74)],'#e377c2',0.25)
tag(A,63,56.5,'④ TG/SW、BG 走列间隙','#a0306a',10)
# 6 kelvin
for (x,y,c) in [(63.47,91.1,'#2ca02c'),(69.17,91.1,'#2ca02c'),(106.5,40.8,'#2ca02c'),(106.5,35.1,'#2ca02c')]:
    A.plot([x],[y],marker='o',ms=9,mfc=c,mec='k',zorder=11)
tag(A,112,38.5,'⑥ 开尔文取样点','#2ca02c',10)
# 7 tie
A.plot([79],[55],marker='*',ms=22,color='gold',mec='k',zorder=11)
tag(A,82.5,52.3,'⑦ 唯一桥接点','#8a6d00',10)
# bottom
zone(B,[(62.3,67.9),(97,67.9),(97,71.7),(109.4,71.7),(109.4,76.2),(97,76.2),(97,77.5),(62.3,77.5)],'#ff9900',0.3)
tag(B,64,79.2,'② SW 底层主通道（约 9.6 mm）','#c06000',10)
zone(B,[(24.6,78.9),(32.3,78.9),(32.3,76),(46,76),(46,74),(58,74),(58,82),(32.3,82),(32.3,89),(24.6,89)],'#e6550d',0.25)
tag(B,16,92,'③a 电池正极底层主力（≥13.8 mm）','#a33a00',10)
zone(B,[(114.4,32.4),(122,32.4),(122,49),(108.2,49),(108.2,53.6),(121,53.6),(121,63.4),(89,63.4),(89,54),(97,54),(97,43),(100,33)],'#1f77b4',0.18,'--')
tag(B,99,58.6,'③f PGND 回流（底层 ≥ 19 mm）','#1f4f8f',10)
for i in range(3):
    xl=62.0+10.5*i
    B.add_patch(Rectangle((xl,77.9),5,5.2,fill=False,ec='purple',ls='--',lw=1.6,zorder=8))
    B.add_patch(Rectangle((xl,68.5),5,5,fill=False,ec='purple',ls='--',lw=1.6,zorder=8))
tag(B,62,86.5,'⑧ 散热孔 / 铜岛 / 凸台（紫虚线）','purple',10)
for x in (44.8,55.7):
    B.add_patch(Rectangle((x-1.5,73.8),4.5,3.0,fill=True,fc='#e6550d',alpha=0.5,ec='k',lw=0.5,zorder=9))
tag(B,40,70.2,'③a 源极脚旁过孔阵列','#a33a00',9)
plt.tight_layout(); plt.savefig('/home/user/hengliu/docs/仿真/布线演算/布线步骤图_20261028.png',dpi=95)
