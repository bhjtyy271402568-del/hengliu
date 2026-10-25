# 10.25 版输入级瞬态模型：纯 Python 后向欧拉 + 牛顿迭代，不依赖第三方库
# 位号按 10.25 原理图：R3 100k、U1 稳压管、R5 1k、Q3 PNP、C5 米勒电容、R9 10k、R7 1k、D1 12 V、C1 栅源电容、
# Q1∥Q2 SUM110P08（合成一只：K、Cgs、Cgd 都按两只并联）、R1 + C20 阻尼支路、Cin = C2/C3、Cload = 母线电容
# 电源：理想电压源 vin(t) 串 Rs（电池内阻 + 线缆电阻），不含线缆电感
import math
Vt = 0.02585
def lexp(x):            # 限幅指数，防溢出
    return math.exp(x) if x < 40 else math.exp(40) * (1 + x - 40)
def solve(A, b):
    n = len(b); M = [A[i][:] + [b[i]] for i in range(n)]
    for i in range(n):
        piv = max(range(i, n), key=lambda r: abs(M[r][i])); M[i], M[piv] = M[piv], M[i]
        if abs(M[i][i]) < 1e-30: M[i][i] = 1e-30
        for r in range(i + 1, n):
            f = M[r][i] / M[i][i]
            for k in range(i, n + 1): M[r][k] -= f * M[i][k]
    x = [0.0] * n
    for i in reversed(range(n)):
        x[i] = (M[i][n] - sum(M[i][k] * x[k] for k in range(i + 1, n))) / M[i][i]
    return x
# 默认值是 V1 截图的旧参数；10.25 版的参数由 sweep.py 的 base() 设置
P = dict(Rs=0.05, Cin=20e-6, R1=0.3, C20=100e-6, R3=100e3, R5=1e3, C5=100e-9, R9=10e3, R7=1e3, C1=1e-9,
         Cgs=16e-9, Cgd=1.2e-9, Cload=600e-6, Rload=2e3, Vz1=43.0, Vz2=12.0, beta=100.0, IS=1e-14, Vth=2.5, K=20.0)
N = 7  # VT V20 VA VB VC VG VO
def dev(v, p):
    VT, V20, VA, VB, VC, VG, VO = v
    aF = p['beta'] / (1 + p['beta']); aR = 0.5
    IF = p['IS'] * (lexp((VT - VB) / Vt) - 1); IR = p['IS'] * (lexp((VC - VB) / Vt) - 1)
    IE = IF / aF - IR; IC = IF - IR / aR; IB = IE - IC
    d = VT - VG
    iD1 = (d - p['Vz2']) / 5 if d > p['Vz2'] else (-((-d) - 0.7) / 1 if -d > 0.7 else 0.0)
    x = (d - p['Vth']) / 0.05
    vov = 0.05 * math.log1p(math.exp(x)) if x < 60 else d - p['Vth']
    vsd = VT - VO
    if vsd >= 0: imos = p['K'] * vov * vov if vsd >= vov else p['K'] * (2 * vov * vsd - vsd * vsd)
    else:
        imos = -(p['K'] * vov * vov if -vsd >= vov else p['K'] * (2 * vov * (-vsd) - vsd * vsd))
        imos -= ((-vsd) - 0.7) / 0.01 if -vsd > 0.7 else 0
    iz = (VA - p['Vz1']) / 10 if VA > p['Vz1'] else 0.0
    return IE, IC, IB, iD1, imos, iz
def residual(v, vp, VIN, dt, p):
    VT, V20, VA, VB, VC, VG, VO = v
    IE, IC, IB, iD1, imos, iz = dev(v, p)
    d = lambda a, b: (a - b) / dt
    iS = (VIN - VT) / p['Rs']
    iR1 = (VT - V20) / p['R1']
    cC5 = p['C5'] * d(VB - VC, vp[3] - vp[4])
    cGT = (p['C1'] + p['Cgs']) * d(VG - VT, vp[5] - vp[0])
    cGO = p['Cgd'] * d(VG - VO, vp[5] - vp[6])
    return [ -iS + p['Cin'] * d(VT, vp[0]) + iR1 + (VT - VA) / p['R3'] + IE - cGT + iD1 + imos,
             -iR1 + p['C20'] * d(V20, vp[1]),
             -(VT - VA) / p['R3'] + iz + (VA - VB) / p['R5'],
             -(VA - VB) / p['R5'] + cC5 - IB,
             VC / p['R9'] + (VC - VG) / p['R7'] - cC5 - IC,
             -(VC - VG) / p['R7'] + cGT + cGO - iD1,
             p['Cload'] * d(VO, vp[6]) - cGO - imos + VO / p['Rload'] ]
def step(v, vp, VIN, dt, p):
    x = v[:]
    for it in range(80):
        r = residual(x, vp, VIN, dt, p)
        J = [[0.0] * N for _ in range(N)]
        for j in range(N):
            h = 1e-6 * max(1.0, abs(x[j])); xs = x[:]; xs[j] += h
            rs = residual(xs, vp, VIN, dt, p)
            for i in range(N): J[i][j] = (rs[i] - r[i]) / h
        dx = solve(J, [-ri for ri in r]); m = max(abs(q) for q in dx)
        if m > 2.0: dx = [q * 2.0 / m for q in dx]
        x = [a + b for a, b in zip(x, dx)]
        if m < 1e-7: return x, True
    return x, False
def run(vin, T, p, dtmax=1e-5, rec=2e-5, v0=None):
    v = v0[:] if v0 else [0.0] * N; t = 0.0; dt = 1e-7; out = []; nxt = 0; pk = 0.0; pkin = 0.0
    while t < T:
        x, ok = step(v, v, vin(t + dt), dt, p)
        if not ok:
            dt /= 4
            if dt < 1e-13: raise SystemExit('不收敛 %g' % t)
            continue
        t += dt; v = x
        IE, IC, IB, iD1, imos, iz = dev(v, p)
        iin = (vin(t) - v[0]) / p['Rs']
        pk = max(pk, imos); pkin = max(pkin, iin)
        if t >= nxt:
            out.append([round(t * 1e3, 4), round(v[0], 3), round(v[4], 3), round(v[5], 3), round(v[6], 3), round(pk, 3), round(pkin, 3)])
            nxt += rec; pk = 0.0; pkin = 0.0
        dt = min(dt * 1.25, dtmax)
    return out, v
