#!/usr/bin/env python3
"""check_pinout.py —— QFN-48 引脚表自检

检查：
  1. 脚号 1..48 连续无重复，另有 EP 一行
  2. 分组小计与文档声明一致（29 功能 + 19 电源/地）
  3. 每个引脚的域取值合法，电源/地脚不与信号脚同名冲突
  4. 与架构需求对齐：必须存在 VINP/VINN、CLKP/CLKN、VREF5/VREF2/VCM/VREFN、
     SPI 四线、CAL_TRIG、RSTN、LVDS 三对
用法：python3 scripts/check_pinout.py [--verbose]
"""
from __future__ import annotations

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "interface" / "pinout_qfn48.csv"

# 分组 -> (期望脚数, 是否计入"功能脚")
EXPECT = {
    "analog_in": (2, True),
    "ref": (4, True),
    "clk": (2, True),
    "lvds_out": (8, True),
    "spi": (6, True),
    "test": (3, True),
    "spare": (4, True),
    "pwr5": (4, False),
    "pwr18a": (2, False),
    "pwr18d": (1, False),
    "pwr_io": (2, False),
    "gnd": (10, False),
    "ep": (1, False),
}
REQUIRED = {
    "VINP", "VINN", "CLKP", "CLKN", "VREF5", "VREF2", "VCM", "VREFN",
    "SCLK", "SDI", "SDO", "CS", "CAL_TRIG", "RSTN",
    "DOUTP", "DOUTN", "CLKOUTP", "CLKOUTN", "DRDYP", "DRDYN",
}
VALID_DOMAIN = {"5V", "2.5V", "1.8V", "0V", "-"}
VALID_TYPE = {"AI", "AO", "DI", "DO", "IO", "LVDS", "PWR", "GND"}


def main() -> int:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")))
    errors: list[str] = []

    pins = [r["pin"] for r in rows]
    body = [p for p in pins if p != "EP"]
    if len(body) != 48:
        errors.append(f"脚数 {len(body)} != 48")
    if sorted(int(p) for p in body) != list(range(1, 49)):
        errors.append("脚号不是 1..48 连续无重复")
    if pins.count("EP") != 1:
        errors.append("EP 行缺失或重复")

    # 分组小计
    groups: dict[str, int] = {}
    for r in rows:
        groups[r["group"]] = groups.get(r["group"], 0) + 1
    for g, (want, _) in EXPECT.items():
        got = groups.get(g, 0)
        if got != want:
            errors.append(f"分组 {g}: {got} 脚，期望 {want}")
    func = sum(len([r for r in rows if r["group"] == g]) for g, (_, f) in EXPECT.items() if f)
    pwr = sum(len([r for r in rows if r["group"] == g]) for g, (_, f) in EXPECT.items() if not f and g != "ep")
    if (func, pwr) != (29, 19):
        errors.append(f"功能/电源地 = {func}/{pwr}，期望 29/19")

    # 域与类型
    for r in rows:
        if r["domain"] not in VALID_DOMAIN:
            errors.append(f"PIN {r['pin']} {r['name']}: 域 {r['domain']} 非法")
        if r["type"] not in VALID_TYPE:
            errors.append(f"PIN {r['pin']} {r['name']}: 类型 {r['type']} 非法")
        if r["type"] in ("PWR", "GND") and r["group"] not in ("pwr5", "pwr18a", "pwr18d", "pwr_io", "gnd", "ep"):
            errors.append(f"PIN {r['pin']} {r['name']}: 电源/地脚归到了 {r['group']}")

    # 需求覆盖
    names = {r["name"] for r in rows}
    missing = sorted(REQUIRED - names)
    if missing:
        errors.append(f"缺少必需信号: {missing}")

    # 同名信号脚不能同时出现在两个不同域
    dom_by_name: dict[str, set[str]] = {}
    for r in rows:
        if r["type"] not in ("PWR", "GND"):
            dom_by_name.setdefault(r["name"], set()).add(r["domain"])
    for n, ds in dom_by_name.items():
        if len(ds) > 1:
            errors.append(f"{n} 同时出现在多个域 {ds}")

    if "--verbose" in sys.argv:
        for r in rows:
            print(f"{r['pin']:>3} {r['name']:<9} {r['type']:<5} {r['domain']:<5} {r['group']}")

    print(f"引脚 {len(body)} + EP；功能 {func} / 电源地 {pwr}")
    print("分组：" + "  ".join(f"{g}={groups.get(g,0)}" for g in EXPECT))
    if errors:
        print(f"\n[FAIL] {len(errors)} 项")
        for e in errors:
            print("  -", e)
        return 1
    print("\n[OK] 引脚表自洽：编号连续、分组小计正确、必需信号齐全")
    return 0


if __name__ == "__main__":
    sys.exit(main())
