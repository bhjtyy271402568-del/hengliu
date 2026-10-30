"""铜皮电流分布：每层按 h 网格离散，片电阻 Rs（2 oz），过孔按孔壁电阻连层，焊盘当理想端子。"""
import pickle,sys,math,collections,numpy as np,shapely
from shapely.geometry import Point,box
from shapely.ops import unary_union
import scipy.sparse as sp, scipy.sparse.linalg as spl
G=pickle.load(open(sys.argv[1],'rb')); CU=G['CU']
H=0.25; RHO=1.72e-8; T=70e-6; RS=RHO/T            # 0.246 mΩ/sq
TP=20e-6                                            # 孔铜
ZL={1:0.0,15:0.28,16:1.415,2:1.70}                  # mm, 层中心近似位置
LAY=[1,15,16,2]
P={(p['r'],p['n']):p for p in G['pads']}
def solve(net,terms,label):
    xs=np.arange(0,128,H)+H/2; ys=np.arange(0,95,H)+H/2
    X,Y=np.meshgrid(xs,ys)
    idx={}; n=0; masks={}
    for L in LAY:
        g=CU.get((L,net))
        m=np.zeros(X.shape,bool) if g is None else shapely.contains_xy(g,X,Y)
        masks[L]=m
        ii=np.full(X.shape,-1,int); k=m.sum(); ii[m]=np.arange(n,n+k); n+=k; idx[L]=ii
    rows=[];cols=[];vals=[]
    def add(a,b,gc):
        rows.extend([a,b,a,b]); cols.extend([a,b,b,a]); vals.extend([gc,gc,-gc,-gc])
    gl=1/RS
    for L in LAY:
        ii=idx[L]
        a=ii[:,:-1]; b=ii[:,1:]; s=(a>=0)&(b>=0)
        for u,v in zip(a[s],b[s]): add(u,v,gl)
        a=ii[:-1,:]; b=ii[1:,:]; s=(a>=0)&(b>=0)
        for u,v in zip(a[s],b[s]): add(u,v,gl)
    def cell(L,x,y):
        j=int(x/H); i=int(y/H)
        if 0<=i<X.shape[0] and 0<=j<X.shape[1]: return idx[L][i,j]
        return -1
    nv=0
    for v in G['vias']:
        if v['net']!=net: continue
        pres=[(L,cell(L,v['x'],v['y'])) for L in LAY]; pres=[q for q in pres if q[1]>=0]
        for (L1,c1),(L2,c2) in zip(pres,pres[1:]):
            R=RHO*(ZL[L2]-ZL[L1])*1e-3/(math.pi*v['d']*1e-3*TP); add(c1,c2,1/R)
        nv+=1
    # THT 焊盘：各层焊盘范围内的格子互连
    for p in G['pads']:
        if p['net']!=net or not p['hole']: continue
        c=p['g'].centroid; cs=[cell(L,c.x,c.y) for L in LAY]; cs=[q for q in cs if q>=0]
        for a,b in zip(cs,cs[1:]): add(a,b,1e3)
    # 端子：超级节点
    N0=n; inj=[]
    for k,(pads,I) in enumerate(terms):
        node=n; n+=1; cnt=0
        for key in pads:
            p=P[key]; g=p['g']
            for L in p['Ls']:
                m=shapely.contains_xy(g.buffer(0.05),X,Y)&masks[L]
                for c in idx[L][m]: add(node,c,1e2); cnt+=1
        inj.append((node,I,cnt))
    A=sp.csr_matrix((vals,(rows,cols)),shape=(n,n))
    b=np.zeros(n)
    for node,I,_ in inj: b[node]=I
    ref=inj[-1][0]
    keep=np.ones(n,bool); keep[ref]=False
    Ar=A[keep][:,keep]; br=b[keep]
    # 孤岛会让矩阵奇异：加极小对地电导
    Ar=Ar+sp.identity(Ar.shape[0])*1e-9
    V=np.zeros(n); V[keep]=spl.spsolve(Ar.tocsc(),br)
    res={'label':label,'net':net,'vias':nv,'terms':[(t[0],t[1],c) for t,(_,_,c) in zip(terms,inj)]}
    res['Vterm']=[V[node]*1e3 for node,_,_ in inj]
    # 电流密度 A/mm、功率
    out={}
    tot=0
    for L in LAY:
        ii=idx[L]; m=masks[L]
        if not m.any(): continue
        Vg=np.full(X.shape,np.nan); Vg[m]=V[ii[m]]
        gx=np.zeros(X.shape); gy=np.zeros(X.shape)
        d=(Vg[:,1:]-Vg[:,:-1]); d=np.nan_to_num(d); gx[:,1:]+=d/2; gx[:,:-1]+=d/2
        d=(Vg[1:,:]-Vg[:-1,:]); d=np.nan_to_num(d); gy[1:,:]+=d/2; gy[:-1,:]+=d/2
        J=np.hypot(gx,gy)/(H*1e-3)/RS/1000   # A/mm
        J[~m]=0
        pw=(J*1000)**2*RS*(H*1e-3)**2        # W per cell
        tot+=pw.sum()
        out[L]=J
    res['P']=tot; res['J']=out; res['X']=X; res['Y']=Y; res['masks']=masks
    return res
if __name__=='__main__':
    pass
