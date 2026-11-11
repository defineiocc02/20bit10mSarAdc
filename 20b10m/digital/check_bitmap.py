#!/usr/bin/env python3
"""check_bitmap.py —— T03 数字位映射复算（**不是 RTL 仿真**）

本机没有 iverilog/verilator/yosys，无法编译/仿真 digital/*.sv。
本脚本按 Sar1Ctrl.sv / Sar2Ctrl.sv 里的索引表达式在 Python 里重算一遍，
用来确认两件事：
  1) 轮次账：Sar1 = 7 轮、Sar2 = 19 轮；每个位被写且只被写一次；
  2) tb_SarCtrls.sv 里写死的期望常数（d1=0x7C8 / d2=0x492 / dt=0x49）对不对。

只复算「索引与拼接」，不复算时序、不复算模拟量。
用法：python3 check_bitmap.py
"""
import sys

NR_C0, NR_C1 = 2, 5
NR_ALL1 = NR_C0 + NR_C1          # 7
NB_D2, NB_REP = 11, 8
NR_ALL2 = NB_D2 + NB_REP         # 19


def sar1(cmp_fn, c4):
    sar2 = [None] * 2
    fine = [None] * 5
    for rnd in range(NR_ALL1):
        c = cmp_fn(rnd)
        if rnd < NR_C0:
            sar2[(NR_C0 - 1) - rnd] = c
        else:
            fine[(NR_ALL1 - 1) - rnd] = c
    assert None not in sar2, "sar2 有未写的位"
    assert None not in fine, "fine 有未写的位"
    d1 = 0
    for i, b in enumerate([c4] + sar2 + fine[0:4] + [0]):
        d1 = (d1 << 1) | b
    # 注意：拼接顺序 {c4, sar2, fine[4:1], 1'b0}
    assert fine[4] is not None
    return d1, sar2, fine


def sar1_exact(cmp_fn, c4):
    """严格按 {c4[3:0], sar2[1:0], fine[4:1], 1'b0} 拼，避免上面那种手写顺序的风险"""
    sar2 = [None] * 2
    fine = [None] * 5
    for rnd in range(NR_ALL1):
        c = cmp_fn(rnd)
        if rnd < NR_C0:
            sar2[(NR_C0 - 1) - rnd] = c
        else:
            fine[(NR_ALL1 - 1) - rnd] = c
    bits = []
    bits += [(c4 >> k) & 1 for k in (3, 2, 1, 0)]
    bits += [sar2[1], sar2[0]]
    bits += [fine[4], fine[3], fine[2], fine[1]]
    bits += [0]
    v = 0
    for b in bits:
        v = (v << 1) | b
    return v, sar2, fine


def sar2(cmp_fn):
    d2 = [None] * NB_D2
    dt = [None] * NB_REP
    for rnd in range(NR_ALL2):
        c = cmp_fn(rnd)
        if rnd < NB_D2:
            d2[(NB_D2 - 1) - rnd] = c
        else:
            dt[(NB_REP - 1) - (rnd - NB_D2)] = c
    assert None not in d2, "d2 有未写的位（原 D4 的 d2[0] 缺失就是这个 assert 挂）"
    assert None not in dt, "dt 有未写的位"
    # d2[i] / dt[i] 的下标就是位号，拼值时按位权加，不能顺序左移
    v2 = sum(b << i for i, b in enumerate(d2))
    vd = sum(b << i for i, b in enumerate(dt))
    return v2, vd, d2, dt


fail = 0

# ---- Sar1：cmp = (rnd%3==0)，coarse 全 1 → c4 = 15 ----
d1, sar2v, finev = sar1_exact(lambda r: 1 if r % 3 == 0 else 0, 15)
print(f"Sar1: rounds={NR_ALL1} sar2={sar2v} fine={finev}")
print(f"      d1 = 0x{d1:03X} = {d1}  bit0={d1 & 1}")
if d1 != 0x7C8:
    print("      [FAIL] 期望 0x7C8，与 tb_SarCtrls.sv 写死的不一致")
    fail += 1
if d1 & 1:
    print("      [FAIL] d1[0] 必须恒 0（ARCH_V2 D-03）")
    fail += 1

# ---- Sar1 LSB-first 反例：若索引写成 sar2[rnd]，期望值应当不同 ----
def sar1_lsb(cmp_fn, c4):
    sar2 = [0] * 2
    fine = [0] * 5
    for rnd in range(NR_ALL1):
        c = cmp_fn(rnd)
        if rnd < NR_C0:
            sar2[rnd] = c
        else:
            fine[rnd - NR_C0] = c
    bits = [(c4 >> k) & 1 for k in (3, 2, 1, 0)] + [sar2[1], sar2[0]] \
        + [fine[4], fine[3], fine[2], fine[1]] + [0]
    v = 0
    for b in bits:
        v = (v << 1) | b
    return v

d1_lsb = sar1_lsb(lambda r: 1 if r % 3 == 0 else 0, 15)
print(f"      反例(LSB-first) d1 = 0x{d1_lsb:03X} —— 与 0x7C8 不同，故 tb 能区分位序")
if d1_lsb == d1:
    print("      [FAIL] 位序测试无区分度")
    fail += 1

# ---- Sar2：19 轮 ----
d2v, dtv, d2l, dtl = sar2(lambda r: 1 if r % 3 == 0 else 0)
print(f"Sar2: rounds={NR_ALL2} d2[10:0]={d2l} dt[7:0]={dtl}")
print(f"      d2 = 0x{d2v:03X} = {d2v}   dt = 0x{dtv:02X} = {dtv}")
if d2v != 0x492:
    print("      [FAIL] 期望 0x492")
    fail += 1
if dtv != 0x49:
    print("      [FAIL] 期望 0x49")
    fail += 1
if d2l[0] is None:
    print("      [FAIL] d2[0] 未写")
    fail += 1

# ---- 原 D4 复现：idx 递减到 0 就停 → d2[0] 永远没写 ----
d2_bug = [None] * NB_D2
idx = 10
for _ in range(10):          # 原实现最多只走 10 次
    d2_bug[idx] = 1
    idx -= 1
print(f"原 D4 复现: 写入的位号 = {[i for i, v in enumerate(d2_bug) if v is not None]}")
print(f"            未写的位号 = {[i for i, v in enumerate(d2_bug) if v is None]}")
if d2_bug[0] is not None:
    print("      [FAIL] 原 D4 的模型写错了")
    fail += 1

# ---- 拍数预算 ----
print("\n拍数/时间预算（ARCH_V2 §5 包络）:")
print(f"  Sar1 ΦC0: {NR_C0} 轮 / 10 ns = {10.0/NR_C0:.2f} ns/轮")
print(f"  Sar1 ΦC1: {NR_C1} 轮 / 15 ns = {15.0/NR_C1:.2f} ns/轮")
print(f"  Sar2 ΦC2: {NR_ALL2} 轮 / 40 ns = {40.0/NR_ALL2:.3f} ns/轮  <- 硬指标")
for per_bit in (2.10, 2.36):
    need = NR_ALL2 * per_bit
    print(f"  若每轮含握手 {per_bit:.2f} ns → 共 {need:.1f} ns "
          f"({'装得下' if need <= 40.0 else '装不下，超 %.1f ns' % (need - 40.0)})")

print("\n结果:", "OK" if fail == 0 else f"{fail} 项失败")
sys.exit(0 if fail == 0 else 1)
