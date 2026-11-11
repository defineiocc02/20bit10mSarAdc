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
def fig_inl() -> Path:
    c = static.curves(bits=10, unit_sigma=0.002, seed=7)
    code, raw, cal = c["code"], c["inl_raw"], c["inl_cal"]
    step = max(1, len(code) // 256)
    sl = slice(None, None, step)

    fig, ax = canvas(94)
    ax.plot(code[sl], raw[sl], ".", ms=1.4, color=ORANGE, label="未校准（seed=7 示例）  [模型]")
    ax.plot(code[sl], cal[sl], ".", ms=1.4, color=BLUE, label="校准后（有限样本）  [模型]")
    ax.axhline(0, color=GRAY, lw=0.5)
    ax.set_xlabel("DAC1 码 (0..1023)")
    ax.set_ylabel("INL (LSB1)")
    ax.grid(alpha=0.25, lw=0.4)
    ax.legend(fontsize=6.4, loc="upper right", frameon=True, framealpha=0.95, edgecolor="#B4B2A9")

    pk_raw = float(np.max(np.abs(raw)))
    pk_cal = float(np.max(np.abs(cal)))
    ax.annotate(f"本芯片: {pk_raw:.3f} → {pk_cal:.3f} LSB1\n10 芯片: 17.8 → 0.64 ppm  [模型]",
                xy=(0.03, 0.10), xycoords="axes fraction", fontsize=7.2, va="bottom",
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#B4B2A9", lw=0.5))

    head(fig, f"DAC1 静态 INL：0.2% 失配下，校准把 {pk_raw/1024*1e6:.1f} ppm 压到 {pk_cal/1024*1e6:.2f} ppm",
         "曲线为 seed=7 示例；10 芯片 17.8±4.4 → 0.64±0.04 ppm；out-of-sample 1.9 ppm（见 f6）")
    foot(fig, [FOOT_COMMON.format(data="model.static → charge_model.dac1_curves，1024 码", n=1024, seeds="seed=7 + 10 chips"),
               "说明: 16.4 ppm 与 0.3 ppm 是同一模型的开/关校准对比；不是论文实测，也不是硅测。"])
    return save(fig, "f4_inl")


# ---------------------------------------------------------------- 5. skew / gain（10 seeds）
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


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    outs = [fig_spectrum(), fig_averaging(), fig_shuffle(), fig_inl(), fig_skew_gain()]
    f6 = fig_crossval()
    if f6:
        outs.append(f6)
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
            {"stem": "f4_inl", "question": "0.2% 失配的 INL 与校准残差", "source": "model.static, seed 7 + 10 chips", "evidence": "L1"},
            {"stem": "f5_skew_gain", "question": "交织 skew/增益失配的代价", "source": "model.adc.simulate, 10 seeds", "evidence": "L1"},
            {"stem": "f6_crossval", "question": "哪些技术效果统计显著", "source": "model.crossval, K=10", "evidence": "L1"},
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
