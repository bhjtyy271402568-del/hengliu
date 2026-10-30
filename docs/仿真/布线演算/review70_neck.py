"""走线端点接触检查：端头圆和同网铜重叠 < 30% 的列出，并用 Gerber 收缩法量颈部宽度。用法：python3 review70_neck.py geo.pkl lay.pkl"""
import pickle,sys,math,collections
from shapely.geometry import Point,box,LineString
G=pickle.load(open(sys.argv[1],'rb')); LAY=pickle.load(open(sys.argv[2],'rb'))
objs=collections.defaultdict(list)
for i,t in enumerate(G['tracks']): objs[(t['L'],t['net'])].append(('T%d'%i,LineString([(t['x0'],t['y0']),(t['x1'],t['y1'])]).buffer(t['w']/2,16)))
for p in G['pads']:
    for L in p['Ls']: objs[(L,p['net'])].append(('P'+p['r']+'.'+p['n'],p['g']))
for v in G['vias']:
    for L in (1,15,16,2): objs[(L,v['net'])].append(('V(%.2f,%.2f)'%(v['x'],v['y']),Point(v['x'],v['y']).buffer(v['D']/2,32)))
def neck(L,a,b):
    W=box(min(a.x,b.x)-2,min(a.y,b.y)-2,max(a.x,b.x)+2,max(a.y,b.y)+2); cu=LAY[L].intersection(W); last=None
    for e in (0.0,0.02,0.04,0.05,0.06,0.075,0.1,0.125,0.15,0.2):
        g=cu.buffer(-e,8) if e>0 else cu
        P=list(getattr(g,'geoms',[g]))
        ia=[i for i,p in enumerate(P) if p.distance(a)<=e+0.01]; ib=[i for i,p in enumerate(P) if p.distance(b)<=e+0.01]
        if not set(ia)&set(ib): return last
        last=e
    return last
rows=[]
for i,t in enumerate(G['tracks']):
    l=LineString([(t['x0'],t['y0']),(t['x1'],t['y1'])])
    for end,(x,y) in ((0,(t['x0'],t['y0'])),(1,(t['x1'],t['y1']))):
        cap=Point(x,y).buffer(t['w']/2,16); A=cap.area; best=0;bk=None;bg=None
        for k,g in objs[(t['L'],t['net'])]:
            if k=='T%d'%i: continue
            a=g.intersection(cap).area
            if a>best: best,bk,bg=a,k,g
        if not (0<best/A<0.3): continue
        # point on track 0.25 mm back
        d=min(0.25,l.length/2); a=l.interpolate(d if end==0 else l.length-d)
        # point deep in target: representative point of target minus cap region
        b=bg.difference(Point(x,y).buffer(t['w'])).representative_point() if not bg.difference(Point(x,y).buffer(t['w'])).is_empty else bg.representative_point()
        e=neck(t['L'],a,b)
        rows.append((None if e is None else round(2*e,2),t['net'],'L%d'%t['L'],round(x,3),round(y,3),'w%.3f'%t['w'],bk))
rows.sort(key=lambda r:(r[0] if r[0] is not None else -1))
for r in rows: print(r)
