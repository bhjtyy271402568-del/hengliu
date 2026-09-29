import json
import re
from pathlib import Path

DECK_DIR = Path(r"C:\Users\Administrator\Desktop\henliu\LT3763_老师一对一研讨版")
OUTLINE = DECK_DIR / "outline.md"
SPEC = DECK_DIR / "deck_spec.json"

layout_map = {
    1: ("cover", "用整板PCB建立项目第一印象", "整板PCB作为大幅主视觉，标题与四项核心指标置于留白区域"),
    2: ("agenda", "建立从介绍到请老师把关的交流顺序", "四段连续路线图，从电路板介绍、设计依据、PCB实现到老师结论"),
    3: ("context", "说明应用需求和首版实验板定位", "左侧需求背景，右侧36V、29V、18A、522W四个关键数字"),
    4: ("data evidence", "集中呈现设计边界", "工程规格表配合工作边界示意，避免营销式指标卡"),
    5: ("architecture", "说明能量、控制、设定与辅助四条路径", "横向主功率流程居中，控制与辅助路径在上下分层标注"),
    6: ("annotated evidence", "在整板上建立接口和节点名称", "大幅PCB图加外围引线标注，右下角保留简短图例"),
    7: ("annotated evidence", "帮助老师快速定位板上功能分区", "整板PCB为主体，以半透明区域框标出四个功能区"),
    8: ("process", "区分平均功率路径、高di/dt路径和续流路径", "功率区PCB为主体，三种颜色箭头分别标出三类电流路径"),
    9: ("concept", "解释为何采用LT3763", "数据手册证据左侧，右侧按控制职责和选择理由讲解"),
    10: ("architecture", "解释芯片内部各闭环和驱动关系", "内部框图占主要区域，右侧用中文导读按四条路径解释"),
    11: ("calculation", "推导输出电压设定", "左侧数据手册与中文导读，右侧按电阻值、公式、结果、验证项逐步推导"),
    12: ("comparison", "区分正常调节值和内部过压阈值", "同一分压网络下并列比较1.206V与1.515V两条计算链"),
    13: ("calculation", "说明18A工作点和20.4A典型硬件量程", "沿用已批准样张布局"),
    14: ("process", "推导MCU/DAC到CTRL1的电压换算", "从18A目标到45mV、CTRL1约1.32V、DAC约2.94V的四步信号链"),
    15: ("data evidence", "说明CTRL2温度降额曲线", "左侧数据手册与中文导读，右侧温度—允许电流估算表和设计含义"),
    16: ("calculation", "推导UVLO启动与关闭阈值", "电阻分压示意配两条公式，右侧解释适用输入范围"),
    17: ("concept", "澄清FBIN的功能边界", "输入电压下降到输出电流折返的因果流程，附功能与非功能对照"),
    18: ("calculation", "核对36V满载下输入平均电流余量", "功率平衡公式居中，右侧比较15.3A工作点和18至22A输入限流范围"),
    19: ("concept", "解释IVIN滤波网络为何较慢", "左侧数据手册原文与中文导读，右侧RC网络、平均采样用途和保护边界"),
    20: ("comparison", "同时说明开关频率和补偿网络", "左右两部分分别为200kHz频率设定和R4/C42补偿起点，底部为样机验证项"),
    21: ("process", "解释INTVCC到BOOST的驱动供电链", "INTVCC、D5、C76、BOOST-SW和TG组成简洁流程，旁边列PCB约束"),
    22: ("data evidence", "用关键参数说明主MOS选型", "左侧器件数据手册与中文导读，右侧电压、导通电阻、栅极电荷和并联目的"),
    23: ("comparison", "区分静态导通损耗和动态开关风险", "左右对照导通损耗与开关损耗，中间强调并联动态均流"),
    24: ("calculation", "推导L6纹波和峰值电流", "参数列在左，公式链居中，右侧以额定和饱和电流作裕量比较"),
    25: ("calculation", "核对两只采样电阻的稳态损耗与热风险", "R1与R12并排计算，下方说明焊盘、铜皮和脉冲因素"),
    26: ("annotated evidence", "说明不同电容在高频和低频中的分工", "PCB局部图为主体，旁边按本地MLCC、远端大电容、输出电容解释"),
    27: ("architecture", "说明输入保护器件的动作链和耐压关系", "输入保护PCB与三张器件证据组合，配从TVS到P-MOS和栅极钳位的中文导读"),
    28: ("calculation", "推导输入RC阻尼支路的脉冲应力", "以能量、初始电流、瞬时功率、时间常数四步计算为主，突出脉冲额定需要查证"),
    29: ("concept", "说明LM5164辅助电源的作用与验证顺序", "数据手册证据配36V到12V再到控制电源的流程和中文导读"),
    30: ("architecture", "说明四层全2oz与制造约束", "四层剖面示意配铜厚、孔工艺和仍需检查的局部瓶颈"),
    31: ("annotated evidence", "逐段审查顶层大电流路径", "顶层功率区大图加编号路径，侧边列焊盘出口、窄颈、转角和连接器检查项"),
    32: ("annotated evidence", "聚焦半桥最小高di/dt环路", "半桥PCB局部图大幅展示，用闭合箭头标出MLCC、上下桥和GND回路"),
    33: ("annotated evidence", "解释SW节点面积控制原则", "内层SW图为主体，旁边对照需要保留与应避免的跨层扩展"),
    34: ("annotated evidence", "检查Kelvin采样入口和敏感线", "功率区图上分别标出大电流路径与两根差分采样路径，右侧列布线原则"),
    35: ("comparison", "比较L3、底层和过孔阵列的电流分工", "三张层视图并列，使用相同位置框和简短中文导读进行跨层对照"),
    36: ("summary", "确认不再反复讨论的已定事项", "一张简洁确认清单，按输出目标、铜厚工艺、本地电容和SW处理分组"),
    37: ("review", "集中呈现需要老师重点判断的五项风险", "按控制环、并联MOS、开关环、采样与层间、输入保护五条排序"),
    38: ("timeline", "给出可执行的分级上电流程", "四阶段水平时间线，每阶段标出检查内容和停止条件"),
    39: ("matrix", "建立波形、温度和工况的测量清单", "波形与温度两列，底部用工况轴串联启动、阶跃、满载和故障"),
    40: ("summary", "把老师意见转化为可执行结论", "必须修改、必须验证、可以保留三列，底部给出会后闭环动作"),
}

visual_map = {
    2: "四阶段工程交流路线图",
    3: "关键指标与首版实验板定位",
    4: "工程规格和工作边界表",
    5: "同步Buck系统级能量与控制框图",
    14: "DAC到CTRL1的逐级换算流程",
    16: "UVLO电阻分压和迟滞阈值示意",
    17: "FBIN输入电压折返因果流程",
    18: "输入输出功率平衡计算",
    20: "频率设定与环路补偿双主题",
    21: "自举驱动供电链",
    23: "MOS静态与动态损耗对照",
    24: "电感纹波三角波和裕量比较",
    25: "R1与R12功耗对照",
    28: "RC阶跃能量与脉冲应力计算链",
    30: "四层2oz层叠剖面",
    36: "已确认事项清单",
    37: "老师审查重点优先级列表",
    38: "分级上电时间线",
    39: "测量矩阵",
    40: "三类结论框架",
}

text = OUTLINE.read_text(encoding="utf-8")
matches = list(re.finditer(r"^## Slide (\d+)：(.+)$", text, re.M))
slides = []
for idx, match in enumerate(matches):
    number = int(match.group(1))
    title = match.group(2).strip()
    block = text[match.end(): matches[idx + 1].start() if idx + 1 < len(matches) else text.find("## 素材映射规则")]
    top_bullets = [m.group(1).strip() for m in re.finditer(r"^- (.+)$", block, re.M)]
    role_line = next((x for x in top_bullets if x.startswith("角色：")), "角色：正文")
    key_points = [x for x in top_bullets if not x.startswith("角色：") and x != "Required images:"]
    req_images = []
    pattern = re.compile(r"^  - (.+?)\n(?:.*\n)*?\s+!\[([^\]]+)\]\(([^)]+)\)", re.M)
    for desc, alt, rel in pattern.findall(block):
        is_datasheet = Path(rel).name.lower().startswith(("lt_", "bsc_", "sum_", "bzt_", "lm_"))
        req_images.append({
            "path": rel,
            "role": desc.strip() + "；" + alt.strip(),
            "fidelity": ("strict datasheet input asset; preserve the original English text, figure numbers, curves, axes, labels, values and device model" if is_datasheet else "strict PCB input asset; preserve all components, pads, vias, copper shapes, nets and relative positions"),
        })
    role, intent, composition = layout_map[number]
    datasheet_page = any("datasheet" in x.get("fidelity", "") for x in req_images)
    constraints = [
        "使用已批准Slide 13作为风格参考，只匹配配色、字体气质、密度和视觉语言，不复制相同版式",
        "所有中文、器件编号、数值、单位和公式必须准确清晰，不得出现乱码或额外问句",
        "面向老师一对一技术研讨，先解释设计依据，再陈述需要验证的边界，不使用营销或耸动措辞",
        "不得显示页码、水印、无关Logo或装饰性电路图",
    ]
    if datasheet_page:
        constraints.append("数据手册导读只保留必要的1至2句，指出看哪一段或哪幅图以及它支持什么结论；若公式和标注已充分说明，不再增加重复说明框")
    if req_images:
        constraints.append("严格输入素材必须原样可辨识地嵌入；只允许等比例缩放或裁切，不得重绘、替换、改变网络或数据")
    slide = {
        "number": number,
        "title": title,
        "role": role,
        "intent": intent,
        "key_points": key_points,
        "speaker_focus": "先说明本页结论，再按视觉顺序解释计算、数据手册依据或PCB证据。",
        "local_context": {"required_background": "；".join(key_points)},
        "layout": {
            "composition": composition,
            "content_zones": "单行标题区、主体证据/计算区、必要时一条简短结论或验证提示",
            "variation_rule": "保持同一蓝白专业风格，但相邻页面避免重复相同卡片布局",
            "spacing": "清晰对齐、留白充分、重要内容不重叠，标题不得换行",
        },
        "visual_elements": {"main_visual": visual_map.get(number, "使用本页严格输入素材作为主要证据" if req_images else "与本页工程关系匹配的简洁技术示意")},
        "constraints": constraints,
    }
    if req_images:
        slide["required_images"] = req_images
        slide["source_image_rules"] = "将严格素材作为原始证据；PCB图只加外围箭头、边框或标注，数据手册图配中文导读。"
    if number == 13:
        slide["sample_approved"] = True
    slides.append(slide)

spec = {
    "deck_name": "LT3763_老师一对一研讨版",
    "language": "Chinese",
    "goal": "先向老师完整介绍36V输入、约29V/18A输出的LT3763同步降压恒流电源板，再说明原理图参数如何计算、器件为何这样选择、设计怎样落实到四层PCB，最后请老师对尚未闭环的问题和样机验证边界给出结论。",
    "deck_context": {
        "source_summary": "首版约522W同步Buck恒流电源板，控制器为LT3763，标称36V输入、29V/18A输出，四层全2oz，盘中孔采用树脂塞孔加电镀盖孔。主线是设计介绍和依据说明，而不是问题清单。",
        "core_claim": "设计者能够说明每个关键参数的计算和选型依据；对补偿、动态均流、输入保护配合、局部高电流与热性能等无法仅靠静态计算闭环的事项，请老师划分为必须修改、必须验证和可以保留。",
        "canonical_terms": ["LT3763", "VCC_BAT", "$1N947", "SW", "L6", "R1", "R12", "CTRL1", "CTRL2", "FBIN", "SENSE±", "IVINP/N", "Kelvin采样"],
        "datasheet_explanation_rule": "数据手册截图旁只做必要的1至2句中文导读；如果公式或标注已将关系说清，不重复解释，也不为此增加页面。",
    },
    "selected_image_backend": "built-in image tool",
    "max_concurrent_slides": 3,
    "sample_generation_method": {
        "backend_used": "built-in image tool",
        "tool_name": "image_gen",
        "mode": "edit",
        "prompt_source": "conversation-approved Slide 13 generation and revision prompts",
        "size": "16:9 landscape, built-in generated resolution",
        "quality": "built-in default",
        "model_config": "built-in image generation default; model identifier not exposed",
        "approved_sample_path": str(DECK_DIR / "origin_image" / "slide_13.png"),
        "input_context_preparation": "parent inspects every local required image with view_image; workers use referenced_image_paths including approved sample and required assets",
        "handoff_rule": "Subagents must use the same built-in image_gen edit path with the approved sample as style-only reference and return a blocker if unavailable.",
    },
    "style": {
        "name": "清爽专业风（面向老师一对一技术研讨）",
        "visual_direction": "白色或极浅蓝背景，深蓝单行标题，克制的蓝灰分隔线，清晰证据链和工程计算层级；像工程师带着原理图和数据手册逐项讲解，不像正式答辩海报或营销仪表盘",
        "color_palette": "主色深蓝#123B7A，辅助蓝#2563EB和浅蓝#EEF5FF，中性文字#1F2937，风险或待验证信息仅少量使用琥珀色",
        "typography": "清晰无衬线中文；标题粗体且单行；公式和关键参数明显放大；正文左对齐，最小字号保持屏幕可读",
        "texture_and_finish": "干净平面化技术资料风，轻边框、少量浅色底，不使用厚重阴影、霓虹或卡通装饰",
        "datasheet_treatment": "原文截图作为证据，最多配1至2句中文导读；避免重复说明和额外信息框",
        "pcb_treatment": "PCB截图保持原始网络和几何，只允许外围标签、半透明区域、箭头和编号标注",
    },
    "approved_style_reference": {
        "path": str(DECK_DIR / "origin_image" / "slide_13.png"),
        "role": "approved sample slide style reference",
        "fidelity": "match palette, typography mood, density and engineering explanation style only; do not copy exact layout or content",
    },
    "slides": slides,
}

SPEC.write_text(json.dumps(spec, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"wrote {SPEC} with {len(slides)} slides")
