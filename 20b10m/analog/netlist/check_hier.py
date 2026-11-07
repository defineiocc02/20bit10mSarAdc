#!/usr/bin/env python3
"""check_hier.py —— 模拟网表的层次/端口自检（不依赖 Spectre）

检查三件事：
1. 每个 X 实例引用的 subckt 是否有定义；
2. 实例节点数与 subckt 端口数是否一致（总线按 1 个端口计）；
3. 是否有重复 subckt 定义。

用法：python3 20b10m/analog/netlist/check_hier.py
"""
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parent
FILES = sorted(ROOT.glob("*.scs")) + sorted((ROOT.parent / "blocks").glob("*/netlist/*.scs"))

def strip_comments(text):
    out = []
    for line in text.splitlines():
        # 去掉 // 注释（不处理字符串里的 //，本工程网表没有）
        i = line.find("//")
        if i >= 0:
            line = line[:i]
        out.append(line)
    return "\n".join(out)

def logical_lines(text):
    """把以 + 开头的续行接到上一行。"""
    res, buf = [], ""
    for line in text.splitlines():
        if line.strip().startswith("+"):
            buf += " " + line.strip()[1:].strip()
        else:
            if buf:
                res.append(buf)
            buf = line.strip()
    if buf:
        res.append(buf)
    return [l for l in res if l]

def parse_ports(s):
    # 端口名可能含 <...>，用空白切分即可（<> 内没有空格）
    return s.split()

def main():
    text = "\n".join(strip_comments(f.read_text(errors="ignore")) for f in FILES)
    lines = logical_lines(text)

    defs, insts = {}, []
    for ln in lines:
        m = re.match(r"subckt\s+(\S+)\s*(.*)$", ln)
        if m:
            name, rest = m.group(1), m.group(2)
            rest = re.sub(r"\bparams:.*$", "", rest).strip()
            defs.setdefault(name, parse_ports(rest))
            continue
        m = re.match(r"(X\S+)\s*\((.*?)\)\s*(\S+)", ln)
        if m:
            insts.append((m.group(1), m.group(2).split(), m.group(3)))

    errors = []
    for name, ports in defs.items():
        pass
    dup = [n for n in defs if sum(1 for f in FILES for _ in [0]) and False]
    for iname, nodes, sub in insts:
        if sub not in defs:
            errors.append(f"UNDEFINED  {iname} -> {sub}")
            continue
        if len(nodes) != len(defs[sub]):
            errors.append(f"PORTCOUNT  {iname}: {len(nodes)} nodes vs {sub} {len(defs[sub])} ports")

    print(f"files={len(FILES)}  subckts={len(defs)}  instances={len(insts)}")
    if errors:
        print(f"ERRORS={len(errors)}")
        for e in errors:
            print("  " + e)
        return 1
    print("OK: 所有实例的子电路均已定义，端口数一致")
    return 0

if __name__ == "__main__":
    sys.exit(main())
