"""嘉立创 EDA 专业版工程（.epro2）解析：列出板子、导出器件表、对比两个版本、检查未登记的原理图文件。

用法：
  python3 -I tools/epro_snapshot.py 工程.epro2            # 器件表（默认取最近修改的那块板）
  python3 -I tools/epro_snapshot.py --diff 旧.epro2 新.epro2
  python3 -I tools/epro_snapshot.py --status              # 会话开始时由钩子调用
"""
import argparse
import collections
import datetime
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import zipfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
LOG = ROOT / "docs" / "原理图版本.md"
EXTS = (".epro2", ".epro", ".enet")
TZ = datetime.timezone(datetime.timedelta(hours=8))


def fingerprint(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()[:12]


def load(path):
    """按文档分组读取 .epru 记录：{uuid: {type, time, meta, recs}}。"""
    with zipfile.ZipFile(path) as z:
        names = [n for n in z.namelist() if n.endswith(".epru")]
        if not names:
            sys.exit(f"{path}：里面没有 .epru，只支持 .epro2 格式")
        text = z.read(names[0]).decode("utf-8")
    docs, cur = {}, None
    for line in text.splitlines():
        i = line.find("||")
        if i < 0:
            continue
        try:
            head = json.loads(line[:i])
            body = line[i + 2:]
            body = body[:-1] if body.endswith("|") else body
            rec = json.loads(body) if body else {}
        except ValueError:
            continue
        if head.get("type") == "DOCHEAD":
            cur = docs.setdefault(rec.get("uuid"), {
                "type": rec.get("docType"), "time": rec.get("updateTime") or 0, "meta": {}, "recs": []})
        elif cur is not None:
            if head.get("type") == "META":
                cur["meta"] = rec
            elif cur["type"] in ("SCH_PAGE", "PCB", "DEVICE"):
                cur["recs"].append((head, rec))
    return docs


def boards(docs):
    """每块板 = 一份原理图（可多页）+ PCB，按最后修改时间从新到旧排列。"""
    out = []
    for uid, d in docs.items():
        if d["type"] != "BOARD":
            continue
        schs = {u for u, s in docs.items() if s["type"] == "SCH" and s["meta"].get("board") == uid}
        pages = [u for u, s in docs.items() if s["type"] == "SCH_PAGE" and s["meta"].get("schematic") in schs]
        pcbs = [u for u, s in docs.items() if s["type"] == "PCB" and s["meta"].get("board") == uid]
        time = max([docs[u]["time"] for u in pages + pcbs] or [d["time"]])
        out.append({"title": d["meta"].get("title", uid), "pages": pages, "pcbs": pcbs, "time": time})
    return sorted(out, key=lambda b: b["time"], reverse=True)


def stamp(ms):
    return datetime.datetime.fromtimestamp(ms / 1000, TZ).strftime("%Y-%m-%d %H:%M") if ms else "?"


def attrs_by_parent(recs):
    attrs = collections.defaultdict(dict)
    for head, rec in recs:
        if head.get("type") == "ATTR" and rec.get("parentId"):
            attrs[rec["parentId"]][rec.get("key")] = rec.get("value")
    return attrs


def components(docs, pages):
    devices = {}
    for u, d in docs.items():
        if d["type"] == "DEVICE":
            devices[u] = dict(d["meta"].get("attributes") or {})
            devices[u].update({r.get("key"): r.get("value") for h, r in d["recs"] if h.get("type") == "ATTR"})
    rows = {}
    for page in pages:
        recs = docs[page]["recs"]
        ids = {h.get("id") for h, r in recs if h.get("type") == "COMPONENT"}
        for cid, a in attrs_by_parent(recs).items():
            if cid not in ids or not a.get("Designator"):
                continue
            dev = devices.get(a.get("Device"), {})
            row = rows.setdefault(a["Designator"], {"value": "", "mpn": "", "bom": True})
            row["value"] = row["value"] or a.get("Value") or dev.get("Value") or ""
            row["mpn"] = row["mpn"] or a.get("Manufacturer Part") or dev.get("Manufacturer Part") or ""
            if str(a.get("Add into BOM", "yes")).lower() in ("no", "false"):
                row["bom"] = False
    return rows


def pad_nets(docs, pcb):
    recs = docs[pcb]["recs"]
    des = {cid: a["Designator"] for cid, a in attrs_by_parent(recs).items() if a.get("Designator")}
    pads = {}
    for head, rec in recs:
        if head.get("type") != "PAD_NET":
            continue
        key = head.get("id")
        try:
            key = json.loads(key) if isinstance(key, str) else key
        except ValueError:
            continue
        if isinstance(key, list) and len(key) >= 3 and key[1] in des:
            pads[f"{des[key[1]]}.{key[2]}"] = rec.get("padNet") or ""
    return pads


def net_groups(pads, keep):
    """把 keep 里的焊盘按网络分组；未连接的焊盘各自一组。"""
    groups = collections.defaultdict(set)
    for pad in keep:
        groups[pads[pad] or ("", pad)].add(pad)
    return groups


def net_label(net, pads):
    if isinstance(net, str) and not net.startswith("$"):
        return net
    return f"未命名网络（{short(pads, 3)}）" if isinstance(net, str) else f"未连接（{net[1]}）"


def natural(des):
    m = re.match(r"([A-Za-z_]*)(\d*)(.*)", des)
    return (m.group(1), int(m.group(2) or 0), m.group(3))


def pick(path):
    docs = load(path)
    bs = boards(docs)
    if not bs:
        sys.exit(f"{path}：没有找到板子")
    return docs, bs


def describe(path, bs):
    print(f"# {pathlib.Path(path).name}（指纹 `{fingerprint(path)}`）\n")
    print("| 板 | 原理图页 | PCB | 最后修改（UTC+8） |\n|---|---|---|---|")
    for b in bs:
        print(f"| {b['title']} | {' '.join(p[:8] for p in b['pages'])} | {' '.join(p[:8] for p in b['pcbs'])} | {stamp(b['time'])} |")
    print(f"\n下面取最近修改的板：**{bs[0]['title']}**\n")


def show(path):
    docs, bs = pick(path)
    describe(path, bs)
    rows = components(docs, bs[0]["pages"])
    print("| 位号 | 值 | 型号 | 备注 |\n|---|---|---|---|")
    for des in sorted(rows, key=natural):
        r = rows[des]
        print(f"| {des} | {r['value']} | {r['mpn']} | {'' if r['bom'] else '不进 BOM'} |")


def short(pads, limit=6):
    pads = sorted(pads, key=natural)
    return "、".join(pads[:limit]) + (f" 等 {len(pads)} 个" if len(pads) > limit else "") if pads else "无"


def diff(old, new):
    (od, ob), (nd, nb) = pick(old), pick(new)
    describe(old, ob)
    describe(new, nb)
    oc, nc = components(od, ob[0]["pages"]), components(nd, nb[0]["pages"])
    fmt = lambda r: f"{r['value'] or '-'} / {r['mpn'] or '-'}{'' if r['bom'] else '（不进 BOM）'}"
    print("## 器件变化\n")
    for des in sorted(set(oc) | set(nc), key=natural):
        if des not in nc:
            print(f"- 删除 {des}：{fmt(oc[des])}")
        elif des not in oc:
            print(f"- 新增 {des}：{fmt(nc[des])}")
        elif oc[des] != nc[des]:
            print(f"- 改值 {des}：{fmt(oc[des])} → {fmt(nc[des])}")
    if not (ob[0]["pcbs"] and nb[0]["pcbs"]):
        print("\n（有一边没有 PCB，跳过连接关系对比）")
        return
    op, np_ = pad_nets(od, ob[0]["pcbs"][0]), pad_nets(nd, nb[0]["pcbs"][0])
    common = set(op) & set(np_)
    og, ng = net_groups(op, common), net_groups(np_, common)
    old_of = {pad: net for net, pads in og.items() for pad in pads}
    print("\n## 连接变化（按 PCB 焊盘网络，只看两版都有的焊盘；自动网络名每版会重编号，只比连接关系）\n")
    for net, pads in sorted(ng.items(), key=lambda kv: natural(min(kv[1], key=natural))):
        sources = collections.defaultdict(set)
        for pad in pads:
            sources[old_of[pad]].add(pad)
        if len(sources) == 1:
            old = next(iter(sources))
            if og[old] == pads:
                if isinstance(old, str) and isinstance(net, str) and old != net and not (old + net).count("$"):
                    print(f"- 改名：{old} → {net}")
                continue
        parts = "；".join(f"原 {net_label(o, og[o])} 的 {short(sp)}" for o, sp in sources.items())
        print(f"- {net_label(net, pads)}：{parts}")
    fresh = sorted((p for p in np_ if p not in common and p.split(".")[0] not in oc), key=natural)
    if fresh:
        print("\n## 新增器件的连接\n")
        groups = net_groups(np_, set(np_))
        for pad in fresh:
            net = np_[pad] or ("", pad)
            print(f"- {pad}：{net_label(net, groups[net])}，连 {short(groups[net] - {pad})}")


def status():
    try:
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "-z"], capture_output=True, text=True, check=True).stdout
        files = [f for f in out.split("\0") if f.endswith(EXTS)]
    except (OSError, subprocess.CalledProcessError):
        files = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.suffix in EXTS]
    seen = set(re.findall(r"`([0-9a-f]{12})`", LOG.read_text(encoding="utf-8"))) if LOG.exists() else set()
    fresh = [f for f in files if fingerprint(ROOT / f) not in seen]
    if fresh:
        print(f"【原理图检查】有 {len(fresh)} 个原理图文件没有登记：{'、'.join(fresh)}。"
              "先用 tools/epro_snapshot.py --diff 和上一版对比，核对项目记忆，再登记到 docs/原理图版本.md。")
    else:
        print(f"【原理图检查】{len(files)} 个原理图文件都已登记，没有新版本。")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="*")
    ap.add_argument("--diff", action="store_true", help="对比两个文件：旧 新")
    ap.add_argument("--status", action="store_true", help="列出没有登记的原理图文件")
    args = ap.parse_args()
    if args.status:
        status()
    elif args.diff and len(args.files) == 2:
        diff(*args.files)
    elif len(args.files) == 1 and not args.diff:
        show(args.files[0])
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
