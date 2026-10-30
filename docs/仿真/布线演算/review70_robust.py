"""收缩连通测试：Gerber 每层铜向内收 e，窄于 2e 的颈部断开；再按过孔 / 插件孔连层，查每个网络的焊盘是否仍连通。"""
import pickle,sys,collections
from shapely.geometry import Point
from shapely.strtree import STRtree
G=pickle.load(open(sys.argv[1],'rb')); LAY=pickle.load(open(sys.argv[2],'rb')); e=float(sys.argv[3])
nodes=[]  # (L, geom)
idx={}
for L in (1,15,16,2):
    g=LAY[L].buffer(-e,8)
    P=[p for p in getattr(g,'geoms',[g]) if not p.is_empty]
    idx[L]=(len(nodes),STRtree(P),P)
    nodes+= [(L,p) for p in P]
par=list(range(len(nodes)))
def f(i):
    while par[i]!=i: par[i]=par[par[i]]; i=par[i]
    return i
def find(L,pt,tol=0.0):
    off,tr,P=idx[L]
    return [off+j for j in tr.query(pt.buffer(tol+1e-6)) if P[j].distance(pt)<=tol+1e-6]
# vias and THT holes connect layers (barrel): use centre point with tolerance = pad radius - e
for v in G['vias']:
    pt=Point(v['x'],v['y']); hits=[]
    for L in (1,15,16,2): hits+=find(L,pt,max(0,v['D']/2-e-0.01))
    for h in hits[1:]: par[f(h)]=f(hits[0])
for p in G['pads']:
    if p['hole']:
        pt=p['g'].centroid; hits=[]
        for L in (1,15,16,2): hits+=find(L,pt,0.3)
        for h in hits[1:]: par[f(h)]=f(hits[0])
bad=collections.defaultdict(lambda: collections.defaultdict(list))
for p in G['pads']:
    if not p['net']: continue
    pt=p['g'].representative_point(); r=[]
    for L in p['Ls']: r+=find(L,pt,0.05)
    root=f(r[0]) if r else ('none',p['r'],p['n'])
    bad[p['net']][root].append(p['r']+'.'+p['n'])
n=0
for net,gr in bad.items():
    if len(gr)>1:
        n+=1; small=sorted(gr.values(),key=len)
        print(net,'分成',len(gr),'组；小组：',small[:-1])
print('e=%.3f mm（颈部 < %.2f mm 视为断开）：断开网络 %d 个'%(e,2*e,n))
