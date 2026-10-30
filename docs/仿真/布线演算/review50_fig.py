"""10-30 版（c5791fa86ffe）问题标注图，坐标 y 向上（和嘉立创一致）。"""
import pickle,sys,math,numpy as np,matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from shapely.geometry import box,Point,Polygon
plt.rcParams['font.family']='WenQuanYi Zen Hei'
G=pickle.load(open(sys.argv[1],'rb')); CU=G['CU']; CUR=pickle.load(open(sys.argv[2],'rb'))
col={'PGND':'#4a7fc1','GND':'#9fd8c4','VCC_OUT':'#3d9e4f','LT_SW':'#9b6fd1','LT_VIN':'#e88fc8','DCBUS':'#e8a95c','VCC_BAT':'#e05a5a','GND_BAT':'#bbbbbb','LT_SHUNT_P':'#8c4a3a','$1N562':'#ff8800'}
def pp(ax,p,c,a):
    v=[];cd=[]
    for r in [p.exterior]+list(p.interiors):
        xy=np.asarray(r.coords); v+=list(xy); cd+=[Path.MOVETO]+[Path.LINETO]*(len(xy)-2)+[Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(v,cd),fc=c,ec='none',alpha=a))
def layer(ax,L,B,nets=None,alpha=0.75,tracks=True,labels=True):
    for (l,n),g in CU.items():
        if l!=L or (nets and n not in nets): continue
        g=g.intersection(B)
        for p in getattr(g,'geoms',[g]):
            if p.geom_type=='Polygon' and not p.is_empty: pp(ax,p,col.get(n,'#555555'),alpha if n in col else 0.9)
    if labels:
        for c in G['C']:
            if (L==1 and not c['b']) or (L==2 and c['b']):
                b=c['bb']
                if box(b[0],b[1],b[0]+b[2],b[1]+b[3]).intersects(B):
                    ax.add_patch(plt.Rectangle((b[0],b[1]),b[2],b[3],fill=False,ec='k',lw=0.6)); ax.text(b[0]+b[2]/2,b[1]+b[3]/2,c['r'],fontsize=8,ha='center',va='center',clip_on=True)
def setup(ax,B,t):
    x0,y0,x1,y1=B.bounds; ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.set_title(t,fontsize=13); ax.grid(alpha=.25)
fig,axs=plt.subplots(2,3,figsize=(27,17))
# 1 CN14 底面贴片
ax=axs[0,0]; B=box(100,0,128,40); layer(ax,2,B)
for n,cx in (('VCC_OUT',110.85),('PGND',121.35)):
    ax.add_patch(plt.Circle((cx,28.4),3.81,fc='none',ec='r',lw=2)); ax.text(cx,28.4,'CN14\n'+n,ha='center',va='center',fontsize=10,color='r')
for r in ('C85','C105'):
    p=[p for p in G['pads'] if p['r']==r and p['n']=='1'][0]; x,y=p['g'].exterior.xy; ax.plot(x,y,'r-',lw=2)
ax.annotate('C85 地焊盘离插件焊盘 0.56 mm\nC105 地焊盘 0.69 mm\nC85 正极焊盘压在插件焊盘上',xy=(114.7,25.0),xytext=(101,36),fontsize=11,arrowprops=dict(arrowstyle='->',color='r'),color='r')
ax.text(103,4,'C97：Ø10 × 16.5 电解装在底面',fontsize=11,color='r')
setup(ax,B,'① 底层（透视）：CN14 插件焊点旁的贴片件')
# 2 PWM 走在 L3 PGND 上
ax=axs[0,1]; B=box(35,30,95,55); layer(ax,16,B,labels=False,alpha=0.6)
for t in G['tracks']:
    if t['net']=='PWM': ax.plot([t['x0'],t['x1']],[t['y0'],t['y1']],color='r' if t['L']==2 else 'm',lw=2.5)
ax.annotate('PWM（底层，y 39.6）\n下面 30 mm 是 L3 PGND',xy=(65,39.6),xytext=(50,47),fontsize=12,color='r',arrowprops=dict(arrowstyle='->',color='r'))
setup(ax,B,'② L3 铺铜 + PWM 走线（红 = 底层段）')
# 3 输入电流 ADC 线贴着 LM5164 SW
ax=axs[0,2]; B=box(28,14,50,36); layer(ax,1,B)
for t in G['tracks']:
    if t['L']==1 and t['net']=='SHURUDIANLIUJIANCE': ax.plot([t['x0'],t['x1']],[t['y0'],t['y1']],'r-',lw=2.5)
ax.annotate('输入电流 ADC 线\n离 LM5164 开关节点 0.2 mm，约 8 mm\n（说明里说已绕开，实际没动）',xy=(42,30.4),xytext=(29,20),fontsize=11,color='r',arrowprops=dict(arrowstyle='->',color='r'))
setup(ax,B,'③ 顶层：输入电流 ADC 线（红）和 LM5164 SW（橙）')
# 4 空铺铜
ax=axs[1,0]; B=box(0,28,100,70); layer(ax,2,B,labels=False,alpha=0.5)
M=0.0254
def outline(path):
    pts=[];t=path[0];i=0
    while i<len(t):
        v=t[i]
        if isinstance(v,str): i+=2 if v=='ARC' else 1; continue
        pts.append((t[i]*M,t[i+1]*M)); i+=2
    return Polygon(pts)
for h,r in G['R']:
    if h['type']=='POUR' and r and r['name'] in ('INPUT_PGND_BOTTOM_RETURN','PGND_BOTTOM_4'):
        x,y=outline(r['path']).exterior.xy; ax.plot(x,y,'r--',lw=2.5); ax.text(np.mean(x),np.mean(y),r['name']+'\n填充 = 0',ha='center',fontsize=11,color='r')
ax.add_patch(plt.Rectangle((55,32),32,12,fill=False,ec='m',lw=2.5,ls=':')); ax.text(71,45,'顶层这块原来是 PGND，现在空着（约 300 mm²）',ha='center',fontsize=11,color='m')
setup(ax,B,'④ 底层：两块铺铜轮廓填充为 0（红虚线）')
# 5 电流密度（顶层，各通路取最大）
ax=axs[1,1]; X,Y=CUR['X'],CUR['Y']; J=np.zeros(X.shape)
for label,Js,P in CUR['res']:
    if 1 in Js: J=np.maximum(J,Js[1])
im=ax.pcolormesh(X,Y,np.ma.masked_less(J,0.3),cmap='inferno_r',vmin=0,vmax=10,shading='auto'); plt.colorbar(im,ax=ax,label='A/mm（40 A）',shrink=0.7)
for (x,y,t) in ((70.4,88.1,'LT_VIN 出 R42：12.8'),(111.1,44.9,'L8→R56 只走顶层：12.1'),(60.1,88.4,'DCBUS：9.1'),(86.6,74.1,'SW：7.4')):
    ax.plot(x,y,'co',ms=8); ax.text(x+1,y+1.2,t,fontsize=10,color='c',fontweight='bold')
setup(ax,box(20,30,128,95),'⑤ 顶层电流密度（40 A，各通路叠加取最大）')
# 6 上次未改
ax=axs[1,2]; B=box(55,60,100,95); layer(ax,2,B,labels=True,alpha=0.5)
for i in range(3):
    x0=62.0+10.5*i
    for y0,y1 in ((77.9,83.1),(68.5,73.5)): ax.add_patch(plt.Rectangle((x0,y0),5,y1-y0,fc='#ff9999',ec='r',lw=2,alpha=.5))
ax.text(56,92,'凸台区仍盖阻焊（未开窗）\nC65 / C67 / C68 / C74 离上管凸台 0.46–0.50 mm（未改）\n角孔禁铜、C9 / C16 / C17 补孔（未改）',fontsize=11,color='r',va='top')
setup(ax,B,'⑥ 上次（25.5 节）提的，这版都没改')
plt.tight_layout(); plt.savefig(sys.argv[3],dpi=60)
