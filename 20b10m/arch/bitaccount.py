"""位账、量程链、电容分压的自洽检查。"""
from __future__ import annotations

import math

from .common import Check, PASS, FAIL, WARN
from .params import ARCH as A


def run() -> list[Check]:
    out: list[Check] = []

    # B1 位账
    res = A.resolution_bits
    out.append(Check("B1", "位账 10+11-2+1.5",
                     f"{res:.1f} bit", "20.5 bit",
                     PASS if abs(res - 20.5) < 1e-9 else FAIL,
                     "1.5 = 0.5·log2(8)"))

    # B2 分辨率×LSB = 满量程
    fs = 2 ** res * A.lsb_total_v
    out.append(Check("B2", "2^20.5 × LSB_total = FS",
                     f"{fs:.4f} Vpp", "10.0000 Vpp",
                     PASS if abs(fs - A.fs_pp) < 1e-6 else FAIL,
                     f"LSB_total={A.lsb_total_v*1e6:.3f} µV"))

    # B3 LSB 链
    lsb2 = A.residual_span_v / 2 ** A.n2_bits
    out.append(Check("B3", "LSB2 = 4·LSB1 / 2^11",
                     f"{lsb2*1e6:.3f} µV", "19.07 µV",
                     PASS if abs(lsb2 - A.lsb2_v) < 1e-12 else FAIL,
                     f"LSB1={A.lsb1_v*1e3:.3f} mV，残差跨距={A.residual_span_v*1e3:.2f} mV"))

    # B4 RA 输出摆幅
    ra_out = A.residual_span_v * A.a_ra
    out.append(Check("B4", "残差跨距 × A_RA",
                     f"{ra_out:.3f} Vpp", "1.25 Vpp",
                     PASS if abs(ra_out - 1.25) < 0.01 else FAIL,
                     f"A_RA={A.a_ra:g}"))

    # B5 CT 分压
    k = A.k_inc
    node = ra_out * k
    out.append(Check("B5", "k_INC = C_INC/(C_INC+C_DAC2,eff)",
                     f"{k:.4f} → {node*1e3:.1f} mVpp", "≈0.49 / 615 mVpp",
                     PASS if 0.48 <= k <= 0.50 else FAIL,
                     f"C_DAC2,eff={A.c_dac2_eff_f*1e15:.1f} fF（含桥接 {A.c_br_effective_f*1e15:.1f} fF）"))

    # B6 输出字长与 LSB：22 bit 的 LSB 固定为 0.5 LSB_total，量程 141% FS（余量给失调）
    lsb_out = 0.5 * A.lsb_total_v
    span = 2 ** A.out_bits * lsb_out
    ratio = span / A.fs_pp
    out.append(Check("B6", "22 bit × 0.5 LSB_total 是否装得下 FS",
                     f"LSB={lsb_out*1e6:.3f} µV，量程 {span:.2f} V = {ratio*100:.0f}% FS",
                     "≥100% FS",
                     PASS if ratio >= 1.0 else FAIL,
                     f"余量 {ratio-1:.1%} 给失调/过载；中心 0x200000；"
                     f"若改成 21 bit 只有 {2**21*lsb_out/A.fs_pp*100:.0f}% FS，装不下"))

    # B7 单位电容合规
    units_inc = A.c_inc_f / A.cu_f
    units_dac2 = A.c_dac2_array_f / A.cu_f
    ok = abs(units_inc - round(units_inc)) < 1e-6 and abs(units_dac2 - round(units_dac2)) < 1e-6
    out.append(Check("B7", "C_INC / DAC2 阵列是单位电容整数倍",
                     f"{units_inc:.3f} / {units_dac2:.3f} 单位", "整数",
                     PASS if ok else FAIL,
                     "架构造型要求全片只用 32/64/1024 单位三种块"))

    # B8 片池容量
    need = 2 * A.slices_active  # 8 转换 + 8 采样
    out.append(Check("B8", "片池 18 = 8 转换 + 8 采样 + 2 备",
                     f"{A.slices_total} 片（需 {need} + 2 备）", "18",
                     PASS if A.slices_total == need + 2 else FAIL,
                     "每片 200 ns 用一次"))

    return out
