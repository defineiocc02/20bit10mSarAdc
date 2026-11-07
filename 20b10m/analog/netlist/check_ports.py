#!/usr/bin/env python3
"""check_ports.py —— 数模端口一致性检查

比较：
1. analog/netlist/digital_stubs.scs 的 DigitalTop_stub 端口
2. digital/DigitalTop.sv 的 module DigitalTop 端口
输出：端口清单 CSV（interface/ports_10m.csv）与差异报告。
"""
import re, csv, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]      # 20b10m/
SCS = ROOT / "analog/netlist/digital_stubs.scs"
SV  = ROOT / "digital/DigitalTop.sv"
OUT = ROOT / "interface/ports_10m.csv"

def bus(name):
    m = re.match(r"(\w+)<(\d+):(\d+)>", name)
    if m:
        return m.group(1), int(m.group(2)) - int(m.group(3)) + 1
    return name, 1

def scs_ports():
    text = SCS.read_text()
    m = re.search(r"subckt\s+DigitalTop_stub\s+(.*?)ends", text, re.S)
    toks = [t for t in m.group(1).split() if t != "+"]
    res = []
    for t in toks:
        b, w = bus(t)
        res.append((b, w, "inout"))
    return res

def sv_ports():
    text = SV.read_text()
    m = re.search(r"module\s+DigitalTop\s*\((.*?)\);", text, re.S)
    body = re.sub(r"//.*", "", m.group(1))
    res, cur_d, cur_w = [], None, 1
    for part in [x.strip() for x in body.split(",")]:
        mm = re.match(r"(input|output|inout)\b", part)
        if mm:
            cur_d = mm.group(1)
            cur_w = 1
            part = part[mm.end():].strip()
        mb = re.search(r"\[(\d+):(\d+)\]", part)
        if mb:
            cur_w = abs(int(mb.group(1)) - int(mb.group(2))) + 1
        ids = [i for i in re.findall(r"[A-Za-z_]\w*", part)
               if i not in ("logic", "wire", "tri")]
        if not ids or cur_d is None:
            continue
        res.append((ids[-1], cur_w, cur_d))
    return res

def main():
    a = scs_ports(); d = sv_ports()
    amap = {n: (w, dr) for n, w, dr in a}
    dmap = {n: (w, dr) for n, w, dr in d}

    errs = []
    for n, (w, _) in amap.items():
        if n not in dmap:
            errs.append(f"SV 缺端口: {n}")
        elif dmap[n][0] != w:
            errs.append(f"位宽不一致: {n} scs={w} sv={dmap[n][0]}")
    for n in dmap:
        if n not in amap:
            errs.append(f"stub 缺端口: {n}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["module", "port", "width", "sv_direction"])
        for n, (wd, dr) in dmap.items():
            w.writerow(["DigitalTop", n, wd, dr])

    print(f"stub ports={len(amap)}  sv ports={len(dmap)}")
    if errs:
        print("ERRORS:")
        for e in errs: print("  " + e)
        return 1
    print("OK: DigitalTop 模拟黑盒与 SV 端口逐字一致")
    return 0

if __name__ == "__main__":
    sys.exit(main())
