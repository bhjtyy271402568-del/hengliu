import pickle,json,sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
L=pickle.load(open(sys.argv[1],'rb')); fp=json.load(open(sys.argv[2])); M=0.0254
c=fp['components']; comps=[dict(zip(c['fields'],r)) for r in c['rows']]
F=fp['pins']['fields']; pins=[dict(zip(F,r)) for r in fp['pins']['rows']]
def draw(ax,g,col,a=1):
    for q in getattr(g,'geoms',[g]):
        if q.is_empty: continue
        xs,ys=q.exterior.xy; ax.fill(xs,ys,color=col,alpha=a,lw=0)
        for h in q.interiors: x,y=h.xy; ax.fill(x,y,color='white',lw=0)
x0,y0,x1,y1=[float(v) for v in sys.argv[4:8]] if len(sys.argv)>7 else (0,0,99,95)
fig,axs=plt.subplots(1,2,figsize=(22,8))
for ax,k,col,side in ((axs[0],1,'#c0392b','T'),(axs[1],2,'#2471a3','B')):
    draw(ax,L[k],col,0.55)
    for p in pins:
        if p['NET_NAME'] in ('AUX_IN','BAT_GND','AUX_GND','P15_RAW','N15_RAW','GALVO_P15','GALVO_N15','CARD_P15','BAT_PROT') and (p['LAYER']==side or p['HOLE_SIZE']):
            ax.text(p['PIN_X']*M,p['PIN_Y']*M,p['NET_NAME'].replace('GALVO_','G').replace('_RAW','r'),fontsize=6,color="k",clip_on=True)
    for cc in comps:
        if cc['COMPONENT_NAME'].startswith('PAD'): continue
        if cc['LAYER']==side: ax.text(cc['X_COORDINATE']*M,cc['Y_COORDINATE']*M,cc['COMPONENT_NAME'],fontsize=10,color="k",weight="bold",ha="center",clip_on=True)
    ax.set_xlim(x0,x1); ax.set_ylim(y0,y1); ax.set_aspect('equal'); ax.grid(alpha=.3); ax.set_title({1:'Top',2:'Bottom (seen from top)'}[k])
plt.tight_layout(); plt.savefig(sys.argv[3],dpi=110)
