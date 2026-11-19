"""两点之间沿某网络铜的最窄颈：二分收缩量 r，A、B 仍连通的最大 r，颈宽≈2r。用法：neck2.py G lay.pkl 网络:引脚A,引脚B ..."""
import pickle,json,re,sys
from shapely.geometry import Point
G,L=sys.argv[1],pickle.load(open(sys.argv[2],'rb')); M=0.0254
fp=json.load(open(G+'/FlyingProbeTesting.json')); F=fp['pins']['fields']; pins=[dict(zip(F,r)) for r in fp['pins']['rows']]
def drills(f):
    T={};cur=None;out=[]
    for ln in open(f):
        m=re.match(r'T(\d+)C([\d.]+)',ln)
        if m: T[m.group(1)]=float(m.group(2)); continue
        m=re.match(r'^T(\d+)$',ln.strip())
        if m: cur=T.get(m.group(1)); continue
        m=re.match(r'X(-?[\d.]+)Y(-?[\d.]+)',ln)
        if m and cur: out.append((float(m.group(1)),float(m.group(2)),cur))
    return out
holes=drills(G+'/Drill_PTH_Through_Via.DRL')+drills(G+'/Drill_PTH_Through.DRL')
byname={}
for p in pins: byname.setdefault(p['PIN_NAME'],p)
def netpieces(net):
    pts=[Point(p['PIN_X']*M,p['PIN_Y']*M) for p in pins if p['NET_NAME']==net]
    out={}
    for k in (1,2):
        out[k]=[q for q in L[k].geoms if any(q.intersects(pt) for pt in pts)]
    return out
def conn(cu,a,b,r):
    isl=[(k,g) for k in (1,2) for q in cu[k] for g in getattr(q.buffer(-r),'geoms',[q.buffer(-r)]) if not g.is_empty]
    par=list(range(len(isl)))
    def f(i):
        while par[i]!=i: par[i]=par[par[i]]; i=par[i]
        return i
    for x,y,d in holes:
        c=Point(x,y).buffer(d/2+r+0.02)
        h=[i for i,(k,g) in enumerate(isl) if g.intersects(c)]
        for j in h[1:]: par[f(j)]=f(h[0])
    def nodes(p):
        pt=Point(p['PIN_X']*M,p['PIN_Y']*M).buffer(r+0.25)
        ks=(1,2) if p['HOLE_SIZE'] else ((1,) if p['LAYER']=='T' else (2,))
        return {f(i) for i,(k,g) in enumerate(isl) if k in ks and g.intersects(pt)}
    return bool(nodes(byname[a]) & nodes(byname[b]))
for arg in sys.argv[3:]:
    net,ab=arg.split(':'); a,b=ab.split(',')
    cu=netpieces(net); lo,hi=0.0,4.0
    if not conn(cu,a,b,0.01): print(arg,'不连通(0.01)'); continue
    for _ in range(14):
        mid=(lo+hi)/2
        if conn(cu,a,b,mid): lo=mid
        else: hi=mid
    print(f'{arg:32} 最窄约 {2*lo:5.2f} mm')
