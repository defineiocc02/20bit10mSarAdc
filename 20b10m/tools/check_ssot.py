#!/usr/bin/env python3
"""check_ssot.py —— 唯一口径闸门

检查四件事：
1. spec/params.yaml 的派生量与公式一致；
2. behavioral/src/sar20b/config.py 的 NumericalContract 与本表一致；
3. model/params.py 的 LSB2 与本表一致；
4. 活跃文件里不出现被取代的旧值（20.5 / G=128 / 1039 / 28 pF / D1<10:0> /
   Dac2_12b / ΦRA 25 / ΦC2 40 / C_INC 1 pF），除非该行带 SSOT-ALLOW。

用法：python3 tools/check_ssot.py [-v]
退出码：0 全过；1 有失败。
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent

LIVE_GLOBS = [
    "README.md",
    "spec/SSOT.md",
    "spec/params.yaml",
    "interface/*.md",
    "interface/*.csv",
    "digital/*.sv",
    "model/params.py",
    "behavioral/src/sar20b/config.py",
    "analog/blocks/*/spec.md",
    "analog/blocks/*/netlist/*.scs",
]

SKIP_FORBIDDEN = {"spec/SSOT.md", "spec/params.yaml", "tools/check_ssot.py"}

REQUIRED = [
    ("interface/ANALOG_DIGITAL_IF.md", "D1[9:0]"),
    ("interface/ANALOG_DIGITAL_IF.md", "D1_MASK[125:0]"),
    ("interface/ANALOG_DIGITAL_IF.md", "D2[11:0]"),
    ("digital/DigitalTop.sv", "[9:0]  D1"),
    ("digital/DigitalTop.sv", "[11:0] D2"),
    ("digital/DigitalTop.sv", "output logic [125:0] D1_MASK"),
    ("analog/blocks/SdacPool18/netlist/SdacPool18.scs", "D<125:0>"),
    ("analog/blocks/Dac2_11b/netlist/Dac2_11b.scs", "RST"),
]

FORBIDDEN = [
    ("20.5 bit", "位账已被 BL-v3 取代为 20.00"),
    ("G=128", "G 已冻结为 32"),
    ("G = 128", "G 已冻结为 32"),
    ("1039", "一级单位数已冻结为 1024"),
    ("28.05 pF", "一级总容已冻结为 27.648 pF"),
    ("28 pF", "一级总容已冻结为 27.648 pF"),
    ("D1<10:0>", "D1 已改为 10 位"),
    ("D1[10:0]", "D1 已改为 10 位"),
    ("Dac2_12b", "目录/标题已改为 Dac2_11b（as-wired）"),
    ("ΦRA 25", "ΦRA 已改为 20 ns"),
    ("ΦC2 40", "ΦC2 已改为 45 ns"),
    ("C_INC 1 pF", "C_INC 已改为 864 fF"),
    ("1.0 pF/侧", "C_INC 已改为 864 fF"),
]


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def load_live() -> list[Path]:
    out: list[Path] = []
    for g in LIVE_GLOBS:
        out.extend(sorted(ROOT.glob(g)))
    seen, uniq = set(), []
    for p in out:
        if p.is_file() and p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


def check_derived(d: dict, errs: list[str]) -> None:
    f = d["frozen"]
    der = d["derived"]
    lsb1 = f["fs_diff_v"] / 2**f["n1"]
    window = 2**f["n_red"] * lsb1
    lsb2 = window / 2**f["n2"]
    lsb_total = f["fs_diff_v"] / 2**f["n_total"]
    lsb_xfer = f["fs_diff_v"] / 2**f["n_xfer"]
    c1 = f["units_per_side"] * f["c_unit_f"]
    ra_out = window * f["g_ra"]
    k_inc = f["c_inc_f"] / (f["c_inc_f"] + 0.892e-12)
    node = ra_out * k_inc
    checks = [
        ("lsb1_v", der["lsb1_v"], lsb1),
        ("resid_window_pp_v", der["resid_window_pp_v"], window),
        ("lsb2_v", der["lsb2_v"], lsb2),
        ("lsb_total_v", der["lsb_total_v"], lsb_total),
        ("lsb_xfer_v", der["lsb_xfer_v"], lsb_xfer),
        ("c_dac1_side_f", der["c_dac1_side_f"], c1),
        ("ra_out_pp_v", der["ra_out_pp_v"], ra_out),
        ("k_inc", der["k_inc"], k_inc),
        ("dac2_node_pp_v", der["dac2_node_pp_v"], node),
        ("lsb2_node_v", der["lsb2_node_v"], node / 2**f["n2"]),
    ]
    for name, got, want in checks:
        if abs(got - want) > max(1e-12, abs(want) * 1e-6):
            errs.append(f"派生量 {name}: params.yaml={got!r} 公式={want!r}")
    if abs(lsb2 - lsb_total) / lsb_total > 1e-12:
        errs.append("位账不自洽：LSB2 != FS/2^20")
    if f["n_total"] != f["n1"] + f["n2"] - f["n_red"]:
        errs.append("n_total != n1 + n2 - n_red")


def check_behavioral(errs: list[str]) -> None:
    p = ROOT / "behavioral/src/sar20b/config.py"
    try:
        tree = ast.parse(p.read_text())
    except Exception as e:  # noqa: BLE001
        errs.append(f"behavioral config 解析失败：{e}")
        return
    vals: dict[str, object] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.Constant):
                vals[node.target.id] = node.value.value
    want = {"n1": 10, "n2": 12, "n_red": 2, "n_xfer": 22,
            "g_ra": 32.0, "units_per_side": 1024, "c_unit_f": 27e-15}
    for k, v in want.items():
        if k in vals and vals[k] != v:
            errs.append(f"NumericalContract.{k}={vals[k]!r}，应为 {v!r}")
    src = p.read_text()
    if '"u3b7"' not in src:
        errs.append("behavioral 缺 candidate_u3b7 profile")


def check_model(errs: list[str]) -> None:
    p = ROOT / "model/params.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("_wb_mparams", p)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
    except Exception as e:  # noqa: BLE001
        errs.append(f"model/params.py 执行失败：{e}")
        return
    val = getattr(mod, "LSB2", None)
    if val is None:
        errs.append("model/params.py 找不到 LSB2")
        return
    if abs(float(val) - 9.5367431640625e-06) > 1e-15:
        errs.append(f"model LSB2={val!r}，应为 9.5367431640625e-06（10+12−2）")
    if getattr(mod, "N_TOTAL", None) != 20:
        errs.append(f"model N_TOTAL={getattr(mod, 'N_TOTAL', None)!r}，应为 20")


def check_forbidden(files: list[Path], verbose: bool, errs: list[str]) -> None:
    hits = 0
    for p in files:
        r = rel(p)
        if r in SKIP_FORBIDDEN:
            continue
        text = p.read_text(errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if "SSOT-ALLOW" in line:
                continue
            for pat, why in FORBIDDEN:
                if pat in line:
                    hits += 1
                    errs.append(f"{r}:{i} 出现 `{pat}`（{why}）")
                    if verbose:
                        print(f"  {r}:{i}: {line.strip()[:120]}")
    if hits == 0 and verbose:
        print("  旧值扫描：0 命中")


def check_required(errs: list[str]) -> None:
    for r, token in REQUIRED:
        p = ROOT / r
        if not p.exists():
            errs.append(f"缺文件：{r}")
            continue
        if token not in p.read_text(errors="ignore"):
            errs.append(f"{r} 缺必需标记：`{token}`")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()

    ypath = ROOT / "spec/params.yaml"
    if not ypath.exists():
        print("FAIL: 缺 spec/params.yaml")
        return 1
    d = yaml.safe_load(ypath.read_text())

    errs: list[str] = []
    check_derived(d, errs)
    check_behavioral(errs)
    check_model(errs)
    files = load_live()
    check_forbidden(files, args.verbose, errs)
    check_required(errs)

    print(f"files={len(files)}  checks=5  errors={len(errs)}")
    for e in errs:
        print(f"  [FAIL] {e}")
    if not errs:
        print("SSOT OK")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
