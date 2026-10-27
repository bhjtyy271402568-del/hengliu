import json, math, copy, sys
cur = json.load(open('aux_cur.json'))
C = {c['r']: c for c in cur['c']}

def move(ref, nx, ny, rot=0):
    c = C[ref]; cx, cy = c['x'], c['y']
    a = math.radians(rot)
    def tf(x, y):
        dx, dy = x - cx, y - cy
        return nx + dx * math.cos(a) - dy * math.sin(a), ny + dx * math.sin(a) + dy * math.cos(a)
    def rect(x, y, w, h):
        pts = [tf(x, y), tf(x + w, y), tf(x, y + h), tf(x + w, y + h)]
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        return [round(min(xs), 3), round(min(ys), 3), round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3)]
    c['bb'] = rect(*c['bb'])
    c['p'] = [rect(*p[:4]) + p[4:] for p in c['p']]
    c['x'], c['y'] = nx, ny

def add(ref, x, y, nets, bottom=True, L=3.2, Wd=1.6):
    # 1206，水平：pad1 在左
    pw, ph = 1.5, 1.7
    C[ref] = dict(r=ref, b=1 if bottom else 0, x=x, y=y, bb=[x - L / 2, y - Wd / 2, L, Wd],
                  p=[[x - L / 2 - pw / 2 + .1, y - ph / 2, pw, ph, nets[0], '1', 0], [x + L / 2 - pw / 2 - .1, y - ph / 2, pw, ph, nets[1], '2', 0]])

# 一次侧
move('C10', 43.6, 28.9, 90)          # 原来压在 U3 第 2、3 脚上且网络对调
move('Q2', 39.0, 11.5, 180)          # 栅极 / 源极脚朝向 U1
move('R3', 20.0, 17.2)
move('R4', 20.0, 13.6)
move('R5', 17.8, 17.2, 90)
move('R6', 17.8, 13.6, 90)
# +15 V 侧
move('D6', 98.5, 91.2)
move('L3', 107.6, 91.5)
move('R14', 112.5, 89.5, 90)
move('C19', 115.6, 91.5, 90)
move('C18', 105.3, 81.1)
move('J4', 122.5, 88.5, 90)
add('C22', 91.6, 79.1, ('P15_RAW', 'AUX_GND'))   # U2 输出脚旁 1 µF（新增）
add('C23', 91.6, 75.3, ('P15_RAW', 'AUX_GND'))   # U2 输出脚旁 10 µF（新增）
# 振镜接口居中、两只都 +15 在上
move('J2', 122.5, 62.5, 180)
move('J3', 122.5, 45.5, 180)
move('C13', 118.5, 72.8)
move('C16', 118.5, 35.0)
# −15 V 侧
move('D5', 90.4, 29.0, 90)
move('D7', 100.0, 47.5)
move('R13', 114.5, 32.8)
out = dict(cur); out['c'] = list(C.values())
json.dump(out, open('aux_new.json', 'w'))
