"""figures_ssot.py —— 效果图（每张图带来源脚注）

规则（与 spec/SSOT.md §8 一致）：
- 每张图只回答一个问题；
- 图上每个"效果数字"必须带来源标签：[模型] / [论文] / [估算]；
- 脚注写清：脚本、数据函数、N、seed、口径、证据等级、日期；
- 不把模型值写成"实测"，不把片级 shuffle 写成 DEM。

运行：cd 20b10m && python3 -m model.figures_ssot
输出：docs/figures/*.png / *.svg / *.pdf + manifest.json
"""

from __future__ import annotations

import hashlib
import json
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
W_MM = 146.0
BLUE, ORANGE, GREEN, GRAY, RED = "#0072B2", "#D55E00", "#009E73", "#5F5E5A", "#A32D2D"

FOOT_COMMON = ("来源: model/figures_ssot.py · 数据: {data} · N={n} · seed={seed}\n"
               "口径: SSOT 20.00 bit (10+12−2) · G=32 · 等级: L1 行为模型（非前仿/非硅测） · 2026-11-11")


def canvas(h_mm: float = 94.0):
    viz.chinese_style()
    fig, ax = plt.subplots(figsize=(W_MM / 25.4, h_mm / 25.4))
    fig.subplots_adjust(left=0.105, right=0.975, top=0.80, bottom=0.38)
    return fig, ax


def head(fig, title: str, subtitle: str) -> None:
    fig.text(0.015, 0.965, title, fontsize=10.5, fontweight=600, va="top")
    fig.text(0.015, 0.905, subtitle, fontsize=7.4, color=GRAY, va="top")


def foot(fig, notes) -> None:
    import textwrap
    if isinstance(notes, str):
        notes = [notes]
    lines = []
    for n in notes:
        for seg in str(n).split("\n"):
            lines += textwrap.wrap(seg, width=58)
    y = getattr(fig, "_foot_y", 0.200)
    for ln in lines[:5]:
        fig.text(0.015, y, ln, fontsize=6.2, color=GRAY, va="bottom")
        y -= 0.028
    fig._foot_y = y


def save(fig, stem: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / stem
    viz.save(fig, p)
    plt.close(fig)
    return p


def metric(fin, fs, *, seeds=2, **kw):
    n = P.n
    fc = round(fin * n / fs) * fs / n
    rows = [fft_metrics(simulate(fc, fs=fs, seed=900 + s, **kw)[0], fs, fc) for s in range(seeds)]
    return {k: float(np.mean([r[k] for r in rows]))
            for k in ("DR_dB", "SNDR_dB", "SFDR_dBc")}


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
    foot(fig, FOOT_COMMON.format(data="model.adc.simulate + model.metrics.fft_metrics", n=n, seed=11))
    foot(fig, "说明: 曲线来自模型；绝对 SNDR/DR 未标定，不能写进数据手册或论文实测栏。")
    return save(fig, "f1_spectrum")


# ---------------------------------------------------------------- 2. 8× 平均
def fig_averaging() -> Path:
    ms = [1, 2, 4, 8]
    sndr = [metric(100e3, 10e6, M=m, seeds=2)["SNDR_dB"] for m in ms]
    ref = sndr[0] + 10 * np.log10(ms)

    fig, ax = canvas(92)
    ax.plot(ms, sndr, "o-", color=BLUE, ms=4, lw=1.1, label="模型 SNDR  [模型]")
    ax.plot(ms, ref, "--", color=GRAY, lw=0.8, label=r"理想 $\sqrt{M}$（+3 dB/倍频）")
    ax.set_xscale("log", base=2)
    ax.set_xticks(ms)
    ax.set_xticklabels([str(m) for m in ms])
    ax.set_xlabel("重复次数 M")
    ax.set_ylabel("SNDR (dB)")
    ax.grid(alpha=0.25, lw=0.4)
    ax.legend(fontsize=6.6, loc="lower right", frameon=True, framealpha=0.95, edgecolor="#B4B2A9")

    gain = sndr[-1] - sndr[0]
    ax.annotate(f"M=1→8: +{gain:.2f} dB  [模型]\n论文 p.47: +2 dB  [论文]",
                xy=(0.03, 0.97), xycoords="axes fraction", fontsize=7.4, va="top",
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#B4B2A9", lw=0.5))

    head(fig, "8× LSB 重复：模型只值 +1.7 dB，不是 4.5 dB",
         "ρ=0.61 为反解值（stress），不是实测；M=8 的收益按噪声口径记，不进码宽")
    foot(fig, FOOT_COMMON.format(data="model.adc.simulate, M 扫描, 2 seeds/点", n=P.n, seed="900-901"))
    foot(fig, "说明: ρ 的来源是 M_eff 反解（model/params.py 注释），不是硅上相关实测；不要把 +1.7 dB 写成论文复现值。")
    return save(fig, "f2_averaging")


# ---------------------------------------------------------------- 3. 片级 shuffle
def fig_shuffle() -> Path:
    base = dict(enabled=True, gain=5e-5, offset=50e-6, skew=1e-12)
    off = metric(100e3, 10e6, interleave={**base, "shuffle": False}, seeds=2)
    on = metric(100e3, 10e6, interleave={**base, "shuffle": True}, seeds=2)

    fig, ax = canvas(92)
    x = np.arange(2)
    w = 0.34
    dr = [off["DR_dB"], on["DR_dB"]]
    sf = [off["SFDR_dBc"], on["SFDR_dBc"]]
    b1 = ax.bar(x - w/2, dr, w, color=BLUE, label="DR (dB)")
    b2 = ax.bar(x + w/2, sf, w, color=ORANGE, label="SFDR (dBc)")
    for bars in (b1, b2):
        for b in bars:
            ax.text(b.get_x() + b.get_width()/2, b.get_height() + 0.6,
                    f"{b.get_height():.1f}", ha="center", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(["固定轮换", "随机选片"])
    ax.set_ylim(88, 132)
    ax.set_ylabel("dB / dBc")
    ax.grid(axis="y", alpha=0.25, lw=0.4)
    ax.legend(fontsize=6.8, loc="upper left", frameon=False)

    fig.text(0.015, 0.845, "注意：这是片级 8/18 随机选片，不是 CDAC 单位级 DEM；不能引用为 DEM 收益",
             fontsize=6.8, color=RED)

    head(fig, f"片级随机选片：{dr[1]-dr[0]:+.1f} dB DR 换 {sf[1]-sf[0]:+.1f} dBc SFDR",
         "18 片池每样本随机抽 8 片；片间 gain/offset/skew 被打散成噪声")
    foot(fig, FOOT_COMMON.format(data="model.adc.simulate, interleave={gain 50 ppm, offset 50 uV, skew 1 ps}", n=P.n, seed="900-901"))
    foot(fig, "说明: 效果来源是片级误差平均，不是单位电容 DEM；DEM 在本仓库未实现（见 SSOT OPEN-5）。")
    return save(fig, "f3_shuffle")


# ---------------------------------------------------------------- 4. INL / DNL
def fig_inl() -> Path:
    c = static.curves(bits=10, unit_sigma=0.002, seed=7)
    code = c["code"]
    raw = c["inl_raw"]
    cal = c["inl_cal"]
    step = max(1, len(code) // 256)
    sl = slice(None, None, step)

    fig, ax = canvas(94)
    ax.plot(code[sl], raw[sl], ".", ms=1.4, color=ORANGE, label="未校准  [模型]")
    ax.plot(code[sl], cal[sl], ".", ms=1.4, color=BLUE, label="校准后  [模型]")
    ax.axhline(0, color=GRAY, lw=0.5)
    ax.set_xlabel("DAC1 码 (0..1023)")
    ax.set_ylabel("INL (LSB1)")
    ax.grid(alpha=0.25, lw=0.4)
    ax.legend(fontsize=6.8, loc="upper right", frameon=False)

    pk_raw = float(np.max(np.abs(raw)))
    pk_cal = float(np.max(np.abs(cal)))
    ax.annotate(f"峰值 INL: {pk_raw:.3f} → {pk_cal:.3f} LSB1\n"
                f"折 FS: {pk_raw/1024*1e6:.1f} → {pk_cal/1024*1e6:.2f} ppm  [模型]",
                xy=(0.04, 0.10), xycoords="axes fraction", fontsize=7.4, va="bottom",
                bbox=dict(boxstyle="round,pad=0.35", fc="white", ec="#B4B2A9", lw=0.5))

    head(fig, f"DAC1 静态 INL：0.2% 单位失配下，校准把 {pk_raw/1024*1e6:.1f} ppm 压到 {pk_cal/1024*1e6:.2f} ppm",
         "8 片 × 128 单位，3 unary + 7 binary；差分互补开关；σu=0.2% 是 stress 档，非 PDK")
    foot(fig, FOOT_COMMON.format(data="model.static.curves → charge_model.dac1_curves, 1024 码", n=1024, seed=7))
    foot(fig, "说明: 16.4 ppm 与 0.3 ppm 是同一模型的开/关校准对比；不是论文实测，也不是硅测。")
    return save(fig, "f4_inl")


# ---------------------------------------------------------------- 5. skew / gain
def fig_skew_gain() -> Path:
    skews = [0.5, 1.0, 2.0, 4.0]
    s_skew = [metric(2e6, 10e6, interleave=dict(enabled=True, shuffle=True, gain=2e-5, offset=20e-6, skew=s*1e-12), seeds=2)["SNDR_dB"] for s in skews]
    gains = [10, 50, 100]
    s_gain = [metric(100e3, 10e6, interleave=dict(enabled=True, shuffle=True, gain=g*1e-6, offset=0, skew=0), seeds=2)["SNDR_dB"] for g in gains]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(W_MM / 25.4, 90 / 25.4))
    fig.subplots_adjust(left=0.09, right=0.98, top=0.80, bottom=0.38, wspace=0.35)

    ax1.plot(skews, s_skew, "o-", color=BLUE, ms=4, lw=1.0)
    ax1.set_xscale("log", base=2)
    ax1.set_xticks(skews)
    ax1.set_xticklabels([str(s) for s in skews])
    ax1.set_xlabel("片间采样偏斜 (ps)")
    ax1.set_ylabel("SNDR (dB)")
    ax1.grid(alpha=0.25, lw=0.4)
    ax1.annotate(f"2 ps: {s_skew[2]:.1f} dB  [模型]\n0.5→2 ps: {s_skew[2]-s_skew[0]:+.1f} dB",
                 xy=(0.06, 0.10), xycoords="axes fraction", fontsize=6.8, va="bottom")

    ax2.plot(gains, s_gain, "s-", color=ORANGE, ms=4, lw=1.0)
    ax2.set_xscale("log")
    ax2.set_xticks(gains)
    ax2.set_xticklabels([str(g) for g in gains])
    ax2.set_xlabel("片间增益失配 (ppm)")
    ax2.set_ylabel("SNDR (dB)")
    ax2.grid(alpha=0.25, lw=0.4)
    ax2.annotate(f"50 ppm: {s_gain[1]:.1f} dB  [模型]\n10→50 ppm: {s_gain[1]-s_gain[0]:+.1f} dB",
                 xy=(0.06, 0.10), xycoords="axes fraction", fontsize=6.8, va="bottom")

    head(fig, f"交织误差：2 ps 偏斜掉 {s_skew[0]-s_skew[2]:.1f} dB，50 ppm 增益失配掉 {s_gain[0]-s_gain[1]:.1f} dB",
         "2 MHz 输入（偏斜最敏感）；10 kHz 输入（增益失配）；18 片随机选 8，2 seeds/点")
    foot(fig, FOOT_COMMON.format(data="model.adc.simulate + slice_errors", n=P.n, seed="900-901"))
    foot(fig, "说明: skew/增益的绝对幅度是 stress 假设；曲线只给趋势与量级，不是封装/版图实测。")
    return save(fig, "f5_skew_gain")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    outs = [fig_spectrum(), fig_averaging(), fig_shuffle(), fig_inl(), fig_skew_gain()]
    files = []
    for p in outs:
        for ext in (".png", ".svg", ".pdf"):
            q = p.with_suffix(ext)
            if q.exists():
                files.append(q)
    man = {
        "schema": "sar20_10m_effect_figures_v1",
        "script": "model/figures_ssot.py",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "date": "2026-11-11",
        "ssot": "spec/SSOT.md",
        "figures": [
            {"stem": "f1_spectrum", "question": "100 kHz 输入的 SNDR/DR/SFDR 是多少",
             "source": "model.adc.simulate + fft_metrics", "evidence": "L1 model"},
            {"stem": "f2_averaging", "question": "8× LSB 重复值多少 dB",
             "source": "model.adc.simulate, M sweep", "evidence": "L1 model + paper p.47"},
            {"stem": "f3_shuffle", "question": "片级随机选片换到什么",
             "source": "model.adc.simulate, interleave", "evidence": "L1 model"},
            {"stem": "f4_inl", "question": "0.2% 失配下 INL 与校准残差",
             "source": "model.static → charge_model", "evidence": "L1 model"},
            {"stem": "f5_skew_gain", "question": "交织 skew/增益失配的代价",
             "source": "model.adc.simulate + slice_errors", "evidence": "L1 model, stress 假设"},
        ],
        "outputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "limits": [
            "所有曲线是行为模型输出，不是前仿/后仿/硅测",
            "绝对 SNDR/DR 未标定；只用于技术排序与量级",
            "片级 shuffle 不是 CDAC 单位级 DEM",
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"figures: {len(outs)} stems, {len(files)} files -> {OUT}")


if __name__ == "__main__":
    main()
