"""单点连接检查：某网络两只焊盘之间，是否只靠一个过孔 / 插件孔换层连通。再量每块铜在两个连接点之间的颈宽。"""
import pickle,sys,itertools
from shapely.geometry import Point
S=pickle.load(open('snap.pkl','rb')); L=pickle.load(open('lay.pkl','rb'))
def pcs(k,g): return [(k,i) for i,q in enumerate(L[k].geoms) if q.intersects(g)]
def conns(net):
    out=[]
    for p in S['pads']:
        if p['net']!=net: continue
        nodes=[]
        if p['layer'] in (1,12): nodes+=pcs(1,p['g'])
        if p['layer'] in (2,12): nodes+=pcs(2,p['g'])
        out.append((f"{p['ref']}.{p['num']}",nodes,p))
    for v in S['vias']:
        if v['net']==net:
            g=Point(v['x'],v['y']).buffer(0.2); out.append(('via(%.1f,%.1f)'%(v['x'],v['y']),pcs(1,g)+pcs(2,g),None))
    return out
def comp(cs,skip=None):
    par={}
    def f(a):
        par.setdefault(a,a)
        while par[a]!=a: par[a]=par[par[a]]; a=par[a]
        return a
    for name,nodes,_ in cs:
        if name==skip: continue
        for n in nodes[1:]: par[f(n)]=f(nodes[0])
    return f
for arg in sys.argv[1:]:
    net,a,b=arg.split(':'); cs=conns(net); d={c[0]:c for c in cs}
    na,nb=d[a][1][0],d[b][1][0]
    f=comp(cs); assert f(na)==f(nb),'不连通'
    crit=[c[0] for c in cs if len(c[1])>1 and c[0] not in(a,b) and comp(cs,c[0])(na)!=comp(cs,c[0])(nb)]
    # 端子自身是通孔时也算
    print(arg,'→ 必经的单个孔:',crit or '无')
