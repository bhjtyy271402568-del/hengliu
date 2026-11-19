import pickle,json,re,sys,collections
from shapely.geometry import Point
G,L=sys.argv[1],pickle.load(open(sys.argv[2],'rb')); M=0.0254
fp=json.load(open(G+'/FlyingProbeTesting.json')); F=fp['pins']['fields']; pins=[dict(zip(F,r)) for r in fp['pins']['rows']]
def drills(f,kind):
    T={};cur=None;out=[]
    for ln in open(f):
        m=re.match(r'T(\d+)C([\d.]+)',ln)
        if m: T[m.group(1)]=float(m.group(2)); continue
        m=re.match(r'^T(\d+)$',ln.strip())
        if m: cur=T.get(m.group(1)); continue
        m=re.match(r'X(-?[\d.]+)Y(-?[\d.]+)',ln)
        if m and cur: out.append((float(m.group(1)),float(m.group(2)),cur,kind))
    return out
holes=drills(G+'/Drill_PTH_Through_Via.DRL','via')+drills(G+'/Drill_PTH_Through.DRL','pth')
for net in sys.argv[3:]:
    pts=[(p['PIN_NAME'],Point(p['PIN_X']*M,p['PIN_Y']*M),p['LAYER'],p['HOLE_SIZE']) for p in pins if p['NET_NAME']==net and not p['PIN_NAME'].startswith('PAD')]
    pcs={k:[(i,q) for i,q in enumerate(L[k].geoms) if any(q.intersects(pt) for _,pt,_,_ in pts)] for k in (1,2)}
    # also pieces touched by via of this net region
    links=collections.Counter(); vias=collections.defaultdict(list)
    for x,y,d,kind in holes:
        c=Point(x,y)
        t=[i for i,q in enumerate(L[1].geoms) if q.contains(c)]; b=[i for i,q in enumerate(L[2].geoms) if q.contains(c)]
        for i in t:
            for j in b:
                if any(i==ii for ii,_ in pcs[1]) or any(j==jj for jj,_ in pcs[2]):
                    links[(i,j)]+=1; vias[(i,j)].append((round(x,1),round(y,1),kind,d))
    print('==',net)
    for k in (1,2):
        for i,q in pcs[k]:
            on=[n for n,pt,l,h in pts if q.intersects(pt) and (h or l==('T' if k==1 else 'B'))]
            print(' L%d 块%d 面积%.0f 含引脚'%(k,i,q.area),on)
    for (i,j),n in links.items():
        print(' 顶块%d-底块%d 过孔/通孔数 %d'%(i,j,n), vias[(i,j)][:8])
