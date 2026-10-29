import pickle,json,collections,sys
from shapely.geometry import box,Polygon,Point,LineString
from shapely.ops import unary_union
sys.path.insert(0,'z33'); from load import load
G=pickle.load(open('z43/geo.pkl','rb'))
LN={1:'L1',15:'L2',16:'L3',2:'L4'}
B=box(0.5,0.5,127.5,94.5)
R=load('z43/p.epro2')['9a0fbfd22df79247']['recs']; M=0.0254
keep=[]
for h,r in R:
    if h['type']=='REGION' and r:
        p=r['path'][0]
        if p[0]=='CIRCLE': keep.append(Point(p[1]*M,p[2]*M).buffer(p[3]*M))
        elif p[0]=='R': x,y,w,hh=[v*M for v in p[1:5]]; keep.append(box(x,y-hh,x+w,y))
        else:
            q=[v for v in p if not isinstance(v,str)]; keep.append(Polygon([(q[i]*M,q[i+1]*M) for i in range(0,len(q),2)]))
K=unary_union([k for k in keep if k.intersects(B)])
Zg=Polygon(json.load(open('z41/zone.json')))
res={}
for L in (1,15,16,2):
    cu=[]
    for t in G['tracks']:
        if t['L']==L: cu.append(LineString([(t['x0'],t['y0']),(t['x1'],t['y1'])]).buffer(t['w']/2))
    for v in G['vias']: cu.append(Point(v['x'],v['y']).buffer(v['D']/2))
    for p in G['pads']:
        if L in p['Ls']: cu.append(p['g'])
    for p in G['pours']:
        if p['L']==L: cu.append(p['g'])
    U=unary_union(cu)
    comps=[c for c in G['C'] if (L==1 and not c['b']) or (L==2 and c['b'])]
    empty=B.difference(U.buffer(0.35)).difference(K)
    gs=sorted([g for g in getattr(empty,'geoms',[empty]) if g.area>15],key=lambda g:-g.area)
    cov=U.intersection(B).area/B.area
    print('==',LN[L],'copper coverage %.0f%%'%(cov*100),'empty>15mm2:',len(gs),'total',round(sum(g.area for g in gs)))
    for g in gs[:14]:
        c=g.representative_point(); zone='信号地区' if Zg.contains(c) else '功率区'
        print('   ',round(g.area),'mm2',[round(v,1) for v in g.bounds],zone)
    res[L]=gs
pickle.dump(res,open('z43/empty.pkl','wb'))
