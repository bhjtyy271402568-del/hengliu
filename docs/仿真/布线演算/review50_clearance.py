import pickle,collections,math,sys
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely.strtree import STRtree
G=pickle.load(open(sys.argv[1],'rb'))
LN={1:'L1',15:'L2',16:'L3',2:'L4'}
# objects per layer (not pours) with net
objs=collections.defaultdict(list)
for t in G['tracks']: objs[t['L']].append(('T',t['net'],LineString([(t['x0'],t['y0']),(t['x1'],t['y1'])]).buffer(t['w']/2,8)))
for p in G['pads']:
    for L in p['Ls']: objs[L].append(('P:'+p['r']+'.'+p['n'],p['net'],p['g']))
for v in G['vias']:
    for L in (1,2): objs[L].append(('V',v['net'],Point(v['x'],v['y']).buffer(v['D']/2,12)))
    for L in (15,16): objs[L].append(('Vd',v['net'],Point(v['x'],v['y']).buffer(v['d']/2,12)))  # drill only on inner
pours=collections.defaultdict(list)
for p in G['pours']:
    if not p['g'].is_empty: pours[p['L']].append((p['name'],p['net'],p['g']))
out=collections.Counter(); ex=collections.defaultdict(list)
for L in LN:
    O=objs[L]; geoms=[o[2] for o in O]; tree=STRtree(geoms)
    # object-object
    for i,(k,n,g) in enumerate(O):
        for j in tree.query(g.buffer(0.15)):
            if j<=i: continue
            k2,n2,g2=O[j]
            if n==n2 or not n or not n2: continue
            d=g.distance(g2)
            if d<0.15:
                key=(LN[L],'obj',n,n2); out[key]+=1
                if len(ex[key])<3: ex[key].append((k,k2,round(d,3),round(g.centroid.x,1),round(g.centroid.y,1)))
    # pour vs object
    for name,n,pg in pours[L]:
        for j in tree.query(pg.buffer(0.15)):
            k2,n2,g2=O[j]
            if n==n2 or not n2: continue
            d=pg.distance(g2)
            if d<0.15:
                key=(LN[L],'pour',name,n2); out[key]+=1
                if len(ex[key])<3: ex[key].append((k2,round(d,3),round(g2.centroid.x,1),round(g2.centroid.y,1)))
    # pour vs pour
    P=pours[L]
    for i in range(len(P)):
        for j in range(i+1,len(P)):
            if P[i][1]==P[j][1]: continue
            d=P[i][2].distance(P[j][2])
            if d<0.15:
                key=(LN[L],'pourpour',P[i][0],P[j][0]); out[key]+=1; ex[key].append(round(d,3))
for k,v in sorted(out.items()): print(k,v,ex[k])
print('checked')
