"""Gerber 每块铜按网络归类：同一块铜里出现两个网络 = 短路；工程里的铜在 Gerber 找不到 = 漏导出。用法：在含 geo.pkl、lay.pkl 的目录运行。"""
import pickle,collections
from shapely.strtree import STRtree
G=pickle.load(open('geo.pkl','rb')); CU=G['CU']; LAY=pickle.load(open('lay.pkl','rb'))
LN={1:'L1',15:'L2',16:'L3',2:'L4'}
for L in (1,15,16,2):
    gp=list(getattr(LAY[L],'geoms',[LAY[L]])); tree=STRtree(gp)
    nets=collections.defaultdict(set); miss=[]
    for (l,n),g in CU.items():
        if l!=L or not n: continue
        for p in getattr(g,'geoms',[g]):
            if p.area<0.01: continue
            # sample points: representative + few interior
            pts=[p.representative_point()]
            hit=set()
            for q in pts:
                for j in tree.query(q):
                    if gp[j].contains(q): hit.add(j)
            if not hit: miss.append((n,round(p.area,2),round(p.centroid.x,1),round(p.centroid.y,1)))
            for j in hit: nets[j].add(n)
    multi=[(j,sorted(s)) for j,s in nets.items() if len(s)>1]
    print(LN[L],'pieces',len(gp),'multi-net',len(multi))
    for j,s in multi: print('   SHORT?',s,[round(v,1) for v in gp[j].bounds],round(gp[j].area,1))
    big=[m for m in miss if m[1]>0.3]
    print('   geo copper not in gerber (>0.3mm2):',len(big),big[:15])
    orphan=[(round(gp[j].area,2),[round(v,1) for v in gp[j].bounds]) for j in range(len(gp)) if j not in nets and gp[j].area>0.5]
    print('   gerber pieces without net (>0.5):',len(orphan),orphan[:10])
