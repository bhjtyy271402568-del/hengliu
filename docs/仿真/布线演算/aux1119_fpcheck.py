"""用飞针数据（焊盘中心 + 网络）+ 过孔钻孔 + Gerber 铜，查连通、短路、单孔换层。"""
import json,pickle,sys,re
from shapely.geometry import Point
from shapely.ops import unary_union
G=sys.argv[1]; lay=pickle.load(open(sys.argv[2],'rb'))
M=0.0254
fp=json.load(open(G+'/FlyingProbeTesting.json'))
F=fp['pins']['fields']; pins=[dict(zip(F,r)) for r in fp['pins']['rows']]
def drills(f):
    out=[];T={};cur=None
    for l in open(f):
        l=l.strip()
        m=re.match(r'T(\d+)C([\d.]+)',l)
        if m: T[m.group(1)]=float(m.group(2)); continue
        m=re.match(r'^T(\d+)$',l)
        if m: cur=T[m.group(1)]; continue
        m=re.match(r'X([-\d.]+)Y([-\d.]+)',l)
        if m: out.append((float(m.group(1)),float(m.group(2)),cur))
    return out
vias=drills(G+'/Drill_PTH_Through_Via.DRL'); pth=drills(G+'/Drill_PTH_Through.DRL')
pieces={k:list(lay[k].geoms) for k in (1,2)}
def hit(k,pt):
    return [i for i,q in enumerate(pieces[k]) if q.intersects(pt)]
# node graph: copper pieces; vias/pth join top & bottom pieces
par={}
def f(a):
    par.setdefault(a,a)
    while par[a]!=a: par[a]=par[par[a]]; a=par[a]
    return a
def u(a,b): par[f(a)]=f(b)
holes=vias+pth
for x,y,d in holes:
    pt=Point(x,y).buffer(d/2+0.05)
    t=hit(1,pt); b=hit(2,pt)
    for i in t+[]:
        for j in b: u((1,i),(2,j))
# pin -> pieces
pn={}
for p in pins:
    x,y=p['PIN_X']*M,p['PIN_Y']*M; pt=Point(x,y)
    ks=[1] if p['LAYER']=='T' else [2] if p['LAYER']=='B' else [1,2]
    nodes=[(k,i) for k in ks for i in hit(k,pt)]
    pn[p['PIN_NAME']]=(p['NET_NAME'],nodes)
    if len(nodes)>1:
        for n in nodes[1:]: u(nodes[0],n)
nets={}
for name,(net,nodes) in pn.items(): nets.setdefault(net,[]).append((name,nodes))
bad=[];short={}
for net,lst in nets.items():
    if not net: continue
    roots={f(ns[0]) for _,ns in lst if ns}
    miss=[nm for nm,ns in lst if not ns]
    if len(roots)>1 or miss: bad.append((net,len(roots),miss))
    for r in roots: short.setdefault(r,set()).add(net)
print('网络数',len([n for n in nets if n]),'断开',bad)
print('短路',[s for s in short.values() if len(s)>1])
pickle.dump(dict(pins=pn,vias=vias,pth=pth),open(sys.argv[3],'wb'))
