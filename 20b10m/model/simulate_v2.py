# [CODE-INDEX] simulate_v2.py —— 信号流级行为模型（v2）
#
# 与 v1（adc.simulate）的根本区别：
#   v1: out = quantize(vin + Σ加性误差)      -> 误差只降 SNR，不产生失真
#   v2: code = SAR(vin + 判决域内的误差)      -> 误差改变判决，产生 INL/DNL/谐波
#   所以 v1 的 SNDR - DR = 0.03 dB（失真项为零），v2 才能给出有意义的 SNDR。
#
# 结构：逐样本 → 一级 10 判决（6 粗 + 5 精合并为逐位）→ 余差 → RA → 二级 12 判决 + 8× 重复 → 重构
# 状态：参考 droop 跨样本累积（一阶 RC），是本模型唯一的跨样本记忆。
#
# ⚠️ 参数来源：τ/A0/t_avail 等标 TODO 者待架构（T01）确认；当前值是我按物理量级的估计。
# 单位：V / s / F / Ω；输出为重构码（int）。
"""信号流级 SAR 行为模型：让非理想进入判决域。"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .params import P, LSB1, LSB2, N_TOTAL


@dataclass
class CfgV2:
    """v2 的非理想配置。全部默认关闭，逐个开以做归因。"""
    # 参考
    vref: float = 5.0                # 单侧参考（差分 FS=10 Vpp）
    c_decap: float = 300e-12         # 片上去耦
    r_buf: float = 20.0              # buffer 输出阻抗
    droop_en: bool = False
    # 专利 US10826519B1：内部参考先预充到接近外部电平，切换后只补差额
    ref_precharge: bool = False      # True = droop 只按 Δcode 算（预置后只补差值）
    # droop 的求解粒度："sample" = 整样本一个值（旧，保守）；"insample" = 逐位求值（真实）
    droop_mode: str = "sample"
    # 专利 US10707889B1：tracking 相位用上一样本结果预置 DAC，跳过 reset
    pretrack: bool = False

    # DAC 建立
    settle_en: bool = False
    settle_tau: float | None = None  # TODO(T01)；= R_on × C_dac
    t_bit: float = 3e-9              # 每次判决可用时间（ΦC1 15 ns / 5）

    # 比较器
    meta_en: bool = False
    meta_tau: float | None = None    # TODO(T01)
    meta_t_avail: float = 1.0e-9

    # RA
    g_ra: float = 32.0
    a0_db: float | None = None       # TODO(T01)
    ra_tau: float | None = None      # TODO(T01)
    ra_t_settle: float = 17e-9

    # 噪声（与 v1 同源，便于对照）
    ktc: float = 17.3e-6          # 采样 kT/C -> 加到输入
    cmp_n: float = 9.7e-6         # 比较器 -> 加到输入
    ref_n: float = 2.9e-6         # 参考 -> 加到输入
    ra_n: float = 24.0e-6         # RA 宽带 -> 加到「余差」，不是输入
    noise_en: bool = True

    # 8× LSB 重复（论文 p.47：DAC2 码冻结，连续读 M 次再平均）
    M_rep: int = 1                # 1 = 不做重复
    rho_rep: float = 0.61         # 相邻两次读的相关系数（AR(1)）
    rep_weight: str = "tri"       # "tri" = 二阶 CoI 三角权；"box" = 均匀
    rep_dac_step: float = 0.0     # 每次重复 DAC2 动的量（LSB1），0 = 码冻结


def _sar_convert(x, n_bits, lsb, cfg, rng, droop_state, t_bit, c_unit=27e-15):
    """一次逐位 SAR 转换，返回 (code, v_dac, 新 droop 状态)。

    droop_mode="insample" 时，每次切换后按 t_bit 更新 droop 并用于该位判决；
    "sample" 时整个转换用同一个 droop（旧行为，保守）。
    """
    v_dac = 0.0
    code = 0
    droop = droop_state
    rec = float(np.exp(-t_bit / (cfg.r_buf * cfg.c_decap)))
    settle_f = (1.0 - float(np.exp(-t_bit / cfg.settle_tau))) if (cfg.settle_en and cfg.settle_tau) else 1.0
    meta_thr = (float(np.exp(-cfg.meta_t_avail / cfg.meta_tau)) * lsb
                if (cfg.meta_en and cfg.meta_tau) else 0.0)
    for b in range(n_bits):
        w = lsb * (2 ** (n_bits - 1 - b))
        # 参考电压：droop_mode="insample" 时用「本位之前累积的 droop」
        vref_eff = (cfg.vref - droop) if cfg.droop_en else cfg.vref
        v_trial = (v_dac + w) * (vref_eff / cfg.vref)

        # 建立未完成：实际输出还在路上
        if cfg.settle_en and cfg.settle_tau:
            v_trial = v_dac + (v_trial - v_dac) * settle_f

        # 比较器（含亚稳态：差距极小时随机）
        diff = x - v_trial
        if meta_thr > 0.0 and abs(diff) < meta_thr:
            diff = rng.normal(0, meta_thr)
        if diff >= 0:
            code |= (1 << (n_bits - 1 - b))   # 位序必须与权重 LSB·2^(N-1-b) 对应
            v_dac = v_dac + w
            # 只有「接 VREF」的位才从参考取电荷；不置位接 GND，不取
            if cfg.droop_en and cfg.droop_mode == "insample":
                dq = (2 ** (n_bits - 1 - b)) * c_unit * cfg.vref
                droop = droop * rec + dq / cfg.c_decap
    return code, v_dac, droop


def simulate_v2(fin=None, fs=None, n=None, *, cfg: CfgV2 | None = None, seed=1,
                inl_lsb1=None, dither_lsb1=0.0, vin=None):
    """返回 (重构码, 输入电压)。码为 N_TOTAL 位无符号偏移二进制。

    inl_lsb1 : (1024,) 数组或 None
        DAC1 逐码静态失配（LSB1 单位），来自 charge_model.inl_profile()。
        判决后加到 v_dac 上——影响余差，从而影响二级能否补回来。
    dither_lsb1 : float
        DAC 域 dither 幅度（LSB1）。判决前随机加入、数字侧同量减去（去扰）。
    """
    cfg = cfg or CfgV2()
    fs = P.fs if fs is None else fs
    n = P.n if n is None else n
    rng = np.random.default_rng(seed)

    if vin is not None:
        vin = np.asarray(vin, float)
        n = len(vin)
    else:
        t = np.arange(n) / fs
        vin = P.amp * np.sin(2 * np.pi * fin * t)

    if cfg.noise_en:
        vin_n = (vin
                 + rng.normal(0, cfg.ktc, n)
                 + rng.normal(0, cfg.cmp_n, n)
                 + rng.normal(0, cfg.ref_n, n))
    else:
        vin_n = vin.copy()

    codes = np.empty(n, dtype=np.int64)
    droop = 0.0
    dt_amp = float(dither_lsb1) * LSB1
    prev_code = None             # tracking 预置用（专利 US10707889B1）
    c_unit = 27e-15
    decay_s = np.exp(-(1.0 / fs) / (cfg.r_buf * cfg.c_decap))
    off = P.fs_diff / 2          # 双极性 -> 单极性平移（SAR 从 0 向上逼近）
    for i in range(n):
        # 样本间：参考在采样期（约 1/fs）内恢复 —— 衰减必须放在转换之前
        if cfg.droop_en:
            droop *= decay_s
        x = vin_n[i] + off
        # ---- 一级 ----
        c1, v_dac1, droop = _sar_convert(x, P.N1, LSB1, cfg, rng, droop, cfg.t_bit * 2)

        # ---- 参考 droop 的状态更新（sample 模式；insample 已在转换内累积）----
        if cfg.droop_en and cfg.droop_mode == "sample":
            if cfg.pretrack and prev_code is not None:
                d_units = abs(c1 - prev_code)
            elif cfg.ref_precharge and prev_code is not None:
                d_units = abs(c1 - prev_code)
            else:
                d_units = c1
            dq = d_units * c_unit * cfg.vref
            droop = droop + dq / cfg.c_decap
        elif cfg.droop_en and cfg.droop_mode == "insample":
            pass          # 已在 _sar_convert 内部逐位累积
        prev_code = c1
        # ---- DAC1 静态失配（逐码）----
        if inl_lsb1 is not None:
            v_dac1 = v_dac1 + float(inl_lsb1[int(c1)]) * LSB1

        # ---- DAC 域 dither（判决后注入，数字侧同量去扰）----
        if dt_amp:
            d = rng.uniform(-dt_amp, dt_amp)
            v_dac1 = v_dac1 + d
        else:
            d = 0.0

        # ---- 余差 ----
        resid = x - v_dac1
        # RA 非理想：都作用在「折输入」域的余差上（G 只影响 RA 输出摆幅，不影响归一化位置）
        if cfg.a0_db:
            a0 = 10 ** (cfg.a0_db / 20.0)
            resid = resid * (1.0 - 1.0 / a0)
        if cfg.ra_tau and cfg.ra_t_settle:
            resid = resid * (1.0 - np.exp(-cfg.ra_t_settle / cfg.ra_tau))
        # ---- 二级（12 bit，窗口折输入 ±2 LSB1），可选 M 次重复读 ----
        wk = 2 * LSB1
        M = max(1, int(cfg.M_rep))
        if M == 1:
            r1 = resid
            if cfg.noise_en:
                r1 = r1 + rng.normal(0, cfg.ra_n)
            rel = np.clip(r1 / wk, -1.0, 1.0)
            c2 = int(np.round((rel + 1.0) * 0.5 * (2 ** P.N2))) - 1
        else:
            # AR(1) 序列：同一样本的 M 次读之间相关
            nz = np.empty(M)
            nz[0] = rng.normal(0, cfg.ra_n) if cfg.noise_en else 0.0
            for m in range(1, M):
                nz[m] = (cfg.rho_rep * nz[m-1]
                         + rng.normal(0, cfg.ra_n * np.sqrt(max(0.0, 1 - cfg.rho_rep**2)))
                         if cfg.noise_en else 0.0)
            if cfg.rep_weight == "tri":      # 二阶 CoI：1,2,...,M/2,...,2,1
                w = np.minimum(np.arange(1, M+1), np.arange(M, 0, -1)).astype(float)
            else:
                w = np.ones(M)
            w = w / w.sum()
            acc = 0.0
            for m in range(M):
                # 论文 p.47：重复期间 DAC2 只动最低位（rep_dac_step），默认 0
                r_m = resid + nz[m] + m * cfg.rep_dac_step * LSB1
                rel = np.clip(r_m / wk, -1.0, 1.0)
                acc += w[m] * (np.round((rel + 1.0) * 0.5 * (2 ** P.N2)) - 1)
            c2 = int(np.round(acc))
        c2 = int(np.clip(c2, 0, 2 ** P.N2 - 1))
        # ---- 重构（标准两级冗余重组，结果已是偏移二进制，中心 2^(N-1)）----
        # 去扰：二级编码的是 (resid_ideal − d)，所以数字端要「加回」d
        d_code = (d / LSB1) * (2 ** (P.N2 - P.R)) if dt_amp else 0.0
        raw = c1 * (2 ** (P.N2 - P.R)) + (c2 - 2 ** (P.N2 - 1)) + d_code
        codes[i] = min(max(raw, 0), 2 ** N_TOTAL - 1)

    # 偏移二进制（20 bit）
    return codes, vin


def codes_to_volts(codes):
    """重构码（偏移二进制，中心 2^(N-1)）-> 伏特（差分），用于 FFT。"""
    full = 2 ** N_TOTAL
    return np.asarray(codes, dtype=float) / full * P.fs_diff - P.fs_diff / 2
