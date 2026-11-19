import re,sys
from shapely.geometry import Point,box,Polygon
from shapely.ops import unary_union
from shapely import affinity
def parse(fn):
    t=open(fn,encoding='utf-8',errors='ignore').read()
    fs=re.search(r'%FSLAX(\d)(\d)Y',t); dec=int(fs.group(2))
    ap={}
    for m in re.finditer(r'%ADD(\d+)([A-Za-z0-9_]+),?([^*]*)\*%',t):
        ap[m.group(1)]=(m.group(2),[float(v) for v in m.group(3).split('X') if v])
    shapes=[];cur=None;x=y=0;region=False;pts=[]
    for cmd in re.split(r'\*',t):
        cmd=cmd.strip().lstrip('%')
        if cmd.startswith('G36'): region=True;pts=[];continue
        if cmd.startswith('G37'):
            if len(pts)>2: shapes.append(Polygon(pts).buffer(0))
            region=False;continue
        m=re.match(r'^(?:G0?1)?D(\d+)$',cmd)
        if m and int(m.group(1))>=10: cur=m.group(1);continue
        m=re.match(r'^(?:G0?[123])?(?:X(-?\d+))?(?:Y(-?\d+))?(?:I-?\d+)?(?:J-?\d+)?D0?([123])$',cmd)
        if m:
            nx=int(m.group(1))/10**dec if m.group(1) else x; ny=int(m.group(2))/10**dec if m.group(2) else y; d=m.group(3)
            if region:
                if d=='2': 
                    if len(pts)>2: shapes.append(Polygon(pts).buffer(0))
                    pts=[(nx,ny)]
                else: pts.append((nx,ny))
            elif d=='3' and cur in ap:
                k,p=ap[cur]
                if k=='C': s=Point(nx,ny).buffer(p[0]/2)
                elif k=='R': s=box(nx-p[0]/2,ny-p[1]/2,nx+p[0]/2,ny+p[1]/2)
                elif k=='O':
                    w,h=p[0],p[1]; r=min(w,h)/2
                    s=box(nx-w/2+ (r if w>h else 0),ny-h/2+(r if h>w else 0),nx+w/2-(r if w>h else 0),ny+h/2-(r if h>w else 0)).buffer(r)
                else: s=Point(nx,ny).buffer(0.3)
                shapes.append(s)
            elif d=='1' and cur in ap and not region:
                k,p=ap[cur]
                from shapely.geometry import LineString
                shapes.append(LineString([(x,y),(nx,ny)]).buffer(p[0]/2))
            x,y=nx,ny
    return shapes
def drills(fn):
    out=[];tools={};cur=None
    for l in open(fn):
        l=l.strip()
        m=re.match(r'T(\d+)C([\d.]+)',l)
        if m: tools[m.group(1)]=float(m.group(2));continue
        m=re.match(r'^T(\d+)$',l)
        if m: cur=m.group(1);continue
        m=re.match(r'X([-\d.]+)Y([-\d.]+)',l)
        if m: out.append((float(m.group(1)),float(m.group(2)),tools[cur]))
    return out
g=sys.argv[1]
vias=drills(g+'/Drill_PTH_Through_Via.DRL')
for side,f in (('顶','Gerber_TopPasteMaskLayer.GTP'),('底','Gerber_BottomPasteMaskLayer.GBP')):
    pads=parse(g+'/'+f)
    hit=[]
    for vx,vy,d in vias:
        c=Point(vx,vy).buffer(d/2)
        for i,p in enumerate(pads):
            if p.intersects(c): hit.append((vx,vy,d,i,round(p.area,2),[round(v,1) for v in p.bounds]));break
    print(side,'贴片焊盘',len(pads),'过孔',len(vias),'落在焊盘(钢网开口)里的过孔',len(hit))
    from collections import defaultdict
    grp=defaultdict(list)
    for h in hit: grp[(h[3],h[4],tuple(h[5]))].append(h[2])
    for k,v in grp.items(): print('  焊盘面积',k[1],'mm2 范围',k[2],'孔数',len(v),'孔径',sorted(set(v)))
