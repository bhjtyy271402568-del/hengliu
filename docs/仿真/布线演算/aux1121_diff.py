"""两版辅助板 Gerber 铜对比图：灰 = 新版铜，绿 = 新增，红框 = 删掉；标注改动区和窄颈。
用法：aux1121_diff.py 旧lay.pkl 新lay.pkl 新飞针.json 输出.png"""
import pickle,json,sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif']=['WenQuanYi Zen Hei','DejaVu Sans']; plt.rcParams['axes.unicode_minus']=False
a=pickle.load(open(sys.argv[1],'rb')); b=pickle.load(open(sys.argv[2],'rb')); fp=json.load(open(sys.argv[3])); M=0.0254
c=fp['components']; comps=[dict(zip(c['fields'],r)) for r in c['rows']]
def fill(ax,g,col,al=1,edge=None):
    for q in getattr(g,'geoms',[g]):
        if q.is_empty or q.geom_type!='Polygon': continue
        x,y=q.exterior.xy
        if edge: ax.plot(x,y,color=edge,lw=1.2)
        else:
            ax.fill(x,y,color=col,alpha=al,lw=0)
            for h in q.interiors: hx,hy=h.xy; ax.fill(hx,hy,color='white',lw=0)
notes={1:[(84,46,'R12 转向、阻尼支路\n1.60 mm'),(82,10,'R13 转向\n1.60 mm'),(90,86,'R14 / C18 挪位\n1.60 mm')],
       2:[(10,22,'J1.2→D1.1 底层整片\n7.0 mm'),(76,76,'U2.8→D4 / C11\n1.98→3.20 / 0.72→2.18 mm'),(76,26,'U3.5→D5 / C14\n1.34→4.39 / 1.17→3.49 mm')]}
fig,axs=plt.subplots(1,2,figsize=(20,9.4))
for ax,k,side,ttl in ((axs[0],1,'T','顶层'),(axs[1],2,'B','底层（从顶面看）')):
    fill(ax,b[k],'#9aa5b1',0.55)
    add=b[k].difference(a[k]).buffer(-0.05).buffer(0.05); rem=a[k].difference(b[k]).buffer(-0.05).buffer(0.05)
    fill(ax,add,'#1e8449',0.95); fill(ax,rem,None,edge='#c0392b')
    for cc in comps:
        if cc['COMPONENT_NAME'].startswith('PAD') or cc['LAYER']!=side: continue
        ax.text(cc['X_COORDINATE']*M,cc['Y_COORDINATE']*M,cc['COMPONENT_NAME'],fontsize=8,ha='center',va='center',color='#1b2631',weight='bold')
    for x,y,t in notes[k]:
        ax.annotate(t,(x,y),fontsize=10,color='#145a32',ha='center',bbox=dict(boxstyle='round,pad=0.25',fc='#eafaf1',ec='#1e8449',lw=0.8))
    ax.set_xlim(0,99); ax.set_ylim(0,95); ax.set_aspect('equal'); ax.grid(alpha=.25)
    ax.set_title(f'{ttl}　灰 = R2 铜　绿 = 比 11-19 版新增　红框 = 删掉',fontsize=12)
fig.suptitle('辅助板 R2（c137d020f433）对 11-19 版（426ce3d71f55）：器件只动 R12 / R13 / R14 / C18，铜改在输入 TVS 和三处输出钳位、阻尼支路',fontsize=13)
plt.tight_layout(rect=(0,0,1,0.95)); plt.savefig(sys.argv[4],dpi=110)
