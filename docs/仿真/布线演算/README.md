# 布线演算脚本（2026-10-27）

- `aux_cur.json`：从 10-27 工程（指纹 `c183273c7a5e`）提取的辅助电源板器件和焊盘（mm，y 向上；焊盘为旋转后的外接矩形，网络取自 PCB）。
- `drc.py`：焊盘间距和本体重叠检查（原脚本读 `pagedata.json`，含两块板）。
- `router.py`：两层网格 A* 布线（0.25 mm 格点，电源按电流取线宽，细间距引脚旁允许收窄到 0.25 mm），地网络最后铺铜并检查连通。
  `python3 -I router.py aux_cur.json out.json`
- `place_aux.py`：在 `aux_cur.json` 基础上挪动 / 旋转 / 新增器件，生成 `aux_new.json`（建议摆放）。
- `rail_len.py`、`gnd_path.py`：沿铜计算关键路径长度、地铺铜回流距离。
- 需要 numpy、scipy。结果是“比较两种摆放难易”的演算，不是最终走线。

## 恒流源板（四层）
- `main_cur.json`：10-27 恒流源板器件和焊盘；`geom.json`：散热器凸台、安装孔（来自 Codex 交付包 geometry.json）。
- `router4.py`：L1 / L3 / L4 三层走线，L2 当 GND / PGND 平面（按焊盘就近分区）；40 A 网络按“焊盘周围铺铜”生成铺铜区，
  其他线不能穿过别人的铺铜区；大电流网络上的小焊盘按尾巴走线，开尔文线强制接到 R56 / R42 焊盘；最后给地小焊盘找过孔位置。
  `python3 -I router4.py main_cur.json out.json geom.json`（单轮约 3–4 分钟）
- `place_main.py`：在现状上挪动器件（带重叠 / 间距 / 凸台 / 安装孔检查），生成 `main_new.json`。

## 10-30 终审（指纹 `46a44fa67e30`，复核文件第 27 节）
- `review60_gerber.py`：渲染 Gerber 四层铜、阻焊、丝印、钢网（支持宏孔径、圆弧、区域），输出 lay.pkl。`python3 -I review60_gerber.py Gerber目录 lay.pkl`
- `review60_gerber_nets.py`：按网络核对 Gerber 每块铜（短路 / 漏导出）；`review60_gap.py`：异网最小间距；`review60_refvoid.py`：信号线参考面；`review60_drl.py`：钻孔读取。
- `review60_fig.py`：终审标注图 `终审标注_20261030.png`。
- 注意：`review50_geo.py` 要传第 4 个参数（Codex 快照 JSON），否则 U2（MCU）封装属性为空会被漏掉，VCC 会被误报为断开。
- 10-30 四层补铜版（`3f423d36ddb0`，复核文件 27.7 节）：`review70_robust.py geo.pkl lay.pkl 0.05`（Gerber 收缩连通测试：颈部 < 2e 视为断开）、
  `review70_viacontact.py`、`review70_neck.py`、`review70_necks.py`（窄接头放大图 `窄接头_20261030.png`）。

## 辅助板前端布局规划（2026-10-31）
- `aux_front_plan.py aux_cur.json 输出.png`：10-27 版辅助板防反接 + LM5069 + 放行的现状与建议摆放（y 向上），图 `辅助板前端布局规划_20261031.png`。说明见 `docs/辅助板前端布局规划_2026-10-31.md`。
