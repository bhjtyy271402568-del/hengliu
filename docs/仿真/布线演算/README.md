# 布线演算脚本（2026-10-27）

- `aux_cur.json`：从 10-27 工程（指纹 `c183273c7a5e`）提取的辅助电源板器件和焊盘（mm，y 向上；焊盘为旋转后的外接矩形，网络取自 PCB）。
- `drc.py`：焊盘间距和本体重叠检查（原脚本读 `pagedata.json`，含两块板）。
- `router.py`：两层网格 A* 布线（0.25 mm 格点，电源按电流取线宽，细间距引脚旁允许收窄到 0.25 mm），地网络最后铺铜并检查连通。
  `python3 -I router.py aux_cur.json out.json`
- `place_aux.py`：在 `aux_cur.json` 基础上挪动 / 旋转 / 新增器件，生成 `aux_new.json`（建议摆放）。
- `rail_len.py`、`gnd_path.py`：沿铜计算关键路径长度、地铺铜回流距离。
- 需要 numpy、scipy。结果是“比较两种摆放难易”的演算，不是最终走线。
