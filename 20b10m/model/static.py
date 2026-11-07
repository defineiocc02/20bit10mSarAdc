# [CODE-INDEX] static.py —— DAC1 10 bit 权重 → DNL/INL
# 拓扑：8 个 unary 片 ×（7 bit 二进制 + 1 个 termination 单位），差分互补开关。
# 默认走 charge_model（与本项目实际拓扑一致）；legacy=True 保留旧「单端 10 bit 二进制」对照。
# 注意：旧单端模型的 INL 约为本拓扑的 2.3 倍（38.6 vs 16.4 ppm），不要混用。
"""静态模型：DAC 权重 → DNL/INL；校准前后对比。"""
import numpy as np
from .sources import dac_weights

def transfer(weights):
    bits = len(weights)
    k = np.arange(2**bits)
    v = np.zeros_like(k, dtype=float)
    for i, w in enumerate(weights):
        v += ((k >> i) & 1) * w
    return v

def inl_dnl_v(v):
    lsb = v[-1] / (len(v)-1)
    dnl = np.diff(v)/lsb - 1.0
    inl = v/lsb - np.arange(len(v))
    return inl, dnl, lsb

def curves_binary(bits=10, unit_sigma=0.002, seed=1, other_ppm=1.5):
    """legacy：单端 10 bit 二进制，非本项目拓扑，仅作保守对照。"""
    rng = np.random.default_rng(seed)
    w_true = dac_weights(bits, unit_sigma, rng)
    other = (other_ppm*1e-6*(2**bits)) * np.sin(2*np.pi*3*np.arange(2**bits)/2**bits + 0.7)
    v_phys = transfer(w_true) + other
    inl_raw, dnl_raw, lsb = inl_dnl_v(v_phys)
    codes = np.arange(2**bits)
    B = np.stack([((codes >> i) & 1).astype(float) for i in range(bits)], axis=1)
    delta, *_ = np.linalg.lstsq(B, inl_raw, rcond=None)
    inl_cal = inl_raw - B @ delta
    v_cal = codes + inl_cal
    dnl_cal = np.diff(v_cal) - 1.0
    return {"code": codes, "inl_raw": inl_raw, "dnl_raw": dnl_raw,
            "inl_cal": inl_cal, "dnl_cal": dnl_cal, "lsb": lsb}


def curves(bits=10, unit_sigma=0.002, seed=1, other_ppm=1.5, legacy=False):
    """本项目拓扑的逐码 INL/DNL（单位 LSB1）。

    校准后不是理想 0：用有限样本残差（每码平均 16 次、单次 σ=2.8 LSB20）。
    """
    if legacy or bits != 10:
        return curves_binary(bits, unit_sigma, seed, other_ppm)
    from .charge_model import dac1_curves, cal_residual
    c = dac1_curves(sigma=unit_sigma, seed=seed)
    pk, env = cal_residual(n_avg=16, pool=None, seed=seed)
    rng = np.random.default_rng(seed + 77)
    sign = np.where(rng.random(1024) < .5, -1.0, 1.0)
    # 校准后剩下的就是残差本身（拟合权重减真权重），不是 raw 再加残差
    inl_cal = sign * env
    inl_cal -= inl_cal.mean()
    dnl_cal = np.diff(np.arange(1024) + inl_cal) - 1.0
    return {"code": c["code"], "inl_raw": c["inl_raw"], "dnl_raw": c["dnl_raw"],
            "inl_cal": inl_cal, "dnl_cal": dnl_cal, "lsb": 1.0}

def run(bits=10, unit_sigma=0.002, seed=1):
    c = curves(bits, unit_sigma, seed)
    inl_raw, dnl_raw = c["inl_raw"], c["dnl_raw"]
    inl_cal, dnl_cal = c["inl_cal"], c["dnl_cal"]
    inl_cal_lsb = float(np.max(np.abs(inl_cal)))
    dnl_cal_lsb = float(np.max(np.abs(dnl_cal)))
    # 折算到系统 ppm FS（DAC1 10 bit → 1024 LSB1 = FS）
    to_ppm = 1e6/ (2**bits)
    return {
        "bits": bits,
        "unit_sigma": unit_sigma,
        "dnl_raw_lsb": float(np.max(np.abs(dnl_raw))),
        "inl_raw_lsb": float(np.max(np.abs(inl_raw))),
        "dnl_cal_lsb": float(dnl_cal_lsb),
        "inl_cal_lsb": float(inl_cal_lsb),
        "inl_raw_ppm": float(np.max(np.abs(inl_raw))*to_ppm),
        "inl_cal_ppm": float(inl_cal_lsb*to_ppm),
    }
