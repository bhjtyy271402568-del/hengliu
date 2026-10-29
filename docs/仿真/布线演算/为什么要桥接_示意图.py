import logging
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Polygon, Circle
logging.getLogger('matplotlib.font_manager').setLevel(logging.ERROR)
plt.rcParams['font.sans-serif']=['WenQuanYi Zen Hei','DejaVu Sans']
RED='#d62728'; BLU='#1f77b4'; CY='#17a2b8'; YEL='#ffd700'; GRY='#555555'
fig,axs=plt.subplots(2,3,figsize=(22,14))
for ax in axs.flat: ax.set_xlim(0,10); ax.set_ylim(0,8); ax.axis('off'); ax.set_aspect('equal')
def W(ax,pts,c='k',lw=2.5,ls='-'): ax.plot([p[0] for p in pts],[p[1] for p in pts],color=c,lw=lw,ls=ls,solid_capstyle='round',zorder=3)
def arrow(ax,a,b,c): ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='-|>',lw=3,color=c,mutation_scale=22),zorder=6)
def cap(ax,x,y,vertical=True,c='k',label=None):
    if vertical:
        W(ax,[(x-0.45,y+0.12),(x+0.45,y+0.12)],c,4); W(ax,[(x-0.45,y-0.12),(x+0.45,y-0.12)],c,4)
    else:
        W(ax,[(x-0.12,y-0.45),(x-0.12,y+0.45)],c,4); W(ax,[(x+0.12,y-0.45),(x+0.12,y+0.45)],c,4)
    if label: ax.text(x+0.6,y,label,fontsize=13,va='center',color=c)
def batt(ax,x,y,label='5 V'):
    W(ax,[(x-0.5,y+0.15),(x+0.5,y+0.15)],'k',4); W(ax,[(x-0.25,y-0.15),(x+0.25,y-0.15)],'k',4)
    ax.text(x+0.6,y+0.25,'+',fontsize=16); ax.text(x+0.6,y-0.45,'-',fontsize=16); ax.text(x-1.6,y-0.1,label,fontsize=13)
def res(ax,x0,x1,y,label=None):
    ax.add_patch(Rectangle((x0,y-0.2),x1-x0,0.4,fc='white',ec='k',lw=2,zorder=4))
    if label: ax.text((x0+x1)/2,y+0.35,label,fontsize=12,ha='center')
def mos(ax,x,y,label='下管'):
    # gate plate at x, channel at x+0.35
    W(ax,[(x,y-0.8),(x,y+0.8)],'k',4); W(ax,[(x+0.35,y-1.0),(x+0.35,y+1.0)],'k',4)
    W(ax,[(x+0.35,y+0.85),(x+1.2,y+0.85),(x+1.2,y+1.8)]); W(ax,[(x+0.35,y-0.85),(x+1.2,y-0.85),(x+1.2,y-1.8)])
    ax.text(x+1.35,y+1.5,'漏极 D',fontsize=12); ax.text(x+1.35,y-1.7,'源极 S',fontsize=12); ax.text(x-0.3,y+1.1,'栅极 G',fontsize=12,ha='right')
    ax.text(x+0.6,y+0.05,label,fontsize=12,color=GRY)
def bar(ax,x0,x1,y,c,label):
    W(ax,[(x0,y),(x1,y)],c,9); ax.text((x0+x1)/2,y-0.55,label,fontsize=13,ha='center',color=c,weight='bold')
def note(ax,x,y,t,ec='#888',fs=13): ax.text(x,y,t,fontsize=fs,va='top',bbox=dict(fc='white',ec=ec,boxstyle='round,pad=0.4'),zorder=7)
# ---------- ① MOS = 电容
ax=axs[0,0]; ax.set_title('① 下管开不开，看“栅极比源极高多少”（VGS）',fontsize=15)
mos(ax,5.0,4.3)
W(ax,[(2.0,4.3),(5.0,4.3)])
W(ax,[(3.4,4.3),(3.4,3.2)],BLU,2,'--'); cap(ax,3.4,2.95,True,BLU); W(ax,[(3.4,2.7),(3.4,2.0),(6.2,2.0),(6.2,2.5)],BLU,2,'--')
ax.text(1.2,2.6,'栅极和源极之间\n其实是个小电容 Cgs',fontsize=13,color=BLU)
note(ax,0.4,7.6,'VGS = 栅极电压 - 源极电压\nVGS ≈ 0 V：关　　VGS ≈ 5 V：完全导通\n开管 = 给 Cgs 充电到约 5 V；关管 = 把电放掉')
# ---------- ② 充电要闭合圈
ax=axs[0,1]; ax.set_title('② 给电容充电，“去”和“回”两根线都得接',fontsize=15)
batt(ax,1.6,4.2); W(ax,[(1.6,4.35),(1.6,5.6),(3.6,5.6),(3.6,4.32)]); cap(ax,3.6,4.2); W(ax,[(3.6,4.08),(3.6,2.8),(1.6,2.8),(1.6,4.05)])
arrow(ax,(2.0,5.6),(3.2,5.6),RED); arrow(ax,(3.2,2.8),(2.0,2.8),CY)
ax.text(1.4,1.9,'圈闭合：电荷流得动\n电容充上 5 V （√）',fontsize=13,color='green')
batt(ax,6.4,4.2); W(ax,[(6.4,4.35),(6.4,5.6),(8.4,5.6),(8.4,4.32)]); cap(ax,8.4,4.2); W(ax,[(8.4,4.08),(8.4,2.8),(7.7,2.8)]); W(ax,[(7.1,2.8),(6.4,2.8),(6.4,4.05)])
ax.text(7.25,2.55,'×',fontsize=30,color=RED,ha='center')
ax.text(6.2,1.9,'回去的线断了：\n一点电荷也流不动 （×）',fontsize=13,color=RED)
note(ax,0.3,7.6,'就像电池只接了正极、负极悬空，电容永远充不上。')
# ---------- ③ U9 内部
ax=axs[0,2]; ax.set_title('③ U9 里的 BG 驱动 = 一块 5 V“电池”+ 两个开关',fontsize=15)
ax.add_patch(FancyBboxPatch((0.6,1.6),6.0,5.0,boxstyle='round,pad=0.1',fc='#fff7d6',ec='k',lw=2)); ax.text(0.8,6.25,'U9（LT3763）',fontsize=14,weight='bold')
batt(ax,2.2,4.1,'INTVCC\n5 V'); W(ax,[(2.2,4.25),(2.2,5.4),(4.2,5.4)]); W(ax,[(4.2,5.4),(4.9,5.0)],'k',3)  # upper switch open-ish
ax.text(4.1,5.65,'上拉开关',fontsize=12)
W(ax,[(5.0,5.0),(5.0,2.9)]); W(ax,[(5.0,4.1),(7.6,4.1)]); ax.text(6.7,4.35,'BG 脚',fontsize=13,weight='bold')
W(ax,[(5.0,2.9),(4.3,2.5)],'k',3); ax.text(3.0,2.85,'下拉开关',fontsize=12)
W(ax,[(2.2,3.95),(2.2,2.2)]); W(ax,[(4.2,2.5),(4.2,2.2)])
bar(ax,1.4,5.6,2.2,CY,'')
W(ax,[(3.5,2.2),(3.5,0.9)],CY,4); ax.text(3.7,1.05,'GND 脚 + 底部散热焊盘',fontsize=13,color=CY)
note(ax,6.9,7.6,'LT3763 只有这一种地：\n“电池”的负极、芯片的\n信号基准都是 GND。\n\n它只伸出一根线 BG，\n回来的那根线必须\n回到 GND 脚。',fs=12.5)
# ---------- ④ 有桥接
def scene(ax,bridge):
    ax.add_patch(FancyBboxPatch((0.3,3.3),2.6,2.6,boxstyle='round,pad=0.08',fc='#fff7d6',ec='k',lw=2)); ax.text(0.45,5.55,'U9',fontsize=14,weight='bold')
    batt(ax,1.5,4.6,''); ax.text(0.45,4.5,'5V',fontsize=12)
    W(ax,[(1.5,4.75),(1.5,5.3),(2.9,5.3)]); W(ax,[(2.9,5.3),(3.6,5.3)]); ax.text(3.0,5.5,'BG',fontsize=13,weight='bold')
    res(ax,3.6,4.6,5.3,'栅极电阻'); W(ax,[(4.6,5.3),(6.4,5.3)])
    mos(ax,6.4,5.3)
    W(ax,[(7.6,3.5),(7.6,2.6)])
    W(ax,[(1.5,4.45),(1.5,2.6)])
    bar(ax,0.4,3.6,2.6,CY,'GND（信号地）'); bar(ax,5.4,9.6,2.6,BLU,'PGND（功率地）')
    if bridge:
        ax.add_patch(Rectangle((3.4,2.25),2.2,0.7,fc=YEL,ec='k',lw=2,zorder=5)); ax.text(4.5,1.6,'桥接铜',fontsize=14,weight='bold',ha='center')
        arrow(ax,(2.0,5.3),(3.3,5.3),RED); arrow(ax,(4.8,5.3),(6.0,5.3),RED)
        arrow(ax,(7.6,3.3),(7.6,2.75),BLU); arrow(ax,(7.0,2.6),(5.9,2.6),BLU); arrow(ax,(3.3,2.6),(2.0,2.6),CY); arrow(ax,(1.5,2.75),(1.5,3.6),CY)
    else:
        ax.text(4.5,2.35,'× 断开 ×',fontsize=20,color=RED,ha='center',weight='bold')
        arrow(ax,(2.0,5.3),(3.3,5.3),'#e0a0a0')
ax=axs[1,0]; ax.set_title('④ 两张地用桥接铜连上：圈闭合，下管打开',fontsize=15); scene(ax,True)
note(ax,0.3,7.7,'电荷：5 V(+) → BG → 栅极电阻 → 栅极（Cgs）→ 源极\n→ PGND → 桥接铜 → GND → 回到 5 V(-)\nCgs 充到 5 V，VGS = 5 V → 下管导通 （√）',ec='green')
ax=axs[1,1]; ax.set_title('⑤ 两张地不连：圈断了，下管开不了',fontsize=15); scene(ax,False)
note(ax,0.3,7.7,'U9 的 5 V 是“比 GND 高 5 V”；源极在 PGND 上，\n和 GND 之间没有导线 → 电荷回不去 → Cgs 充不上\n栅源间 12 kΩ 下拉把 VGS 按在 0 V → 下管一直关着 （×）',ec=RED)
# ---------- ⑥ 桥接位置
ax=axs[1,2]; ax.set_title('⑥ 圈一定穿过桥接铜，所以桥接放哪，圈就被拉到哪',fontsize=15)
def mini(y0,far,label,col):
    ax.add_patch(Rectangle((0.6,y0+0.6),1.4,1.2,fc='#fff7d6',ec='k',lw=1.5)); ax.text(1.3,y0+1.2,'U9',ha='center',fontsize=12)
    ax.add_patch(Rectangle((6.8,y0+0.6),1.4,1.2,fc='#dbe9f6',ec='k',lw=1.5)); ax.text(7.5,y0+1.2,'下管',ha='center',fontsize=12)
    W(ax,[(2.0,y0+1.6),(6.8,y0+1.6)],RED,3)
    if not far:
        pts=[(6.8,y0+0.8),(4.4,y0+0.8),(2.0,y0+0.8)]
        W(ax,pts,BLU,3); ax.add_patch(Rectangle((4.0,y0+0.6),0.8,0.4,fc=YEL,ec='k',zorder=5))
        ax.add_patch(Polygon([(2.0,y0+1.6),(6.8,y0+1.6),(6.8,y0+0.8),(2.0,y0+0.8)],fc=col,alpha=0.15))
    else:
        pts=[(6.8,y0+0.8),(8.9,y0+0.8),(8.9,y0+3.0),(0.3,y0+3.0),(0.3,y0+1.0),(0.6,y0+1.0)]
        W(ax,pts,BLU,3); ax.add_patch(Rectangle((0.1,y0+2.0),0.4,0.8,fc=YEL,ec='k',zorder=5))
        ax.add_patch(Polygon([(2.0,y0+1.6),(6.8,y0+1.6),(6.8,y0+0.8),(8.9,y0+0.8),(8.9,y0+3.0),(0.3,y0+3.0),(0.3,y0+1.0),(2.0,y0+1.0)],fc=col,alpha=0.15))
    ax.text(2.2,y0+0.15,label,fontsize=13,color=col,weight='bold')
mini(4.2,True,'桥接在远处：圈很大（Codex 版约 96 mm，计算）',RED)
mini(0.6,False,'桥接在 U9 和下管中间：圈小（优化版约 23 mm）','green')
ax.text(0.3,7.8,'红 = BG 去路　蓝 = 回路　黄 = 桥接铜',fontsize=12)
plt.tight_layout(); plt.savefig('/home/user/hengliu/docs/仿真/布线演算/为什么要桥接_示意图.png',dpi=90)
