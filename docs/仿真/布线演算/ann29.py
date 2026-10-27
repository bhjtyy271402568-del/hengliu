import json, matplotlib, logging; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Polygon
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
plt.rcParams['font.sans-serif']=['WenQuanYi Zen Hei','DejaVu Sans']
C=json.load(open('lay29.json')); D={c['r']:c for c in C}
col={'LT_VIN':'#d62728','DCBUS':'#ff9896','LT_SW':'#ff9900','PGND':'#1f77b4','GND':'#2ca02c','LT_SHUNT_P':'#9467bd','VCC_OUT':'#8c564b','LT_TG':'#e377c2','LT_BG':'#17becf'}
x0,x1,y0,y1=52,112,56,95
fig,axs=plt.subplots(1,2,figsize=(24,8.6))
bb=dict(fc='white',ec='none',alpha=0.88)
for side,ax in enumerate(axs):
    ax.add_patch(Rectangle((0,0),128,95,fill=False,ec='k',lw=1.5))
    for h in [[64,52.5],[100,88]]: ax.add_patch(Circle(h,1.6,fc='w',ec='k'))
    for c in C:
        if not(x0-12<c['x']<x1+12 and y0-12<c['y']<y1+12): continue
        mine=(c['b']==side); bx,by,bw,bh=c['bb']
        ax.add_patch(Rectangle((bx,by),bw,bh,fill=False,ec='k' if mine else '#dddddd',lw=0.6 if mine else 0.3,zorder=2))
        for p in c['p']:
            x,y,w,h,net,num,th,ly=p
            if not mine and not th: continue
            ax.add_patch(Rectangle((x,y),w,h,fc=col.get(net,'#999999'),ec='k',lw=0.2,alpha=0.8 if mine else 0.3,zorder=3))
        if mine and x0<c['x']<x1 and y0<c['y']<y1: ax.text(c['x'],c['y'],c['r'],fontsize=6.5,ha='center',va='center',zorder=6,fontweight='bold')
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.grid(True,lw=0.25)
A,B=axs
A.set_title('顶层',fontsize=14); B.set_title('底层（从上透视）',fontsize=14)
# overlaps top
for r,q in [('C113','Q6'),('C71','Q6'),('C75','Q5'),('C76','Q7'),('C77','Q7'),('C111','Q7')]:
    c=D[r]; p=[p for p in c['p'] if p[4]=='LT_VIN'][0]
    A.add_patch(Rectangle((p[0]-0.2,p[1]-0.2),p[2]+0.4,p[3]+0.4,fill=False,ec='red',lw=2.5,zorder=9))
A.annotate('① 必须改：6 只电容的 VIN 焊盘压在上管漏极脚上（重叠约 1.1 mm，同网络，DRC 不报）\n   电容排上移约 1.4 mm（焊盘下沿 ≥ 83.1）；C113 再避开 R42',(66.3,82.6),(53,93.3),fontsize=10,color='red',bbox=bb,arrowprops=dict(arrowstyle='->',color='red'),zorder=10)
A.add_patch(Polygon([(62.3,69.7),(97,69.7),(97,76.2),(89.9,76.2),(89.9,73.1),(62.3,73.1)],fc='orange',alpha=0.25,ec='darkorange',ls='--',lw=1.8,zorder=4))
A.text(90.5,62.5,'顶层 SW 通道已打开：\n下管漏极之间约 3.3 mm\n（R59/R57/R61 横放到下面）',fontsize=9.5,color='#c05000',bbox=bb,zorder=10)
for i in range(3):
    xl=62.0+10.5*i
    A.add_patch(Rectangle((xl,77.9),5.0,5.2,fill=False,ec='purple',ls='--',lw=1.5,zorder=7))
    A.add_patch(Rectangle((xl,68.5),5.0,5.0,fill=False,ec='purple',ls='--',lw=1.5,zorder=7))
A.text(53,57,'紫虚线 = 按这一版位置的凸台（上管 y 77.9–83.1，下管 y 68.5–73.5）',fontsize=9,color='purple',bbox=bb)
# bottom
for r in ['C107','C108','C67','C110','C73']:
    c=D[r]; bx,by,bw,bh=c['bb']
    B.add_patch(Rectangle((bx-0.15,by-0.15),bw+0.3,bh+0.3,fill=False,ec='red',lw=2.2,zorder=9))
B.annotate('② 必须改：C107 压在 C67、C110 上，C108 压在 C73 上\n   底层电容排上移约 0.6 mm 即可',(80.3,82.5),(53,93.3),fontsize=10,color='red',bbox=bb,arrowprops=dict(arrowstyle='->',color='red'),zorder=10)
B.add_patch(Polygon([(62.3,67.9),(97,67.9),(97,71.7),(109.4,71.7),(109.4,76.2),(97,76.2),(97,77.5),(62.3,77.5)],fc='orange',alpha=0.22,ec='darkorange',ls='--',lw=1.8,zorder=4))
B.text(66,74.6,'底层 SW 带约 9.6 mm（y 67.9–77.5）已让出',fontsize=9.5,color='#c05000',bbox=bb,zorder=10)
for r in ['R71','C94']:
    c=D[r]; bx,by,bw,bh=c['bb']; B.add_patch(Rectangle((bx-0.15,by-0.15),bw+0.3,bh+0.3,fill=False,ec='#b36b00',lw=2,zorder=9))
B.add_patch(Rectangle((89,61),7,6.4,fill=True,fc='#2ca02c',alpha=0.18,ec='green',ls='--',lw=1.5,zorder=5))
B.annotate('③ 建议：R71/C94 离 Q10 约 11–13 mm，\n   且占了 L8 下的 PGND 回流通道；\n   挪到绿框（Q10 右下，SW 带下方）',(102,63.5),(97,57.2),fontsize=9.5,color='#2e7d32',bbox=bb,arrowprops=dict(arrowstyle='->',color='#2e7d32'),zorder=10)
B.annotate('R67（NTC）已回到板上：Q8 源极正下方',(75,67),(53,60),fontsize=9.5,color='#1f4f8f',bbox=bb,arrowprops=dict(arrowstyle='->',color='#1f4f8f'),zorder=10)
plt.tight_layout(); plt.savefig('/home/user/hengliu/docs/仿真/布线演算/功率级核对_20261028.png',dpi=105)
