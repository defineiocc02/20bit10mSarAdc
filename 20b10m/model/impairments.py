# [CODE-INDEX] impairments.py —— 非理想效应（行为级，可插拔）
# 现状：现有 adc.simulate() 是「输入折算」模型，没有余差/RA 输出等中间节点。
#       本模块把缺失效应做成「输入折算 + 码相关加性误差」，每项独立开关。
# 参数：全部默认 None / enabled=False，默认不启用，不改变历史结果。
#
# ⚠️ 可信度分级（2026-11-08 实跑后标注，勿跨级引用）：
#   【形式可用，参数待定】settling / finite_gain / ra_bandwidth / metastability
#        —— 一阶 RC 或概率式是标准做法，只需架构给 τ/A0/t_avail 的真值。
#   【形式存疑，仅供参考】droop / charge_injection / ron_nonlinearity / kickback
#        —— 这三项的真实机制需要「信号流级 + 状态」，输入折算只能给上界估计；
#           实跑显示 droop 与 Ron 的量级对参数极敏感（±10× 级），不可作为结论。
#        —— 正确的闭式模型待 T01（架构）回传后用其形式替换。
# 单位：V / s / F / Ω / LSB（除注明外，误差折到输入端）。
"""非理想效应模块：settling / droop / 亚稳态 / 有限增益 / 带宽 / 电荷注入 / Ron 非线性 / kickback。"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .params import P, LSB1, LSB_TOTAL

# ---------------------------------------------------------------- 配置


@dataclass
class Cfg:
    """所有效应的总配置。默认全关。"""
    # DAC 建立（ΦC1 5 次精试 + ΦC0 粗量化）
    settle_en: bool = False
    settle_tau: float | None = None      # s，= R_on × C_dac；TODO(T01)
    settle_t_bit: float = 3e-9           # s，ΦC1 每次精试可用时间（15 ns / 5）
    settle_startup: float = 5e-9         # s，ΦC1 起点的额外余量

    # 参考 droop（带状态：一阶 RC 恢复）
    droop_en: bool = False
    c_decap: float = 300e-12             # F，片上去耦
    r_buf: float = 20.0                  # Ω，参考 buffer 输出阻抗
    vref: float = 5.0                    # V
    t_cmp: float = 3.0e-9                # s，切换后到首次比较的时间

    # 比较器亚稳态（概率错码）
    meta_en: bool = False
    meta_tau: float | None = None        # s，latch 再生时间常数；TODO(T01)
    meta_t_avail: float = 1.0e-9         # s，留给再生的时间
    meta_scale: float = 0.5              # 错码幅度（LSB1）

    # RA 有限增益（静态增益误差 → 余差缩放，折输入要再 ÷G）
    a0_en: bool = False
    a0_db: float | None = None           # dB；TODO(T01)
    g_ra: float = 32.0                   # 级间增益（BL-v3）

    # RA 有限带宽（建立残余，折输入）
    rabw_en: bool = False
    ra_tau: float | None = None          # s
    ra_t_settle: float = 17e-9           # s，ΦRA 20 ns 内的建立时间

    # 开关电荷注入（常数偏移 + 码相关部分）
    qinj_en: bool = False
    q_inj: float | None = None           # C，注入电荷；TODO(T01)
    c_sample: float = 28e-12             # F

    # 采样开关 Ron 非线性（增益/失真）
    ron_en: bool = False
    ron_delta: float | None = None       # ΔRon/Ron 峰峰；TODO(T01)

    # 参考 kickback（码相关，折输入）
    kick_en: bool = False
    kick_v: float | None = None          # V @RA 输出；TODO(T01)
    kick_ratio: float = 1.0              # replica 抵消后的残余比例（1=未抵消）


IMP = Cfg()


# ---------------------------------------------------------------- 工具


def _codes(vin, n1=None):
    """把输入电压反算成一级码（用于码相关误差）。"""
    n1 = P.N1 if n1 is None else n1
    return np.clip(np.round((vin / P.fs_diff + 0.5) * 2**n1).astype(int), 0, 2**n1 - 1)


def _lsb1_fraction(code):
    """当前码对应的「切换了多少个单位」——用相邻码差近似。"""
    d = np.abs(np.diff(np.r_[code[0], code]))
    return d / 2**P.N1


# ---------------------------------------------------------------- 各效应


def settling(vin, cfg: Cfg = IMP, seed=0):
    """DAC 建立残余（折输入，V）。

    模型：每次精试切换后残余 = 0.5·LSB1 · exp(−t/τ)，
    t 取「本次可用时间」；按码差加权（切换越大残余越大）。
    最坏情况取最后一次切换的残余，不再累积（一阶近似）。
    """
    if not (cfg.settle_en and cfg.settle_tau):
        return np.zeros_like(vin)
    code = _codes(vin)
    frac = _lsb1_fraction(code)                      # 0..1
    t = cfg.settle_t_bit + cfg.settle_startup
    r = np.exp(-t / cfg.settle_tau)
    return 0.5 * LSB1 * frac * r


def droop(vin, cfg: Cfg = IMP):
    """参考 droop（折输入，V）。⚠️ 形式存疑：真实机制需信号流级+状态，本式只给上界。

    模型：每个样本取走 Q = C_dac·ΔV_code 的电荷，参考节点按一阶 RC 恢复；
    取「上一样本结束后剩余 droop」作为本样本的参考误差。
    状态：单极点 v[n] = v[n-1]·exp(−T/(R·C)) + ΔQ/C。
    """
    if not cfg.droop_en:
        return np.zeros_like(vin)
    code = _codes(vin)
    frac = _lsb1_fraction(code)
    c_dac = 2**P.N1 * 27e-15                         # 一级总电容（单侧）
    dq = c_dac * cfg.vref * frac                     # 每次转换取走的电荷
    decay = np.exp(-(1.0 / P.fs) / (cfg.r_buf * cfg.c_decap))
    # 跌落发生后，buffer 在 t_cmp 内已恢复一部分；比较看到的是恢复后的残余
    rec = np.exp(-cfg.t_cmp / (cfg.r_buf * cfg.c_decap))
    v = 0.0
    out = np.empty_like(vin)
    for i in range(len(vin)):
        v = v * decay + dq[i] / cfg.c_decap
        out[i] = v * rec
    # 参考误差 → 输入等效：顶板分压约 0.5，再按 FS/VREF 折算
    return out * 0.5 * (P.fs_diff / cfg.vref)


def metastability(n, cfg: Cfg = IMP, seed=0):
    """比较器亚稳态导致的随机错码（V）。

    模型：每次比较的失败概率 p = exp(−t_avail/τ_latch)；
    一次转换有 N2 次比较，样本级失败概率 1−(1−p)^N2；
    失败时给 ±meta_scale·LSB1 的随机错码。
    """
    if not (cfg.meta_en and cfg.meta_tau):
        return np.zeros(n)
    p1 = np.exp(-cfg.meta_t_avail / cfg.meta_tau)
    p_sample = 1.0 - (1.0 - p1) ** P.N2
    rng = np.random.default_rng(seed + 9001)
    hit = rng.random(n) < p_sample
    sign = rng.choice([-1.0, 1.0], n)
    return hit * sign * cfg.meta_scale * LSB1, p_sample


def finite_gain(vin, cfg: Cfg = IMP):
    """RA 有限增益：余差传递比 1/(1+1/A0) 的误差（折输入）。

    余差幅度上界取 ±2 LSB1（冗余窗口），
    误差 = 余差 · (1/(1+A0) ) ≈ 余差/A0。
    """
    if not (cfg.a0_en and cfg.a0_db):
        return np.zeros_like(vin)
    a0 = 10 ** (cfg.a0_db / 20.0)
    resid_max = 2 * LSB1
    # 余差传递误差 resid/A0 发生在 RA 输出域，折输入要再除以 G
    return np.full_like(vin, resid_max / a0 / cfg.g_ra)


def ra_bandwidth(vin, cfg: Cfg = IMP):
    """RA 建立残余（折输入）：余差上界 × exp(−t/τ) / G。"""
    if not (cfg.rabw_en and cfg.ra_tau):
        return np.zeros_like(vin)
    resid_max = 2 * LSB1
    g = 32.0
    return np.full_like(vin, resid_max * np.exp(-cfg.ra_t_settle / cfg.ra_tau) / g)


def charge_injection(vin, cfg: Cfg = IMP):
    """采样开关电荷注入（折输入）。⚠️ 形式存疑：P/N 互补抵消未建模，本式给单端上界。"""
    if not (cfg.qinj_en and cfg.q_inj):
        return np.zeros_like(vin)
    v = cfg.q_inj / cfg.c_sample
    code = _codes(vin)
    frac = _lsb1_fraction(code)
    return v * (0.5 + 0.5 * frac)


def ron_nonlinearity(vin, cfg: Cfg = IMP):
    """Ron 非线性。⚠️ 形式存疑：真实影响是采样时刻误差（与 dV/dt 相关），
    不是增益压缩。本式对低频信号严重高估，仅供量级上界参考。"""
    if not (cfg.ron_en and cfg.ron_delta):
        return np.zeros_like(vin)
    # Ron 随输入变 → 采样时刻的电荷转移误差，等效为二次失真项
    # 幅度定标：ΔRon/Ron 在 ±FS/2 上的变化 → 增益压缩 a2·v²，a2 = ΔRon/(2·Ron·Vfs)
    a2 = cfg.ron_delta / (2.0 * P.fs_diff)
    return a2 * vin * vin


def ref_kickback(vin, cfg: Cfg = IMP):
    """参考 kickback（折输入）：按码差线性折算。"""
    if not (cfg.kick_en and cfg.kick_v):
        return np.zeros_like(vin)
    code = _codes(vin)
    frac = _lsb1_fraction(code)
    return cfg.kick_v * cfg.kick_ratio / 32.0 * frac


# ---------------------------------------------------------------- 汇总


def apply_all(vin, cfg: Cfg = IMP, seed=0):
    """返回 (总加性误差, 分项字典)。全部折到输入端，单位 V。"""
    parts = {
        "settling": settling(vin, cfg, seed),
        "droop": droop(vin, cfg),
        "finite_gain": finite_gain(vin, cfg),
        "ra_bw": ra_bandwidth(vin, cfg),
        "charge_inj": charge_injection(vin, cfg),
        "ron_nonlin": ron_nonlinearity(vin, cfg),
        "kickback": ref_kickback(vin, cfg),
    }
    meta = metastability(len(vin), cfg, seed)
    if isinstance(meta, tuple):
        meta, p = meta
        parts["meta_p"] = p
    parts["metastability"] = meta
    total = sum(v for k, v in parts.items() if k != "meta_p")
    return total, parts


def describe(cfg: Cfg = IMP):
    """返回「哪些开着、参数是多少、缺哪个」的清单（供报告引用）。"""
    rows = []
    for name, need in [
        ("settling", "settle_tau"), ("droop", "c_decap"),
        ("metastability", "meta_tau"), ("finite_gain", "a0_db"),
        ("ra_bandwidth", "ra_tau"), ("charge_injection", "q_inj"),
        ("ron_nonlinearity", "ron_delta"), ("kickback", "kick_v"),
    ]:
        en = getattr(cfg, f"{name.split('_')[0]}_en", None)
        val = getattr(cfg, need, None)
        rows.append(dict(effect=name, enabled=bool(en),
                         param=need, value=val,
                         ready=bool(en and val is not None)))
    return rows
