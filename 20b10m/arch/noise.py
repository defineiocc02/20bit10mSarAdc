"""噪声预算与 DR：AR(1) 相关平均、RSS、ρ 灵敏度。"""
from __future__ import annotations

import math

import numpy as np

from .common import Check, PASS, WARN, FAIL
from .params import ARCH as A, K_B, T_AMB


def ar_factor(m: int, rho: float) -> float:
    """M 个 AR(1) 样本求平均的方差放大因子 F = 1 + 2Σ(1-k/M)ρ^k。"""
    if m <= 1:
        return 1.0
    return 1.0 + 2.0 * sum((1 - k / m) * rho ** k for k in range(1, m))


def ktc_uv(cs_pf: float = A.cs_pf) -> float:
    """差分 kT/C（两侧采样）：sqrt(2kT/Cs)。"""
    return math.sqrt(2 * K_B * T_AMB / (cs_pf * 1e-12)) * 1e6


def ra_avg_uv(rho: float, ra_broad_uv: float = A.ra_broadband_uv) -> tuple[float, float]:
    f = ar_factor(A.m_repeat, rho)
    m_eff = A.m_repeat / f
    return ra_broad_uv / math.sqrt(m_eff), m_eff


def quant_uv(credit_dt: bool = False) -> float:
    """二级量化噪声（折输入）。credit_dt=True 时计入 DT 的 3 bit 子码。"""
    lsb2 = A.lsb2_v
    if credit_dt:
        return lsb2 / 2 ** 3 / math.sqrt(12) * 1e6
    return lsb2 / math.sqrt(12) * 1e6


def budget(rho: float, credit_dt: bool = False) -> dict:
    ra, m_eff = ra_avg_uv(rho)
    terms = {
        "kT/C": ktc_uv(),
        "RA 宽带(平均后)": ra,
        "RA AZ": A.ra_az_uv,
        "比较器": A.cmp_uv,
        "基准": A.ref_uv,
        "量化": quant_uv(credit_dt),
    }
    total = math.sqrt(sum(v * v for v in terms.values()))
    return {"terms": terms, "total_uv": total, "m_eff": m_eff, "F": ar_factor(A.m_repeat, rho)}


def dr_db(sigma_uv: float, fs_pp: float) -> float:
    """DR = 20log10( (FS_pp/2√2) / σ )。σ 为差分输入折算 RMS。"""
    return 20 * math.log10((fs_pp / (2 * math.sqrt(2))) / (sigma_uv * 1e-6))


def rho_max(target_db: float, fs_pp: float, credit_dt: bool = False) -> float | None:
    lo, hi = 0.0, 0.999
    if dr_db(budget(0.0, credit_dt)["total_uv"], fs_pp) < target_db:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2
        if dr_db(budget(mid, credit_dt)["total_uv"], fs_pp) >= target_db:
            lo = mid
        else:
            hi = mid
    return lo


def run() -> list[Check]:
    out: list[Check] = []
    rho = A.rho()
    b = budget(rho)
    b_dt = budget(rho, credit_dt=True)

    out.append(Check("N1", "ρ = exp(-Δt/τ_RA)",
                     f"{rho:.3f}（Δt={A.dt_beat_ns:g} ns, τ={A.tau_ra_ns:g} ns）",
                     "ARCH D-10 取 0.449",
                     PASS if abs(rho - 0.449) < 0.01 else WARN,
                     "τ_RA 未仿（U1），ρ 是唯一会翻转结论的假设"))

    out.append(Check("N2", "噪声合计（不含 DT 子码 credit）",
                     f"{b['total_uv']:.2f} µV", f"≤{A.noise_target_uv} µV",
                     PASS if b["total_uv"] <= A.noise_target_uv else FAIL,
                     f"M_eff={b['m_eff']:.2f}（理想 8）"))

    out.append(Check("N3", "噪声合计（计入 DT 3 bit 子码）",
                     f"{b_dt['total_uv']:.2f} µV", f"≤{A.noise_target_uv} µV",
                     PASS if b_dt["total_uv"] <= A.noise_target_uv else FAIL,
                     "架构主张 credit；模型 params 目前用 5.505 µV"))

    dr48 = dr_db(b["total_uv"], 2 * 4.8)
    dr50 = dr_db(b["total_uv"], 10.0)
    out.append(Check("N4", "DR（官方口径：满量程 10 Vpp）",
                     f"{dr50:.2f} dB", f"≥{A.dr_target_db} dB",
                     PASS if dr50 >= A.dr_target_db else FAIL,
                     "架构裁决：DR 以满量程定义；amp4.8 只作历史对比"))

    out.append(Check("N5", "DR（遗留口径：amp 4.8 V 峰/侧 = 9.6 Vpp）",
                     f"{dr48:.2f} dB", f"≥{A.dr_target_db} dB",
                     WARN if dr48 < A.dr_target_db else PASS,
                     "同一设计换口径少 3.4 dB 里的 0.35 dB；此口径达不到 102.5，"
                     "不得用于验收"))

    out.append(Check("N6", "ENOB = (DR-1.76)/6.02",
                     f"{(dr50 - 1.76) / 6.02:.2f} bit", "独立于 20.5 bit 字长",
                     PASS, "20.5 bit 是字长，不是精度"))

    r48 = rho_max(A.dr_target_db, 2 * 4.8, credit_dt=True)
    r50 = rho_max(A.dr_target_db, 10.0, credit_dt=True)
    out.append(Check("N7", "DR 达标所需的 ρ 上限（计 DT credit）",
                     f"amp4.8: {r48:.3f} / 满量程: {r50:.3f}", "越大越宽松",
                     PASS if r48 and rho <= r48 else WARN,
                     f"当前 ρ={rho:.3f}；amp4.8 口径下余量 = {(r48 - rho) if r48 else float('nan'):+.3f}"))

    # 抖动（2 MHz，满幅）
    a_pk = 4.8
    jit = a_pk * 2 * math.pi * 2e6 * A.jitter_ps * 1e-12 / math.sqrt(2) * 1e6
    out.append(Check("N8", "抖动噪声 @2 MHz, 1 ps",
                     f"{jit:.1f} µV", "与 26.5 µV 同量级",
                     WARN, "高频才显著；DR 用低频口径，不叠加此项"))
    return out
