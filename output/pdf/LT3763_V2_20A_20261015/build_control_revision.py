"""Deterministic vector reference drawing, not a native EDA project/netlist."""
from pathlib import Path
import hashlib
import json
import math
from html import escape

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib.colors import HexColor
from pypdf import PdfReader
import pypdfium2 as pdfium

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
NAME = 'LT3763_V2_20A_控制原理图_修订B_20261015'
W, H = 2400, 1697
BLACK, GRAY, RED, BLUE = '#24313E', '#627282', '#C34234', '#205C85'
LIGHT, BORDER = '#F3F6F9', '#D6DFE7'
pdfmetrics.registerFont(TTFont('CN', r'C:\Windows\Fonts\simhei.ttf'))
PAGE = landscape(A3)
SCALE = PAGE[0] / W
PDF = OUT / (NAME + '.pdf')
cv = canvas.Canvas(str(PDF), pagesize=PAGE, pageCompression=1)
cv.setTitle('LT3763 V2 固定 20 A 控制原理图 - 修订 B')
cv.setAuthor('工程参考图 / 2026-10-15')


class Sheet:
    def __init__(self, index):
        self.index = index
        self.svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>']
        self.text_bounds = []
        cv.saveState()
        cv.scale(SCALE, SCALE)

    def line(self, x1, y1, x2, y2, color=BLACK, width=2.2, dash=False):
        cv.setStrokeColor(HexColor(color)); cv.setLineWidth(width)
        cv.setDash([7, 5] if dash else [])
        cv.line(x1, H-y1, x2, H-y2)
        da = ' stroke-dasharray="7 5"' if dash else ''
        self.svg.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="{width}"{da}/>')

    def poly(self, pts, color=BLACK, width=2.2, fill=None, closed=False):
        p = cv.beginPath(); p.moveTo(pts[0][0], H-pts[0][1])
        for x,y in pts[1:]: p.lineTo(x,H-y)
        if closed: p.close()
        cv.setDash([]); cv.setStrokeColor(HexColor(color)); cv.setLineWidth(width)
        if fill: cv.setFillColor(HexColor(fill))
        cv.drawPath(p,stroke=1,fill=int(bool(fill)))
        tag = 'polygon' if closed else 'polyline'
        val = ' '.join(f'{x},{y}' for x,y in pts)
        self.svg.append(f'<{tag} points="{val}" fill="{fill or "none"}" stroke="{color}" stroke-width="{width}"/>')

    def rect(self,x,y,w,h,color=BORDER,fill=None,width=1.5):
        self.poly([(x,y),(x+w,y),(x+w,y+h),(x,y+h)],color,width,fill,True)

    def dot(self,x,y,color=BLACK,r=4):
        cv.setFillColor(HexColor(color)); cv.circle(x,H-y,r,stroke=0,fill=1)
        self.svg.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}"/>')

    def text(self,x,y,s,size=21,color=BLACK,anchor='start'):
        tw=pdfmetrics.stringWidth(s,'CN',size)
        tx=x-(tw/2 if anchor=='middle' else tw if anchor=='end' else 0)
        assert tx >= 20 and tx+tw <= W-20, (s,tx,tw)
        assert 15 <= y-size and y <= H-15, (s,y)
        self.text_bounds.append((tx,y-size,tx+tw,y,s))
        cv.setFont('CN',size); cv.setFillColor(HexColor(color)); cv.drawString(tx,H-y,s)
        self.svg.append(f'<text x="{x}" y="{y}" font-family="SimHei,Microsoft YaHei,sans-serif" font-size="{size}" fill="{color}" text-anchor="{anchor}">{escape(s)}</text>')

    def multi(self,x,y,lines,size=20,color=BLACK,step=29):
        for i,s in enumerate(lines): self.text(x,y+i*step,s,size,color)

    def ground(self,x,y,label='GND'):
        self.line(x,y,x,y+12)
        for k,half in enumerate([13,9,4]): self.line(x-half,y+12+k*6,x+half,y+12+k*6)
        if label: self.text(x+20,y+23,label,17,GRAY)

    def rail(self,x,y,label):
        self.line(x-10,y,x+10,y); self.text(x,y-12,label,19,BLACK,'middle')

    def resistor(self,x1,y1,x2,y2,color=BLACK):
        dx,dy=x2-x1,y2-y1; ll=math.hypot(dx,dy); ux,uy=dx/ll,dy/ll; px,py=-uy,ux
        a=min(18,ll*0.22); pts=[(x1,y1),(x1+ux*a,y1+uy*a)]
        for k in range(8):
            u=a+(ll-2*a)*(k+0.5)/8; v=7 if k%2==0 else -7
            pts.append((x1+ux*u+px*v,y1+uy*u+py*v))
        pts += [(x2-ux*a,y2-uy*a),(x2,y2)]; self.poly(pts,color)

    def cap(self,x,y1,y2,label,color=BLACK,side='right'):
        ym=(y1+y2)/2
        self.line(x,y1,x,ym-5,color); self.line(x,y2,x,ym+5,color)
        self.line(x-12,ym-5,x+12,ym-5,color); self.line(x-12,ym+5,x+12,ym+5,color)
        self.multi(x+20 if side=='right' else x-105,ym-4,label.split('|'),18,color,25)

    def diode(self,x,y1,y2,up=False,color=RED,led=False):
        ym=(y1+y2)/2; top,bottom=ym-11,ym+11
        self.line(x,y1,x,top,color); self.line(x,bottom,x,y2,color)
        if up:
            self.poly([(x-11,bottom),(x+11,bottom),(x,top)],color,2,None,True)
            self.line(x-13,top,x+13,top,color)
        else:
            self.poly([(x-11,top),(x+11,top),(x,bottom)],color,2,None,True)
            self.line(x-13,bottom,x+13,bottom,color)
        if led:
            for d in [0,13]:
                self.line(x+17,ym-5+d,x+32,ym-16+d,color,1.6)
                self.poly([(x+24,ym-17+d),(x+32,ym-16+d),(x+29,ym-8+d)],color,1.6)

    def mos(self,gx,gy,dx,sy,name,label_side='right'):
        # Gate at (gx,gy); drain terminal (dx,gy-65); source terminal (dx,sy).
        self.line(gx,gy,dx-27,gy,RED); self.line(dx-27,gy-23,dx-27,gy+23,RED)
        for yy in [gy-24,gy-5,gy+14]: self.line(dx-16,yy,dx-16,yy+10,RED)
        self.line(dx,gy-65,dx,gy-20,RED); self.line(dx,gy-20,dx-16,gy-20,RED)
        self.line(dx-16,gy+20,dx,gy+20,RED); self.line(dx,gy+20,dx,sy,RED)
        self.line(dx-9,gy,dx,gy,RED); self.line(dx,gy,dx,gy+20,RED)
        self.poly([(dx-4,gy-5),(dx-11,gy),(dx-4,gy+5)],RED,1.6)
        xx=dx+18 if label_side=='right' else gx-105
        if name: self.multi(xx,gy-7,[name,'2N7002'],18,RED,24)

    def section(self,x,y,num,title,width):
        self.text(x,y,f'{num:02d}  {title}',25,BLUE)
        self.line(x,y+13,x+width,y+13,BORDER,1.5)

    def end(self,filename):
        self.text(50,1660,'LT3763 V2  |  固定 20 A  |  修订 B  |  2026-10-15',18,GRAY)
        self.text(2350,1660,f'{self.index} / 2  ·  工程修改参考，非原生 EDA 文件',18,GRAY,'end')
        self.svg.append('</svg>')
        (OUT/filename).write_text('\n'.join(self.svg),encoding='utf-8')
        cv.restoreState(); cv.showPage()


s=Sheet(1)
s.text(50,64,'LT3763 V2 · 20 A 纯硬件恒流控制原理图',36)
s.text(50,108,'外部 5 V 持续有效即运行，撤销即停止开关；功率级沿用 V1。红色：新增、改值或改接。',22,GRAY)
s.text(2350,64,'修订 B',26,RED,'end')
s.line(50,135,2350,135,BLUE,2)

# 01 current command
s.section(60,190,1,'电流设定 CTRL1',330)
s.rail(130,255,'VREF'); s.line(130,255,130,280)
s.resistor(130,280,130,355,RED)
s.multi(155,302,['R2  2.94 kΩ','0.1%，改接 VREF'],18,RED,25)
s.line(130,355,130,375); s.dot(130,375)
s.text(83,369,'CTRL1',18,BLACK,'end')
s.resistor(130,375,130,480)
s.multi(155,431,['R19  8.2 kΩ','0.1%'],18,BLACK,25)
s.line(130,480,130,505); s.ground(130,505,'AGND')
s.line(130,375,325,375); s.cap(325,375,505,'C41|100 nF'); s.ground(325,505,'')
s.multi(60,574,['CTRL1 ≈ 1.472 V；典型约 20 A','R1 保持 2.5 mΩ，20 A 时约 50 mV','固定阻值不等于精确 20 A，装板校准'],18,GRAY,27)

# 02 thermal derating
s.section(435,190,2,'温度降额 CTRL2',330)
s.rail(505,255,'VREF'); s.line(505,255,505,280)
s.resistor(505,280,505,355,RED)
s.multi(530,302,['R57  8.2 kΩ','V1 实装 12 kΩ → 8.2 kΩ'],18,RED,25)
s.line(505,355,505,375); s.dot(505,375); s.text(458,369,'CTRL2',18,BLACK,'end')
s.resistor(505,375,505,480)
s.line(490,458,520,400,BLACK,1.6)
s.multi(530,431,['R56  NTC','100 kΩ / B3950'],18,BLACK,25)
s.line(505,480,505,505); s.ground(505,505,'AGND')
s.line(505,375,710,375); s.cap(710,375,505,'C54|100 nF'); s.ground(710,505,'')
s.multi(435,574,['CTRL2 < CTRL1 时降额','约 62 ℃ 起降，指 NTC 自身温度','R58 保持不装；不是 MOS 结温阈值'],18,GRAY,27)

# 03 SS and reference
s.section(60,719,3,'软启动 / 基准去耦',330)
s.rail(130,795,'SS'); s.cap(130,795,1005,'C72|100 nF',RED); s.ground(130,1005,'AGND')
s.rail(320,795,'VREF'); s.cap(320,795,1005,'C2|2.2 μF'); s.ground(320,1005,'')
s.multi(60,1090,['C72：330 nF → 100 nF','SS 清零后首次启动约 13 ms','普通 PWM 关断不重置 SS','后续触发不保证再次慢升'],18,RED,28)

# 04 UVLO
s.section(435,719,4,'欠压门限 / 使能',330)
s.rail(505,795,'DCBUS'); s.line(505,795,505,815)
s.resistor(505,815,505,890,RED); s.text(530,859,'R52  150 kΩ',18,RED)
s.line(505,890,505,915); s.dot(505,915); s.text(530,907,'EN_UVLO',18)
s.resistor(505,915,505,1000,RED); s.text(530,968,'R53  10 kΩ',18,RED)
s.line(505,1000,505,1025); s.ground(505,1025)
s.line(505,915,710,915); s.cap(710,915,1025,'C52|100 nF'); s.ground(710,1025,'')
s.multi(435,1090,['典型开启：28.0 V；关闭：24.3 V','开启计算包含 EN 的 5 μA 下拉','R52/R53 是改值，不再标“不变”'],18,GRAY,28)

# U1 control pin reference block
s.text(1000,267,'U1  LT3763EFE',29,BLACK,'middle')
s.rect(875,300,250,730,BLACK,None,2.4)
left=[('VREF',5,355),('FBIN',10,410),('CTRL1',14,500),('CTRL2',13,580),('SS',15,660),('EN/UVLO',4,740)]
for nm,pn,y in left:
    s.line(815,y,875,y); s.text(856,y-10,str(pn),17,GRAY,'end'); s.text(888,y+7,nm,19)
for nm,pn,y,ext in [('INTVCC',2,355,'INTVCC'),('PWM',22,465,'PWM'),('PWM_OUT',24,555,'NC'),('FAULT',9,645,'FAULT'),('ISMON',19,735,'CN12'),('IVINMON',8,825,'CN17'),('FB',11,915,'FB')]:
    s.line(1125,y,1170,y); s.text(1140,y-10,str(pn),17,GRAY); s.text(1112,y+7,nm,18,BLACK,'end')
    s.text(1180,y+7,ext,18)
    if ext=='NC': s.line(1165,y-5,1175,y+5); s.line(1165,y+5,1175,y-5)
s.line(815,355,815,410); s.dot(815,355); s.text(805,345,'VREF',18,BLACK,'end')
for nm,pn,y in left[2:]: s.text(805,y+7,'EN_UVLO' if nm=='EN/UVLO' else nm,17,BLACK,'end')
s.line(1000,1030,1000,1060); s.ground(1000,1060,'')
s.multi(815,1120,['12 脚 AGND；23/28 脚 GND','29 脚 EP 按原设计接地','21 脚 SYNC 不用时接地','VIN、TG、BG、SW、BOOST、','SENSE±、IVINP/N、VC、RT','及其外围均保留 V1 连接'],18,GRAY,27)

# 05 optocoupler and PWM gate
s.section(1300,190,5,'隔离输入 → PWM 硬件启停',1040)
s.text(1300,238,'5 V 输入；光耦反相 + Q13 反相。WGND 与板内 GND 不直接连接。',19,GRAY)
s.rect(1310,345,75,235,BLACK,None,2)
s.multi(1326,442,['U9','输入'],18,BLACK,28)
s.text(1300,320,'外部 +5 V',19); s.text(1300,618,'外部 WGND',19)
s.text(1393,378,'1',16,GRAY); s.text(1393,563,'2',16,GRAY)
s.line(1385,385,1440,385)
# NC external interlock via CN20; old CN19 is already PGND test point.
s.dot(1440,385,RED,4); s.dot(1490,385,RED,4)
s.line(1440,385,1490,385,RED); s.line(1460,376,1460,361,RED)
s.line(1490,385,1530,385)
s.multi(1410,294,['CN20 外部联锁（常闭）','断开撤销使能；闭合可自动重启'],18,RED,27)
s.resistor(1530,385,1615,385)
s.text(1570,357,'R18  1 kΩ',18,BLACK,'middle')
s.line(1615,385,1740,385); s.dot(1650,385)
s.line(1385,565,1740,565); s.dot(1650,565)
s.diode(1650,385,565,up=True)
s.multi(1515,467,['D13  1N4148','K → U8-1','A → U8-3'],17,RED,25)
s.text(1669,420,'K',16,RED); s.text(1669,548,'A',16,RED)
s.rect(1740,345,180,250,BLACK,None,2)
s.text(1830,437,'U8',23,BLACK,'middle'); s.text(1830,475,'TLP2761',21,BLACK,'middle')
s.text(1830,535,'LED 亮 → VO 低',16,GRAY,'middle')
for x,y,nm,pn,side in [(1740,385,'A',1,'L'),(1740,565,'K',3,'L'),(1920,385,'VDD',6,'R'),(1920,480,'VO',5,'R'),(1920,565,'GND',4,'R')]:
    if side=='L': s.text(x+12,y+6,nm,18); s.text(x-9,y-10,str(pn),16,GRAY,'end')
    else: s.text(x-12,y+6,nm,18,BLACK,'end'); s.text(x+9,y-10,str(pn),16,GRAY)
s.line(1920,385,1955,385); s.line(1955,385,1955,285,RED)
s.line(1955,285,2300,285,RED); s.text(2300,267,'INTVCC ≈ 5 V',20,BLACK,'end')
s.dot(1955,285,RED); s.dot(2115,285,RED); s.dot(2220,285,RED)
s.line(1920,565,1955,565); s.ground(1955,565)
s.line(1920,480,1975,480); s.resistor(1975,480,2055,480)
s.text(2015,455,'R55 220 Ω',18,BLACK,'middle')
s.line(2055,480,2115,480); s.dot(2115,480)
s.resistor(2115,285,2115,410,RED); s.line(2115,410,2115,480,RED)
s.multi(1995,330,['R72 100 kΩ','默认关断'],18,RED,25)
s.mos(2115,480,2220,565,''); s.ground(2220,565)
s.text(2130,615,'Q13  2N7002',18,RED)
s.text(2160,467,'G',15,RED); s.text(2237,431,'D',15,RED); s.text(2237,552,'S',15,RED)
s.resistor(2220,285,2220,380,RED); s.multi(2240,328,['R73','22 kΩ'],18,RED,25)
s.line(2220,380,2220,415); s.dot(2220,405)
s.line(2220,405,2250,405); s.resistor(2250,405,2325,405)
s.text(2285,390,'R40 1 kΩ',16,BLACK,'middle')
s.line(2325,405,2340,405); s.dot(2340,405); s.text(2340,375,'PWM',18,BLACK,'end')
s.cap(2340,405,565,'C60|1 nF',BLACK,'left'); s.ground(2340,565,'')
s.text(2340,648,'R41  10 kΩ：不装',19,RED,'end')
# physically explicit decoupling, logically connected by named nets
s.rail(1360,695,'INTVCC'); s.cap(1360,695,775,'C107|100 nF',RED); s.ground(1360,775)
s.multi(1530,689,['C107 靠近 U8 的 6、4 脚；R72 使 Q13 默认倾向导通关断。',
                    '无信号 / 断线：VO 高 → Q13 导通 → PWM 低。',
                    '信号有效：VO 低 → Q13 截止 → R73 上拉 PWM。',
                    '上下电瞬态是否误使能仍须实测，不能只由静态逻辑保证。'],18,GRAY,29)

# 06 Enable LED (optional)
s.section(1300,865,6,'使能指示（可选）',300)
s.rail(1370,940,'INTVCC'); s.resistor(1370,940,1370,1005,RED)
s.text(1395,979,'R74 3.3 kΩ',18,RED)
s.diode(1370,1005,1090,color=RED,led=True); s.text(1410,1053,'LED3 绿',18,RED)
s.line(1370,1090,1370,1105)
s.mos(1275,1170,1370,1230,'Q14'); s.ground(1370,1230)
s.text(1294,1137,'PWM',18); s.line(1275,1137,1275,1170)
s.text(1300,1290,'只表示 PWM 允许，不代表出光。',18,GRAY)

# 07 Fault indicator
s.section(1650,865,7,'FAULT 指示',320)
s.rail(1710,940,'INTVCC'); s.line(1710,940,1710,965); s.dot(1710,965)
s.line(1710,965,1875,965)
s.resistor(1710,965,1710,1070,RED); s.multi(1735,1011,['R3 10 kΩ','上拉改 INTVCC'],17,RED,25)
s.resistor(1875,965,1875,1035,RED); s.multi(1900,1000,['R75','3.3 kΩ'],17,RED,25)
s.diode(1875,1035,1150,color=RED,led=True); s.text(1900,1120,'LED2 红',18,RED)
s.line(1710,1070,1710,1195); s.line(1710,1195,1875,1195); s.line(1875,1150,1875,1195)
s.dot(1790,1195); s.line(1790,1195,1790,1230); s.text(1810,1237,'FAULT',19)
s.multi(1650,1290,['只指示，不锁停；待机/启动低输出','时也可亮，不等于板子已损坏。'],18,GRAY,26)

# 08 Output voltage ceiling
s.section(2040,865,8,'输出限压',300)
s.rail(2110,940,'VCC_OUT'); s.resistor(2110,940,2110,1040,RED)
s.multi(2135,984,['R30 240 kΩ','232 kΩ → 240 kΩ'],18,RED,26)
s.line(2110,1040,2110,1070); s.dot(2110,1070); s.line(2110,1070,2240,1070); s.text(2255,1077,'FB',19)
s.resistor(2110,1070,2110,1175); s.text(2135,1129,'R49 10 kΩ',18)
s.line(2110,1175,2110,1220); s.ground(2110,1220,'AGND')
s.multi(2040,1290,['典型限压约 30.15 V','本版不改 180 kΩ。'],18,GRAY,26)

# Bottom engineering limits and correct current budget.
s.rect(50,1370,2300,240,BORDER,LIGHT)
s.text(75,1410,'供电预算与使用边界',23,BLUE)
s.multi(75,1451,[
    '功率 MOS 沿用最新 V1：Q1/Q6 = BSC096N10LS5；Q2/Q5 = BSC070N10LS5（不是两颗 BSC028）。',
    '200 kHz、4.5 V 手册 Qg 条件：栅极平均电流约 11.2 mA（典型）/ 13.8 mA（表列最大 Qg）；实际 5 V 需另留余量。',
    '控制/指示负载按约 3～4 mA 预算（含两灯同时亮），另计 U1 内部负载；60 mA 是短路条件典型限流，不是可用 5 V 额度。',
    'C75 47 μF 及 V1 其余原有去耦保留；按有效容值/温升验证。上电带有效信号或联锁重新闭合可自启；本图无故障锁存。',
    'CN19 继续保留为原 PGND 测点；新增联锁改用 CN20，避免位号冲突。控制图未画出的功率/输入保护电路不删。',
],20,BLACK,31)
s.end(NAME+'_第1页_原理图.svg')


t=Sheet(2)
t.text(50,64,'嘉立创修改清单与复核要点',36)
t.text(50,109,'按第 1 页修改；以 2026-10-14 单板 BOM / 2026-09-29 工程为 V1 对照。实物后改值与文件值分别核对。',21,GRAY)
t.line(50,135,2350,135,BLUE,2)

cols=[50,285,790,1290,2350]
rows=[
 ('R2 / R19','10 kΩ / 8.2 kΩ','2.94 kΩ 0.1% / 8.2 kΩ 0.1%','R2 上端由 DAC 改接 VREF；下端仍接 CTRL1；C41 保留。'),
 ('R57 / R58','R57 实装 12 kΩ；R58 不装','R57 8.2 kΩ；R58 仍不装','保留 R56 100 kΩ/B3950 与 C54；约 62 ℃为 NTC 温度。'),
 ('R52 / R53','120 kΩ / 6.34 kΩ','150 kΩ / 10 kΩ','C52 100 nF 保留；典型开启 28.0 V、关闭 24.3 V。'),
 ('C72','330 nF','100 nF','这是改值；SS 清零后约 13 ms；普通 PWM 启停不清零 SS。'),
 ('R30 / R49','232 kΩ / 10 kΩ','240 kΩ / 10 kΩ','固定采用本次 V2 的约 30.15 V 限压；不改 180 kΩ。'),
 ('R3','22 kΩ，上拉 3.3 V','10 kΩ，上拉 INTVCC','也是改值、改接；FAULT 只驱动指示灯，不连接自动锁停。'),
 ('U8 / R55','U8 供电 3.3 V；VO 接 MCU','U8 供电 INTVCC；VO 经 R55 接 Q13 G','R55 保持 220 Ω；C107 100 nF 就近接 U8-6 与 U8-4。'),
 ('D13 / R18','D13 在 R18 输入侧','D13 改到 R18 后，反并联 U8 输入 LED','D13 K → U8-1(A)；D13 A → U8-3(K/WGND)；R18 保持 1 kΩ。'),
 ('Q13 / R72 / R73','无','2N7002 / 100 kΩ / 22 kΩ','R72：G-INTVCC；Q13 S-GND；R73：D-INTVCC；D 经 R40 接 PWM。'),
 ('R40 / C60 / R41','1 kΩ / 1 nF / 10 kΩ','R40、C60 保留；R41 不装','断开原 MCU 对 PWM 的驱动；不要遗漏原 10 kΩ 下拉。'),
 ('CN20 / U9','CN19 已作 PGND 测点','新增 CN20 常闭联锁串在 U9+ 与 R18 前','CN19 不占用；WGND 保持输入侧隔离，不直连板内 GND。'),
 ('R75 / LED2','无本支路','3.3 kΩ + 红色 LED','INTVCC → R75 → LED2 → FAULT；R3 上拉支路并联保留。'),
 ('R74 / LED3 / Q14','无本支路','3.3 kΩ / 绿色 LED / 2N7002（可选）','INTVCC → R74 → LED3 → Q14 D；G-PWM，S-GND。'),
]
top=180; rh=64
t.rect(50,top,2300,rh,BORDER,LIGHT)
for x,head in zip(cols[:-1],['位号 / 功能','V1 对照','V2 修订 B','具体操作 / 注意事项']): t.text(x+15,top+40,head,23,BLUE)
for i,row in enumerate(rows):
    yy=top+rh*(i+1)
    if i%2==0: t.rect(50,yy,2300,rh,BORDER,'#FAFBFC',.6)
    else: t.line(50,yy+rh,2350,yy+rh,BORDER,1)
    for j,ss in enumerate(row):
        size=19 if j!=3 else 18
        # Deterministic wrap at actual embedded-font width.
        avail=cols[j+1]-cols[j]-30; parts=[]; cur=''
        for ch in ss:
            if pdfmetrics.stringWidth(cur+ch,'CN',size)>avail:
                parts.append(cur); cur=ch
            else: cur+=ch
        if cur: parts.append(cur)
        assert len(parts)<=2,(row[0],ss,parts)
        for k,part in enumerate(parts): t.text(cols[j]+15,yy+(27 if len(parts)==2 else 39)+25*k,part,size,RED if j==2 else BLACK)
for x in cols: t.line(x,top,x,top+rh*(len(rows)+1),BORDER,1)

t.section(50,1130,9,'删除 / 保留边界',1090)
t.multi(50,1174,[
    '删除：MCU、晶振、按键、下载/串口及仅服务 MCU 的外围。',
    '辅助 12 V / 5 V / 3.3 V 电源：确认无其他负载后，再删除整支路。',
    '保留：功率级、输入保护、采样/滤波、补偿、RT 与原有去耦。',
    '保留 Q1/Q6 = BSC096，Q2/Q5 = BSC070；不要照旧版 BSC028 替换。',
    '保留 R1 = 2.5 mΩ；本版不改输入保护 MOS、功率电感或 RC 吸收。',
],20,BLACK,32)
t.section(1230,1130,10,'焊接后验证（先电阻负载）',1120)
t.multi(1230,1174,[
    '1. 不接激光器：检查短路、D13 极性、Q13 引脚和 WGND 隔离。',
    '2. 无外部信号上下电：用 VIN 的上/下降沿触发，记录 PWM / ISMON。',
    '3. 保持供电、反复给/撤 5 V：另测重复启动，不假定每次软启动。',
    '4. 测 INTVCC 的直流值、跌落/纹波及 U1 温升；核对输出限压。',
    '5. 用 R1 实际阻值校准 20 A；ISMON 约 1 V，仅作辅助监测。',
],20,BLACK,32)

t.rect(50,1370,2300,117,BORDER,LIGHT)
t.multi(75,1409,[
    '行为边界：上电已有有效信号、联锁恢复闭合，都可能启动；FAULT 不锁停。联锁输入不等同于安全等级急停回路。',
    '尚未完成：嘉立创原生器件引脚映射、网表/ERC、PCB 布局及实板瞬态验收。图面核对不能替代这些步骤。',
    '校准边界：0.1% 分压电阻不能消除 VREF、U1、R1 的误差；ISMON 不能代替快速电流测量来排除窄尖峰。',
],20,BLACK,30)
t.text(50,1530,'依据：ADI LT3763 Rev. C；Infineon BSC070N10LS5 Rev. 2.2 / BSC096N10LS5 Rev. 2.1；本地 V1 工程与单板 BOM。',18,GRAY)
t.text(50,1560,'手册：https://www.analog.com/media/en/technical-documentation/data-sheets/lt3763.pdf',18,GRAY)
t.text(50,1590,'说明：旧 PNG 为本次重绘依据；旧 PDF 与 PNG 的 R73/R74/R75 数值不同，本版已统一为 22 kΩ / 3.3 kΩ / 3.3 kΩ。',18,GRAY)
t.end(NAME+'_第2页_修改清单.svg')
cv.save()

# Read back the actual PDF, render both pages, and validate text/content.
reader=PdfReader(PDF)
assert len(reader.pages)==2
text='\n'.join(p.extract_text() for p in reader.pages)
for required in ['BSC096N10LS5','BSC070N10LS5','2.94','150','240','D13','CN20','R41','22 kΩ','3.3 kΩ','330 nF']:
    assert required in text,required
doc=pdfium.PdfDocument(str(PDF))
for n,page in enumerate(doc):
    img=page.render(scale=3).to_pil()
    img.save(OUT/(NAME+f'_第{n+1}页.png'))
    # High-resolution QA crops are renders, not edits of the supplied bitmap.
    if n==0:
        for label,box in [('隔离触发',(1270,240,2370,825)),('左侧控制',(35,155,790,1200)),('指示与限压',(1260,840,2370,1340))]:
            a,b,c,d=box; sx=img.width/W; sy=img.height/H
            img.crop((int(a*sx),int(b*sy),int(c*sx),int(d*sy))).save(OUT/('QA_'+label+'.png'))

net_contract={
    'U8.1_A':['R18.output','D13.K'],
    'WGND':['U9.2','U8.3_K','D13.A'],
    'Q13.G':['R55.output','R72.bottom'],
    'Q13.D':['R73.bottom','R40.input'],
    'PWM':['U1.22','R40.output','C60.top','Q14.G_optional'],
    'GND':['U8.4','Q13.S','Q14.S_optional'],
    'INTVCC':['U1.2','U8.6','R72.top','R73.top','C107.top','R3.top','R74.top_optional','R75.top'],
    'CN20':'External normally-closed contact in series between U9.1 and R18.input',
    'CN19':'Existing PGND test point, not the new interlock',
    'R41':'DNP',
}
assert 'D13.K' in net_contract['U8.1_A'] and 'D13.A' in net_contract['WGND']
assert not set(net_contract['WGND']) & set(net_contract['GND'])
sources=[ROOT/'LT3763_V2_控制部分原理图.png',ROOT/'LT3763_V2_控制部分原理图.pdf']
qa={'pdf_pages':len(reader.pages),'page_size_pt':list(PAGE),'png_scale':3,
    'text_elements_checked_for_page_bounds':len(s.text_bounds)+len(t.text_bounds),
    'original_sources_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
    'net_contract':net_contract,'native_eda_modified':False,'erc_performed':False,'hardware_tested':False}
(OUT/'校核记录.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pdf':str(PDF),'pages':len(reader.pages),'text_elements':qa['text_elements_checked_for_page_bounds']},ensure_ascii=False))
