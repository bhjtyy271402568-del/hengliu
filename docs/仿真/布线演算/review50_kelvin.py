import pickle,math,sys
from shapely.geometry import LineString,Point,Polygon
from shapely.ops import linemerge,unary_union
G=pickle.load(open(sys.argv[1] if len(sys.argv)>1 else 'z50/geo.pkl','rb')); CU=G['CU']
def thin(net,maxw=0.45):
    return [t for t in G['tracks'] if t['net']==net and t['w']<=maxw]
for net in ('LT_SHUNT_P','VCC_OUT','DCBUS','LT_VIN'):
    ts=thin(net)
    print('==',net,'thin tracks',len(ts),'len %.1f'%sum(math.hypot(t['x1']-t['x0'],t['y1']-t['y0']) for t in ts))
    for t in ts: print('   L%d (%.2f,%.2f)-(%.2f,%.2f) w%.2f'%(t['L'],t['x0'],t['y0'],t['x1'],t['y1'],t['w']))
