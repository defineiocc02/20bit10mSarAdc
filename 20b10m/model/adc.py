# [CODE-INDEX] adc.py —— 动态时域模型（CAAZ / tracking / 部分交织）
# CAAZ：偶 +s、奇 -s，共享 AZ；out=(even-odd)/2；sinc 只乘信号（已知近似）。
# tracking：每样本 M 次读，AR(1) 相关，均匀权平均（非三角 CoI）。
# interleave：18 片选 8，增益/失调/skew 在 8 片内平均；skew 只算一阶斜率误差。
# 注意：这是行为级输入折算模型，不含 settling/参考纹波/抖动/亚稳态。
"""动态时域模型：CAAZ、8× 重复、部分交织。"""
import numpy as np
from .params import P, LSB_TOTAL, LSB2
from .sources import ar1, tracking_noise, slice_errors

def quantize(x, bits=22, fs_diff=P.fs_diff):
    code = np.round((x/fs_diff + 0.5) * 2**bits)
    code = np.clip(code, 0, 2**bits - 1)
    return (code / 2**bits - 0.5) * fs_diff

def simulate(fin, fs=None, n=None, *, caaz=False, M=None, rho=None,
             interleave=None, az_share=1.0, seed=1, dac_inl=None, jitter=0.0):
    """返回输出码（伏特）。interleave=None 或 dict。

    dac_inl: None|"raw"|"cal"|(codes, volts) —— DAC1 静态 INL 折算到输入端的加性误差。
             一阶模型：一阶粗量化码决定落在哪一段 INL 上，二阶以后不再复现（够用于 SFDR 量级）。
    """
    fs = P.fs if fs is None else fs
    n = P.n if n is None else n
    M = P.M if M is None else M
    rho = P.rho if rho is None else rho
    rng = np.random.default_rng(seed)
    raw = 2 if caaz else 1
    nr = n * raw
    t = np.arange(nr) / (fs*raw)
    # jitter：采样时刻抖动，等效于用 t+Δt 求值；默认 0（其余图按理想时钟）
    t_eff = t + (rng.normal(0, jitter, nr) if jitter else 0.0)
    vin = P.amp * np.sin(2*np.pi*fin*t_eff)

    if dac_inl is not None:
        if isinstance(dac_inl, str):
            from .charge_model import inl_profile
            _c, prof = inl_profile(dac_inl)
        else:
            _c, prof = dac_inl
        code1 = np.clip(np.round((vin/P.fs_diff + 0.5) * 1024).astype(int), 0, 1023)
        inl_err = prof[code1]
    else:
        inl_err = np.zeros(nr)

    # 噪声
    ktc = rng.normal(0, P.ktc, nr)
    cmp_n = rng.normal(0, P.cmp, nr)
    ref_n = rng.normal(0, P.ref, nr)
    az = rng.normal(0, P.ra_az, nr)          # CAAZ 时两笔共享（见下）
    # 在环二级量化：残差进 CT2 之前就已经被 ADC2 量化，不能当无限精度。
    # 参考实现用 12 bit / ±0.1 V（LSB 48.8 µV）；我们用本通道 LSB2=19.07 µV，
    # 量化噪声按均匀分布取 LSB/√12 = 5.5 µV（审计 REFERENCE_AUDIT.md §1-7）。
    q2 = rng.uniform(-LSB2/2, LSB2/2, nr)
    ra = tracking_noise(nr, M, rho, P.ra_broad, rng)

    # 交织误差
    if interleave is not None:
        cfg = dict(enabled=True, shuffle=True, gain=0.0, offset=0.0, skew=0.0, n_slices=P.n_slices)
        cfg.update(interleave)
        g, o, sk = slice_errors(cfg["n_slices"], cfg["gain"], cfg["offset"], cfg["skew"], rng)
        slope = 2*np.pi*fin*P.amp*np.cos(2*np.pi*fin*t)
        err = np.zeros(nr)
        for k in range(nr):
            if cfg["shuffle"]:
                idx = rng.choice(cfg["n_slices"], P.active, replace=False)
            else:
                start = (k * P.active) % cfg["n_slices"]
                idx = (start + np.arange(P.active)) % cfg["n_slices"]
            e = (g[idx]-1.0)*vin[k] + o[idx] + sk[idx]*slope[k]
            err[k] = e.mean()
        base = vin + err
    else:
        base = vin

    if caaz:
        # 偶数笔 +，奇数笔 −；AZ 共享；两笔独立噪声平均
        az_e = az[0::2]
        az_o = az[1::2]
        # az_share=1：两笔共享同一 AZ 代（完全抵消）；=0：各自独立 AZ（只剩平均）
        az_odd = az_share*az_e + np.sqrt(max(0.0, 1.0-az_share*az_share))*az_o
        # DAC 静态误差不随斩波换号：奇偶两笔的 INL 被 (even+odd)/2 平均
        xe = (base[0::2] + ktc[0::2] + cmp_n[0::2] + ref_n[0::2] + ra[0::2]
              + az_e + inl_err[0::2] + q2[0::2])
        xo = (-base[1::2] + ktc[1::2] + cmp_n[1::2] + ref_n[1::2] + ra[1::2]
              + az_odd + inl_err[1::2] + q2[1::2])
        out = (xe - xo) / 2.0
        # ⚠️ 2026-11-08 修正：配对平均的 sinc 响应已经隐含在 (xe-xo)/2 里
        # （xe/xo 是相邻样本，相隔 1/(fs*raw)），不能再显式乘 cos。
        # 原实现多乘一次 cos(pi*f/(2fs))：2 MHz 下幅比 0.951^2 = 0.9045，
        # 而配对本身的响应是 0.951。见 UA1R2 REPORT 4.3 的同源缺陷。
        # out *= np.cos(np.pi*fin/(2*fs))     # <- 已删除
    else:
        out = base + ktc + cmp_n + ref_n + ra + az + inl_err + q2

    return quantize(out), t

def ramp(n, fs=None):
    fs = P.fs if fs is None else fs
    return np.linspace(-P.amp, P.amp, n, endpoint=False)
