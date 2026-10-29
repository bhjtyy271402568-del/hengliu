import re,sys,math
from shapely.geometry import Polygon,Point,LineString,box
from shapely.ops import unary_union
from shapely.validation import make_valid
def render(path):
    txt=open(path).read().replace('\n','')
    blocks=[b for b in re.split(r'\*',txt)]
    ap={}; cur=None; x=y=0; pol='D'; layer=None; region=False; rpts=[]; mode='G01'
    dark=[]; out=None
    ops=[]  # sequence of (pol, geom)
    def sc(v): return int(v)/1e6
    i=0
    for b in blocks:
        b=b.strip('%')
        if not b: continue
        if b.startswith('ADD'):
            m=re.match(r'ADD(\d+)([CRO]),([\d.]+)(?:X([\d.]+))?',b)
            if m: ap[int(m.group(1))]=(m.group(2),float(m.group(3)),float(m.group(4) or 0))
            continue
        if b.startswith('LP'): pol=b[2]; continue
        if b.startswith('G04') or b.startswith('FS') or b.startswith('MO') or b=='G75': continue
        if b=='G36': region=True; rpts=[]; contours=[]; continue
        if b=='G37':
            if len(rpts)>2: contours.append(make_valid(Polygon(rpts)))
            g=Polygon()
            for c in contours: g=g.symmetric_difference(c)
            ops.append((pol,g)); region=False; continue
        m=re.match(r'(G0[123])?(?:D(\d+))?$',b)
        if b.startswith('G54D') or (m and m.group(2) and int(m.group(2))>=10 and not m.group(1)):
            d=int(re.findall(r'D(\d+)',b)[0]); cur=d; continue
        m=re.match(r'(G0[123])?X(-?\d+)Y(-?\d+)(?:I(-?\d+)J(-?\d+))?D0([123])',b)
        if m:
            if m.group(1): mode=m.group(1)
            nx,ny=sc(m.group(2)),sc(m.group(3)); dcode=m.group(6)
            if mode in('G02','G03') and m.group(4) is not None and dcode=='1':
                cx,cy=x+sc(m.group(4)),y+sc(m.group(5)); r=math.hypot(x-cx,y-cy)
                a0=math.atan2(y-cy,x-cx); a1=math.atan2(ny-cy,nx-cx)
                if mode=='G02':
                    if a1>=a0: a1-=2*math.pi
                else:
                    if a1<=a0: a1+=2*math.pi
                n=max(4,int(abs(a1-a0)*r/0.05)); seg=[(cx+r*math.cos(a0+(a1-a0)*k/n),cy+r*math.sin(a0+(a1-a0)*k/n)) for k in range(1,n+1)]
            else: seg=[(nx,ny)]
            if region:
                if dcode=='2':
                    if len(rpts)>2: contours.append(make_valid(Polygon(rpts)))
                    rpts=[(nx,ny)]
                else:
                    if not rpts: rpts=[(x,y)]
                    rpts+=seg
            else:
                a=ap.get(cur)
                if dcode=='3' and a:
                    t,w,h=a
                    g=Point(nx,ny).buffer(w/2,16) if t=='C' else (box(nx-w/2,ny-h/2,nx+w/2,ny+h/2) if t=='R' else (LineString([(nx-(w-h)/2,ny),(nx+(w-h)/2,ny)]).buffer(h/2) if w>=h else LineString([(nx,ny-(h-w)/2),(nx,ny+(h-w)/2)]).buffer(w/2)))
                    ops.append((pol,g))
                elif dcode=='1' and a:
                    ops.append((pol,LineString([(x,y)]+seg).buffer(a[1]/2,8)))
            x,y=nx,ny
    img=Polygon()
    batch=[]; bp='D'
    for p,g in ops:
        if p!=bp and batch:
            u=unary_union(batch); img=img.union(u) if bp=='D' else img.difference(u); batch=[]
        bp=p; batch.append(g)
    if batch:
        u=unary_union(batch); img=img.union(u) if bp=='D' else img.difference(u)
    return img
if __name__=='__main__':
    import pickle
    img=render(sys.argv[1]); pickle.dump(img,open(sys.argv[2],'wb')); print('area',round(img.area,1),'parts',len(getattr(img,'geoms',[img])))
