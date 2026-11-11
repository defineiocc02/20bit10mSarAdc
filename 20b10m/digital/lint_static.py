#!/usr/bin/env python3
"""lint_static.py —— 针对 digital/*.sv 的静态启发式检查（**不是编译、不是仿真**）

本机没有 iverilog/verilator/yosys。本脚本用正则做 5 类可判定的结构检查，
输出用于 LINT_REPORT.md 的「静态检查项」证据：

  C1 多驱动：同一信号（按基名归一）被 >=2 个 always 块 / assign 驱动
  C2 输出端口无驱动
  C3 门控时钟/异步事件：posedge 上出现非 clk 信号（自定时结构，需人工确认）
  C4 case 无 default
  C5 always_ff 的复位分支未覆盖某些寄存器

已知局限（必须在报告里声明）：
  - 正则不是语法分析器，看不懂 generate/macro/函数体内部的赋值；
  - 位选重叠冲突只按基名报（d1 与 d1[3] 视为同一基名，这对多驱动检查是对的）；
  - 不做运算位宽传播（那要 verilator -Wall）；
  - 一行多条语句里嵌在 for/if 内部的赋值可能漏检。
用法：python3 lint_static.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FILES = ["DigitalTop.sv", "SliceSched.sv", "Sinc2.sv", "ReconWeights.sv",
         "FramePack.sv", "Sar1Ctrl.sv", "Sar2Ctrl.sv", "SerLvds.sv"]

KW = {"if", "else", "begin", "end", "case", "endcase", "for", "while", "return",
      "assign", "always", "always_ff", "always_comb", "always_latch", "default",
      "endfunction", "endtask", "function", "task", "initial", "generate"}

LHS_RE = re.compile(r"^([A-Za-z_]\w*)\s*(\[[^\]]*\])?\s*(<=|=(?!=))")
ASSIGN_RE = re.compile(r"\bassign\s+([A-Za-z_]\w*)")


def strip_comments(txt: str) -> str:
    txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
    txt = re.sub(r"//[^\n]*", "", txt)
    return txt


def stmt_lhs(frag: str):
    """从一个语句片段里取被赋值的基名；跳过 if()/else/begin/end 前缀。"""
    f = frag.strip()
    for _ in range(6):
        m = re.match(r"(?:else|begin|end)\b\s*", f)
        if m:
            f = f[m.end():]
            continue
        m = re.match(r"if\s*\([^()]*\)\s*", f)
        if m:
            f = f[m.end():]
            continue
        break
    m = LHS_RE.match(f)
    if m and m.group(1) not in KW:
        return m.group(1)
    return None


def split_always(text):
    """返回 [(kind, start_line, body_text)]"""
    blocks = []
    pat = re.compile(r"\b(always_ff|always_comb|always_latch|always)\b")
    for m in pat.finditer(text):
        start = m.start()
        line_no = text[:start].count("\n") + 1
        i = m.end()
        n = len(text)
        depth = 0
        started = False
        while i < n:
            tok = re.compile(r"\b(begin|end)\b(?!case|function|task|generate|module)").search(text, i)
            if not tok:
                break
            if tok.group(1) == "begin":
                depth += 1
                started = True
            else:
                depth -= 1
            i = tok.end()
            if started and depth == 0:
                break
            if not started:            # 单语句 always，没有 begin
                semi = text.find(";", i)
                if semi != -1:
                    i = semi + 1
                break
        blocks.append((m.group(1), line_no, text[m.end():i]))
    return blocks


def main():
    report, total_issue = [], 0

    for fname in FILES:
        p = HERE / fname
        if not p.exists():
            report.append(f"!! {fname} 不存在")
            continue
        txt = strip_comments(p.read_text(encoding="utf-8", errors="replace"))

        # ---------------- 驱动源收集 ----------------
        drivers = {}
        blocks = split_always(txt)
        for kind, start, body in blocks:
            seen = set()
            for frag in re.split(r";", body):
                nm = stmt_lhs(frag)
                if nm:
                    seen.add(nm)
            for nm in seen:
                drivers.setdefault(nm, []).append(f"{kind}@{start}")
        for m in ASSIGN_RE.finditer(txt):
            drivers.setdefault(m.group(1), []).append("assign")
        # 例化的端口连接：只用来**抑制 C2 误报**（别把子模块驱动的输出算成无驱动）。
        # 不并入 drivers，否则同一信号喂两个子模块会被误判成两个驱动源。
        inst_drv = {m.group(1) for m in re.finditer(r"\.\s*\w+\s*\(\s*([A-Za-z_]\w*)\s*\)", txt)}

        # ---------------- C1 多驱动 ----------------
        multi = {k: v for k, v in drivers.items() if len(v) > 1}
        if multi:
            total_issue += len(multi)
            report.append(f"\n[{fname}] C1 **多驱动** {len(multi)} 个:")
            for k, v in sorted(multi.items()):
                report.append(f"    {k:14s} <- {', '.join(v)}")
        else:
            report.append(f"[{fname}] C1 多驱动: 无")

        # ---------------- C2 输出端口无驱动 ----------------
        outs = re.findall(r"\boutput\s+(?:logic|wire|reg)?\s*(?:\[[^\]]*\]\s*)?([A-Za-z_]\w*)", txt)
        dead = [o for o in dict.fromkeys(outs) if o not in drivers and o not in inst_drv]
        if dead:
            total_issue += len(dead)
            report.append(f"[{fname}] C2 **输出无驱动**: {dead}")

        # ---------------- C3 非 clk 的 posedge ----------------
        ev = re.findall(r"posedge\s+(\w+)", txt)
        odd = sorted({e for e in ev if e not in ("clk", "CLK200")})
        if odd:
            report.append(f"[{fname}] C3 非主时钟的 posedge: {odd}  (自定时/异步复位结构，需人工确认)")

        # ---------------- C4 case 无 default ----------------
        n_case = len(re.findall(r"\bcase\b", txt))
        n_def = len(re.findall(r"\bdefault\s*:", txt))
        if n_case and n_def < n_case:
            total_issue += 1
            report.append(f"[{fname}] C4 case {n_case} 个 / default {n_def} 个 —— 覆盖不全")

        # ---------------- C5 复位未覆盖 ----------------
        for kind, start, body in blocks:
            if not kind.startswith("always_ff"):
                continue
            all_names = {n for n in (stmt_lhs(f) for f in re.split(r";", body)) if n}
            # 复位分成两种写法：if(!rstn) begin ... end  和  if(!rstn) 单语句;
            m = re.search(r"if\s*\(\s*!\s*[rR][sS][tT][nN]\s*\)", body)
            if not m:
                total_issue += 1
                report.append(f"[{fname}] C5 always_ff@{start} 找不到 `if (!rstn)` 复位分支")
                continue
            tail = body[m.end():].lstrip()
            if tail.startswith("begin"):
                end = body.find("end", m.end())
                rst_part = body[m.end():end]
            else:
                semi = body.find(";", m.end())
                rst_part = body[m.end():semi if semi != -1 else len(body)]
            rst_names = {n for n in (stmt_lhs(f) for f in re.split(r";", rst_part)) if n}
            missing = all_names - rst_names
            if missing:
                total_issue += 1
                report.append(f"[{fname}] C5 always_ff@{start} **复位未覆盖**: {sorted(missing)}")

    print("\n".join(report))
    print(f"\n=== 启发式问题计数: {total_issue} ===")
    print("（0 不代表可综合/可仿真通过；只是本脚本覆盖的 5 类里没发现问题）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
