"""40 A 双板机壳 B1（外观重设计，沿用 Codex A0 的内部结构和坐标）。
坐标：mm，主板左下角板底为原点，Z 向上（同 A0 装配）。用法：cq 环境 python enclosure_b1.py 输出目录
生成：各外观件 STEP（tray / lid / front / rear / feet / baffles / fan_standoffs）和 parts.pkl（供装配和渲染）。"""
import sys, os, math, pickle
import cadquery as cq
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
FONT = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
if not os.path.exists(FONT): FONT = None

# ---- 主尺寸（与 A0 一致的包络和安装位置） ----
X0, X1 = -8.0, 136.0          # 外宽 144（A0 侧板外 −8..136）
ZB, ZT = -49.0, 84.0          # 底外 / 顶外
SEAM = 74.0                   # 上盖与托盘分缝
YF, YR = -11.0, 147.0         # 管壳前后端
T = 2.0                       # 壁厚
PT = 3.0                      # 端板厚
FAN_C = (64.0, 20.0)          # 风扇中心 x, z（A0）
FAN_PITCH = 105.0

def box(x0, x1, y0, y1, z0, z1):
    return cq.Workplane('XY').box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))
def plane_front(y):  return cq.Plane(origin=(0, y, 0), xDir=(1, 0, 0), normal=(0, -1, 0))   # 局部 (x, z)，向 −Y 挤出
def plane_rear(y):   return cq.Plane(origin=(0, y, 0), xDir=(-1, 0, 0), normal=(0, 1, 0))   # 局部 (−x, z)，向 +Y
def plane_left(x):   return cq.Plane(origin=(x, 0, 0), xDir=(0, -1, 0), normal=(-1, 0, 0))  # 局部 (−y, z)，向 −X
def plane_right(x):  return cq.Plane(origin=(x, 0, 0), xDir=(0, 1, 0), normal=(1, 0, 0))    # 局部 (y, z)，向 +X
def plane_top(z):    return cq.Plane(origin=(0, 0, z), xDir=(1, 0, 0), normal=(0, 0, 1))
def rrect(pl, cx, cz, w, h, r, depth):
    return cq.Workplane(pl).center(cx, cz).sketch().rect(w, h).vertices().fillet(r).finalize().extrude(depth)
def label(pl, cx, cz, txt, size, depth):
    return cq.Workplane(pl).center(cx, cz).text(txt, size, depth, fontPath=FONT, halign='center', valign='center')

# ---- 托盘（底 + 两侧，外底边 R3）与内部螺钉槽 ----
tray = box(X0, X1, YF, YR, ZB, SEAM).edges('|Y and <Z').fillet(3.0)
tray = tray.cut(box(X0 + T, X1 - T, YF - 1, YR + 1, ZB + T, SEAM + 1).edges('|Y and <Z').fillet(1.0))
for xa, xb in ((X0 + T, X0 + T + 5), (X1 - T - 5, X1 - T)):                 # 底角螺钉槽（型材自带）
    tray = tray.union(box(xa, xb, YF, YR, ZB + T, ZB + T + 5))
# 底板过孔：A0 的 4 颗尼龙底螺钉（M3，头 Ø5.5 × 2.2 mm 在底板下面，脚垫高 4 mm 盖得住）
BASE_SCREWS = [(3.487, 3.487), (92.987, 3.487), (3.487, 60.487), (124.487, 91.487)]
for (x, y) in BASE_SCREWS:
    tray = tray.cut(cq.Workplane('XY').center(x, y).circle(1.7).extrude(T + 6).translate((0, 0, ZB - 1)))
# ---- 上盖（顶 + R8 圆角 + 裙边到分缝，内侧舌片挡住 0.5 mm 阴影缝） ----
lid = box(X0, X1, YF, YR, SEAM + 0.5, ZT).edges('|Y and >Z').fillet(8.0)
lid = lid.cut(box(X0 + T, X1 - T, YF - 1, YR + 1, SEAM - 1, ZT - T).edges('|Y and >Z').fillet(6.0))
for xa, xb in ((X0 + T, X0 + T + 1.6), (X1 - T - 1.6, X1 - T)):
    lid = lid.union(box(xa, xb, YF, YR, SEAM - 4.0, SEAM + 0.5))           # 舌片
for xa, xb in ((X0 + T, X0 + T + 5), (X1 - T - 5, X1 - T)):
    lid = lid.union(box(xa, xb, YF, YR, ZT - T - 5, ZT - T))                # 顶角螺钉槽

# ---- 端板外形：托盘 + 上盖的外轮廓 ----
def endplate(y0, y1):
    p = box(X0, X1, y0, y1, ZB, ZT).edges('|Y and <Z').fillet(3.0).edges('|Y and >Z').fillet(8.0)
    face = '<Y' if y0 < YF else '>Y'
    return p.faces(face).edges().chamfer(0.8)
front = endplate(YF - PT, YF)
rear = endplate(YR, YR + PT)
fy = YF - PT; ry = YR + PT

# 端板四角沉头孔（拧进托盘 / 上盖螺钉槽）
def screw_pts():
    return [(X0 + T + 2.5, ZB + T + 2.5), (X1 - T - 2.5, ZB + T + 2.5), (X0 + T + 2.5, ZT - T - 2.5), (X1 - T - 2.5, ZT - T - 2.5)]
for (x, z) in screw_pts():
    front = front.cut(cq.Workplane(plane_front(YF + 0.1)).center(x, z).circle(1.7).extrude(PT + 0.3))
    front = front.cut(cq.Workplane(plane_front(fy + 1.6)).center(x, z).circle(3.0).extrude(1.7))
    rear = rear.cut(cq.Workplane(plane_rear(YR - 0.1)).center(-x, z).circle(1.7).extrude(PT + 0.3))
    rear = rear.cut(cq.Workplane(plane_rear(ry - 1.6)).center(-x, z).circle(3.0).extrude(1.7))

# ---- 前面板：鳍片对齐的竖缝（三条带）+ 接口窗 + 刻字 ----
PITCH = 128.0 / (37 - 1 + 1e-9) if False else 3.5222222
centers = [0.6 + PITCH / 2 + i * PITCH for i in range(36)]            # 36 条鳍片通道中心
def slots(xs, z0, z1, w=2.0):
    s = None
    for x in xs:
        c = cq.Workplane(plane_front(YF + 0.1)).center(x, (z0 + z1) / 2).slot2D(z1 - z0, w, angle=90).extrude(PT + 0.3)
        s = c if s is None else s.union(c)
    return s
front = front.cut(slots(centers, -43.0, -11.0))                                 # 鳍片出风（鳍片 z −44..−10.5）
front = front.cut(slots([c for c in centers if 4 < c < 97], 21.0, 37.0))       # 两板之间
front = front.cut(slots([c for c in centers if 3 < c < 125], 50.0, 77.0))      # 辅助板上方
WIN_CN14 = (102.9, 129.2, -3.7, 17.7); WIN_U3 = (41.3, 52.3, -3.2, 11.7)
for (xa, xb, za, zb) in (WIN_CN14, WIN_U3):
    front = front.cut(rrect(plane_front(YF + 0.1), (xa + xb) / 2, (za + zb) / 2, xb - xa, zb - za, 2.0, PT + 0.3))
ENG = 0.3
front_text = [  # (文字, x, z, 字高)
    ('LASER OUT', 116.0, 31.5, 3.2), ('40 A MAX', 116.0, 26.0, 2.6),
    ('+', 110.85, 19.8, 3.0), ('−', 121.35, 19.8, 3.0), ('SHOOT 5 V', 46.8, 14.6, 2.2),
    ('CC-40  LASER DRIVER', 31.0, 43.2, 3.0)]
front_ink = None
for t, x, z, s in front_text:
    e = label(plane_front(fy + ENG), x, z, t, s, ENG + 0.05)
    front = front.cut(e)
    ink = label(plane_front(fy + ENG), x, z, t, s, 0.06)
    front_ink = ink if front_ink is None else front_ink.union(ink)
# 输出窗橙色饰圈（警示色，凸出 0.8 mm）
xa, xb, za, zb = WIN_CN14
bezel = rrect(plane_front(fy), (xa + xb) / 2, (za + zb) / 2, xb - xa + 3.0, zb - za + 3.0, 3.0, 0.8)
bezel = bezel.cut(rrect(plane_front(fy + 0.1), (xa + xb) / 2, (za + zb) / 2, xb - xa, zb - za, 2.0, 1.2))

# ---- 后面板：六角孔风扇网 + 风扇螺钉孔 + 刻字 ----
R_GRILL, HEX, WEB = 56.0, 6.0, 1.3
pts = []
dx = HEX + WEB; dz = dx * math.sqrt(3) / 2
for j in range(-12, 13):
    for i in range(-12, 13):
        x = i * dx + (dx / 2 if j % 2 else 0); z = j * dz
        if math.hypot(x, z) + HEX / 2 < R_GRILL: pts.append((-(FAN_C[0] + x), FAN_C[1] + z))
grill = cq.Workplane(plane_rear(YR - 0.1)).pushPoints(pts).polygon(6, HEX * 2 / math.sqrt(3)).extrude(PT + 0.3)
rear = rear.cut(grill)
ring = cq.Workplane(plane_rear(ry)).center(-FAN_C[0], FAN_C[1]).circle(R_GRILL + 3.0).circle(R_GRILL + 0.6).extrude(0.6)
rear = rear.union(ring)
for sx in (-1, 1):
    for sz in (-1, 1):
        x = FAN_C[0] + sx * FAN_PITCH / 2; z = FAN_C[1] + sz * FAN_PITCH / 2
        rear = rear.cut(cq.Workplane(plane_rear(YR - 0.1)).center(-x, z).circle(2.2).extrude(PT + 0.3))
rear_ink = None
for t, x, z, s in (('AIR IN', FAN_C[0], -43.0, 3.0), ('12 V FAN', FAN_C[0] + 46, -43.0, 2.2)):
    rear = rear.cut(label(plane_rear(ry - ENG), -x, z, t, s, ENG + 0.05))
    ink = label(plane_rear(ry - ENG), -x, z, t, s, 0.06)
    rear_ink = ink if rear_ink is None else rear_ink.union(ink)

# ---- 侧窗和刻字（左：电池输入、辅助输入；右：振镜、控制卡） ----
WINS_L = [((64.3, 90.6, -3.7, 17.7), 'BATTERY IN  30–42 V', 21.5), ((32.8, 49.1, 39.9, 49.9), 'AUX IN', 53.0),
          ((7.7, 22.7, 0.3, 7.5), 'DEBUG', 11.0)]                       # CN4 调试口（托盘侧壁不可拆，开窗）
WINS_R = [((31.9, 68.7, 38.4, 59.0), 'GALVO X · Y   ±15 V', 62.5), ((75.2, 89.0, 38.4, 59.0), 'CARD 15 V', 62.5)]
side_ink = None
for (ya, yb, za, zb), t, tz in WINS_L:
    tray_cut = rrect(plane_left(X0 + T + 0.1), -(ya + yb) / 2, (za + zb) / 2, yb - ya, zb - za, 2.5, T + 0.3)
    tray = tray.cut(tray_cut)
    tray = tray.cut(label(plane_left(X0 + ENG), -(ya + yb) / 2, tz, t, 2.8, ENG + 0.05))
    ink = label(plane_left(X0 + ENG), -(ya + yb) / 2, tz, t, 2.8, 0.06); side_ink = ink if side_ink is None else side_ink.union(ink)
for (ya, yb, za, zb), t, tz in WINS_R:
    tray = tray.cut(rrect(plane_right(X1 - T - 0.1), (ya + yb) / 2, (za + zb) / 2, yb - ya, zb - za, 2.5, T + 0.3))
    tray = tray.cut(label(plane_right(X1 - ENG), (ya + yb) / 2, tz, t, 2.8, ENG + 0.05))
    ink = label(plane_right(X1 - ENG), (ya + yb) / 2, tz, t, 2.8, 0.06); side_ink = ink if side_ink is None else side_ink.union(ink)
# 上盖顶面一行字
lid = lid.cut(label(plane_top(ZT - ENG), 64.0, 4.0, '40 A CONSTANT-CURRENT LASER DRIVER', 3.0, ENG + 0.05))
lid_ink = label(plane_top(ZT - ENG), 64.0, 4.0, '40 A CONSTANT-CURRENT LASER DRIVER', 3.0, 0.06)

# ---- 鳍片旁路挡条（逼风走鳍片，A0 两侧各漏约 6 mm）、风扇支柱、脚垫 ----
baffles = box(X0 + T, 0.0, 0.0, 95.0, ZB + T + 5, -4.5).union(box(128.0, X1 - T, 0.0, 95.0, ZB + T + 5, -4.5))
fan_st = None
for sx in (-1, 1):
    for sz in (-1, 1):
        x = FAN_C[0] + sx * FAN_PITCH / 2; z = FAN_C[1] + sz * FAN_PITCH / 2
        s = cq.Workplane(plane_rear(137.4)).center(-x, z).circle(4.0).circle(2.2).extrude(YR - 137.4)
        fan_st = s if fan_st is None else fan_st.union(s)
feet = None
for x in (16.0, 112.0):                      # 避开底螺钉头（头半径 2.75 + 脚半径 7.5 + 余量）
    for y in (-1.0, 135.0):
        f = cq.Workplane('XY').center(x, y).circle(7.5).extrude(4.0).translate((0, 0, ZB - 4.0)).edges('<Z').fillet(1.5)
        feet = f if feet is None else feet.union(f)

PARTS = {'TRAY': (tray, (0.80, 0.81, 0.83)), 'LID': (lid, (0.80, 0.81, 0.83)),
         'FRONT_PANEL': (front, (0.16, 0.17, 0.19)), 'REAR_PANEL': (rear, (0.16, 0.17, 0.19)),
         'LASER_BEZEL': (bezel, (0.93, 0.42, 0.12)), 'FIN_BYPASS_BAFFLES': (baffles, (0.30, 0.31, 0.33)),
         'FAN_STANDOFFS': (fan_st, (0.12, 0.12, 0.13)), 'FEET': (feet, (0.07, 0.07, 0.08))}
INK = {'INK_FRONT': front_ink, 'INK_REAR': rear_ink, 'INK_SIDE': side_ink, 'INK_LID': lid_ink}
for k, (w, c) in PARTS.items():
    cq.exporters.export(w, os.path.join(OUT, f'B1_{k}.step'))
    bb = w.val().BoundingBox(); print(k, round(bb.xmin, 1), round(bb.ymin, 1), round(bb.zmin, 1), round(bb.xmax, 1), round(bb.ymax, 1), round(bb.zmax, 1), w.val().isValid())
pickle.dump({'parts': {k: (w.val(), c) for k, (w, c) in PARTS.items()}, 'ink': {k: v.val() for k, v in INK.items()}}, open(os.path.join(OUT, 'parts.pkl'), 'wb'))
