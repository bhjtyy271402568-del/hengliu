import sys,json,math
sys.path.insert(0,'/home/user/hengliu/tools')
import epro_snapshot as E
exec(open('fp.py').read().split("fps={u")[0])
fps={u:d for u,d in docs.items() if d['type']=='FOOTPRINT'}
MIL=0.0254
D=E.load('/tmp/claude-0/-home-user-hengliu/a8a90bca-9729-5c7b-bb22-b897755cc992/scratchpad/可调恒流源_恒流源板与辅助电源板.epro2')
def nums(path):
    out=[]
    for v in path:
        if isinstance(v,(int,float)): out.append(v)
        elif isinstance(v,list): out+=nums(v)
    return out
OUT={}
for title,pid in (('main','9a0fbfd22df79247'),('aux','fac41427ef69b76d')):
    recs=docs[pid]['recs']; at=E.attrs_by_parent(recs); pn=E.pad_nets(D,pid)
    comps=[]
    for h,r in recs:
        if h['type']!='COMPONENT': continue
        a=at.get(h['id'],{}); d=a.get('Designator'); f=a.get('Footprint') or ('6cff2be3cbfcb21b' if (d=='U2' and title=='main') else None)
        if not d or f not in fps: continue
        ang=math.radians(r['angle']); bot=r['layerId']==2
        def tf(x,y):
            if bot: y=-y   # 嘉立创底层：封装局部 y 取反后再旋转（按原生全局焊盘核对过）
            return ((r['x']+x*math.cos(ang)-y*math.sin(ang))*MIL,(r['y']+x*math.sin(ang)+y*math.cos(ang))*MIL)
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
                P.append([round(min(xs),2),round(min(ys),2),round(max(xs)-min(xs),2),round(max(ys)-min(ys),2),pn.get(f"{d}.{p['num']}",''),p['num'],1 if p.get('hole') else 0])
            if h2['type']=='POLY' and p.get('layerId')==48:
                q=nums(p['path']); body+= [tf(x,y) for x,y in zip(q[0::2],q[1::2])]
        if body:
            xs=[q[0] for q in body]; ys=[q[1] for q in body]
        else:
            xs=[q[0] for q in P]+[q[0]+q[2] for q in P]; ys=[q[1] for q in P]+[q[1]+q[3] for q in P]
        bb=[round(min(xs),2),round(min(ys),2),round(max(xs)-min(xs),2),round(max(ys)-min(ys),2)]
        comps.append(dict(r=d,b=1 if bot else 0,bb=bb,p=P,x=round(r['x']*MIL,2),y=round(r['y']*MIL,2)))
    holes=[[round(r['centerX']*MIL,2),round(r['centerY']*MIL,2),round(r['hole']['width']*MIL,2)] for h,r in recs if h['type']=='PAD' and r.get('hole')]
    keep=[[round(r['path'][0][1]*MIL,2),round(r['path'][0][2]*MIL,2),round(r['path'][0][3]*MIL,2)] for h,r in recs if h['type']=='REGION' and r['path'] and r['path'][0][0]=='CIRCLE']
    rects=[r['path'] for h,r in recs if h['type']=='REGION' and r['path'] and r['path'][0]!='CIRCLE' and not (isinstance(r['path'][0],list) and r['path'][0][0]=='CIRCLE')]
    outline=[r['path'] for h,r in recs if h['type']=='POLY' and r.get('polyType')=='BOARD_OUTLINE']
    OUT[title]=dict(c=comps,holes=holes,keep=keep)
    print(title,len(comps),'holes',holes,'keep',keep,'outline',outline,'rects',str(rects)[:300])
json.dump(OUT,open('pagedata.json','w'),ensure_ascii=False,separators=(',',':'))
import os; print(os.path.getsize('pagedata.json'))
