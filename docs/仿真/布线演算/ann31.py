import json, matplotlib, logging; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
plt.rcParams['font.sans-serif']=['WenQuanYi Zen Hei','DejaVu Sans']
C=json.load(open('lay31.json')); D={c['r']:c for c in C}
col={'LT_VIN':'#d62728','DCBUS':'#ff9896','LT_SW':'#ff9900','PGND':'#1f77b4','GND':'#2ca02c','LT_SHUNT_P':'#9467bd','VCC_OUT':'#8c564b','VCC_BAT':'#e6550d','GND_BAT':'#636363'}
bb=dict(fc='white',ec='none',alpha=0.9)
fig,axs=plt.subplots(1,2,figsize=(24,11.5),gridspec_kw=dict(width_ratios=[1,1.35]))
def draw(ax,x0,x1,y0,y1,side=0):
    ax.add_patch(Rectangle((0,0),128,95,fill=False,ec='k',lw=1.5))
    for c in C:
        if not(x0-12<c['x']<x1+12 and y0-12<c['y']<y1+12): continue
        mine=c['b']==side; bx,by,bw,bh=c['bb']
        ax.add_patch(Rectangle((bx,by),bw,bh,fill=False,ec='k' if mine else '#dddddd',lw=0.6 if mine else 0.3,zorder=2))
        for p in c['p']:
            if not mine and not p[6]: continue
            ax.add_patch(Rectangle((p[0],p[1]),p[2],p[3],fc=col.get(p[4],'#aaaaaa'),ec='k',lw=0.2,alpha=0.8 if mine else 0.3,zorder=3))
        if mine and x0<c['x']<x1 and y0<c['y']<y1: ax.text(c['x'],c['y'],c['r'],fontsize=7,ha='center',va='center',fontweight='bold',zorder=6)
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.grid(True,lw=0.25)
A,B=axs
draw(A,14,66,52,96); A.set_title('输入区（顶层）',fontsize=14)
q1,q2=D['Q1']['bb'],D['Q2']['bb']
A.add_patch(Rectangle((q2[0],q1[1]),q1[0]+q1[2]-q2[0],q2[1]+q2[3]-q1[1],fc='red',alpha=0.35,ec='red',lw=2.5,zorder=8))
A.add_patch(Rectangle((53.879-5,84-1.6),10,9.1,fill=False,ec='green',ls='--',lw=2.2,zorder=8))
A.annotate('① Q1、Q2 本体叠了约 3 × 7.7 mm（散热片同网络，DRC 不报）\n   Q2 放回 (53.879, 84.0)（绿虚线），已核对不碰别的件',(46.5,86),(15.5,94.2),fontsize=10,color='red',bbox=bb,arrowprops=dict(arrowstyle='->',color='red'),zorder=10)
A.add_patch(Rectangle((27.7,57.0),3.7,1.9,fill=False,ec='red',lw=2.5,zorder=8))
A.add_patch(Rectangle((31.4,63.4),4.5,1.6,fill=False,ec='green',ls='--',lw=2,zorder=8))
A.annotate('② D3 压在 R1 本体下面\n   挪到绿框（约 (33.6, 64.2)，阴极靠 Q4 第 4 脚）',(29.6,57.9),(15.5,53.2),fontsize=10,color='red',bbox=bb,arrowprops=dict(arrowstyle='->',color='red'),zorder=10)
A.add_patch(Rectangle((33,74.5),25,2.4,fc='#e6550d',alpha=0.25,ec='#e6550d',ls='--',lw=1.8,zorder=4))
A.add_patch(Rectangle((32.2,81.3),26,2.4,fc='#e6550d',alpha=0.18,ec='#e6550d',ls='--',lw=1.5,zorder=4))
A.annotate('③ 电池正极（约 31 A）到 Q1/Q2 源极脚：\n   栅极脚挡在中间，上下各只有约 2.4 mm；底层被 C9–C19 占满\n   → 栅极网络（D1、C1、R6、R7、Q3、C5）下移 2–3 mm，\n      栅极脚打孔到底层（R8 已在底层），两条带都铺 VCC_BAT',(45,75.5),(15.5,62.5),fontsize=9.5,color='#a33a00',bbox=bb,arrowprops=dict(arrowstyle='->',color='#a33a00'),zorder=10)
draw(B,54,126,28,96); B.set_title('开尔文检测线（顶层，示意）',fontsize=14)
def kel(ax,pts,c,lab=None,xy=None):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; ax.plot(xs,ys,color=c,lw=2.4,ls='-',zorder=9)
for pts in [[(69.2,88.4),(64.5,80),(59,62),(66,54),(68.6,53.7)],[(72.4,88.4),(72.6,86),(70.6,80.5),(63,64),(68,56),(70.4,55.7)]]:
    kel(B,pts,'#d62728')
for pts in [[(106,40.8),(100,46),(90,52.8),(87.8,52.8)],[(106,35.1),(99,44),(90,50.8),(87.8,50.8)],[(107,40.8),(96,38.5),(94.5,38.2)],[(107,35.1),(96,37.6),(94.5,37.5)]]:
    kel(B,pts,'#6a3d9a')
B.text(56,90.5,'④ 开尔文线：从采样电阻焊盘内侧单独引出，走 L3，成对、不接任何铺铜\n   1 mm 宽 6 mm 的 2 oz 铜约 0.04 mΩ，40 A 时 1.6 mV ≈ 满量程 48 mV 的 3.4%',fontsize=10,color='#4a1486',bbox=bb,zorder=10)
B.text(56,30,'红：R42 → R43 / R44（IVINP / IVINN）约 35 mm；紫：R56 → R66 / R69（SENSE±）约 30 mm、→ U201 第 7、8 脚约 15 mm',fontsize=9.5,bbox=bb,zorder=10)
plt.tight_layout(); plt.savefig('/home/user/hengliu/docs/仿真/布线演算/全面复核_20261028.png',dpi=100)
