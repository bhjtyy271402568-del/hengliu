import pickle,collections,math,sys
import shapely,numpy as np
G=pickle.load(open(sys.argv[1],'rb')); CU=G['CU']
adj={1:15,2:16,16:2}
power={'PGND','GND','LT_SW','LT_VIN','DCBUS','VCC_BAT','GND_BAT','VCC_OUT','LT_SHUNT_P'}
refnets=('GND','PGND')
res=collections.defaultdict(list)
for t in G['tracks']:
    if t['net'] in power or t['L'] not in adj: continue
    rl=adj[t['L']]; l=math.hypot(t['x1']-t['x0'],t['y1']-t['y0']); n=max(2,int(l/0.2))
    xs=np.linspace(t['x0'],t['x1'],n); ys=np.linspace(t['y0'],t['y1'],n)
    lab=np.array(['other']*n,dtype=object)
    for rn in refnets:
        g=CU.get((rl,rn))
        if g is not None: lab[shapely.contains_xy(g,xs,ys)]=rn
    res[t['net']].append((t['L'],list(zip(xs,ys,lab))))
for net,segs in res.items():
    ev=[]
    for L,pts in segs:
        for (x0,y0,a),(x1,y1,b) in zip(pts,pts[1:]):
            if a!=b and {a,b}=={'GND','PGND'}: ev.append(('L%d'%L,round(x0,1),round(y0,1),a+'→'+b))
    if ev: print(net,len(ev),ev[:6])
print('--- 经过短缝（<1.5 mm）从 GND 进 PGND 或反过来')
for net,segs in res.items():
    # concatenate per segment; runs
    ev=[]
    for L,pts in segs:
        runs=[]
        for x,y,a in pts:
            if runs and runs[-1][0]==a: runs[-1][2]=(x,y); runs[-1][3]+=1
            else: runs.append([a,(x,y),(x,y),1])
        for i in range(1,len(runs)-1):
            if runs[i][0]=='other' and runs[i][3]*0.2<1.5 and {runs[i-1][0],runs[i+1][0]}=={'GND','PGND'}:
                ev.append(('L%d'%L,round(runs[i][1][0],1),round(runs[i][1][1],1)))
        for i in range(1,len(runs)):
            if {runs[i-1][0],runs[i][0]}=={'GND','PGND'}: ev.append(('L%d'%L,round(runs[i][1][0],1),round(runs[i][1][1],1)))
    if ev: print(net,len(ev),ev[:8])
