import json,math,sys,numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_flow
C=json.load(open(sys.argv[1])); D={c['r']:c for c in C}
NET=sys.argv[2]; side=int(sys.argv[3])   # 0 top,1 bottom
src=sys.argv[4].split(','); snk=sys.argv[5].split(',')
x0,x1,y0,y1=[float(v) for v in sys.argv[6].split(',')]
h=0.15; CL=0.3
nx=int((x1-x0)/h); ny=int((y1-y0)/h)
xs=x0+(np.arange(nx)+0.5)*h; ys=y0+(np.arange(ny)+0.5)*h
X,Y=np.meshgrid(xs,ys)
free=np.ones((ny,nx),bool); S_=np.zeros_like(free); T_=np.zeros_like(free)
def rect(p,inf):
    return (X>=p[0]-inf)&(X<=p[0]+p[2]+inf)&(Y>=p[1]-inf)&(Y<=p[1]+p[3]+inf)
for c in C:
    for p in c['p']:
        onl = p[6] or (c['b']==side)
        key=c['r']+'.'+p[5]
        if key in src: S_|=rect(p,0); continue
        if key in snk: T_|=rect(p,0); continue   # 另一层的焊盘按投影（打孔换层）
        if not onl: continue
        if p[4]==NET: continue
        free&=~rect(p,CL)
for hx,hy in [(34.5,91.5),(64,52.5),(100,88),(3.5,60.5)]:
    free&=~(((X-hx)**2+(Y-hy)**2)<(2.7+CL)**2)
free&=(X>0.5)&(X<127.5)&(Y>0.5)&(Y<94.5)
free|=S_|T_
idx=-np.ones((ny,nx),int); cells=np.argwhere(free); idx[free]=np.arange(len(cells))
n=len(cells); s=2*n; t=2*n+1; BIG=10**6
rows=[];cols=[];cap=[]
for k,(i,j) in enumerate(cells):
    rows.append(2*k);cols.append(2*k+1);cap.append(BIG if (S_[i,j] or T_[i,j]) else 1)
    for di,dj in ((0,1),(1,0),(1,1),(1,-1)):
        a,b=i+di,j+dj
        if 0<=a<ny and 0<=b<nx and idx[a,b]>=0:
            m=idx[a,b]; rows+= [2*k+1,2*m+1]; cols+=[2*m,2*k]; cap+=[BIG,BIG]
    if S_[i,j]: rows.append(s);cols.append(2*k);cap.append(BIG)
    if T_[i,j]: rows.append(2*k+1);cols.append(t);cap.append(BIG)
G=csr_matrix((np.array(cap,dtype=np.int32),(rows,cols)),shape=(2*n+2,2*n+2))
r=maximum_flow(G,s,t)
print('min cut cells',r.flow_value,'≈ width mm',round(r.flow_value*h,2))
# find cut: residual reachability
F=r.flow.tocsr(); R=(G-F); R.data=np.maximum(R.data,0); R.eliminate_zeros()
from scipy.sparse.csgraph import breadth_first_order
reach=set(breadth_first_order(R,s,directed=True,return_predecessors=False).tolist())
cut=[cells[k] for k in range(n) if (2*k in reach) and (2*k+1 not in reach)]
pts=[(round(x0+(j+0.5)*h,2),round(y0+(i+0.5)*h,2)) for i,j in cut]
if pts:
    xs_=[p[0] for p in pts]; ys_=[p[1] for p in pts]
    print('cut region x',min(xs_),max(xs_),'y',min(ys_),max(ys_),'n',len(pts))
json.dump({'pts':pts,'free':free.tolist() if False else None},open(sys.argv[7],'w'))
