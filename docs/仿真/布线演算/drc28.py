import json, math, itertools
C=json.load(open('lay28.json'))
def shape(c,p):
    x,y,w,h,net,num,th,ly=p
    return dict(ref=c['r'],num=num,net=net,x0=x,y0=y,x1=x+w,y1=y+h,round=bool(th) and abs(w-h)<0.05,layers={0,1} if th else ({1} if c['b'] else {0}))
exec(open('drc.py').read().split('def gap')[1].join(['def gap','']) if False else '')
src=open('drc.py').read(); g0=src.index('def gap'); g1=src.index('for board')
exec(src[g0:g1])
S=[shape(c,p) for c in C for p in c['p']]
bad=[]
for a,b in itertools.combinations(S,2):
    if a['ref']==b['ref'] or not (a['layers']&b['layers']): continue
    if a['net'] and a['net']==b['net']: continue
    d=gap(a,b)
    if d<0.25: bad.append((round(d,2),f"{a['ref']}.{a['num']}({a['net']})",f"{b['ref']}.{b['num']}({b['net']})",'顶' if a['layers']&b['layers']=={0} else ('底' if a['layers']&b['layers']=={1} else '两层')))
bad.sort(); print('pad<0.25',len(bad))
for x in bad: print(' ',x)
# body overlaps same side (smd) 
print('off board:',[ (c['r'],c['x'],c['y']) for c in C if not (0<=c['x']<=128 and 0<=c['y']<=95)])
print('nettie candidates:',[c['r'] for c in C if {p[4] for p in c['p']}>={'GND','PGND'}])
