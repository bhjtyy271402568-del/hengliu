"""过孔接触面积检查：每个过孔和同网铜（不含过孔自身）的重叠面积，少于两层 > 0.02 mm² 的列出。用法：python3 review70_viacontact.py geo.pkl"""
import pickle,collections,sys
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
G=pickle.load(open(sys.argv[1],'rb'))
objs=collections.defaultdict(list)
for t in G['tracks']: objs[(t['L'],t['net'])].append(LineString([(t['x0'],t['y0']),(t['x1'],t['y1'])]).buffer(t['w']/2,16))
for p in G['pads']:
    for L in p['Ls']: objs[(L,p['net'])].append(p['g'])
for p in G['pours']: objs[(p['L'],p['net'])].append(p['g'])
CU={k:unary_union(v) for k,v in objs.items()}
# other vias of same net (via-to-via chains)
vd=collections.defaultdict(list)
for v in G['vias']: vd[v['net']].append(v)
res=[]
for v in G['vias']:
    disc=Point(v['x'],v['y']).buffer(v['D']/2,32)
    per={}
    for L in (1,15,16,2):
        g=CU.get((L,v['net']))
        a=g.intersection(disc).area if g is not None else 0
        # via-via overlap
        for w in vd[v['net']]:
            if w is v: continue
            if Point(w['x'],w['y']).distance(Point(v['x'],v['y']))<(v['D']+w['D'])/2: a+=1e-3
        per[L]=a
    good=[L for L,a in per.items() if a>0.02]
    weak=[L for L,a in per.items() if 0<a<=0.02]
    if len(good)<2: res.append((v['net'],round(v['x'],3),round(v['y'],3),v['d'],{L:round(a,4) for L,a in per.items() if a>0}))
print('vias with <2 solid layer contacts:',len(res))
for r in res: print('  ',r)
