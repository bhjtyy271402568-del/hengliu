import sys,pickle,numpy as np
sys.argv=[sys.argv[0],sys.argv[1]]+sys.argv[2:]
exec(open(__file__.replace('review50_run_cur.py','review50_cur.py')).read())
S=lambda r,ns:[(r,str(n)) for n in ns]
D=0.8
cases=[
 ('VCC_BAT 输入 CN3.2→Q1/Q2',"VCC_BAT",[([('CN3','2')],40),(S('Q1',[3])+S('Q2',[3]),-40)]),
 ('DCBUS Q1/Q2→R42',"DCBUS",[([('Q1','4'),('Q2','4')],40),([('R42','1')],-40)]),
 ('LT_VIN R42→上管',"LT_VIN",[([('R42','2')],40),([('Q5','8')],-40/3),([('Q6','8')],-40/3),([('Q7','8')],-40/3)]),
 ('LT_SW 管→L8（D=0.8）',"LT_SW",[(S('Q5',[1,2,3]),40*D/3),(S('Q6',[1,2,3]),40*D/3),(S('Q7',[1,2,3]),40*D/3),([('Q8','5')],40*(1-D)/3),([('Q9','5')],40*(1-D)/3),([('Q10','5')],40*(1-D)/3),([('L8','1')],-40)]),
 ('LT_SW 管→L8（D=0.45）',"LT_SW",[(S('Q5',[1,2,3]),40*.45/3),(S('Q6',[1,2,3]),40*.45/3),(S('Q7',[1,2,3]),40*.45/3),([('Q8','5')],40*.55/3),([('Q9','5')],40*.55/3),([('Q10','5')],40*.55/3),([('L8','1')],-40)]),
 ('LT_SHUNT_P L8→R56',"LT_SHUNT_P",[([('L8','2')],40),([('R56','1')],-40)]),
 ('VCC_OUT R56→CN14',"VCC_OUT",[([('R56','2')],40),([('CN14','2')],-40)]),
 ('PGND CN14→下管/Q4（D=0.8）',"PGND",[([('CN14','1')],40),(S('Q8',[1,2,3]),-40*(1-D)/3),(S('Q9',[1,2,3]),-40*(1-D)/3),(S('Q10',[1,2,3]),-40*(1-D)/3),(S('Q4',[1,2,3]),-40*D)]),
 ('PGND CN14→下管/Q4（D=0.45）',"PGND",[([('CN14','1')],40),(S('Q8',[1,2,3]),-40*.55/3),(S('Q9',[1,2,3]),-40*.55/3),(S('Q10',[1,2,3]),-40*.55/3),(S('Q4',[1,2,3]),-40*.45)]),
 ('GND_BAT Q4→CN3.1',"GND_BAT",[([('Q4','5')],40),([('CN3','1')],-40)]),
]
allres=[]
for label,net,terms in cases:
    r=solve(net,terms,label)
    J=r['J']
    def top(L,k=3):
        j=J[L]; fl=np.argsort(j.ravel())[::-1][:400]
        pts=[];
        for f in fl:
            i,jj=divmod(f,j.shape[1]); x,y=r['X'][i,jj],r['Y'][i,jj]
            if all(abs(x-a)+abs(y-b)>3 for a,b,_ in pts): pts.append((round(x,1),round(y,1),round(j[i,jj],1)))
            if len(pts)>=k: break
        return pts
    s={L:(round(float(np.percentile(J[L][r['masks'][L]],99.5)),1) if r['masks'][L].any() else 0) for L in J}
    print(f"{label}: 铜损 {r['P']:.2f} W，端子电压(mV) {[round(v,1) for v in r['Vterm']]}，过孔 {r['vias']}")
    for L in J:
        if r['masks'][L].any(): print('    L',L,'99.5%分位 A/mm',s[L],'最大点',top(L))
    allres.append((label,{L:r['J'][L] for L in J},r['P']))
pickle.dump(dict(res=allres,X=r['X'],Y=r['Y']),open(sys.argv[2] if len(sys.argv)>2 else 'z50/cur.pkl','wb'))
