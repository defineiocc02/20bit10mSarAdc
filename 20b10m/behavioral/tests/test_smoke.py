# [CODE-INDEX] test_smoke.py —— 最小闭环与不变量测试
#
# 规范 §16：测试不能只验证「代码没报错」。这里每条都断言物理不变量。
"""核心不变量测试。"""

import numpy as np
import pytest

from sar20b.config import NumericalContract, PROFILES, make_config
from sar20b.core.pipeline import Pipeline, make_pipeline
from sar20b.analysis.spectrum import fft_metrics, psd_check


# ---------------------------------------------------------------- 合同

def test_contract_selfconsistent():
    """位账 10+12−2 必须让 LSB2 恰好等于分析 LSB。"""
    c = NumericalContract()
    assert c.n_total == 20
    assert c.check() == []
    assert abs(c.lsb2_v - c.lsb_analysis_v) / c.lsb_analysis_v < 1e-12


def test_contract_detects_bad_bit_budget():
    """改错位账必须被 check() 抓到，而不是静默通过。"""
    c = NumericalContract(n2=11)          # 11+10−2=19，与 LSB2 不自洽
    assert c.check() != []


# ---------------------------------------------------------------- 配置

def test_unknown_profile_rejected():
    with pytest.raises(KeyError):
        make_config("nonexistent_profile")


def test_native_as_wired_is_7bit():
    """当前网表的真实接法必须暴露为 7 判决，不能悄悄按 10 位算。"""
    cfg = make_config("native_as_wired")
    p = Pipeline(cfg)
    assert p.n1 == 7
    assert len(p.weights) == 7
    # 最低步长 = 8 单位（8 片并联），LSB_eff = 8 × 9.766 mV
    assert abs(p.lsb1_eff - 8 * 9.765625e-3) < 1e-9


# ---------------------------------------------------------------- 码域

def test_ideal_zero_mismatch_gives_zero_inl():
    """σu=0 时全链 INL 必须是 0 —— 这是码域闭合的判据。"""
    p = make_pipeline("ideal", noise_enabled=False, sigma_u=0.0)
    n = 512
    v = np.linspace(-4.8, 4.8, n, endpoint=False)
    outs = p.run(2.5 + v / 2, 2.5 - v / 2)
    codes = p.codes(outs)
    ideal = (v / 10.0 + 0.5) * 2 ** 20
    err = (codes >> 2) - ideal
    A = np.stack([np.ones_like(ideal), ideal], 1)
    coef, *_ = np.linalg.lstsq(A, err, rcond=None)
    inl = err - A @ coef
    assert np.max(np.abs(inl)) < 1.0, f"σu=0 的 INL 应为 0，实测 {np.max(np.abs(inl)):.3f}"


def test_residual_within_one_lsb1():
    """逐次逼近的残差必须落在 [0, LSB1]（单侧），否则判据方向错了。"""
    p = make_pipeline("ideal", noise_enabled=False, sigma_u=0.0)
    n = 256
    v = np.linspace(-4.5, 4.5, n, endpoint=False)
    outs = p.run(2.5 + v / 2, 2.5 - v / 2)
    lsb1s = 5.0 / 1024
    res = np.array([o.v_resid_v for o in outs])
    assert res.min() >= -1e-12
    assert res.max() <= lsb1s + 1e-12


def test_d1_matches_floor():
    """d1 必须等于 floor(x/LSB1)，容差只允许浮点级。"""
    p = make_pipeline("ideal", noise_enabled=False, sigma_u=0.0)
    n = 256
    v = np.linspace(-4.0, 4.0, n, endpoint=False)
    x = 2.5 + v / 2
    outs = p.run(x, 2.5 - v / 2)
    lsb1s = 5.0 / 1024
    # 阈值：只允许 ±1 码（浮点边界），不允许成段偏移（那说明 SAR 判据方向错）
    dev = np.array([outs[i].ctx.d1_raw - int(np.floor(x[i] / lsb1s)) for i in range(n)])
    assert np.max(np.abs(dev)) <= 1, f"d1 偏差超过 1 码：max|dev|={np.max(np.abs(dev))}"
    assert np.mean(dev == 0) > 0.95, f"d1 精确命中率过低：{np.mean(dev == 0):.3f}"


def test_mismatch_scales_inl():
    """失配 10 倍 → INL 约 10 倍（线性响应，不是随机跳变）。"""
    def inl_at(sg):
        p = make_pipeline("ideal", noise_enabled=False, sigma_u=sg)
        n = 512
        v = np.linspace(-4.5, 4.5, n, endpoint=False)
        outs = p.run(2.5 + v / 2, 2.5 - v / 2)
        codes = p.codes(outs)
        ideal = (v / 10.0 + 0.5) * 2 ** 20
        err = (codes >> 2) - ideal
        A = np.stack([np.ones_like(ideal), ideal], 1)
        c, *_ = np.linalg.lstsq(A, err, rcond=None)
        return float(np.max(np.abs(err - A @ c)))
    a, b = inl_at(0.0002), inl_at(0.002)
    assert 5 < b / max(a, 1e-9) < 20, f"σu×10 应给 INL×~10，实测 {a:.2f} -> {b:.2f}"


# ---------------------------------------------------------------- 指标

def test_fft_rejects_incoherent():
    x = np.sin(2 * np.pi * 100_000 * np.arange(4096) / 10e6)
    with pytest.raises(ValueError):
        fft_metrics(x, 10e6, 100_000)     # 不是整数 bin


def test_parseval():
    """PSD 积分必须与时域功率一致（交叉检查另一条路径）。"""
    rng = np.random.default_rng(1)
    x = rng.normal(0, 0.5, 4096) + 0.3 * np.sin(2 * np.pi * 41 * np.arange(4096) / 4096)
    r = psd_check(x, 10e6)
    assert r["parseval_rel_err"] < 1e-6


def test_ideal_sndr_approaches_20bit():
    """σu=0、无噪声时 SNDR 应接近 20 bit 理论值（约 122 dB）。"""
    cfg = make_config("ideal", sigma_u=0.0, noise_enabled=False)
    pipe = Pipeline(cfg)
    n, k = 4096, 41
    fs = cfg.contract.fs_hz
    fin = k * fs / n
    t = np.arange(n) / fs
    v = 4.8 * np.sin(2 * np.pi * fin * t)
    outs = pipe.run(2.5 + v / 2, 2.5 - v / 2)
    codes = pipe.codes(outs)
    x = codes / 2 ** 22 * 10.0 - 5.0
    m = fft_metrics(x, fs, fin)
    assert m["sndr_db"] > 118.0, f"理想 SNDR 太低：{m['sndr_db']:.1f}"
    assert m["enob_bit"] > 19.0
