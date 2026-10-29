import pickle,collections,heapq,math
import numpy as np
from shapely.geometry import box,Point
from shapely import contains_xy
G=pickle.load(open('z41/geo.pkl','rb')); O=pickle.load(open('z41/cu2.pkl','rb')); N=pickle.load(open('z41/cu_new.pkl','rb'))
B=box(66.0,59.2,69.2,62.9)
h=0.2; xs=np.arange(0,128,h)+h/2; ys=np.arange(0,95,h)+h/2; X,Y=np.meshgrid(xs,ys)
vias=[v for v in G['vias'] if v['net']=='PGND']
def grids(cu,extra):
    L={}
    for lay in (1,15,16,2):
        g=cu.get((lay,'PGND'))
        if lay==1: g=g.difference(B).union(extra) if extra is not None else g
        L[lay]=contains_xy(g,X,Y)
    return L
vm=set()
for v in vias: vm.add((int(v['y']/h),int(v['x']/h)))
nb=[(1,0,h),(-1,0,h),(0,1,h),(0,-1,h),(1,1,h*1.414),(1,-1,h*1.414),(-1,1,h*1.414),(-1,-1,h*1.414)]
def bfs(L,src,targets):
    dist={}; pq=[]
    for (i,j) in zip(*np.where(contains_xy(src.buffer(0.3),X,Y) & L[1])): dist[(1,i,j)]=0; pq.append((0,(1,i,j)))
    heapq.heapify(pq); res={}
    while pq and len(res)<len(targets):
        d,(lay,i,j)=heapq.heappop(pq)
        if dist.get((lay,i,j),1e9)<d: continue
        for k,t in targets.items():
            if k not in res and t.contains(Point(xs[j],ys[i])): res[k]=round(d,1)
        for di,dj,c in nb:
            ni,nj=i+di,j+dj
            if 0<=ni<X.shape[0] and 0<=nj<X.shape[1] and L[lay][ni,nj] and d+c<dist.get((lay,ni,nj),1e9):
                dist[(lay,ni,nj)]=d+c; heapq.heappush(pq,(d+c,(lay,ni,nj)))
        if (i,j) in vm:
            for l2 in (1,15,16,2):
                if l2!=lay and L[l2][i,j] and d+1.8<dist.get((l2,i,j),1e9): dist[(l2,i,j)]=d+1.8; heapq.heappush(pq,(d+1.8,(l2,i,j)))
    return res
tg={'Q9':box(62.6,62.3,66.4,66.0),'Q8':box(73.1,62.3,76.9,66.0),'Q10':box(83.6,62.3,87.4,66.0)}
EP=(79.0,55.0)
cands={'A 现状（U9 北侧）':(O,box(78.59,50.37,79.58,53.22),None),
       'B 优化版（U9 西南）':(N,B,B),
       'C 理想（U9 正南）':(N,box(76.0,60.6,80.0,62.9),box(76.0,60.6,80.0,62.9)),
       'D U9 东南':(N,box(87.4,59.6,89.4,62.9),box(87.4,59.6,89.4,62.9)),
       'E 远处（输入区边上）':(N,box(61.5,54.0,64.5,57.5),box(61.5,54.0,64.5,57.5))}
for name,(cu,br,extra) in cands.items():
    L=grids(cu,extra) if extra is not None else grids(cu,None)
    r=bfs(L,br,tg)
    c=br.centroid; g=math.hypot(c.x-EP[0],c.y-EP[1])
    print(name,'PGND 段（桥→各下管源极）',r,' GND 段（桥→U9 裸焊盘，直线）',round(g,1))
