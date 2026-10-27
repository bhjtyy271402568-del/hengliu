import sys,json,math
exec(open('fp32.py').read().split("fps={u")[0])
fps={u:d for u,d in docs.items() if d['type']=='FOOTPRINT'}
J=json.load(open(sys.argv[1]))
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
            cx,cy,r=t[1:4]; out.extend([(cx-r,cy-r),(cx+r,cy+r),(cx-r,cy+r),(cx+r,cy-r)]); return
        if isinstance(t,list) and any(isinstance(v,list) for v in t):
            for v in t: walk(v); return
        i=0; mode='L'
        while i<len(t):
            v=t[i]
            if isinstance(v,str):
                mode=v; i+=1
                if mode=='ARC': i+=1   # skip angle
                elif mode=='CARC': i+=1
                continue
            if i+1<len(t) and not isinstance(t[i+1],str):
                out.append((t[i],t[i+1])); i+=2
            else: i+=1
    walk(path); return out
miss=set();comps=[]
for c in J:
    if c.get('primitiveType')!='Component': continue
    d=c.get('designator'); f=c['footprint']['uuid'] if c.get('footprint') else None
    if f not in fps: miss.add((d,c['footprint']['name'] if c.get('footprint') else None)); continue
    pn={str(p['padNumber']):p.get('net','') for p in c.get('pads',[])}
    ang=math.radians(c['rotation']); bot=c['layer']==2
    def tf(x,y):
        if bot: y=-y
        return ((c['x']+x*math.cos(ang)-y*math.sin(ang))*MIL,(c['y']+x*math.sin(ang)+y*math.cos(ang))*MIL)
    P=[];body=[]
    for h2,p in fps[f]['recs']:
        if h2['type']=='PAD':
            dp=p.get('defaultPad') or {}
            if dp.get('padType')=='POLYGON':
                q=nums(dp['path']); pts=[tf(x,y) for x,y in zip(q[0::2],q[1::2])]
            else:
                w,hh=dp.get('width',20),dp.get('height',20); pa=math.radians(p.get('padAngle',0))
                pts=[]
                for sx,sy in ((-1,-1),(1,-1),(1,1),(-1,1)):
                    lx,ly=sx*w/2,sy*hh/2
                    pts.append(tf(p['centerX']+lx*math.cos(pa)-ly*math.sin(pa),p['centerY']+lx*math.sin(pa)+ly*math.cos(pa)))
            xs=[q[0] for q in pts]; ys=[q[1] for q in pts]
            P.append([round(min(xs),3),round(min(ys),3),round(max(xs)-min(xs),3),round(max(ys)-min(ys),3),pn.get(str(p['num']),''),str(p['num']),1 if p.get('hole') else 0, p.get('layerId')])
        if h2['type']=='POLY' and p.get('layerId')==48:
            for (x,y) in bodypts(p['path']): body.append(tf(x,y))
    if body: xs=[q[0] for q in body]; ys=[q[1] for q in body]
    else: xs=[q[0] for q in P]+[q[0]+q[2] for q in P]; ys=[q[1] for q in P]+[q[1]+q[3] for q in P]
    comps.append(dict(r=d,b=1 if bot else 0,bb=[round(min(xs),3),round(min(ys),3),round(max(xs)-min(xs),3),round(max(ys)-min(ys),3)],p=P,x=round(c['x']*MIL,3),y=round(c['y']*MIL,3),rot=c['rotation'],fp=c['footprint']['name']))
print('comps',len(comps),'missing',miss)
json.dump(comps,open('lay32.json','w'),ensure_ascii=False)
