"""DAC1 静态 INL：蒙特卡洛（单位电容失配）+ 校准残差标度。

独立于 model/：这里只用 arch/params.py 的参数与 numpy。
"""
from __future__ import annotations

import numpy as np

from .common import Check, PASS, WARN, FAIL
from .params import ARCH as A


def build_transfer(unit_err: np.ndarray, slices: int = 8) -> np.ndarray:
    """1024 码的误差（单位：Cu）。

    unit_err[s, u]：第 s 片第 u 个单位的相对误差（Cu 为单位）。
    高 3 bit = unary 选片，低 7 bit = 片内二进制。
    """
    cu = 1.0
    # 每片：7 个位权（1,2,4,...,64 单位）的误差 = 对应单位误差求和
    bit_err = np.zeros((A.slices_total, 7))
    idx = 0
    for s in range(A.slices_total):
        u = 0
        for j in range(7):
            n = 2 ** j
            bit_err[s, j] = unit_err[s, u:u + n].sum()
            u += n
        # 余下 1 个 dummy 不参与
    slice_err = np.array([unit_err[s].sum() for s in range(A.slices_total)])

    err = np.zeros(1024)
    for code in range(1024):
        u, k = code >> 7, code & 127
        e = slice_err[:u].sum()
        for j in range(7):
            if (k >> j) & 1:
                e += bit_err[u, j]
        err[code] = e
    return err


def inl_ppm(err: np.ndarray) -> float:
    """去掉最佳拟合直线后的峰值 INL（ppm FS）。FS = 1024 Cu。"""
    x = np.arange(len(err), dtype=float)
    a, b = np.polyfit(x, err, 1)
    resid = err - (a * x + b)
    return float(np.max(np.abs(resid)) / 1024 * 1e6)


def monte_carlo(trials: int = 60, sigma_u: float = A.sigma_unit, seed: int = 100) -> dict:
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(trials):
        e = rng.normal(0.0, sigma_u, size=(A.slices_total, A.units_per_slice))
        vals.append(inl_ppm(build_transfer(e)))
    v = np.array(vals)
    return {"mean_ppm": float(v.mean()), "p95_ppm": float(np.percentile(v, 95)),
            "max_ppm": float(v.max()), "trials": trials}


def cal_residual_ppm(n_avg: int, sigma_meas_lsb20: float = A.cal_meas_noise_lsb,
                     n_weights: int = 126) -> float:
    """校准残差：每个权重测 n 次，残余 INL ≈ σ_m/√n·√N / FS。

    σ_m 以 LSB20 计；1 LSB20 = FS/2^20.5，故折成 Cu 需 ×1024/2^20.5。
    """
    cu_per_lsb = 1024 / 2 ** 20.5
    sigma_cu = sigma_meas_lsb20 * cu_per_lsb
    return sigma_cu / np.sqrt(n_avg) * np.sqrt(n_weights) / 1024 * 1e6


def run() -> list[Check]:
    out: list[Check] = []
    mc = monte_carlo()
    out.append(Check("C1", "DAC1 静态 INL（MC，σ_u=0.2%，含片间失配）",
                     f"{mc['mean_ppm']:.1f} ppm（p95 {mc['p95_ppm']:.1f}）",
                     "文档 16.4 ppm（另一套失配假设）",
                     WARN,
                     f"{mc['trials']} 次；本模型把 18 片的整片失配也算进去（σ=0.2%·√128≈2.3% Cu），"
                     "文档 16.4 ppm 依赖「同一阵列互补开关」假设——两者不可直接比，不作对错判据"))

    # 校准残差标度
    r1 = cal_residual_ppm(1)
    r16 = cal_residual_ppm(16)
    r256 = cal_residual_ppm(256)
    out.append(Check("C2", "校准残差（按 2.8 LSB20/权 的文档口径）",
                     f"n=1: {r1:.1f} / 16: {r16:.2f} / 256: {r256:.2f} ppm",
                     "文档：2.3 / 0.57 / 0.14 ppm",
                     FAIL if abs(r1 - 2.3) > 1 else WARN,
                     "同一组数差 ~10×：若 2.8 LSB20 是每权测量噪声，n=1 应为 "
                     f"{r1:.1f} ppm；文档的 2.3 ppm 对应 ≈{2.3/ r1 * 2.8:.2f} LSB20/权。两者不能同时成立"))

    out.append(Check("C3", "残差按 1/√n 缩放",
                     f"{r1/r16:.2f}×（n 1→16）", "4.00×",
                     PASS if abs(r1 / r16 - 4) < 0.05 else FAIL,
                     "标度律本身成立；绝对值取决于 C2 的口径"))

    out.append(Check("C4", "校准判据 ≤1.5 ppm 所需平均次数",
                     f"n≈{int(np.ceil((r1/1.5)**2))}", "≤256",
                     PASS if (r1 / 1.5) ** 2 <= 256 else WARN,
                     "按 2.8 LSB20/权 口径反推；口径变了这条跟着变"))

    return out
