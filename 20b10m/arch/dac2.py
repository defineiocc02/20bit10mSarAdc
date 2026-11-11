"""DAC2 6+5 分段：电荷守恒传输曲线

主阵（5 bit，32 单位含 dummy）与子阵（6 bit，64 单位含 dummy）
经桥容 Cb 耦合。解两节点电荷守恒，得到 2048 个码的 Vout。

用途：验证 Cb=28 fF（网表现值）到底是不是 11 bit，以及 55.7 fF 会不会掉位。
"""
from __future__ import annotations

import numpy as np

from .params import ARCH

# 位权（单位电容个数）；bit0 = LSB；最后一个是 dummy：有电容、恒接 0
# dummy 必须计入总容（否则主阵只有 31 单位、子阵 63 单位，最优点会假移到 1 C_u）
W_MAIN = [1, 2, 4, 8, 16, 1]          # 32 单位（31 有效 + 1 dummy）
W_SUB = [1, 2, 4, 8, 16, 32, 1]       # 64 单位（63 有效 + 1 dummy）
N_MAIN_CODE = 32
N_SUB_CODE = 64


def vout(main_code: int, sub_code: int, c_br_f: float, cu_f: float = ARCH.cu_f,
         vref: float = 2.5) -> float:
    """两节点电荷守恒：初态全 0，翻转后求顶板电压。"""
    cm = np.array(W_MAIN, float) * cu_f
    cs = np.array(W_SUB, float) * cu_f
    bm = np.array([(main_code >> k) & 1 for k in range(5)] + [0], float)
    bs = np.array([(sub_code >> k) & 1 for k in range(6)] + [0], float)

    am = cm.sum() + c_br_f
    as_ = cs.sum() + c_br_f
    qm = (cm * bm).sum() * vref
    qs = (cs * bs).sum() * vref
    det = am * as_ - c_br_f * c_br_f
    return (qm * as_ + c_br_f * qs) / det


def transfer(c_br_f: float) -> np.ndarray:
    return np.array([vout(m, s, c_br_f) for m in range(N_MAIN_CODE)
                     for s in range(N_SUB_CODE)])


def dnl(v: np.ndarray) -> np.ndarray:
    steps = np.diff(v)
    ideal = (v[-1] - v[0]) / (len(v) - 1)
    return steps / ideal - 1.0


def audit(c_br_f: float) -> dict:
    v = transfer(c_br_f)
    d = dnl(v)
    return {
        "cbr_fF": c_br_f * 1e15,
        "monotonic": bool((d > -1).all()),
        "max_abs_dnl_pct": float(np.max(np.abs(d)) * 100),
        "min_step_lsb": float(np.min(np.diff(v)) / ((v[-1] - v[0]) / (len(v) - 1))),
        "negative_steps": int((np.diff(v) < 0).sum()),
        "span_mV": float((v[-1] - v[0]) * 1e3),
    }


def ideal_cbr() -> float:
    """子阵 64 码铺满 1 个主 LSB：64·Cb = 64 + Cb  →  Cb = 64/63 C_u"""
    return 64.0 / 63.0 * ARCH.cu_f
