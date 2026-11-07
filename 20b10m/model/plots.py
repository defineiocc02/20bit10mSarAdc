"""plots.py —— 模型图（沿用 20b10mtask 的 mm/字体/SVG+PNG/manifest 方案）

运行：cd 20b10m && python3 -m model.plots
输出：model/results/figures/fig*.png|svg|pdf + manifest.json
"""

from __future__ import annotations

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
RES = ROOT / "model/results"
# 注意：不能写进 results/figures——那会覆盖 figures.py 的 41 图 manifest（本轮踩过）
OUT = RES / "figures_plots"

BASE = "#626C75"   # 基线/关闭
CAAZ = "#0072B2"   # 开启/目标
WARN = "#D55E00"
GOOD = "#009E73"
NEUTRAL = "#333333"


def _load():
    return json.loads((RES / "results.json").read_text(encoding="utf-8"))


def fig_caaz(res):
    rows = res["caaz"]
    fin = np.array([r["fin"] / 1e3 for r in rows])
    b = np.array([r["base_DR_dB"] for r in rows])
    c = np.array([r["caaz_DR_dB"] for r in rows])
    fig, ax = plt.subplots(figsize=(viz.WIDTH_MM / viz.MM, 78 / viz.MM))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.78, bottom=0.20)
    ax.plot(fin, b, "o-", color=BASE, ms=3, label="无 CAAZ")
    ax.plot(fin, c, "s-", color=CAAZ, ms=3, label="CAAZ")
    for x, y0, y1 in zip(fin, b, c):
        ax.annotate(f"{y1-y0:+.2f} dB", (x, y1), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=6.4, color=CAAZ)
    ax.set(xscale="log", xlabel="输入频率（kHz）", ylabel="DR（dB）",
           xticks=[100, 1000, 2000], xticklabels=["0.1", "1", "2"])
    ax.grid(alpha=0.26)
    ax.legend(frameon=False, loc="lower left", fontsize=7)
    viz.annotate(fig, "CAAZ 的频率响应：10 MS/s 输出 / 20 MS/s raw",
                 "增益 = 两点平均（3 dB）+ AZ 共享抵消；2 MHz 开始受 sinc 衰落",
                 "数据：model/results/results.json；脚本：model/plots.py。绝对 DR 为模型值，未标定，不可签核。")
    return fig, (146, 78)


def fig_tracking(res):
    rows = res["tracking"]
    M = np.array([r["M"] for r in rows])
    dr = np.array([r["DR_dB"] for r in rows])
    fig, ax = plt.subplots(figsize=(viz.WIDTH_MM / viz.MM, 76 / viz.MM))
    fig.subplots_adjust(left=0.12, right=0.97, top=0.77, bottom=0.21)
    ax.plot(M, dr, "o-", color=CAAZ, ms=3)
    ax.annotate(f"M=1→8：{dr[-1]-dr[0]:+.2f} dB", (M[-1], dr[-1]),
                textcoords="offset points", xytext=(-6, 10), ha="right",
                fontsize=7, color=CAAZ)
    ax.set(xscale="log", xlabel="重复次数 M", ylabel="DR（dB）",
           xticks=M, xticklabels=[str(m) for m in M])
    ax.grid(alpha=0.26)
    viz.annotate(fig, "8× tracking 的有效平均：只有 +1.7 dB",
                 f"ρ={P.rho:.2f} 的 AR(1) 相关噪声；不是理论 4 dB",
                 "数据：results.json 的 tracking 表；ρ 未实测，属推断值。")
    return fig, (146, 76)


def fig_interleave(res):
    rows = res["interleave"]
    skew = [r for r in rows if "2MHz skew" in r["case"] and "shuffle" not in r["case"]]
    x = [r["skew_ps"] for r in skew]
    dr = [r["DR_dB"] for r in skew]
    sf = [r["SFDR_dBc"] for r in skew]

    sh = [r for r in rows if r["case"] in ("10MS/s shuffle=False", "10MS/s shuffle=True")]
    labels = ["不洗牌", "洗牌"]
    dr2 = [r["DR_dB"] for r in sh]
    sf2 = [r["SFDR_dBc"] for r in sh]

    fig, axes = plt.subplots(1, 2, figsize=(viz.WIDTH_MM / viz.MM, 86 / viz.MM))
    fig.subplots_adjust(left=0.095, right=0.975, top=0.76, bottom=0.20, wspace=0.34)
    ax = axes[0]
    ax.plot(x, dr, "o-", color=CAAZ, ms=3, label="DR")
    ax.plot(x, sf, "s--", color=WARN, ms=3, label="SFDR")
    ax.set(xlabel="片间 skew（ps）", ylabel="dB", xticks=x, xticklabels=[f"{v:g}" for v in x])
    ax.grid(alpha=0.26); ax.legend(frameon=False, fontsize=6.4, loc="center right")
    ax.set_title("2 MHz：skew 扫描", loc="left", fontsize=7.4)
    ax = axes[1]
    xx = np.arange(len(labels))
    ax.bar(xx - 0.18, dr2, 0.34, color=CAAZ, label="DR")
    ax.bar(xx + 0.18, sf2, 0.34, color=WARN, label="SFDR")
    ax.set(xticks=xx, xticklabels=labels, ylabel="dB", ylim=(80, 135))
    ax.grid(alpha=0.26, axis="y"); ax.legend(frameon=False, fontsize=6.4, loc="upper left", ncol=2)
    ax.set_title("100 kHz：洗牌把杂散换成噪声", loc="left", fontsize=7.4)
    viz.annotate(fig, "部分交织：skew 与失配的代价",
                 "18 片池、8 转换 + 8 采样 + 2 备；2 MHz 下 skew 2 ps 掉约 4 dB",
                 "数据：results.json 的 interleave 表；一阶 skew 模型，未含采样网络带宽。")
    return fig, (146, 86)


def fig_static():
    c = static.curves(10, 0.002, 7)
    code = c["code"]
    fig, axes = plt.subplots(2, 1, figsize=(viz.WIDTH_MM / viz.MM, 110 / viz.MM), sharex=True)
    fig.subplots_adjust(left=0.12, right=0.97, top=0.82, bottom=0.16, hspace=0.30)
    axes[0].step(code, c["inl_raw"], where="post", color=BASE, lw=0.8, label="校准前")
    axes[0].step(code, c["inl_cal"], where="post", color=CAAZ, lw=0.9, label="位权校准后")
    axes[1].step(code[1:], c["dnl_raw"], where="post", color=BASE, lw=0.8)
    axes[1].step(code[1:], c["dnl_cal"], where="post", color=CAAZ, lw=0.9)
    axes[0].set_ylabel("INL（LSB1）"); axes[1].set_ylabel("DNL（LSB1）")
    axes[1].set_xlabel("DAC1 码（10 bit）")
    for ax in axes:
        ax.grid(alpha=0.26)
    axes[0].legend(frameon=False, fontsize=6.8, loc="upper right")
    viz.annotate(fig, "DAC1 静态线性度：校准前后",
                 "σu=0.2%，位权失配 + 1.5 ppm 非位权残差；校准只扣位权项",
                 "数据：model/static.py curves(10,0.002,7)；LSB1=9.766 mV。20.5 bit 逐码 INL 不可直接测。")
    return fig, (146, 110)


def fig_spectrum():
    n = P.n
    fs = P.fs
    fin = round(100e3 * n / fs) * fs / n
    fig, ax = plt.subplots(figsize=(viz.WIDTH_MM / viz.MM, 82 / viz.MM))
    fig.subplots_adjust(left=0.11, right=0.97, top=0.78, bottom=0.20)
    floor = {}
    for caaz, color, label in ((False, BASE, "无 CAAZ"), (True, CAAZ, "CAAZ")):
        x, _ = simulate(fin, fs=fs, caaz=caaz, seed=11)
        spec = np.abs(np.fft.rfft(x - x.mean())) / (n / 2)
        p = spec**2
        k = 101
        smooth = np.convolve(p, np.ones(k)/k, mode="same")
        dbfs = 10 * np.log10(np.maximum(smooth / (P.fs_diff/2)**2, 1e-24))
        f = np.fft.rfftfreq(n, 1 / fs) / 1e6
        ax.plot(f[1:], dbfs[1:], lw=0.8, color=color, label=label)
        band = (f > 1) & (f < 4)
        floor[label] = np.median(dbfs[band])
    d = floor["CAAZ"] - floor["无 CAAZ"]
    ax.text(0.98, 0.58, f"1–4 MHz 噪声底差 {d:+.2f} dB", transform=ax.transAxes,
            ha="right", va="center", fontsize=7.2, color=CAAZ,
            bbox=dict(facecolor="white", edgecolor="none", alpha=0.85, pad=1.5))
    ax.set(xlim=(0, 5), ylim=(-160, 5), xlabel="频率（MHz）", ylabel="幅度（dBFS）")
    ax.grid(alpha=0.24)
    ax.legend(frameon=False, fontsize=7, loc="upper right")
    viz.annotate(fig, "输出频谱：CAAZ 开关对比",
                 f"{fin/1e3:.1f} kHz、10 MS/s、{n} 点相干采样",
                 "数据：model/adc.py simulate；矩形窗，101 bin 平滑。绝对噪底为模型值，未标定。")
    return fig, (146, 82)


def main():
    res = _load()
    OUT.mkdir(parents=True, exist_ok=True)
    font = viz.chinese_style()
    figs = [("fig1_caaz", fig_caaz(res)), ("fig2_tracking", fig_tracking(res)),
            ("fig3_interleave", fig_interleave(res)), ("fig4_static", fig_static()),
            ("fig5_spectrum", fig_spectrum())]
    outputs, dims = [], []
    for name, (fig, (w, h)) in figs:
        paths = viz.save(fig, OUT / name)
        outputs += paths
        dims.append((w, h))
        plt.close(fig)
    viz.write_manifest(
        OUT, script=Path(__file__), data=[RES / "results.json"],
        outputs=outputs, dims=dims, font=font,
        extra={"notes": "CAAZ/tracking/interleave/static/spectrum；绝对指标未标定，不可签核"},
    )
    print("wrote", len(outputs), "figure files to", OUT)


if __name__ == "__main__":
    main()
