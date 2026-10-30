import pickle,sys
from shapely.geometry import box,Point
G=pickle.load(open(sys.argv[1],'rb'))
C=G['C']
def bb(c): b=c['bb']; return box(b[0],b[1],b[0]+max(b[2],.05),b[1]+max(b[3],.05))
print('== 本体重叠（同面，>0.05 mm²）')
for i,a in enumerate(C):
    for c in C[i+1:]:
        if a['b']!=c['b']: continue
        x=bb(a).intersection(bb(c)).area
        if x>0.05: print('  ',a['r'],c['r'],'底' if a['b'] else '顶',round(x,2))
print('== 插件焊盘（底面焊点）1.0 mm 内的异网贴片焊盘')
tht=[p for p in G['pads'] if p['hole'] and p['net']]
import math
for t in tht:
    w=t['g'].bounds; cx,cy=(w[0]+w[2])/2,(w[1]+w[3])/2; R=(w[2]-w[0])/2
    circ=Point(cx,cy).buffer(R)
    for p in G['pads']:
        if p['hole'] or p['r']==t['r']: continue
        d=circ.distance(p['g'])
        if d<1.0:
            side='底' if 2 in p['Ls'] else '顶'
            print('  ',t['r']+'.'+t['n'],t['net'],'Ø%.2f'%(2*R),'<->',p['r']+'.'+p['n'],p['net'],side,'%.2f mm'%d,'同网重叠' if p['net']==t['net'] and d==0 else '')
