"""Gerber 上不同网络铜之间的最小间距（< 0.25 mm 全列出）。用法同 review60_gerber_nets.py。"""
import pickle,collections
from shapely.strtree import STRtree
G=pickle.load(open('geo.pkl','rb')); CU=G['CU']; LAY=pickle.load(open('lay.pkl','rb'))
LN={1:'L1',15:'L2',16:'L3',2:'L4'}
for L in (1,15,16,2):
    gp=list(getattr(LAY[L],'geoms',[LAY[L]])); tree=STRtree(gp)
    lab={}
    for (l,n),g in CU.items():
        if l!=L or not n: continue
        for p in getattr(g,'geoms',[g]):
            if p.area<0.005: continue
            q=p.representative_point()
            for j in tree.query(q):
                if gp[j].contains(q): lab.setdefault(j,set()).add(n)
    res=[]
    for i,g in enumerate(gp):
        for j in tree.query(g.buffer(0.25)):
            if j<=i: continue
            a=lab.get(i,{'?'}); b=lab.get(j,{'?'})
            if a==b and '?' not in a: continue
            d=g.distance(gp[j])
            if d<0.25: res.append((round(d,3),sorted(a),sorted(b),[round(v,1) for v in g.centroid.coords[0]]))
    res.sort()
    hist=collections.Counter(round(r[0],2) for r in res)
    print(LN[L],'pairs<0.25mm',len(res),'min',res[0][0] if res else None)
    for r in res[:12]: print('   ',r)
