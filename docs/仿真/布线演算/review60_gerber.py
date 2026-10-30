"""Gerber 铜层渲染（支持 C/R/O、宏孔径 4 号轮廓、1 号圆、21 号矩形、区域 G36/37、圆弧）。坐标转成板坐标（减原点）。"""
import re,sys,math,pickle
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
from shapely.validation import make_valid
from shapely import affinity
OX,OY=-214.198142,42.261000
def render(path):
    txt=open(path).read()
    macros={}
    for m in re.finditer(r'%AM([^*]+)\*(.*?)%',txt,re.S):
        macros[m.group(1)]=m.group(2).replace('\n','')
    body=re.sub(r'%AM.*?%','',txt,flags=re.S).replace('\n','')
    ap={}; cur=None; x=y=0; region=False; rpts=[]; contours=[]; mode='G01'; ops=[]
    def sc(v): return int(v)/1e6
    for b in body.split('*'):
        b=b.strip('%')
        if not b: continue
        if b.startswith('ADD'):
            m=re.match(r'ADD(\d+)([A-Za-z_][A-Za-z0-9_]*)(?:,(.*))?$',b)
            if m:
                n=int(m.group(1)); t=m.group(2); par=[float(v) for v in (m.group(3) or '').split('X') if v]
                ap[n]=(t,par)
            continue
        if b.startswith(('G04','FS','MO','LP','G75','TF','TA','TD','TO')): continue
        if b=='G36': region=True; rpts=[]; contours=[]; continue
        if b=='G37':
            if len(rpts)>2: contours.append(make_valid(Polygon(rpts)))
            g=Polygon()
            for c in contours: g=g.symmetric_difference(c)
            ops.append(g); region=False; continue
        if re.match(r'^(G54)?D(\d+)$',b) and int(re.findall(r'D(\d+)',b)[0])>=10:
            cur=int(re.findall(r'D(\d+)',b)[0]); continue
        m=re.match(r'(G0[123])?X(-?\d+)Y(-?\d+)(?:I(-?\d+)J(-?\d+))?D0([123])',b)
        if not m:
            m2=re.match(r'(G0[123])$',b)
            if m2: mode=m2.group(1)
            continue
        if m.group(1): mode=m.group(1)
        nx,ny=sc(m.group(2)),sc(m.group(3)); dc=m.group(6)
        if mode in('G02','G03') and m.group(4) is not None and dc=='1':
            cx,cy=x+sc(m.group(4)),y+sc(m.group(5)); r=math.hypot(x-cx,y-cy)
            a0=math.atan2(y-cy,x-cx); a1=math.atan2(ny-cy,nx-cx)
            if mode=='G02':
                if a1>=a0: a1-=2*math.pi
            else:
                if a1<=a0: a1+=2*math.pi
            n=max(4,int(abs(a1-a0)*r/0.03)); seg=[(cx+r*math.cos(a0+(a1-a0)*k/n),cy+r*math.sin(a0+(a1-a0)*k/n)) for k in range(1,n+1)]
        else: seg=[(nx,ny)]
        if region:
            if dc=='2':
                if len(rpts)>2: contours.append(make_valid(Polygon(rpts)))
                rpts=[(nx,ny)]
            else:
                if not rpts: rpts=[(x,y)]
                rpts+=seg
        else:
            a=ap.get(cur)
            if a and dc=='3':
                t,p=a
                if t=='C': g=Point(nx,ny).buffer(p[0]/2,24)
                elif t=='R': g=box(nx-p[0]/2,ny-p[1]/2,nx+p[0]/2,ny+p[1]/2)
                elif t=='O':
                    w,h=p[0],p[1]
                    g=LineString([(nx-(w-h)/2,ny),(nx+(w-h)/2,ny)]).buffer(h/2,16) if w>=h else LineString([(nx,ny-(h-w)/2),(nx,ny+(h-w)/2)]).buffer(w/2,16)
                elif t in macros:
                    parts=[]
                    for prim in macros[t].split('*'):
                        def ev(q):
                            for k in range(9,0,-1): q=q.replace('$%d'%k,'(%r)'%(p[k-1] if k-1<len(p) else 0))
                            return float(eval(q.replace('x','*').replace('X','*')))
                        v=[ev(q) for q in prim.split(',') if q]
                        if not v: continue
                        if v[0]==4:
                            k=int(v[2]); pts=[(v[3+2*i],v[4+2*i]) for i in range(k+1)]; rot=v[3+2*(k+1)]
                            pg=make_valid(Polygon(pts)); pg=affinity.rotate(pg,rot,origin=(0,0)); parts.append(pg)
                        elif v[0]==1: parts.append(Point(v[3],v[4]).buffer(v[2]/2,24))
                        elif v[0]==20:
                            pg=LineString([(v[3],v[4]),(v[5],v[6])]).buffer(v[2]/2,cap_style=2); parts.append(affinity.rotate(pg,v[7],origin=(0,0)))
                        elif v[0]==21:
                            pg=box(v[4]-v[2]/2,v[5]-v[3]/2,v[4]+v[2]/2,v[5]+v[3]/2); parts.append(affinity.rotate(pg,v[6],origin=(0,0)))
                        else: print('unknown prim',v[0],t,file=sys.stderr)
                    g=affinity.translate(unary_union(parts),nx,ny)
                else: print('unknown ap',t,file=sys.stderr); g=None
                if g is not None: ops.append(g)
            elif a and dc=='1':
                ops.append(LineString([(x,y)]+seg).buffer(a[1][0]/2,12))
        x,y=nx,ny
    img=unary_union([o for o in ops if not o.is_empty])
    return affinity.translate(img,-OX,-OY)
if __name__=='__main__':
    out={}
    for f,L in (('Gerber_TopLayer.GTL',1),('Gerber_InnerLayer1.G1',15),('Gerber_InnerLayer2.G2',16),('Gerber_BottomLayer.GBL',2),('Gerber_TopSolderMaskLayer.GTS','tsm'),('Gerber_BottomSolderMaskLayer.GBS','bsm'),('Gerber_TopSilkscreenLayer.GTO','tso'),('Gerber_BottomSilkscreenLayer.GBO','bso'),('Gerber_TopPasteMaskLayer.GTP','tsp'),('Gerber_BottomPasteMaskLayer.GBP','bsp')):
        g=render(sys.argv[1]+'/'+f); out[L]=g; print(f,round(g.area,1),len(getattr(g,'geoms',[g])))
    pickle.dump(out,open(sys.argv[2],'wb'))
