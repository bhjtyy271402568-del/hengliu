"""信号线下一层参考面：标出空（void）、异网（other）、PGND 段。用法：python3 review60_refvoid.py 网络1,网络2（读当前目录 geo.pkl、lay.pkl）。"""
import pickle,math,sys,collections
import shapely,numpy as np
G=pickle.load(open('geo.pkl','rb')); CU=G['CU']; LAY=pickle.load(open('lay.pkl','rb'))
adj={1:15,2:16,16:2}
for net in sys.argv[1].split(','):
    runs=[]
    for t in G['tracks']:
        if t['net']!=net or t['L'] not in adj: continue
        rl=adj[t['L']]; l=math.hypot(t['x1']-t['x0'],t['y1']-t['y0']); n=max(2,int(l/0.1))
        xs=np.linspace(t['x0'],t['x1'],n); ys=np.linspace(t['y0'],t['y1'],n)
        m=shapely.contains_xy(LAY[rl],xs,ys)
        gm=shapely.contains_xy(CU.get((rl,'GND')),xs,ys) if (rl,'GND') in CU else np.zeros(n,bool)
        pm=shapely.contains_xy(CU.get((rl,'PGND')),xs,ys) if (rl,'PGND') in CU else np.zeros(n,bool)
        cur=None
        for k in range(n):
            s='void' if not m[k] else ('GND' if gm[k] else ('PGND' if pm[k] else 'other'))
            if s!='GND':
                if cur and cur[0]==s and cur[-1]==k-1: cur[2]=(xs[k],ys[k]); cur[-1]=k
                else:
                    if cur: runs.append(cur)
                    cur=[s,(xs[k],ys[k]),(xs[k],ys[k]),t['L'],l/n,k]
                cur[4]+=0
            else:
                if cur: runs.append(cur); cur=None
        if cur: runs.append(cur)
    agg=[(r[0],'L%d'%r[3],round(math.dist(r[1],r[2]),2),tuple(round(v,1) for v in r[1]),tuple(round(v,1) for v in r[2])) for r in runs]
    agg=[a for a in agg if a[2]>=0.5]
    print(net, sorted(agg,key=lambda a:-a[2])[:10])
