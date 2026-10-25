# C1 / C5 / R7 一起扫：插电瞬间误导通、整段缓启动结温、过压切断
# 用法：python3 -I sweep.py          （全部约 2–3 分钟）
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model

# SUM110P08 单脉冲 Zth(j-c)（手册第 5 页读图）拟合成 4 阶 Foster，乘 RthJC 最大 0.4 °C/W
TAUS = [1.5e-4, 6e-4, 2e-3, 6e-3]; R = [0.0, 0.315, 0.544, 0.128]; RJC = 0.4
def tj_rise(trace):                      # trace: [(t 秒, 功率 W)]，返回结到壳最大温升
    T = [0.0] * 4; mx = 0.0; tp = trace[0][0]
    for t, P in trace:
        dt = t - tp; tp = t
        for i in range(4):
            a = math.exp(-dt / TAUS[i]); T[i] = T[i] * a + P * R[i] * RJC * (1 - a)
        mx = max(mx, sum(T))
    return mx

def base(c1, c5, r7, vth):
    """10.25 版参数。假设：Q3 β 100；P 管平方律 K 40 A/V²（两只并联）；U1 稳压 47 V（BZT52-B47 标称）；
    母线 1.013 mF；负载 2 kΩ（激光未开）。
    电容（2026-10-25 第 2 版更正）：Ciss 已包含 Cgd，Cgs = Ciss − Crss = 10.85 − 0.7 = 10.15 nF / 只（Codex 指出）；
    插电时 VDS 从 0 摆到 42 V，Crss 在低压时大得多（手册曲线 0 V 约 4.8 nF），按电荷等效取 Qgd 42 nC / 40 V ≈ 1.05 nF / 只。"""
    p = dict(model.P)
    p.update(C1=c1, C5=c5, R7=r7, Vth=vth, Cload=1013e-6, Vz1=47.0, Cgs=2 * 10.15e-9, Cgd=2 * 1.05e-9, K=40.0)
    return p

def plug(p, vin=42.0, tr=1e-6, T=0.12):
    """插电：输入 1 µs 内从 0 升到 vin。返回 (前 0.5 ms P 管峰值电流, 全程峰值电流, 峰值功率, 能量, 母线到 90% 时间 ms, 结温升, 末态)"""
    o, v = model.run(lambda t: vin * min(t / tr, 1.0), T, p, dtmax=5e-6, rec=5e-6)
    trace = [(r[0] * 1e-3, (r[1] - r[4]) * r[5]) for r in o]
    early = max(r[5] for r in o if r[0] <= 0.5)
    t90 = next((r[0] for r in o if r[4] >= 0.9 * vin), None)
    E = sum(P for _, P in trace) * 5e-6
    return early, max(r[5] for r in o), max(P for _, P in trace), E, t90, tj_rise(trace), v

def ov_ramp(p, v0, rate, vfrom=42.0, dv=14.0):
    """工作中输入以 rate (V/s) 从 42 V 往上升，返回 P 管关断（VSG < Vth）时的输入电压"""
    T = dv / rate + 0.01
    o, _ = model.run(lambda t: vfrom + min(t * rate, dv), T, p, dtmax=2e-5, rec=T / 2000, v0=v0)
    cut = next((r for r in o if r[1] - r[3] < p['Vth']), None)
    return cut[1] if cut else None

if __name__ == '__main__':
    print('== 1. 插电误导通：C5 680 nF；C1 计公差下限；Vth 取手册最小 1.0 V 和 85 °C 时约 0.67 V（−5.5 mV/°C）==')
    for r7 in (1e3, 2.2e3):
        for name, c1 in (('1 nF', 0.9e-9), ('10 nF −10%', 9e-9), ('22 nF −10%', 19.8e-9), ('47 nF −5%', 44.65e-9), ('68 nF −5%', 64.6e-9)):
            e1 = plug(base(c1, 680e-9, r7, 1.0), T=0.002)[0]
            e2 = plug(base(c1, 680e-9, r7, 0.67), T=0.002)[0]
            print(f'R7 {r7/1e3:.1f}k C1 {name:10s}：插电后 0.5 ms 内 P 管峰值 {e1:5.1f} A（Vth 1.0）/ {e2:5.1f} A（Vth 0.67）')
    print('== 2. 缓启动和过压切断：C1 47 nF、R7 1k ==')
    for c5 in (330e-9, 470e-9, 680e-9, 1e-6):
        for vth in (2.5, 1.0):
            p = base(47e-9, c5, 1e3, vth)
            e, im, pk, E, t90, tj, v = plug(p)
            line = (f'C5 {c5*1e9:4.0f} nF Vth {vth}：峰值 {im:4.1f} A / {pk:3.0f} W，能量 {E:.2f} J，90% {t90:4.1f} ms，'
                    f'结温升（一只承担全部）{tj:3.0f} °C')
            if vth == 2.5:
                _, _, _, _, _, _, v = plug(p, T=0.3)   # 等 C5 充到稳态再做过压
                line += f'；慢升压切断点 {ov_ramp(p, v, 1e2):.1f} V（100 V/s）/ {ov_ramp(p, v, 1e3):.1f} V（1 V/ms）'
            print(line, flush=True)
    print('== 3. 直接插到过高电压（C1 47 nF、C5 680 nF） ==')
    for vth in (2.5, 1.0):
        for vin in (50.0, 55.0):
            p = base(47e-9, 680e-9, 1e3, vth)
            o, _ = model.run(lambda t: vin * min(t / 1e-6, 1), 0.1, p, dtmax=5e-6, rec=1e-4)
            print(f'Vth {vth} 插 {vin:.0f} V：母线最高 {max(r[4] for r in o):.2f} V，P 管最大 {max(r[5] for r in o):.2f} A')
