"""时序预算：四个包络内的判决次数与单次时长，检查 90 ns 帧是否闭合。"""
from __future__ import annotations

import math

from .common import Check, PASS, WARN, FAIL
from .params import ARCH as A


def phase_ns(ticks: int) -> float:
    return ticks * A.t_clk_ns


def t_bit_ns(cmp2_ns: float) -> float:
    """二级一拍 = DAC2 建立 + 比较器判决 + 逻辑。"""
    return A.t_dac2_settle_ns + cmp2_ns + A.t_sar2_logic_ns


def run() -> list[Check]:
    out: list[Check] = []
    c0, c1 = phase_ns(A.phi_c0_ticks), phase_ns(A.phi_c1_ticks)
    ra, c2 = phase_ns(A.phi_ra_ticks), phase_ns(A.phi_c2_ticks)
    frame = A.ticks_per_frame * A.t_clk_ns

    out.append(Check("T0", "帧与转换窗",
                     f"帧 {frame:g} ns / 转换 {c0+c1+ra+c2:g} ns",
                     "100 / 90 ns",
                     PASS if abs(frame - 100) < 1e-9 and abs(c0 + c1 + ra + c2 - 90) < 1e-9 else FAIL,
                     "cnt18-19 共 10 ns 做 HOLD/换相，规格里的 guard 5 ns 被吸收"))

    need_c0 = A.t_flash_ns + 2 * A.t_cmp1_ns
    out.append(Check("T1", "ΦC0：flash + 2 次 Cmp1",
                     f"{need_c0:.2f} / {c0:g} ns", "≤ 包络",
                     PASS if need_c0 <= c0 else FAIL,
                     f"余量 {c0-need_c0:.2f} ns；依赖 flash 自然建立（A5 未握手）"))

    need_c1 = 4 * A.t_cmp1_ns
    out.append(Check("T2", "ΦC1：4 次 Cmp1（10 次判决口径）",
                     f"{need_c1:.2f} / {c1:g} ns", "≤ 包络",
                     PASS if need_c1 <= c1 else FAIL,
                     f"余量 {c1-need_c1:.2f} ns"))

    out.append(Check("T3", "ΦRA：建立 22 ns（9.5τ，τ=0.90 ns）",
                     f"{ra:g} ns", "≥ 22 ns",
                     PASS if ra >= 22 else WARN,
                     "可借 3 ns 给 ΦC2（架构退路①）"))

    # ΦC2 两种 Cmp2 口径
    tb_nom = t_bit_ns(A.t_cmp2_ns)
    tb_pess = t_bit_ns(2.36)
    beats = A.n2_bits + A.m_repeat

    out.append(Check("T4", f"ΦC2：{beats} 拍 × 名义 {tb_nom:.2f} ns",
                     f"{beats*tb_nom:.1f} / {c2:g} ns", "≤ 包络",
                     PASS if beats * tb_nom <= c2 else FAIL,
                     f"占用 {beats*tb_nom/c2*100:.0f}%；Cmp2={A.t_cmp2_ns} ns 是 U2 未仿值"))

    out.append(Check("T5", f"ΦC2：{beats} 拍 × 悲观 {tb_pess:.2f} ns（Cmp2=2.36）",
                     f"{beats*tb_pess:.1f} / {c2:g} ns", "≤ 包络",
                     FAIL if beats * tb_pess > c2 else PASS,
                     f"超 {beats*tb_pess-c2:.1f} ns；须借 ΦRA 3 ns 或降 M"))

    out.append(Check("T6", "ΦC2 单拍可用预算",
                     f"{c2/beats:.3f} ns/拍", f"≥ {tb_nom:.2f} ns",
                     PASS if c2 / beats >= tb_nom else FAIL,
                     f"允许 Cmp2 ≤ {c2/beats - A.t_dac2_settle_ns - A.t_sar2_logic_ns:.2f} ns"))

    # 跨域同步开销：done2 要过 2 级同步后才被 clk 域采信
    sync_ns = 2 * A.t_clk_ns
    land = c0 + c1 + ra + c2 + sync_ns
    out.append(Check("T7", "done2 过 2 级同步后的落点",
                     f"{land:g} ns（帧 {frame:g}）", "< 帧长",
                     PASS if land < frame else WARN,
                     "落在帧尾 10 ns 窗口内，余量仅 0 ns（digital 独立报了同一条）"))

    return out
