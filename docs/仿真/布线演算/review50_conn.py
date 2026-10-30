import pickle,collections,sys
from shapely.geometry import Point
G=pickle.load(open(sys.argv[1],'rb')); CU=G['CU']
LN={1:'L1',15:'L2',16:'L3',2:'L4'}
skipL=set(int(x) for x in sys.argv[2].split(',')) if len(sys.argv)>2 else set()
nets=collections.defaultdict(list)
for (L,n),g in CU.items():
    if L in skipL: continue
    for i,p in enumerate(getattr(g,'geoms',[g])): nets[n].append((L,p))
bad={}
WANT={"PGND","VCC_OUT"}
for n,pieces in nets.items():
    if not n: continue
    par=list(range(len(pieces)))
    def f(i):
        while par[i]!=i: par[i]=par[par[i]]; i=par[i]
        return i
    vias=[v for v in G['vias'] if v['net']==n]+[dict(x=p['g'].centroid.x,y=p['g'].centroid.y) for p in G['pads'] if p['net']==n and p['hole']]
    for v in vias:
        pt=Point(v['x'],v['y']); hit=[i for i,(L,p) in enumerate(pieces) if p.distance(pt)<0.05]
        for i in hit[1:]: par[f(i)]=f(hit[0])
    groups=collections.defaultdict(list)
    pads=[p for p in G['pads'] if p['net']==n]
    for p in pads:
        c=p['g'].representative_point(); Ls=p['Ls']
        hit=[i for i,(L,q) in enumerate(pieces) if L in Ls and q.distance(c)<0.01]
        groups[f(hit[0]) if hit else -1].append(p['r']+'.'+p['n'])
    if len(groups)>1: bad[n]=dict(groups)
    # isolated pieces (no pad) area
    padroots={k for k in groups}
    iso=[(LN[L],round(p.area,1),round(p.centroid.x,1),round(p.centroid.y,1)) for i,(L,p) in enumerate(pieces) if f(i) not in padroots and p.area>0.5]
    if iso: print('ISOLATED copper (no pad)',n,iso[:8])
for n,gr in bad.items(): print('SPLIT NET',n,({k:v for k,v in gr.items()} if n in WANT else {k:v[:6] for k,v in gr.items()}))
print('done, nets',len(nets))
