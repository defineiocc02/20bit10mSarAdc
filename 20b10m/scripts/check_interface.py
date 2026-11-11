#!/usr/bin/env python3
"""check_interface.py —— 接口三方一致性检查（不依赖 HDL 工具）

比对三份独立来源：
  1. spec/interfaces_v2.csv        契约（模块/端口/方向/位宽/状态）
  2. 20b10m/digital/*.sv           实现（ANSI 端口声明）
  3. analog/netlist/digital_stubs.scs  模拟侧黑盒视图

检查项：
  A. CSV 中 status=impl 的行，在 RTL 里必须存在且方向/位宽一致
  B. RTL 里的每个端口，CSV 必须有对应行（不能有"藏起来的端口"）
  C. CSV 里 status=planned 的行，RTL 里必须还没有（防止文档超前于实现）
  D. digital_stubs.scs 的 DigitalTop_stub 端口集合必须与 DigitalTop 完全一致

用法：
  python3 scripts/check_interface.py            # 检查，失败退出码 1
  python3 scripts/check_interface.py --emit     # 只打印 RTL 端口清单

退出码：0 全过 / 1 有错误
"""
from __future__ import annotations

import csv
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SV_DIR = ROOT / "digital"
CSV_PATH = ROOT / "spec" / "interfaces_v2.csv"
STUB = ROOT / "analog" / "netlist" / "digital_stubs.scs"

PORT_RE = re.compile(
    r"\b(input|output|inout)\s+(?:logic|wire|reg)?\s*(\[[^\]]*\])?\s*(\w+)"
)


def parse_width(rng: str | None) -> int:
    if not rng:
        return 1
    m = re.match(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]", rng)
    if not m:
        raise ValueError(f"无法解析位宽: {rng}")
    hi, lo = int(m.group(1)), int(m.group(2))
    return abs(hi - lo) + 1


def parse_rtl() -> dict[str, dict[str, tuple[str, int]]]:
    """{module: {port: (dir, width)}}"""
    mods: dict[str, dict[str, tuple[str, int]]] = {}
    for f in sorted(SV_DIR.glob("*.sv")):
        if f.name.startswith("tb_"):
            continue
        txt = f.read_text(encoding="utf-8")
        m = re.search(r"module\s+(\w+)\s*(?:#\s*\(.*?\)\s*)?\((.*?)\);", txt, re.S)
        if not m:
            print(f"[ERR] {f.name}: 找不到 module 声明")
            continue
        mod, body = m.group(1), re.sub(r"//.*", "", m.group(2))
        ports: dict[str, tuple[str, int]] = {}
        for pm in PORT_RE.finditer(body):
            d, w, n = pm.group(1), pm.group(2), pm.group(3)
            if n in ports:
                print(f"[ERR] {mod}: 端口 {n} 重复声明")
            ports[n] = (d, parse_width(w))
        mods[mod] = ports
    return mods


def parse_csv() -> list[dict]:
    with CSV_PATH.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def parse_stub() -> list[str]:
    txt = STUB.read_text(encoding="utf-8")
    txt = re.sub(r"//.*", "", txt)
    m = re.search(r"subckt\s+DigitalTop_stub\s+(.*?)\s+ends", txt, re.S)
    if not m:
        return []
    body = m.group(1).replace("\n", " ").replace("+", " ")
    return [p for p in body.split() if p]


def main() -> int:
    if "--emit" in sys.argv:
        for mod, ports in parse_rtl().items():
            for n, (d, w) in ports.items():
                print(f"{mod},{n},{d},{w}")
        return 0

    errors: list[str] = []
    warns: list[str] = []

    rtl = parse_rtl()
    rows = parse_csv()
    csv_impl = {(r["module"], r["port"]): r for r in rows if r["status"] == "impl"}
    csv_planned = {(r["module"], r["port"]): r for r in rows if r["status"] == "planned"}

    # A: CSV impl -> RTL
    for (mod, port), r in csv_impl.items():
        if mod not in rtl:
            errors.append(f"A: CSV 有模块 {mod}，RTL 里没有")
            continue
        if port not in rtl[mod]:
            errors.append(f"A: CSV 有 {mod}.{port}，RTL 里没有")
            continue
        d, w = rtl[mod][port]
        if d != r["dir"]:
            errors.append(f"A: {mod}.{port} 方向不一致 CSV={r['dir']} RTL={d}")
        if w != int(r["width"]):
            errors.append(f"A: {mod}.{port} 位宽不一致 CSV={r['width']} RTL={w}")

    # B: RTL -> CSV
    for mod, ports in rtl.items():
        for port, (d, w) in ports.items():
            if (mod, port) not in csv_impl:
                errors.append(f"B: RTL 有 {mod}.{port}（{d}/{w}bit），CSV 未登记")

    # C: planned 必须尚未实现
    for (mod, port), r in csv_planned.items():
        if mod in rtl and port in rtl[mod]:
            errors.append(f"C: {mod}.{port} 标为 planned，但 RTL 已实现 → 请改状态")

    # D: stub vs DigitalTop
    stub = parse_stub()
    top = set(rtl.get("DigitalTop", {}))
    norm = lambda s: re.sub(r"<\d+:\d+>", "", s)
    stub_plain = {norm(p) for p in stub}
    if not stub:
        errors.append("D: 解析不到 DigitalTop_stub")
    else:
        if stub_plain != top:
            only_stub = sorted(stub_plain - top)
            only_rtl = sorted(top - stub_plain)
            if only_stub:
                errors.append(f"D: stub 多出 {only_stub}")
            if only_rtl:
                errors.append(f"D: RTL 多出 {only_rtl}")
        # 位宽也要对
        for p in stub:
            m = re.match(r"(\w+)<(\d+):(\d+)>", p)
            if m and m.group(1) in rtl["DigitalTop"]:
                want = abs(int(m.group(2)) - int(m.group(3))) + 1
                got = rtl["DigitalTop"][m.group(1)][1]
                if want != got:
                    errors.append(f"D: {m.group(1)} 位宽 stub={want} RTL={got}")

    impl_n = sum(len(v) for v in rtl.values())
    print(f"RTL 模块 {len(rtl)} 个，端口 {impl_n} 个")
    print(f"CSV 行 {len(rows)}（impl {len(csv_impl)} / planned {len(csv_planned)}）")
    print(f"stub 端口 {len(stub_plain)} 个")
    for w in warns:
        print(f"[WARN] {w}")
    if errors:
        print(f"\n[FAIL] {len(errors)} 项：")
        for e in errors:
            print("  -", e)
        return 1
    print("\n[OK] CSV ↔ RTL ↔ stub 三方一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
