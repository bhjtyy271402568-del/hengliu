import pickle,collections,math,sys
from shapely.geometry import Point
import shapely,numpy as np
G=pickle.load(open(sys.argv[1],'rb')); CU=G['CU']
adj={1:16-1,2:16,16:2}   # L1->L2(15), L4->L3(16), L3->L4(2)
adj={1:15,2:16,16:2}
power={'PGND','GND','LT_SW','LT_VIN','DCBUS','VCC_BAT','GND_BAT','VCC_OUT','LT_SHUNT_P'}
nets_by_layer=collections.defaultdict(dict)
for (L,n),g in CU.items(): nets_by_layer[L][n]=g
res=collections.defaultdict(collections.Counter)
for t in G['tracks']:
    if t['net'] in power or t['L'] not in adj: continue
    rl=adj[t['L']]; l=math.hypot(t['x1']-t['x0'],t['y1']-t['y0']); n=max(1,int(l/0.25))
    xs=np.array([t['x0']+(k+.5)/n*(t['x1']-t['x0']) for k in range(n)]); ys=np.array([t['y0']+(k+.5)/n*(t['y1']-t['y0']) for k in range(n)])
    found=np.array(['none']*n,dtype=object)
    for net,g in nets_by_layer[rl].items():
        m=shapely.contains_xy(g,xs,ys)
        found[m]=net
    for f in found: res[(t['net'],t['L'])][f]+=l/n
LN={1:'L1',2:'L4',16:'L3'}
want=set(sys.argv[2].split(',')) if len(sys.argv)>2 else None
for (net,L),c in sorted(res.items()):
    tot=sum(c.values()); bad=tot-c['GND']
    if (want and net in want) or (not want and bad>3):
        print(net,LN[L],'总 %.1f'%tot,{k:round(v,1) for k,v in c.most_common() if v>0.2})
