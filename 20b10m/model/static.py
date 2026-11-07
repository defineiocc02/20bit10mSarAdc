# [CODE-INDEX] static.py —— DAC1 10 bit 权重 → DNL/INL
# 物理输出用 w_true；校准残差按“权重估计误差 × 2^bits”给上界（不是 LMS 仿真）。
# 不能把 1.9 ppm 当已验证结果；它依赖 1e-6 的估计误差假设。
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

def curves(bits=10, unit_sigma=0.002, seed=1, other_ppm=1.5):
    """返回逐码 INL/DNL：raw 与“按位权校准后”的残差。
    校准模型：用最小二乘把 INL 投影到各位码的激活向量上，扣掉位权误差；
    残差 = 位权校准吃不掉的部分（非线性/寄生/参考 droop 的代理）。"""
    rng = np.random.default_rng(seed)
    w_true = dac_weights(bits, unit_sigma, rng)
    # 位权失配 + 非位权残差（参考 droop/寄生/桥接的代理），后者校准吃不掉
    other = (other_ppm*1e-6*(2**bits)) * np.sin(2*np.pi*3*np.arange(2**bits)/2**bits + 0.7)
    v_phys = transfer(w_true) + other
    inl_raw, dnl_raw, lsb = inl_dnl_v(v_phys)
    codes = np.arange(2**bits)
    B = np.stack([((codes >> i) & 1).astype(float) for i in range(bits)], axis=1)
    delta, *_ = np.linalg.lstsq(B, inl_raw, rcond=None)
    inl_cal = inl_raw - B @ delta
    v_cal = codes + inl_cal
    dnl_cal = np.diff(v_cal) - 1.0
    return {
        "code": codes,
        "inl_raw": inl_raw, "dnl_raw": dnl_raw,
        "inl_cal": inl_cal, "dnl_cal": dnl_cal,
        "lsb": lsb,
    }

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
