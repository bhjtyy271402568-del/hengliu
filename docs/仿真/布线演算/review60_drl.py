"""读嘉立创钻孔文件（含槽孔），坐标减板原点。"""
import re
OX,OY=-214.198142,42.261000
def holes(path):
    tools={};cur=None;out=[]
    for l in open(path):
        l=l.strip()
        m=re.match(r'T(\d+)C([\d.]+)',l)
        if m: tools[m.group(1)]=float(m.group(2)); continue
        m=re.match(r'T(\d+)$',l)
        if m: cur=m.group(1); continue
        m=re.match(r'X(-?[\d.]+)Y(-?[\d.]+)$',l)
        if m and cur: out.append((float(m.group(1))-OX,float(m.group(2))-OY,tools[cur]))
        m=re.match(r'X(-?[\d.]+)Y(-?[\d.]+)G85X(-?[\d.]+)Y(-?[\d.]+)',l)
        if m and cur: out.append((float(m.group(1))-OX,float(m.group(2))-OY,tools[cur],float(m.group(3))-OX,float(m.group(4))-OY))
    return out
