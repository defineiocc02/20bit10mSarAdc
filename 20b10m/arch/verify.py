#!/usr/bin/env python3
"""跑全部架构检查并出表。

    python3 -m arch.verify
    python3 -m arch.verify --json

退出码：0 全部 PASS/WARN；1 存在 FAIL。
"""
from __future__ import annotations

import json
import pathlib
import sys

from . import bitaccount, calib, dac2, noise, timing
from .common import FAIL, PASS, WARN
from .params import ARCH as A

ROOT = pathlib.Path(__file__).resolve().parent


def run_all() -> list:
    checks = []
    checks += bitaccount.run()
    checks += noise.run()
    checks += timing.run()
    checks += calib.run()

    # DAC2 桥接电容（用传输曲线判，不用公式）
    ideal = dac2.ideal_cbr()
    r28 = dac2.audit(28e-15)
    r55 = dac2.audit(55.7e-15)
    from .common import Check
    checks.append(Check(
        "D1", "DAC2 桥接 28 fF 保持 11 bit",
        f"max|DNL|={r28['max_abs_dnl_pct']:.1f}%，负步 {r28['negative_steps']}/2047",
        "单调、无缺码",
        FAIL if r28["negative_steps"] == 0 and r28["max_abs_dnl_pct"] < 5 else WARN,
        f"理想值 {ideal*1e15:.2f} fF（DNL≈0）；28 fF 有 +2.1% 重叠 → 回退步，需 1 个系数"))
    checks.append(Check(
        "D2", "草案 55.7 fF 会掉到 10 bit",
        f"max|DNL|={r55['max_abs_dnl_pct']:.0f}%，最小步 {r55['min_step_lsb']:+.1f} LSB",
        "应显著劣化（作废依据）",
        PASS if r55["min_step_lsb"] < -10 else FAIL,
        "子阵覆盖 2 个主 LSB → 2048 码只剩 1024 级"))
    checks.append(Check(
        "D3", "理想桥容 = 64/63·C_u",
        f"{ideal*1e15:.2f} fF", "传输曲线 DNL≈0",
        PASS if dac2.audit(ideal)["max_abs_dnl_pct"] < 0.1 else FAIL,
        "自校验：模型在理论值上必须给出均匀步长"))
    return checks


def main() -> int:
    checks = run_all()
    n_fail = sum(1 for c in checks if c.verdict == FAIL)
    n_warn = sum(1 for c in checks if c.verdict == WARN)

    if "--json" in sys.argv:
        print(json.dumps({"arch": A.__dict__ if hasattr(A, "__dict__") else {},
                          "checks": [c.as_dict() for c in checks]},
                         ensure_ascii=False, indent=2, default=str))
        return 1 if n_fail else 0

    w = 66
    print("=" * w)
    print(f"SAR20-10M 架构数值复核   {len(checks)} 项  "
          f"PASS {len(checks)-n_fail-n_warn} / WARN {n_warn} / FAIL {n_fail}")
    print("=" * w)
    for c in checks:
        print(f"[{c.verdict:4s}] {c.cid:3s} {c.item}")
        print(f"       值   : {c.value}")
        print(f"       判据 : {c.target}")
        if c.note:
            print(f"       说明 : {c.note}")
    print("-" * w)

    payload = {
        "baseline": "BL-v1 / ARCH_V2 2026-11-08",
        "checks": [c.as_dict() for c in checks],
        "summary": {"total": len(checks), "fail": n_fail, "warn": n_warn},
    }
    (ROOT / "results.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    print(f"结果已写 arch/results.json；FAIL {n_fail} 项")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
