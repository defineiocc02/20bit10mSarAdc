"""figures_ssot.py —— 效果图（每张带来源脚注 + 统计误差）

规则（与 spec/SSOT.md §8 一致）：
- 每张图只回答一个问题；
- 图上每个"效果数字"必须带来源标签：[模型] / [论文] / [估算]；
- 动态图的误差棒 = 10 seeds 的 95% CI（t=2.262）；图与 crossval 用独立 seed 段；
- 脚注写：脚本、数据函数、N、seeds、口径、证据等级、日期；
- 不把模型值写成"实测"，不把片级 shuffle 写成 DEM。

运行：cd 20b10m && python3 -m model.crossval && python3 -m model.figures_ssot
输出：docs/figures/*.png / *.svg / *.pdf + manifest.json
"""

from __future__ import annotations

import hashlib
import json
import math
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .params import P
from .adc import simulate
from .metrics import fft_metrics
from . import static, viz

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"
CV = ROOT / "model" / "results" / "crossval" / "results.json"
W_MM = 146.0
BLUE, ORANGE, GREEN, GRAY, RED, PURPLE = "#0072B2", "#D55E00", "#009E73", "#5F5E5A", "#A32D2D", "#534AB7"
T95 = 2.262
SEEDS = list(range(2000, 2010))  # 与 crossval 的 1000..1009 独立

FOOT_COMMON = ("来源: model/figures_ssot.py · 数据: {data} · N={n} · seeds={seeds}\n"
               "口径: SSOT 20.00 bit (10+12−2) · G=32 · 等级: L1 行为模型（非前仿/非硅测） · 2026-11-12")


def canvas(h_mm: float = 96.0):
    viz.chinese_style()
    fig, ax = plt.subplots(figsize=(W_MM / 25.4, h_mm / 25.4))
    fig.subplots_adjust(left=0.105, right=0.975, top=0.80, bottom=0.38)
    return fig, ax


def head(fig, title: str, subtitle: str) -> None:
    fig.text(0.015, 0.965, title, fontsize=10.5, fontweight=600, va="top")
    fig.text(0.015, 0.905, subtitle, fontsize=7.2, color=GRAY, va="top")


def foot(fig, notes) -> None:
    if isinstance(notes, str):
        notes = [notes]
    lines = []
    for n in notes:
        for seg in str(n).split("\n"):
            lines += textwrap.wrap(seg, width=58)
    y = getattr(fig, "_foot_y", 0.200)
    for ln in lines[:6]:
        fig.text(0.015, y, ln, fontsize=6.2, color=GRAY, va="bottom")
        y -= 0.028
    fig._foot_y = y


def save(fig, stem: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / stem
    viz.save(fig, p)
    plt.close(fig)
    return p


def samples(fin, fs, n, seeds, **kw):
    fc = round(fin * n / fs) * fs / n
    rows = [fft_metrics(simulate(fc, fs=fs, n=n, seed=s, **kw)[0], fs, fc) for s in seeds]
    return {k: np.array([r[k] for r in rows]) for k in ("DR_dB", "SNDR_dB", "SFDR_dBc")}


def mean_ci(x):
    x = np.asarray(x, float)
    k = len(x)
    m = float(x.mean())
    ci = T95 * float(x.std(ddof=1)) / math.sqrt(k)
    return m, ci


# ---------------------------------------------------------------- 1. 频谱
def fig_spectrum() -> Path:
    fs, fin, n = 10e6, 100e3, P.n
    fc = round(fin * n / fs) * fs / n
    x, _ = simulate(fc, fs=fs, seed=11)
    m = fft_metrics(x, fs, fc)
    spec = np.abs(np.fft.rfft(x - x.mean())) / (n / 2)
    f = np.arange(len(spec)) * fs / n / 1e6
    db = 20 * np.log10(np.maximum(spec, 1e-15) / spec.max())

    fig, ax = canvas(96)
    ax.plot(f, db, lw=0.55, color=BLUE)
    ax.set_xlim(0, 5)
    ax.set_ylim(-150, 5)
    ax.set_xlabel("频率 (MHz)")
    ax.set_ylabel("幅度 (dBc)")
    ax.grid(alpha=0.25, lw=0.4)

    ax.annotate(f"SNDR {m['SNDR_dB']:.1f} dB  [模型]\nDR {m['DR_dB']:.1f} dB  [模型]\n"
                f"SFDR {m['SFDR_dBc']:.1f} dBc  [模型]",
                xy=(0.62, 0.86), xycoords="axes fraction", fontsize=7.6,
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#B4B2A9", lw=0.5), va="top")

    head(fig, "100 kHz 输入频谱：约 102 dB 是行为模型值，不是硅测",
         "相干采样 + 矩形窗；fin 吸附到整数 bin；噪声含 kT/C、RA、AZ、Cmp、参考、二级量化")
    foot(fig, [FOOT_COMMON.format(data="model.adc.simulate + model.metrics.fft_metrics", n=n, seeds="seed=11"),
               "说明: 曲线来自模型；绝对 SNDR/DR 未标定，不能写进数据手册或论文实测栏。"])
    return save(fig, "f1_spectrum")


# ---------------------------------------------------------------- 2. 8× 平均（10 seeds）
def fig_averaging() -> Path:
    ms = [1, 2, 4, 8]
    mean, ci = [], []
    for M in ms:
        s = samples(100e3, 10e6, P.n, SEEDS, M=M)["SNDR_dB"]
        m, c = mean_ci(s)
        mean.append(m)
        ci.append(c)
    mean, ci = np.array(mean), np.array(ci)
    ref = mean[0] + 10 * np.log10(ms)

    fig, ax = canvas(92)
    ax.errorbar(ms, mean, yerr=ci, fmt="o-", color=BLUE, ms=4, lw=1.1, capsize=2.5)
    ax.plot(ms, ref, "--", color=GRAY, lw=0.8)
    ax.set_xscale("log", base=2)
    ax.set_xticks(ms)
    ax.set_xticklabels([str(m) for m in ms])
    ax.set_xlabel("重复次数 M")
    ax.set_ylabel("SNDR (dB)")
    ax.grid(alpha=0.25, lw=0.4)
    ax.text(5.0, 106.6, "理想 √M（+3 dB/倍频）", color=GRAY, fontsize=6.6)
    ax.text(5.0, 102.1, "模型（10 seeds）", color=BLUE, fontsize=6.6)

    gain = mean[-1] - mean[0]
    ax.annotate(f"M=1→8: +{gain:.2f} dB  [模型]\n论文 p.47: +2 dB  [论文]",
                xy=(0.03, 0.97), xycoords="axes fraction", fontsize=7.4, va="top",
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#B4B2A9", lw=0.5))

    head(fig, f"8× LSB 重复：模型 {gain:+.2f} dB（10 seeds），不是 4.5 dB",
         "ρ=0.61 为反解值（stress）；均匀权；M=8 的收益按噪声口径记，不进码宽")
    foot(fig, [FOOT_COMMON.format(data="model.adc.simulate，M 扫描", n=P.n, seeds="2000-2009"),
               "说明: 误差棒是 10 seeds 的 95% CI；ρ 不是硅上相关实测，+1.7 dB 不能写成论文复现值。"])
    return save(fig, "f2_averaging")


# ---------------------------------------------------------------- 3. 片级 shuffle（10 seeds）
def fig_shuffle() -> Path:
    base = dict(gain=5e-5, offset=50e-6, skew=1e-12, shuffle=False)
    tech = dict(gain=5e-5, offset=50e-6, skew=1e-12, shuffle=True)
    off = samples(100e3, 10e6, 8192, SEEDS, interleave=base)
    on = samples(100e3, 10e6, 8192, SEEDS, interleave=tech)

    fig, ax = canvas(94)
    x = np.arange(2)
    w = 0.34
    drm = [off["DR_dB"].mean(), on["DR_dB"].mean()]
    drc = [mean_ci(off["DR_dB"])[1], mean_ci(on["DR_dB"])[1]]
    sfm = [off["SFDR_dBc"].mean(), on["SFDR_dBc"].mean()]
    sfc = [mean_ci(off["SFDR_dBc"])[1], mean_ci(on["SFDR_dBc"])[1]]
    b1 = ax.bar(x - w/2, drm, w, yerr=drc, capsize=3, color=BLUE)
    b2 = ax.bar(x + w/2, sfm, w, yerr=sfc, capsize=3, color=ORANGE)
    for bars, name in ((b1, "DR"), (b2, "SFDR")):
        for b in bars:
            ax.text(b.get_x() + b.get_width()/2, b.get_height() - 3,
                    f"{name} {b.get_height():.1f}", ha="center", va="center",
                    fontsize=6.6, color="white", fontweight=500)
    ax.set_xticks(x)
    ax.set_xticklabels(["固定轮换", "随机选片"])
    ax.set_ylim(88, 134)
    ax.set_ylabel("dB / dBc")
    ax.grid(axis="y", alpha=0.25, lw=0.4)

    ddr = on["DR_dB"] - off["DR_dB"]
    dsf = on["SFDR_dBc"] - off["SFDR_dBc"]
    mdr, cdr = mean_ci(ddr)
    msf, csf = mean_ci(dsf)
    ax.annotate(f"ΔDR {mdr:+.1f} ± {cdr:.1f} dB（方向随 seed 段翻转）\n"
                f"ΔSFDR {msf:+.1f} ± {csf:.1f} dBc（稳健）",
                xy=(0.02, 0.97), xycoords="axes fraction", fontsize=6.8, va="top",
                bbox=dict(boxstyle="round,pad=0.32", fc="white", ec="#B4B2A9", lw=0.5))
    fig.text(0.015, 0.845, "注意：这是片级 8/18 随机选片，不是 CDAC 单位级 DEM；不能引用为 DEM 收益",
             fontsize=6.8, color=RED)

    head(fig, f"片级随机选片：SFDR {msf:+.1f} dBc 稳健，DR 方向不稳（{mdr:+.1f} dB）",
         "18 片池每样本随机抽 8 片；gain 50 ppm / offset 50 µV / skew 1 ps；10 seeds")
    foot(fig, [FOOT_COMMON.format(data="model.adc.simulate，interleave", n=8192, seeds="2000-2009"),
               "说明: 本段 ΔDR=−1.7 dB，另一段 +0.9 dB；方向不稳，不能写 DR 换 SFDR。"])
    return save(fig, "f3_shuffle")


# ---------------------------------------------------------------- 4. INL / DNL
def fig_inl_dnl() -> Path:
    """INL + DNL 的前/后对比：曲线、最差码、汇总表。"""
    from .charge_model import dac1_curves, _features

    c = dac1_curves(sigma=0.002, seed=7)
    code, raw_inl, raw_dnl = c["code"], c["inl_raw"], c["dnl_raw"]
    # 有限样本校准：16 次平均、单次 2.8 LSB20 噪声；固定 realization，不玩随机符号
    B = _features(code >> 7, code & 127)
    rng = np.random.default_rng(7 + 1000)
    y = raw_inl + rng.normal(0, (2.8 / 1024) / math.sqrt(16), len(raw_inl))
    w, *_ = np.linalg.lstsq(B, y, rcond=None)
    cal_inl = B @ w - raw_inl
    cal_dnl = np.diff(code + cal_inl) - 1
    leg = static.curves_binary(bits=10, unit_sigma=0.002, seed=1)

    pk = lambda a: float(np.max(np.abs(a)))
    raw_ppm = pk(raw_inl) * 1e6 / 1024
    cal_ppm = pk(cal_inl) * 1e6 / 1024
    leg_ppm = pk(leg["inl_raw"]) * 1e6 / 1024
    raw_dp, cal_dp, leg_dp = pk(raw_dnl), pk(cal_dnl), pk(leg["dnl_raw"])
    miss_raw = int((raw_dnl <= -1).sum())
    miss_cal = int((cal_dnl <= -1).sum())

    fig = plt.figure(figsize=(W_MM / 25.4, 142 / 25.4))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 0.95], hspace=0.62, wspace=0.26,
                          left=0.115, right=0.975, top=0.80, bottom=0.33)
    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[1, 0])
    ax4 = fig.add_subplot(gs[1, 1])

    # A: INL
    ax1.plot(code, raw_inl, color=ORANGE, lw=0.6, label="未校准")
    ax1.plot(code, cal_inl, color=BLUE, lw=0.8, label="校准后（16 次平均）")
    ax1.axhline(0, color=GRAY, lw=0.4)
    ax1.set_xlim(0, 1023)
    ax1.set_xlabel("DAC1 码")
    ax1.set_ylabel("INL (LSB1)")
    ax1.grid(alpha=0.25, lw=0.4)
    ax1.legend(fontsize=6.0, loc="upper right", frameon=True, framealpha=0.95, edgecolor="#B4B2A9")
    ax1.set_title(f"INL：{raw_ppm:.1f} → {cal_ppm:.2f} ppm（{raw_ppm/cal_ppm:.0f}×）",
                  fontsize=8, loc="left", pad=4)

    # B: DNL
    ax2.plot(code[1:], raw_dnl, color=ORANGE, lw=0.6, label="未校准")
    ax2.plot(code[1:], cal_dnl, color=BLUE, lw=0.8, label="校准后")
    ax2.axhline(0, color=GRAY, lw=0.4)
    ax2.set_xlim(0, 1023)
    ax2.set_ylim(-0.02, 0.02)
    ax2.set_xlabel("DAC1 码")
    ax2.set_ylabel("DNL (LSB1)")
    ax2.grid(alpha=0.25, lw=0.4)
    ax2.legend(fontsize=6.0, loc="upper right", frameon=True, framealpha=0.95, edgecolor="#B4B2A9")
    ax2.set_title(f"DNL：{raw_dp:.4f} → {cal_dp:.4f} LSB1（{raw_dp/cal_dp:.0f}×）",
                  fontsize=8, loc="left", pad=4)

    # C: 最差 DNL 码附近
    k = int(np.argmax(np.abs(raw_dnl))) + 1
    lo, hi = max(1, k - 7), min(1023, k + 7)
    zc = np.arange(lo, hi + 1)
    ax3.plot(zc, raw_dnl[lo-1:hi], "o-", color=ORANGE, ms=3, lw=0.8)
    ax3.plot(zc, cal_dnl[lo-1:hi], "s-", color=BLUE, ms=3, lw=0.8)
    ax3.axhline(0, color=GRAY, lw=0.4)
    ax3.set_xlim(lo, hi)
    ax3.set_xlabel("DAC1 码")
    ax3.set_ylabel("DNL (LSB1)")
    ax3.grid(alpha=0.25, lw=0.4)
    ax3.set_title(f"最差 DNL 码附近（code {k}）", fontsize=8, loc="left", pad=4)

    # D: 汇总表
    ax4.axis("off")
    rows = [
        ["指标", "legacy 单端", "3+7 raw", "3+7 校准"],
        ["INL pk (ppm)", f"{leg_ppm:.1f}", f"{raw_ppm:.1f}", f"{cal_ppm:.2f}"],
        ["INL pk (LSB20)", f"{leg_ppm*1.048576:.1f}", f"{raw_ppm*1.048576:.1f}", f"{cal_ppm*1.048576:.2f}"],
        ["DNL pk (LSB1)", f"{leg_dp:.4f}", f"{raw_dp:.4f}", f"{cal_dp:.4f}"],
        ["DNL pk (LSB20)", f"{leg_dp*1024:.1f}", f"{raw_dp*1024:.1f}", f"{cal_dp*1024:.2f}"],
        ["失码", "0", f"{miss_raw}", f"{miss_cal}"],
    ]
    tb = ax4.table(cellText=rows, cellLoc="center", loc="center", colWidths=[0.32, 0.24, 0.20, 0.20])
    tb.auto_set_font_size(False)
    tb.set_fontsize(5.9)
    tb.scale(1.0, 1.0)
    for (r, cc), cell in tb.get_celld().items():
        cell.set_linewidth(0.4)
        cell.set_edgecolor("#B4B2A9")
        if r == 0:
            cell.set_facecolor("#F1EFE8")
    ax4.text(0.0, 1.04, "同一失配档（σu=0.2%，seed=7/1）", transform=ax4.transAxes,
             fontsize=8, va="bottom", ha="left")

    head(fig, "DAC1 的 DNL/INL：校准把 INL 压了 30 倍，DNL 本来就没有失码",
         "σu=0.2%，1024 码；纵轴 LSB1；表含 LSB20；校准=16 次平均的有限样本拟合")
    fig.text(0.015, 0.862, "10 芯片：INL 17.8→0.54 ppm；DNL 0.0235→0.00073 LSB1；失码 0→0",
             fontsize=7.2, color=GRAY, va="top")
    foot(fig, [FOOT_COMMON.format(data="charge_model.dac1_curves + _features 有限样本拟合", n=1024, seeds="seed=7；legacy seed=1"),
               "说明: DNL 本来就没有失码；校准收益是留裕量（2.3%→0.07% LSB1）；legacy 单端仅作对照。"])
    return save(fig, "f4_inl_dnl")


def fig_skew_gain() -> Path:
    skews = [0.5, 1.0, 2.0, 4.0]
    sm, sc = [], []
    for s in skews:
        v = samples(2e6, 10e6, 8192, SEEDS,
                    interleave=dict(gain=2e-5, offset=20e-6, skew=s*1e-12, shuffle=True))["SNDR_dB"]
        m, c = mean_ci(v)
        sm.append(m)
        sc.append(c)
    gains = [10, 50, 100]
    gm, gc = [], []
    for g in gains:
        v = samples(100e3, 10e6, 8192, SEEDS,
                    interleave=dict(gain=g*1e-6, offset=0, skew=0, shuffle=True))["SNDR_dB"]
        m, c = mean_ci(v)
        gm.append(m)
        gc.append(c)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(W_MM / 25.4, 92 / 25.4))
    fig.subplots_adjust(left=0.09, right=0.98, top=0.80, bottom=0.38, wspace=0.35)

    ax1.errorbar(skews, sm, yerr=sc, fmt="o-", color=BLUE, ms=4, lw=1.0, capsize=2.5)
    ax1.set_xscale("log", base=2)
    ax1.set_xticks(skews)
    ax1.set_xticklabels([str(s) for s in skews])
    ax1.set_xlabel("片间采样偏斜 (ps)")
    ax1.set_ylabel("SNDR (dB)")
    ax1.grid(alpha=0.25, lw=0.4)
    ax1.annotate(f"2 ps: {sm[2]:.1f} dB  [模型]\n0.5→2 ps: {sm[2]-sm[0]:+.1f} dB",
                 xy=(0.06, 0.10), xycoords="axes fraction", fontsize=6.8, va="bottom")

    ax2.errorbar(gains, gm, yerr=gc, fmt="s-", color=ORANGE, ms=4, lw=1.0, capsize=2.5)
    ax2.set_xscale("log")
    ax2.set_xticks(gains)
    ax2.set_xticklabels([str(g) for g in gains])
    ax2.set_xlabel("片间增益失配 (ppm)")
    ax2.set_ylabel("SNDR (dB)")
    ax2.grid(alpha=0.25, lw=0.4)
    ax2.annotate(f"50 ppm: {gm[1]:.1f} dB  [模型]\n10→50 ppm: {gm[1]-gm[0]:+.1f} dB",
                 xy=(0.06, 0.10), xycoords="axes fraction", fontsize=6.8, va="bottom")

    head(fig, f"交织误差：2 ps 偏斜掉 {sm[0]-sm[2]:.1f} dB，50 ppm 增益失配掉 {gm[0]-gm[1]:.1f} dB",
         "2 MHz（偏斜）/ 100 kHz（增益）；18 片随机选 8；10 seeds，误差棒 95% CI")
    foot(fig, [FOOT_COMMON.format(data="model.adc.simulate + slice_errors", n=8192, seeds="2000-2009"),
               "说明: skew/增益的绝对幅度是 stress 假设；曲线只给趋势与量级，不是封装/版图实测。"])
    return save(fig, "f5_skew_gain")


# ---------------------------------------------------------------- 6. 交叉验证森林图
def fig_crossval() -> Path | None:
    if not CV.exists():
        print("skip f6: 先跑 python3 -m model.crossval")
        return None
    rows = json.loads(CV.read_text())["rows"]

    def pick(test, cfg, metric):
        for r in rows:
            if r["test"] == test and r["config"] == cfg and r["metric"] == metric:
                return r
        return None

    left = [
        ("8× @100k", pick("T1_averaging", "100kHz/N16384", "SNDR_dB")),
        ("8× @1M", pick("T1_averaging", "1000kHz/N8192", "SNDR_dB")),
        ("CAAZ @0.1M", pick("T2_caaz", "0.1MHz/N8192", "SNDR_dB")),
        ("CAAZ @1M", pick("T2_caaz", "1.0MHz/N8192", "SNDR_dB")),
        ("CAAZ @2M", pick("T2_caaz", "2.0MHz/N8192", "SNDR_dB")),
        ("shuffle SFDR @0.1M", pick("T3_shuffle", "100kHz/50ppm", "SFDR_dBc")),
        ("shuffle SFDR @2M", pick("T3_shuffle", "2MHz/1ps", "SFDR_dBc")),
        ("shuffle DR @0.1M", pick("T3_shuffle", "100kHz/50ppm", "DR_dB")),
        ("skew 0.5→2 ps", pick("T5_skew", "0.5->2ps @2MHz", "SNDR_dB")),
        ("gain 10→50 ppm", pick("T5_gain", "10->50ppm @100kHz", "SNDR_dB")),
    ]

    fig = plt.figure(figsize=(W_MM / 25.4, 128 / 25.4))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.55, 1.0], wspace=0.10,
                          left=0.19, right=0.975, top=0.80, bottom=0.30)
    ax = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])

    ys = np.arange(len(left))[::-1]
    for y, (lab, r) in zip(ys, left):
        if r is None:
            continue
        m, lo, hi = r["delta_mean"], r["ci_low"], r["ci_high"]
        sig = (lo > 0) or (hi < 0)
        color = BLUE if (sig and m > 0) else RED if (sig and m < 0) else GRAY
        ax.errorbar(m, y, xerr=[[m - lo], [hi - m]], fmt="o", color=color, ms=3.8,
                    capsize=2.5, lw=1.0, mfc=color if sig else "white")
    ax.axvline(0, color=GRAY, lw=0.6)
    ax.set_yticks(ys)
    ax.set_yticklabels([x[0] for x in left], fontsize=6.8)
    ax.set_xlabel("Δ (dB)", fontsize=8)
    ax.set_xlim(-8, 26)
    ax.grid(axis="x", alpha=0.25, lw=0.4)
    ax.set_title("动态指标（10 seeds，95% CI）", fontsize=8, loc="left", pad=4)
    ax.text(0.99, 0.02, "实心=CI 不跨 0；空心=不显著", transform=ax.transAxes,
            ha="right", fontsize=6.2, color=GRAY)

    cal = pick("T4_calibration", "sigma=0.2%/10 chips", "INL_ppm")
    oos = pick("T4_calibration_oos", "even->odd split/10 chips", "INL_oos_ppm")
    labels = ["raw", "校准\n(有限样本)", "校准\n(out-of-sample)"]
    vals = [cal["raw_mean"], cal["cal_mean"], oos["tech_mean"]]
    errs = [cal["raw_std"], cal["cal_std"], (oos["ci_high"] - oos["ci_low"]) / 2]
    cols = [ORANGE, BLUE, PURPLE]
    xb = np.arange(3)
    ax2.bar(xb, vals, 0.55, yerr=errs, capsize=3, color=cols)
    for i, v in enumerate(vals):
        ax2.text(i, v * 1.25 + 0.05, f"{v:.2f}", ha="center", fontsize=7)
    ax2.axhline(1.5, color=RED, ls="--", lw=0.8)
    ax2.text(2.0, 3.4, "±1.5 ppm 目标", color=RED, fontsize=6.2, ha="center")
    ax2.set_yscale("log")
    ax2.set_xticks(xb)
    ax2.set_xticklabels(labels, fontsize=6.4)
    ax2.set_ylabel("INL (ppm FS)", fontsize=8)
    ax2.set_ylim(0.2, 60)
    ax2.grid(axis="y", alpha=0.25, lw=0.4)
    ax2.set_title("DAC1 INL：三种口径", fontsize=8, loc="left", pad=4)

    fig.text(0.015, 0.965, "技术有效性交叉验证：10 seeds × 2 频率，结论必须跨 0 检验",
             fontsize=10.5, fontweight=600, va="top")
    fig.text(0.015, 0.905, "左：Δ 的 95% CI（配对差值）；右：INL 的 in-sample / 有限样本 / out-of-sample",
             fontsize=7.2, color=GRAY, va="top")
    foot(fig, [FOOT_COMMON.format(data="model/crossval.py（K=10，种子 1000-1009）", n="N=8192/16384", seeds="1000-1009"),
               "说明: 左图空心=CI 跨 0（不显著）；右图 out-of-sample 1.9 ppm 略超 ±1.5 ppm 目标，属 CONDITIONAL。"])

    return save(fig, "f6_crossval")


def fig_dem_dither() -> Path | None:
    """DEM / dither 的独立贡献：INL 与 DNL 分开画。"""
    src = ROOT / "model" / "results" / "dem_dither.json"
    if not src.exists():
        print("skip f7: 先跑 python3 -m model.tech_effects")
        return None
    d = json.loads(src.read_text())
    s7, agg = d["seed7"], d["chips"]["agg"]
    Ds = [0, 1, 2, 4, 8]
    raw, dem = s7["raw"], s7["DEM"]
    K20 = 1.048576  # 1 ppm FS
    dith_inl = np.array([raw["inl_ppm"]] + [s7[f"dither_D{D}"]["inl_ppm"] for D in Ds[1:]]) * K20
    dith_dnl = np.array([raw["dnl_lsb1"]] + [s7[f"dither_D{D}"]["dnl_lsb1"] for D in Ds[1:]]) * 1024
    both_inl = np.array([dem["inl_ppm"]] + [s7[f"DEM+dither_D{D}"]["inl_ppm"] for D in Ds[1:]]) * K20
    both_dnl = np.array([dem["dnl_lsb1"]] + [s7[f"DEM+dither_D{D}"]["dnl_lsb1"] for D in Ds[1:]]) * 1024

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(W_MM / 25.4, 112 / 25.4))
    fig.subplots_adjust(left=0.10, right=0.975, top=0.80, bottom=0.34, wspace=0.30)

    for ax, ys, ys2, ylab, title in (
        (ax1, dith_inl, both_inl, "INL 峰值 (LSB20)", "INL：DEM 有效，dither 几乎无效"),
        (ax2, dith_dnl, both_dnl, "DNL 峰值 (LSB20)", "DNL：dither 有效，DEM 也有帮助"),
    ):
        ax.axhline(ys[0], color=GRAY, ls="--", lw=0.8)
        ax.plot(Ds, ys, "o-", color=ORANGE, ms=4, lw=1.0, label="仅 dither")
        ax.plot(Ds, ys2, "s-", color=BLUE, ms=4, lw=1.0, label="DEM + dither")
        ax.set_xscale("symlog", linthresh=1)
        ax.set_xticks(Ds)
        ax.set_xticklabels([str(x) for x in Ds])
        ax.set_xlabel("dither 幅度 D (LSB1)")
        ax.set_ylabel(ylab)
        ax.grid(alpha=0.25, lw=0.4)
        ax.set_title(title, fontsize=8, loc="left", pad=4)
    ax1.set_ylim(0, 25)
    ax2.set_ylim(0, 26)
    ax1.legend(fontsize=6.2, loc="center right", frameon=True, framealpha=0.95, edgecolor="#B4B2A9")
    ax2.legend(fontsize=6.2, loc="lower left", frameon=True, framealpha=0.95, edgecolor="#B4B2A9")

    head(fig, "DEM 管 INL，dither 管 DNL：两者互补，不是一回事",
         "共顶板 8 片模型，σu=0.2%；曲线=seed7；D 为码域整数 dither（数字扣除）")
    fig.text(0.015, 0.225, "来源: model/tech_effects.py（共顶板） · N=1024 码 · seeds 1-10 · 口径 SSOT 20.00 bit · L1 行为模型",
             fontsize=6.2, color=GRAY, va="bottom")
    fig.text(0.015, 0.192,
             f"10 芯片 D=2（LSB20）：DEM {agg['DEM']['mean'][0]*K20:.1f}/{agg['DEM']['mean'][1]*1024:.1f}，"
             f"dither {agg['dither_D2']['mean'][0]*K20:.1f}/{agg['dither_D2']['mean'][1]*1024:.1f}，"
             f"both {agg['DEM+dither_D2']['mean'][0]*K20:.1f}/{agg['DEM+dither_D2']['mean'][1]*1024:.1f}",
             fontsize=6.2, color=GRAY, va="bottom")
    fig.text(0.015, 0.159,
             f"倍数：DEM {agg['DEM']['inl_ratio']:.1f}×/{agg['DEM']['dnl_ratio']:.1f}×，"
             f"dither {agg['dither_D2']['inl_ratio']:.1f}×/{agg['dither_D2']['dnl_ratio']:.1f}×，"
             f"both {agg['DEM+dither_D2']['inl_ratio']:.1f}×/{agg['DEM+dither_D2']['dnl_ratio']:.1f}×",
             fontsize=6.2, color=GRAY, va="bottom")
    fig.text(0.015, 0.126, "等效：INL 1 LSB20=0.954 ppm FS；DNL 1 LSB20=1/1024 LSB1。raw 22.9/24.0，校准 0.56/0.75，OOS 2.0",
             fontsize=6.2, color=GRAY, va="bottom")
    fig.text(0.015, 0.094, "说明: dither=码域 dither（非采样注入）；DEM=片级 8 态；每样本噪声 0.03–0.12 ppm。",
             fontsize=6.2, color=GRAY, va="bottom")
    return save(fig, "f7_dem_dither")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    outs = [fig_spectrum(), fig_averaging(), fig_shuffle(), fig_inl_dnl(), fig_skew_gain()]
    f6 = fig_crossval()
    if f6:
        outs.append(f6)
    f7 = fig_dem_dither()
    if f7:
        outs.append(f7)
    files = []
    for p in outs:
        for ext in (".png", ".svg", ".pdf"):
            q = p.with_suffix(ext)
            if q.exists():
                files.append(q)
    man = {
        "schema": "sar20_10m_effect_figures_v2",
        "script": "model/figures_ssot.py",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "date": "2026-11-12",
        "ssot": "spec/SSOT.md",
        "crossval": "model/results/crossval/results.json",
        "seeds_figures": SEEDS,
        "seeds_crossval": list(range(1000, 1010)),
        "figures": [
            {"stem": "f0_architecture", "question": "结构与口径", "source": "netlist + SSOT", "evidence": "L0"},
            {"stem": "f1_spectrum", "question": "100 kHz 的 SNDR/DR/SFDR", "source": "model.adc.simulate", "evidence": "L1"},
            {"stem": "f2_averaging", "question": "8× 重复值多少 dB", "source": "model.adc.simulate, 10 seeds", "evidence": "L1"},
            {"stem": "f3_shuffle", "question": "片级随机选片换到什么", "source": "model.adc.simulate, 10 seeds", "evidence": "L1"},
            {"stem": "f4_inl_dnl", "question": "0.2% 失配的 INL/DNL 与校准残差", "source": "charge_model + finite-sample fit", "evidence": "L1"},
            {"stem": "f5_skew_gain", "question": "交织 skew/增益失配的代价", "source": "model.adc.simulate, 10 seeds", "evidence": "L1"},
            {"stem": "f6_crossval", "question": "哪些技术效果统计显著", "source": "model.crossval, K=10", "evidence": "L1"},
            {"stem": "f7_dem_dither", "question": "DEM 与 dither 各自贡献", "source": "model.tech_effects, K=10", "evidence": "L1"},
        ],
        "outputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "limits": [
            "所有曲线是行为模型输出，不是前仿/后仿/硅测",
            "绝对 SNDR/DR 未标定；只用于技术排序与量级",
            "片级 shuffle 不是 CDAC 单位级 DEM",
            "不能把点估计当结论；看 f6 的 95% CI",
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"figures: {len(outs)} stems, {len(files)} files -> {OUT}")


if __name__ == "__main__":
    main()
