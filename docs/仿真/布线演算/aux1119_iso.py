import pickle,json,sys
from shapely.geometry import Point
from shapely.ops import unary_union, nearest_points
G,L=sys.argv[1],pickle.load(open(sys.argv[2],'rb')); M=0.0254
fp=json.load(open(G+'/FlyingProbeTesting.json')); F=fp['pins']['fields']; pins=[dict(zip(F,r)) for r in fp['pins']['rows']]
SEC={'AUX_GND','P15_RAW','N15_RAW','GALVO_P15','GALVO_N15','CARD_P15','$1N765','$1N768','$1N777','NET_3','NET_4'}
for k in (1,2):
    side='T' if k==1 else 'B'
    pri=[];sec=[];unk=[]
    for q in L[k].geoms:
        nets={p['NET_NAME'] for p in pins if (p['LAYER']==side or p['HOLE_SIZE']) and q.intersects(Point(p['PIN_X']*M,p['PIN_Y']*M))}
        if not nets: unk.append(q); continue
        (sec if nets<=SEC else pri if not (nets&SEC) else unk).append(q)
    P=unary_union(pri); Sx=unary_union(sec)
    d=P.distance(Sx); a,b=nearest_points(P,Sx)
    print('层',k,'一次侧块',len(pri),'二次侧块',len(sec),'未归类块',len(unk),'最小间距 %.2f mm 于 (%.1f,%.1f)-(%.1f,%.1f)'%(d,a.x,a.y,b.x,b.y))
    for q in unk:
        c=q.representative_point(); print('   未归类 面积%.1f (%.1f,%.1f) 距一次侧%.2f 距二次侧%.2f'%(q.area,c.x,c.y,q.distance(P),q.distance(Sx)))
