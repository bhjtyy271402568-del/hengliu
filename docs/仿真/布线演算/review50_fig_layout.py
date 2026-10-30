import pickle,sys,numpy as np,matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.patches import PathPatch
from shapely.geometry import box
plt.rcParams['font.family']='WenQuanYi Zen Hei'
G=pickle.load(open(sys.argv[1],'rb')); CU=G['CU']
col={'PGND':'#4a7fc1','GND':'#9fd8c4','VCC_OUT':'#3d9e4f','LT_SW':'#9b6fd1','LT_VIN':'#e88fc8','DCBUS':'#e8a95c'}
def pp(ax,p,c,a):
    v=[];cd=[]
    for r in [p.exterior]+list(p.interiors):
        xy=np.asarray(r.coords); v+=list(xy); cd+=[Path.MOVETO]+[Path.LINETO]*(len(xy)-2)+[Path.CLOSEPOLY]
    ax.add_patch(PathPatch(Path(v,cd),fc=c,ec='none',alpha=a))
def layer(ax,L,B,a=0.75):
    for (l,n),g in CU.items():
        if l!=L or n not in col: continue
        g=g.intersection(B)
        for p in getattr(g,'geoms',[g]):
            if p.geom_type=='Polygon' and not p.is_empty: pp(ax,p,col[n],a)
def setup(ax,B,t):
    x0,y0,x1,y1=B.bounds; ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.set_title(t,fontsize=13); ax.grid(alpha=.25)
fig,axs=plt.subplots(2,3,figsize=(27,16))
# 1 L2 under FETs
ax=axs[0,0]; B=box(55,58,95,92); layer(ax,15,B)
for i in range(3):
    x0=62+10.5*i
    ax.add_patch(plt.Rectangle((x0,76.4),5,6,fill=False,ec='m',lw=2)); ax.add_patch(plt.Rectangle((x0,67),5,5.9,fill=False,ec='m',lw=2))
ax.annotate('',xy=(69.7,64),xytext=(69.7,87.5),arrowprops=dict(arrowstyle='<-',color='r',lw=3))
ax.annotate('',xy=(80.2,64),xytext=(80.2,87.5),arrowprops=dict(arrowstyle='<-',color='r',lw=3))
ax.text(56,90,'紫框 = 管子；白块 = 过孔避让连成的空洞（管子下只剩约 25% 铜）\n红箭头：高频回流被挤到列间隙（约 4.7 mm 宽）',fontsize=11,va='top')
setup(ax,B,'① L2：换流回路的回流层被过孔阵列挖空')
# 2 split crossings
ax=axs[0,1]; B=box(40,30,100,62); layer(ax,16,B,0.55)
for t in G['tracks']:
    if t['net'] in('PWM','OCP_FAULT'): ax.plot([t['x0'],t['x1']],[t['y0'],t['y1']],color='r' if t['net']=='PWM' else 'm',lw=2.5)
ax.text(42,60,'红 = PWM：底层 (50–80, 39.6) 30 mm 下面是 L3 PGND\n紫 = OCP_FAULT（过流锁存）：在 (84–88, 39–41) 跨分割约 4 mm\n建议都挪进 y 44.5–51 的 GND 走廊',fontsize=11,va='top')
setup(ax,B,'② L3 铺铜 + 两根跨地的控制线')
# 3 sharing
ax=axs[0,2]
up={'Q6':32.5,'Q5':31.0,'Q7':28.9}; lo={'Q9':35.8,'Q8':30.2,'Q10':22.1}
fu=lambda d:136; fl=lambda d:93
def share(dd,fet):
    g={k:1/(fet+v) for k,v in dd.items()}; s=sum(g.values()); return {k:v/s*100 for k,v in g.items()}
su=share(up,136); sl=share(lo,93)
xs=np.arange(3)
ax.bar(xs-0.2,[su[k] for k in ('Q6','Q5','Q7')],0.4,label='上管（左→右 Q6 Q5 Q7）',color='#e88fc8')
ax.bar(xs+0.2,[sl[k] for k in ('Q9','Q8','Q10')],0.4,label='下管（左→右 Q9 Q8 Q10）',color='#9b6fd1')
ax.axhline(33.3,color='k',ls='--'); ax.set_ylim(25,40); ax.set_xticks(xs); ax.set_xticklabels(['左列','中列','右列（靠 L8）'])
for i,k in enumerate(('Q6','Q5','Q7')): ax.text(i-0.2,su[k]+0.3,'%.1f%%'%su[k],ha='center')
for i,k in enumerate(('Q9','Q8','Q10')): ax.text(i+0.2,sl[k]+0.3,'%.1f%%'%sl[k],ha='center')
ax.legend(); ax.set_ylabel('分到的电流 %'); ax.set_title('③ 三只并联管的均流（铜阻 + 热态 RDS(on)，计算）',fontsize=13)
# 4 gate lengths
ax=axs[1,0]
ax.bar(np.arange(3)-0.2,[32.6,22.8,33.0],0.4,label='TG（L3）',color='#c06')
ax.bar(np.arange(3)+0.2,[18.5,11.5,19.4],0.4,label='BG（L1）',color='#36c')
ax.set_xticks(np.arange(3)); ax.set_xticklabels(['左列 Q6/Q9','中列 Q5/Q8','右列 Q7/Q10']); ax.set_ylabel('U9 引脚到栅极电阻 mm'); ax.legend()
ax.set_title('④ 栅极走线长度：中间短 10 mm，约 2 nH、约 0.5 ns（推断）',fontsize=13)
# 5 copper loss
ax=axs[1,1]
labs=['PGND 回流','SW','VCC_BAT','LT_VIN','L8→R56','DCBUS','GND_BAT','VCC_OUT']; vals=[0.86,0.57,0.44,0.37,0.31,0.16,0.08,0.04]
ax.barh(labs[::-1],vals[::-1],color='#e8a95c'); ax.set_xlabel('W（40 A，计算）')
for i,v in enumerate(vals[::-1]): ax.text(v+0.01,i,'%.2f'%v,va='center')
ax.set_title('⑤ 大电流铜损合计约 3.3 W，没有明显窄颈',fontsize=13)
# 6 empty pours/top area
ax=axs[1,2]; B=box(0,28,100,70); layer(ax,2,B,0.5)
ax.add_patch(plt.Rectangle((1,46),34,20,fill=False,ec='r',ls='--',lw=2.5)); ax.text(18,56,'INPUT_PGND_BOTTOM_RETURN\n填充 = 0',ha='center',color='r',fontsize=11)
ax.add_patch(plt.Rectangle((65,32.3),27,5.8,fill=False,ec='r',ls='--',lw=2.5)); ax.text(78,39,'PGND_BOTTOM_4 填充 = 0',ha='center',color='r',fontsize=11)
ax.add_patch(plt.Rectangle((55,32),32,12,fill=False,ec='m',ls=':',lw=2.5)); ax.text(71,45,'顶层这块空着',ha='center',color='m',fontsize=11)
setup(ax,B,'⑥ 底层：两块空铺铜 + 顶层空区')
plt.tight_layout(); plt.savefig(sys.argv[2],dpi=60)
