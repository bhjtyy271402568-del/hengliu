import sys,collections
sys.path.insert(0,'/home/user/hengliu/tools'); import epro_snapshot as E
docs=E.load(sys.argv[1]); b=[x for x in E.boards(docs) if '布局草案' in x['title']][0]
S=E.sch_nets(docs,b['pages']); P=E.pad_nets(docs,b['pcbs'][0])
print('sch pins',len(S),'pcb pads',len(P))
onlyS=sorted(set(S)-set(P),key=E.natural); onlyP=sorted(set(P)-set(S),key=E.natural)
print('只在原理图:',onlyS[:60]); print('只在PCB:',onlyP[:60])
common=set(S)&set(P)
# partition compare: for each sch net, set of pads; map to pcb nets
def groups(N):
    g=collections.defaultdict(set)
    for k in common:
        g[N[k] or ('',k)].add(k)
    return g
gS=groups(S); gP=groups(P)
pin2gP={k:(P[k] or ('',k)) for k in common}
bad=0
for n,pins in sorted(gS.items(),key=lambda kv:str(kv[0])):
    pn=collections.Counter(pin2gP[p] for p in pins)
    if len(pn)>1:
        bad+=1; print('原理图网络',n if isinstance(n,str) else '未连接','在PCB被拆成',[(str(k)[:30],v,[p for p in pins if pin2gP[p]==k][:4]) for k,v in pn.items()])
pin2gS={k:(S[k] or ('',k)) for k in common}
for n,pins in sorted(gP.items(),key=lambda kv:str(kv[0])):
    sn=collections.Counter(pin2gS[p] for p in pins)
    if len(sn)>1:
        bad+=1; print('PCB网络',n if isinstance(n,str) else '未连接','合并了原理图',[(str(k)[:30],v,[p for p in pins if pin2gS[p]==k][:4]) for k,v in sn.items()])
print('差异',bad)
