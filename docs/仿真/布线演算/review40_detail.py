import pickle,sys,matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.geometry import box,Point
plt.rcParams['font.family']='WenQuanYi Zen Hei'
L=pickle.load(open('z43/lay.pkl','rb')); g=pickle.load(open('z43/geo.pkl','rb'))
sys.path.insert(0,'z43'); from drl import holes
H=holes('z43/g/Drill_PTH_Through_Via.DRL')
def draw(ax,geom,c,a=1):
    for p in getattr(geom,'geoms',[geom]):
        if p.is_empty or p.geom_type!='Polygon': continue
        x,y=p.exterior.xy; ax.fill(x,y,color=c,lw=0,alpha=a)
        for i in p.interiors: x,y=i.xy; ax.fill(x,y,color='white',lw=0)
fig,axs=plt.subplots(2,2,figsize=(18,14))
# 1 mask over boss
ax=axs[0,0]; bb=box(60,66,92,87)
draw(ax,L['bot'].intersection(bb),'#9db7e6')
draw(ax,L['bsm'].intersection(bb),'#f2c200')
draw(ax,L['bso'].intersection(bb),'#000000')
for i in range(3):
    x0=62.0+10.5*i
    for y0,y1 in ((77.9,83.1),(68.5,73.5)):
        ax.plot([x0,x0+5,x0+5,x0,x0],[y0,y0,y1,y1,y0],'r-',lw=2.5)
ax.set_xlim(60,92); ax.set_ylim(66,87); ax.set_aspect('equal')
ax.set_title('① 底层（从上往下看，y 向上）：红框 = 散热器凸台\n蓝 = 铜，黄 = 阻焊开窗（只在过孔周围），黑 = 丝印\n凸台压在阻焊上：建议整块开窗')
# 2 boss edge vs bottom caps
ax=axs[0,1]; bb=box(70,80,92,89)
draw(ax,L['bot'].intersection(bb),'#9db7e6')
for i in range(3):
    x0=62.0+10.5*i
    ax.add_patch(plt.Rectangle((x0,77.9),5,5.2,fc='#ff9999',ec='r',lw=2,alpha=.6))
for c in g['C']:
    if c['b'] and c['r'] in('C65','C67','C68','C74','C110','C73','C66'):
        b=c['bb']; ax.add_patch(plt.Rectangle((b[0],b[1]),b[2],b[3],fc='#66bb66',ec='g',alpha=.8)); ax.text(c['x'],c['y']+0.2,c['r'],ha='center',fontsize=11)
for x in (74.4,77.6,84.0,87.1):
    ax.annotate('',xy=(x,83.1),xytext=(x,83.56),arrowprops=dict(arrowstyle='<->',color='k'))
ax.text(80.5,82.2,'只有 0.46–0.50 mm',ha='center',fontsize=13,color='k')
ax.set_xlim(70,92); ax.set_ylim(80,89); ax.set_aspect('equal')
ax.set_title('② 上管凸台（红，建议位置 y 77.9–83.1）和底层 1210 电容（绿）\n凸台上沿改 ≤ 82.6，或电容上移 0.5 mm')
# 3 mounting hole 93,3.5
ax=axs[1,0]
from shapely.affinity import translate
x,y=93,3.5; bb=box(x-5,y-4,x+5,y+5)
draw(ax,L['top'].intersection(bb),'#c87533',0.55)
draw(ax,L['bot'].intersection(bb),'#3366cc',0.45)
ax.add_patch(plt.Circle((x,y),1.6,fc='white',ec='k',lw=2))
ax.add_patch(plt.Circle((x,y),2.75,fill=False,ec='k',ls=':',lw=2)); ax.text(x,y+3.0,'M3 铜柱 / 螺钉头约 Ø5.5',ha='center',fontsize=12)
ax.add_patch(plt.Circle((x,y),3.25,fill=False,ec='r',ls='--',lw=2)); ax.text(x+3.4,y-3.5,'建议禁铜 Ø6.5',color='r',fontsize=12)
ax.text(x-4.6,y+4.3,'顶层 PGND（橙）\n底层 VCC_OUT（蓝）',fontsize=12,va='top')
ax.set_xlim(x-5,x+5); ax.set_ylim(y-4,y+5); ax.set_aspect('equal')
ax.set_title('③ 角孔 (93, 3.5)：铜皮离孔边约 0.3 mm\n尼龙柱没事；换成金属柱 = 输出正负被短接')
# 4 thermal stack
ax=axs[1,1]
items=['结到壳\n(手册)','过孔 56 只\n0.25 mm','阻焊\n(现状)','导热垫\nGR80B']
now=[0.9,5.2,3.19-2.23,2.23]; opt=[0.9,5.2,0,2.23]
import numpy as np
cols=['#888888','#3366cc','#f2c200','#66bb66']
for k,(lab,vals) in enumerate((('现在（阻焊开窗 41%）',now),('凸台区整块开窗',opt))):
    left=0
    for i,v in enumerate(vals):
        ax.barh(k,v,left=left,color=cols[i],ec='k')
        if v>0.3: ax.text(left+v/2,k,f'{v:.1f}',ha='center',va='center',fontsize=12)
        left+=v
    ax.text(left+0.1,k,f'{left:.1f} K/W',va='center',fontsize=13)
ax.set_yticks([0,1]); ax.set_yticklabels(['现在（阻焊开窗 41%）','凸台区整块开窗'],fontsize=12)
ax.set_xlim(0,13); ax.set_xlabel('上管 结 → 散热器 热阻 K/W（计算 / 推断，阻焊按 15 µm、0.25 W/m·K）')
for i,l in enumerate(items): ax.bar(0,0,color=cols[i],label=l.replace('\n',' '))
ax.legend(loc='lower right',fontsize=11)
ax.set_title('④ 上管热路串联：阻焊这一段约 1 K/W（10–25 µm 时 0.6–4.8）\n5 W 时结温约低 5 °C（3–24 °C）')
plt.tight_layout(); plt.savefig('/home/user/hengliu/docs/仿真/布线演算/细查补充_20261029.png',dpi=70)
