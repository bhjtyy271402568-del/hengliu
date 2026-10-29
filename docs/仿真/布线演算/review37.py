"""10-29 版恒流源板复核脚本（复核文件第 23 节）。
用法：python3 -I review37.py 工程.epro2 pours.json 焊盘对应关系.csv
pours.json、焊盘对应关系.csv 来自 Codex 复核包的“核对数据”。坐标 mm，y 向下（与嘉立创画面一致）。
铺铜圆弧按弦近似，离铺铜边 0.1 mm 以内的间距数不可信，以嘉立创 DRC 为准。"""
import sys, json, math, collections, csv
EPRO, POURS, PADCSV = sys.argv[1:4]
import zipfile
def load(p):
    z=zipfile.ZipFile(p); n=[x for x in z.namelist() if x.endswith('.epru')][0]
    text=z.read(n).decode()
    docs={};cur=None
    for line in text.splitlines():
        i=line.find('||')
        if i<0: continue
        try:
            head=json.loads(line[:i]); body=line[i+2:]; body=body[:-1] if body.endswith('|') else body
            rec=json.loads(body) if body else {}
        except ValueError: continue
        if head.get('type')=='DOCHEAD':
            cur=docs.setdefault(rec.get('uuid'),{'type':rec.get('docType'),'recs':[]})
        elif cur is not None: cur['recs'].append((head,rec))
    return docs

D=load(EPRO)
D=load(EPRO)
fps={u:d for u,d in D.items() if d['type']=='FOOTPRINT'}
pcb=D['9a0fbfd22df79247']['recs']
import csv
net={}
for row in csv.DictReader(open(PADCSV,encoding='utf-8-sig')): net[(row['位号'],row['引脚号'])]=row['网络']

MIL=0.0254
def nums(path):
    out=[]
    for v in path:
        if isinstance(v,(int,float)): out.append(v)
        elif isinstance(v,list): out+=nums(v)
    return out
def bodypts(path):
    out=[]
    def walk(t):
        if isinstance(t,list) and t and t[0]=='CIRCLE':
            cx,cy,r=t[1:4]; out.extend([(cx-r,cy-r),(cx+r,cy+r)]); return
        if isinstance(t,list) and any(isinstance(v,list) for v in t):
            for v in t: walk(v); return
        i=0
        while i<len(t):
            v=t[i]
            if isinstance(v,str):
                i+=1
                if v in ('ARC','CARC'): i+=1
                continue
            if i+1<len(t) and not isinstance(t[i+1],str): out.append((t[i],t[i+1])); i+=2
            else: i+=1
    walk(path); return out
attrs={}
for h,r in pcb:
    if h['type']=='ATTR' and r.get('parentId'): attrs.setdefault(r['parentId'],{})[r.get('key')]=r.get('value')
comps=[]
for h,c in pcb:
    if h['type']!='COMPONENT' or not c: continue
    a=attrs.get(h['id'],{}); d=a.get('Designator'); f=a.get('Footprint')
    if f not in fps or not d: continue
    ang=math.radians(c['angle']); bot=c['layerId']==2
    def tf(x,y):
        if bot: y=-y
        return ((c['x']+x*math.cos(ang)-y*math.sin(ang))*MIL,(c['y']+x*math.sin(ang)+y*math.cos(ang))*MIL)
    P=[];body=[]
    for h2,p in fps[f]['recs']:
        if h2['type']=='PAD' and p:
            dp=p.get('defaultPad') or {}
            if dp.get('padType')=='POLYGON':
                q=nums(dp['path']); pts=[tf(p['centerX']+x if False else x,y) for x,y in zip(q[0::2],q[1::2])]
            else:
                w,hh=dp.get('width',20),dp.get('height',20); pa=math.radians(p.get('padAngle',0))
                pts=[]
                for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1)):
                    lx,ly=sx*w/2,sy*hh/2
                    pts.append(tf(p['centerX']+lx*math.cos(pa)-ly*math.sin(pa),p['centerY']+lx*math.sin(pa)+ly*math.cos(pa)))
            xs=[q[0] for q in pts]; ys=[q[1] for q in pts]
            P.append([round(min(xs),3),round(min(ys),3),round(max(xs)-min(xs),3),round(max(ys)-min(ys),3),net.get((d,str(p['num'])),'?'),str(p['num']),1 if p.get('hole') else 0])
        if h2['type']=='POLY' and p and p.get('layerId')==48:
            body+= [tf(x,y) for x,y in bodypts(p['path'])]
    if body: xs=[q[0] for q in body]; ys=[q[1] for q in body]
    else: xs=[q[0] for q in P]+[q[0]+q[2] for q in P]; ys=[q[1] for q in P]+[q[1]+q[3] for q in P]
    comps.append(dict(r=d,b=1 if bot else 0,bb=[round(min(xs),3),round(min(ys),3),round(max(xs)-min(xs),3),round(max(ys)-min(ys),3)],p=P,x=round(c['x']*MIL,3),y=round(c['y']*MIL,3),rot=c['angle']))
from shapely.geometry import Polygon, box, LineString, Point
from shapely.ops import unary_union
MIL=0.0254
R=D['9a0fbfd22df79247']['recs']
C=comps
LAY={1:'L1',15:'L2',16:'L3',2:'L4'}
tracks=[]; vias=[]
for h,r in R:
    if h['type']=='LINE' and r and r.get('layerId') in LAY:
        tracks.append(dict(id=h['id'],net=r['netName'],L=r['layerId'],x0=r['startX']*MIL,y0=r['startY']*MIL,x1=r['endX']*MIL,y1=r['endY']*MIL,w=r['width']*MIL))
    if h['type']=='VIA' and r:
        vias.append(dict(id=h['id'],net=r['netName'],x=r['centerX']*MIL,y=r['centerY']*MIL,d=r['holeDiameter']*MIL,D=r['viaDiameter']*MIL))
arcs=[(h,r) for h,r in R if h['type'] in ('ARC',)]
P=json.load(open(POURS))
def ring(t):
    pts=[];i=0
    t=list(t)
    if t and t[0]=='CIRCLE':
        return list(Point(t[1]*0.254,t[2]*0.254).buffer(t[3]*0.254,16).exterior.coords)
    while i<len(t):
        v=t[i]
        if v=='L': i+=1; continue
        if v=='ARC': i+=2; continue   # skip angle; endpoint follows
        if isinstance(v,str): i+=1; continue
        pts.append((t[i]*0.254,t[i+1]*0.254)); i+=2
    return pts
pours=[]
for p in P:
    geoms=[]
    for f in p['region'].get('pourFills',[]):
        cp=f['path']['complexPolygon']
        rings=[cp] if cp and not isinstance(cp[0],list) else cp
        polys=[Polygon(ring(rg)) for rg in rings if len(ring(rg))>=3]
        if not polys: continue
        # first ring outer, rest holes (even-odd)
        g=polys[0].buffer(0)
        for hp in polys[1:]: g=g.symmetric_difference(hp.buffer(0))
        geoms.append(g)
    pours.append(dict(id=p['id'],net=p['net'],L=p['layer'],name=p.get('name',''),g=unary_union(geoms) if geoms else Polygon()))
pads=[]
for c in C:
    for p in c['p']:
        g=box(p[0],p[1],p[0]+p[2],p[1]+p[3])
        Ls=[1,15,16,2] if p[6] else ([2] if c['b'] else [1])
        pads.append(dict(r=c['r'],n=p[5],net=p[4],Ls=Ls,g=g,hole=p[6]))
cu=collections.defaultdict(list)
for t in tracks:
    cu[(t['L'],t['net'])].append(LineString([(t['x0'],t['y0']),(t['x1'],t['y1'])]).buffer(t['w']/2))
for v in vias:
    for L in LAY: cu[(L,v['net'])].append(Point(v['x'],v['y']).buffer(v['D']/2))
for p in pads:
    for L in p['Ls']: cu[(L,p['net'])].append(p['g'])
for p in pours: cu[(p['L'],p['net'])].append(p['g'])
CU={k:unary_union(v) for k,v in cu.items()}

# ---- 关键检查（第 23 节的数）----
from shapely.geometry import LineString as LS
LN={1:'L1',15:'L2',16:'L3',2:'L4'}
def cut(L,net,p0,p1):
    g=CU.get((L,net))
    if g is None: return []
    s=LS([p0,p1]).intersection(g); gs=list(s.geoms) if hasattr(s,'geoms') else [s]
    return [(round(q.bounds[0],1),round(q.bounds[1],1),round(q.length,1)) for q in gs if not q.is_empty and q.length>0.2]
print('L3 GND 与底层 SW 重叠 mm2', round(CU[(2,'LT_SW')].intersection(CU[(16,'GND')]).area,1))
print('L2 有无 GND 铺铜', any(p['L']==15 and p['net']=='GND' for p in pours))
for y in (45,50,55):
    print('PGND 横截 y=%d'%y,{LN[L]:cut(L,'PGND',(90,y),(128,y)) for L in (1,15,2)})
for x in (94,100,106):
    print('SW 竖截 x=%d'%x,{LN[L]:cut(L,'LT_SW',(x,60),(x,82)) for L in (1,2)})
for (x,y,net) in [(108.2,41.99,'LT_SHUNT_P'),(108.2,33.99,'VCC_OUT'),(69.25,91.15,'LT_VIN'),(63.9,91.15,'DCBUS')]:
    print('采样孔',(x,y),net,'接同网铺铜层',[LN[p['L']] for p in pours if p['net']==net and p['g'].distance(Point(x,y))<0.3])
cu2=collections.defaultdict(list)
for t in tracks: cu2[(t['L'],t['net'])].append(LS([(t['x0'],t['y0']),(t['x1'],t['y1'])]).buffer(t['w']/2))
for p in pads:
    for L in p['Ls']: cu2[(L,p['net'])].append(p['g'])
for p in pours: cu2[(p['L'],p['net'])].append(p['g'])
CU2={k:unary_union(v) for k,v in cu2.items()}
for v in vias:
    pt=Point(v['x'],v['y']).buffer(v['D']/2)
    Ls=[LN[L] for L in (1,15,16,2) if (L,v['net']) in CU2 and CU2[(L,v['net'])].intersects(pt)]
    if len(Ls)<=1: print('只接一层的过孔',v['net'],round(v['x'],2),round(v['y'],2),Ls)
