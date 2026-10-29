import pickle,collections,math
import numpy as np
from shapely.geometry import box,Point
from shapely import vectorized
G=pickle.load(open('z41/geo.pkl','rb')); CU2=pickle.load(open('z41/cu2.pkl','rb'))
h=0.2
xs=np.arange(0,128,h)+h/2; ys=np.arange(0,95,h)+h/2
X,Y=np.meshgrid(xs,ys)
L={}
for lay in (1,15,16,2):
    g=CU2.get((lay,'PGND'))
    L[lay]=vectorized.contains(g,X,Y) if g is not None else np.zeros(X.shape,bool)
vias=[v for v in G['vias'] if v['net']=='PGND']
# multi-layer BFS (Dijkstra with unit steps); via hop cost = 1.8 mm (board thickness equiv)
import heapq
idx=lambda x,y:(int(y/h),int(x/h))
dist={}
start=[]
bridge=box(78.59,50.37,79.58,53.22)
for (i,j) in zip(*np.where(vectorized.contains(bridge.buffer(0.3),X,Y) & L[1])): start.append((1,i,j))
pq=[(0.0,s) for s in start]
for s in start: dist[s]=0
vmap=collections.defaultdict(list)
for v in vias:
    i,j=idx(v['x'],v['y'])
    for lay in (1,15,16,2): vmap[(i,j)].append(lay)
nb=[(1,0,h),(-1,0,h),(0,1,h),(0,-1,h),(1,1,h*1.414),(1,-1,h*1.414),(-1,1,h*1.414),(-1,-1,h*1.414)]
target=box(73.0,62.3,77.0,66.0)  # Q8 source region
best=None
while pq:
    d,(lay,i,j)=heapq.heappop(pq)
    if dist.get((lay,i,j),1e9)<d: continue
    if target.contains(Point(xs[j],ys[i])) and lay in(1,15,2): best=(d,lay); break
    for di,dj,c in nb:
        ni,nj=i+di,j+dj
        if 0<=ni<X.shape[0] and 0<=nj<X.shape[1] and L[lay][ni,nj]:
            nd=d+c
            if nd<dist.get((lay,ni,nj),1e9): dist[(lay,ni,nj)]=nd; heapq.heappush(pq,(nd,(lay,ni,nj)))
    if (i,j) in vmap:
        for l2 in (1,15,16,2):
            if l2!=lay and L[l2][i,j]:
                nd=d+1.8
                if nd<dist.get((l2,i,j),1e9): dist[(l2,i,j)]=nd; heapq.heappush(pq,(nd,(l2,i,j)))
print('shortest PGND path bridge -> Q8 source (mm, incl. 1.8 per layer change):',best)
