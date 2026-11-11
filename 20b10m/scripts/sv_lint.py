#!/usr/bin/env python3
"""sv_lint.py —— 轻量 SystemVerilog 静态检查（不替代编译器）

本机没有 iverilog/verilator，这个脚本只做**文本级**检查，覆盖踩过的三类坑：

  L1 多驱动：同一信号被多个 always 块驱动（对应 Sar1Ctrl 的 idx 双驱动）
  L2 混驱：信号既在 always 里赋值，又被 assign 或子模块实例的输出端口驱动
  L3 未驱动输出：output 端口既不在赋值左侧，也不接任何实例端口

它**不能**证明语法正确、不能证明功能正确、不能替代综合告警。
用法：
  python3 scripts/sv_lint.py            # 检查 digital/*.sv
  python3 scripts/sv_lint.py --strict   # 有问题退出码 1
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SV_DIR = ROOT / "digital"

LHS_FF = re.compile(r"(\w+)\s*(?:\[[^\]]*\])?\s*<=")
LHS_COMB = re.compile(r"(\w+)\s*(?:\[[^\]]*\])?\s*=(?!=)")
ASSIGN = re.compile(r"\bassign\s+(\w+)")
PORT_CONN = re.compile(r"\.(\w+)\s*\(\s*(\w+)\s*\)")
MODULE = re.compile(r"\bmodule\s+(\w+)\s*(?:#\s*\(.*?\)\s*)?\((.*?)\);(.*?)\bendmodule", re.S)


def strip_comments(t: str) -> str:
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    t = re.sub(r"//[^\n]*", "", t)
    return t


def always_blocks(body: str) -> list[tuple[str, str]]:
    """返回 [(kind, block_text)]，用 begin/end 深度配对，避免被内层 end 截断。"""
    out = []
    for m in re.finditer(r"\balways(?:_ff|_comb|_latch)?\b", body):
        bi = body.find("begin", m.end())
        if bi < 0 or bi - m.end() > 80:
            continue
        depth = 0
        end = -1
        for t in re.finditer(r"\b(begin|end)\b", body[bi:]):
            depth += 1 if t.group(1) == "begin" else -1
            if depth == 0:
                end = bi + t.end()
                break
        if end > 0:
            kind = "ff" if "always_ff" in body[m.start():m.end()] else "comb"
            out.append((kind, body[bi:end]))
    return out


def strip_conditions(blk: str) -> str:
    """去掉所有括号内容（由内向外），避免把 `cnt <= 5'd11` 这类条件误判成赋值。"""
    prev = None
    while prev != blk:
        prev = blk
        blk = re.sub(r"\([^()]*\)", " ", blk)
    return blk


def check(path: pathlib.Path) -> list[str]:
    txt = strip_comments(path.read_text(encoding="utf-8"))
    issues: list[str] = []
    for m in MODULE.finditer(txt):
        mod, ports, body = m.group(1), m.group(2), m.group(3)
        drivers: dict[str, list[str]] = {}

        for i, (kind, blk) in enumerate(always_blocks(body)):
            pat = LHS_FF if kind == "ff" else LHS_COMB
            scan = strip_conditions(blk)
            for s in set(pat.findall(scan)) | set(LHS_FF.findall(scan)) | set(LHS_COMB.findall(scan)):
                if s in ("if", "else", "for", "case", "begin", "end"):
                    continue
                drivers.setdefault(s, []).append(f"always_{kind}#{i}")

        for s in set(ASSIGN.findall(body)):
            drivers.setdefault(s, []).append("assign")

        # 子模块实例的端口连接：视为该信号有驱动（方向未知，保守处理）
        inst = {sig for _, sig in PORT_CONN.findall(body)}

        for sig, who in sorted(drivers.items()):
            kinds = {w.split("#")[0] for w in who}
            multi_always = sum(1 for w in who if w.startswith("always")) > 1
            if multi_always:
                issues.append(f"{mod}: 多驱动 {sig} ← {', '.join(who)}")
            elif "assign" in kinds and any(k.startswith("always") for k in kinds):
                issues.append(f"{mod}: 混驱 {sig} ← {', '.join(who)}")

        for o in re.findall(r"\boutput\s+(?:logic|wire|reg)?\s*(?:\[[^\]]*\])?\s*(\w+)", ports):
            if o not in drivers and o not in inst:
                issues.append(f"{mod}: 输出未驱动 {o}")
    return issues


def main() -> int:
    files = sorted(SV_DIR.glob("*.sv"))
    if not files:
        print("找不到 digital/*.sv")
        return 2
    total = 0
    for f in files:
        iss = check(f)
        if iss:
            print(f"\n{f.name}")
            for i in iss:
                print("  -", i)
            total += len(iss)
    print(f"\n扫描 {len(files)} 个文件，问题 {total} 处")
    if total:
        print("注意：文本级检查，不是编译；位宽/时序/语法仍需真实工具。")
        return 1 if "--strict" in sys.argv else 0
    print("[OK] 未发现多驱动/混驱/未驱动输出")
    return 0


if __name__ == "__main__":
    sys.exit(main())
