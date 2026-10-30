"""把 .epro2 里恒流源板（PCB 9a0fbfd22df79247）的实际铺铜填充导出成 pours.json。
用法：python3 -I review50_poured.py 工程.epro2 pours.json"""
import json,sys,zipfile
z=zipfile.ZipFile(sys.argv[1]); t=z.read([n for n in z.namelist() if n.endswith('.epru')][0]).decode().splitlines()
cur=None; pours={}; pd={}
for line in t:
    i=line.find('||')
    if i<0: continue
    h=json.loads(line[:i]); b=line[i+2:]; b=b[:-1] if b.endswith('|') else b
    if h.get('type')=='DOCHEAD': cur=json.loads(b).get('uuid'); continue
    if cur!='9a0fbfd22df79247': continue
    if h['type']=='POUR' and b: pours[h['id']]=json.loads(b)
    if h['type']=='POURED' and b: pd[json.loads(h['id'])[1]]=json.loads(b)
out=[dict(id=k,net=p['netName'],layer=p['layerId'],name=p['name'],order=p['order'],
          region={'pourFills':[{'path':{'complexPolygon':f['path']}} for f in pd.get(k,{}).get('pourFill',[]) if f.get('fill',True)]})
     for k,p in pours.items()]
json.dump(out,open(sys.argv[2],'w')); print(len(out),'pours')
