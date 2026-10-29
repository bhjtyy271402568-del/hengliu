import pickle,collections,math
from shapely.geometry import Point,LineString
G=pickle.load(open('z43/geo.pkl','rb'))
LN={1:'L1',15:'L2',16:'L3',2:'L4'}
power={'PGND','GND','LT_SW','LT_VIN','DCBUS','VCC_BAT','GND_BAT','VCC_OUT','LT_SHUNT_P'}
pads=collections.defaultdict(list)
for p in G['pads']:
    c=p['g'].centroid; pads[p['net']].append((c.x,c.y,p['r']+'.'+p['n']))
def mst(pts):
    if len(pts)<2: return 0
    n=len(pts); inT=[False]*n; d=[1e9]*n; d[0]=0; tot=0
    for _ in range(n):
        u=min((i for i in range(n) if not inT[i]),key=lambda i:d[i]); inT[u]=True; tot+=d[u]
        for v in range(n):
            if not inT[v]:
                w=math.hypot(pts[u][0]-pts[v][0],pts[u][1]-pts[v][1])
                if w<d[v]: d[v]=w
    return tot
rows=[]
segs=collections.defaultdict(list)
for t in G['tracks']: segs[t['net']].append(t)
nv=collections.Counter(v['net'] for v in G['vias'])
for net,ts in segs.items():
    if net in power or not net: continue
    L=sum(math.hypot(t['x1']-t['x0'],t['y1']-t['y0']) for t in ts)
    m=mst(pads[net])
    rows.append((net,round(L,1),round(m,1),round(L/m,2) if m>0.5 else None,nv[net],len(pads[net]),sorted({LN[t['L']] for t in ts})))
print('net, routed mm, MST mm, ratio, vias, pads, layers')
for r in sorted(rows,key=lambda r:-(r[1]-r[2])): 
    if r[1]-r[2]>15 or (r[3] and r[3]>2.2 and r[1]>8): print(r)
# geometry quality: tiny segments, acute angles, non-45
tiny=0; acute=[]; non45=collections.Counter()
by=collections.defaultdict(list)
for t in G['tracks']: by[(t['net'],t['L'])].append(t)
for (net,L),ts in by.items():
    ends=collections.defaultdict(list)
    for t in ts:
        l=math.hypot(t['x1']-t['x0'],t['y1']-t['y0'])
        if l<0.1: tiny+=1
        a=math.degrees(math.atan2(t['y1']-t['y0'],t['x1']-t['x0']))%45
        if l>0.3 and min(a,45-a)>2: non45[net]+=1
        ends[(round(t['x0'],2),round(t['y0'],2))].append((t['x1'],t['y1'])); ends[(round(t['x1'],2),round(t['y1'],2))].append((t['x0'],t['y0']))
    for p,lst in ends.items():
        if len(lst)==2:
            v1=(lst[0][0]-p[0],lst[0][1]-p[1]); v2=(lst[1][0]-p[0],lst[1][1]-p[1])
            n1=math.hypot(*v1); n2=math.hypot(*v2)
            if n1>0.05 and n2>0.05:
                ang=math.degrees(math.acos(max(-1,min(1,(v1[0]*v2[0]+v1[1]*v2[1])/(n1*n2)))))
                if ang<89: acute.append((net,LN[L],p,round(ang)))
print('tiny segments (<0.1mm):',tiny)
print('acute corners (<90°):',len(acute)); [print('  ',a) for a in acute[:25]]
print('non-45° segments by net:',non45.most_common(15))
