"""底部散热器要多大：不同鳍片高度下，散热器温升和上管结温（推断，量级估算）。
模型：
- 37 片鳍片（1.2 mm、间距 3.522 mm、长 95 mm），鳍高 H 可变；
- 风扇 AFB1212HH 按直线风扇曲线（95 CFM / 75.8 Pa，规格书），一半风量走鳍片（其余走两板之间和上层）；
- 风道压降 = 平行板层流摩擦 + 进出口和面板开孔损失（K = 2.5）；
- 换热用平行板发展段努塞尔数，鳍片效率按直肋 tanh(mL)/mL；
- 加底板扩散热阻 0.1 K/W，以及空气沿程升温。
上管：每只 5.0 W，结到散热器约 6.5 K/W（66 孔约 5.5–6.1 + 导热垫 + 扩散）。环境（进风）40 °C。
用法：python3 heatsink_size.py"""
import math
RHO, CP, MU, K_AIR, PR = 1.13, 1007, 1.9e-5, 0.027, 0.71
K_AL = 200.0
N_FIN, T_FIN, PITCH, L = 37, 1.2e-3, 3.5222e-3, 0.095
GAP = PITCH - T_FIN
Q_MAX, P_MAX, SHARE = 95 * 4.719e-4, 75.8, 0.5
P_SINK = 36.0                      # 进散热器的总热量（项目记忆：约 36 W）
P_TOP, R_JS = 5.0, 6.5             # 上管每只功耗、结到散热器热阻
T_AIR = 40.0

def sink(h_fin):
    global Q_MAX, P_MAX
    area_ch = (N_FIN - 1) * GAP * h_fin
    dh = 2 * GAP
    # 风扇曲线和风道压降求交点（二分）
    lo, hi = 1e-5, Q_MAX * SHARE
    for _ in range(60):
        q = (lo + hi) / 2
        v = q / area_ch
        re = RHO * v * dh / MU
        dp = (96 / re * L / dh + 2.5) * 0.5 * RHO * v * v
        q_fan = Q_MAX * (1 - dp / P_MAX) * SHARE
        lo, hi = (q, hi) if q < q_fan else (lo, q)
    v = q / area_ch; re = RHO * v * dh / MU
    gz = dh / L * re * PR
    nu = 7.54 + 0.03 * gz / (1 + 0.016 * gz ** (2 / 3))
    h = nu * K_AIR / dh
    m = math.sqrt(2 * h / (K_AL * T_FIN)); eta = math.tanh(m * h_fin) / (m * h_fin)
    area = N_FIN * 2 * h_fin * L
    r = 1 / (h * eta * area) + 1 / (2 * RHO * CP * q) + 0.1
    return q / 4.719e-4, v, r

FANS = [('120 mm AFB1212HH（规格书）', 95, 75.8), ('92 mm 级（推断 55 CFM / 50 Pa）', 55, 50), ('80 mm 级（推断 40 CFM / 40 Pa）', 40, 40)]

if __name__ == '__main__':
    for name, cfm, pa in FANS[1:]:
        Q_MAX, P_MAX = cfm * 4.719e-4, pa
        for hf in (20, 15):
            c, v, r = sink(hf / 1000); ts = T_AIR + P_SINK * r
            print(f'{name}，鳍高 {hf} mm：散热器 {r:.2f} K/W，{ts:.0f} °C，上管结温 {ts + P_TOP * R_JS:.0f} °C')
    Q_MAX, P_MAX = 95 * 4.719e-4, 75.8
    print('鳍高 mm | 鳍片风量 CFM | 风速 m/s | 散热器 K/W | 散热器温度 °C | 上管结温 °C')
    for hf in (33.5, 25, 20, 15, 10):
        cfm, v, r = sink(hf / 1000)
        ts = T_AIR + P_SINK * r
        print(f'{hf:7.1f} | {cfm:12.1f} | {v:8.1f} | {r:10.2f} | {ts:13.0f} | {ts + P_TOP * R_JS:10.0f}')
    # 风扇停转：机壳外表面自然对流 + 辐射散掉整机热量（散热器大小几乎不起作用）
    a_box = 2 * (0.144 * 0.165 + 0.144 * 0.137 + 0.165 * 0.137)
    for p_all in (50, 60):
        print(f'风扇停：整机 {p_all} W，机壳表面 {a_box:.3f} m²、h ≈ 9 W/m²K → 机内温升约 {p_all / (a_box * 9):.0f} K')
