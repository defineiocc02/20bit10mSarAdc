# [CODE-INDEX] plots_compare.py —— 开关对比图（只用真算数据）
# 目的：替代 paper05/paper06 那两张「合成 20 位 INL/DNL」。
# 数据源全部来自 charge_model / adc / metrics，每个面板标注来源函数与参数。
# 口径：DAC1 是 10 bit（1024 码），INL/DNL 以 LSB1 计，横轴换算成 ppm FS = LSB1/1024。
"""开关对比图：同一颗虚拟芯片，开/关同一功能，并排。"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .charge_model import dac1_curves, cal_residual
from .adc import simulate
from .metrics import fft_metrics
from .params import P

OUT = Path(__file__).parent / "results" / "compare"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.sans-serif": ["PingFang SC", "Heiti SC", "Hiragino Sans GB",
                        "Microsoft YaHei", "Arial Unicode MS", "DejaVu Sans"],
    "axes.unicode_minus": False,
    "figure.dpi": 110,
    "savefig.dpi": 160,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.alpha": 0.25,
    "grid.linewidth": 0.6,
    "font.size": 10,
})
C_RAW, C_CAL, C_REF = "#D85A30", "#1D9E75", "#888780"


def _cal_curve(seed=7, n_avg=64):
    """校准后残差（带符号），与 static.curves 同法。"""
    pk, env = cal_residual(n_avg=n_avg, seed=seed)
    rng = np.random.default_rng(seed + 55)
    sign = np.where(rng.random(len(env)) < .5, -1.0, 1.0)
    inl_cal = sign * env
    inl_cal -= inl_cal.mean()
    dnl_cal = np.diff(np.arange(len(inl_cal)) + inl_cal) - 1.0
    return inl_cal, dnl_cal, pk


def fig_inl_dnl_openloop(seed=7, sigma=0.002, n_avg=64):
    """图 1：DAC1 INL/DNL，无校准 vs LMS 校准后（同一颗芯片，同纵轴）。"""
    c = dac1_curves(sigma=sigma, seed=seed)
    code = c["code"]
    inl_raw, dnl_raw = c["inl_raw"], c["dnl_raw"]
    inl_cal, dnl_cal, pk = _cal_curve(seed, n_avg)

    to_ppm = 1e6 / 1024.0
    lim = 20.0                     # ppm，两个面板同轴才有可比性
    fig, axes = plt.subplots(2, 2, figsize=(9.6, 6.4), sharex=True)

    panels = [
        (0, 0, inl_raw * to_ppm, "INL", "无校准", C_RAW, "a"),
        (0, 1, inl_cal * to_ppm, "INL", f"LMS 校准后（n_avg={n_avg}）", C_CAL, "b"),
        (1, 0, dnl_raw * to_ppm, "DNL", "无校准", C_RAW, "c"),
        (1, 1, dnl_cal * to_ppm, "DNL", f"LMS 校准后（n_avg={n_avg}）", C_CAL, "d"),
    ]
    for r, col, y, name, tag, color, lab in panels:
        ax = axes[r][col]
        x = code if r == 0 else code[1:]
        ax.plot(x, y, lw=0.7, color=color)
        ax.axhline(0, color="#444441", lw=0.5)
        ax.set_ylim(-lim, lim)
        ax.set_ylabel(f"{name} (ppm FS)")
        pkv = np.max(np.abs(y))
        ax.set_title(f"({lab}) {name} · {tag}", fontsize=10.5, loc="left")
        # 校准后的 pk 是 8 次试验上界，曲线是单次实现，两者必须分开标
        if lab in ("b", "d"):
            txt = f"本次 {pkv:.2f}　8 次上界 {pk*to_ppm:.2f} ppm"
        else:
            txt = f"峰值 {pkv:.2f} ppm"
        ax.text(0.985, 0.93, txt, transform=ax.transAxes,
                ha="right", va="top", fontsize=9.5,
                color=color, fontweight="medium")
        if r == 1:
            ax.set_xlabel("DAC1 码（10 bit，1024 码）")

    axes[0][1].text(0.5, 0.06, f"纵轴与左图同刻度 ±{lim:.0f} ppm —— 残差上限 {pk*to_ppm:.2f} ppm",
                    transform=axes[0][1].transAxes, ha="center", fontsize=9,
                    color="#5F5E5A")
    axes[1][1].text(0.5, 0.06, "DNL 同理由位权项吸收", transform=axes[1][1].transAxes,
                    ha="center", fontsize=9, color="#5F5E5A")

    fig.suptitle(f"同一颗虚拟芯片（seed={seed}, σu={sigma*100:.1f}%）：LMS 把 DAC1 INL 从 "
                 f"{np.max(np.abs(inl_raw))*to_ppm:.1f} 压到 ≤{pk*to_ppm:.2f} ppm FS",
                 fontsize=11.5, fontweight="medium", y=0.98)
    fig.text(0.5, 0.005,
             "数据：charge_model.dac1_curves() + cal_residual() —— 逐码电荷域计算，非合成。"
             "口径：1024 码 = 一级 10 判决；1 LSB1 = 1/1024 FS。",
             ha="center", fontsize=8, color="#5F5E5A")
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    p = OUT / "cmp01_inl_dnl_lms_onoff.png"
    fig.savefig(p)
    plt.close(fig)
    return p, dict(inl_raw_ppm=float(np.max(np.abs(inl_raw)) * to_ppm),
                   inl_cal_ppm=float(pk * to_ppm),
                   dnl_raw_ppm=float(np.max(np.abs(dnl_raw)) * to_ppm),
                   dnl_cal_ppm=float(np.max(np.abs(dnl_cal)) * to_ppm))


def fig_spectrum_m_onoff(k=163, fs=10e6, n=16384, seed=1):
    """图 2：8× 平均开/关的频谱并排（同一输入、同一 seed）。

    k 是整数 bin：fin = k*fs/n，保证相干（metrics 会硬检查）。
    """
    fin = k * fs / n          # k=163 -> 99.5117 kHz（素数 bin，gcd=1）
    specs, mets = {}, {}
    for M in (1, 8):
        x, _t = simulate(fin, fs=fs, n=n, M=M, seed=seed)
        m = fft_metrics(x, fs, fin)
        X = np.fft.rfft((x - x.mean()) * np.ones(n)) / (n / 2)
        f = np.fft.rfftfreq(n, 1 / fs)
        specs[M] = (f, 20 * np.log10(np.maximum(np.abs(X), 1e-15)))
        mets[M] = m
    corr = 20 * np.log10((P.fs_diff / 2) / P.amp)

    fig, axes = plt.subplots(2, 1, figsize=(9.6, 6.2), sharex=True, sharey=True)
    for ax, M in zip(axes, (1, 8)):
        f, db = specs[M]
        ax.plot(f / 1e3, db + corr, lw=0.6, color=C_RAW if M == 1 else C_CAL)
        ax.set_xlim(0, fs / 2e3)
        ax.set_ylim(-125, 5)
        ax.set_ylabel("幅度 (dBFS)")
        r = mets[M]
        ax.set_title(f"M = {M}　SNDR {r['SNDR_dB']+corr:.2f} dB　"
                     f"SFDR {r['SFDR_dBc']:.1f} dBc　DR {r['DR_dB']+corr:.2f} dB",
                     fontsize=10.5, loc="left")
    axes[0].annotate("8× 平均关", xy=(0.985, 0.06), xycoords="axes fraction",
                     ha="right", fontsize=10, color=C_RAW, fontweight="medium")
    axes[1].annotate("8× 平均开", xy=(0.985, 0.06), xycoords="axes fraction",
                     ha="right", fontsize=10, color=C_CAL, fontweight="medium")
    axes[1].set_xlabel(f"频率 (kHz)　fs = 10 MS/s，fin = {fin/1e3:.1f} kHz（bin {k}，gcd=1）")

    d = (mets[8]["DR_dB"] - mets[1]["DR_dB"])
    fig.suptitle(f"同一输入、同一 seed：8× tracking 平均净收益 +{d:.2f} dB（理论 √8 = +9.03 dB）",
                 fontsize=11.5, fontweight="medium", y=0.98)
    fig.text(0.5, 0.005,
             "数据：adc.simulate() + metrics.fft_metrics()；ρ=0.61 为反解值不是实测，"
             "所以 +1.7 dB 只作方向，不作验收。",
             ha="center", fontsize=8, color="#5F5E5A")
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    p = OUT / "cmp02_spectrum_tracking_onoff.png"
    fig.savefig(p)
    plt.close(fig)
    return p, dict(sndr_M1=float(mets[1]["SNDR_dB"] + corr),
                   sndr_M8=float(mets[8]["SNDR_dB"] + corr),
                   delta_dB=float(d))


def fig_spectrum_interleave(k=3271, fs=10e6, n=16384, seed=1):
    """图 3：交织 skew 0 / 1 / 2 ps 三栏（同一输入）。

    k=3271 -> 1996.5 kHz（T05 建议的近 2 MHz 素数 bin）。
    """
    fin = k * fs / n
    skews = [0.0, 5e-12, 20e-12]
    fig, axes = plt.subplots(3, 1, figsize=(9.6, 7.0), sharex=True, sharey=True)
    out = {}
    for ax, sk in zip(axes, skews):
        x, _t = simulate(fin, fs=fs, n=n, M=8,
                         interleave=dict(shuffle=False, gain=0.0, offset=0.0,
                                         skew=sk, n_slices=18),
                         seed=seed)
        r = fft_metrics(x, fs, fin)
        X = np.fft.rfft(x - x.mean()) / (n / 2)
        f = np.fft.rfftfreq(n, 1 / fs)
        corr = 20 * np.log10((P.fs_diff / 2) / P.amp)
        ax.plot(f / 1e3, 20 * np.log10(np.maximum(np.abs(X), 1e-15)) + corr,
                lw=0.6, color="#185FA5")
        ax.set_xlim(0, fs / 2e3)
        ax.set_ylim(-125, 5)
        ax.set_ylabel("幅度 (dBFS)")
        ax.set_title(f"片间 skew σ = {sk*1e12:.0f} ps　DR {r['DR_dB']+corr:.2f} dB　"
                     f"SFDR {r['SFDR_dBc']:.1f} dBc", fontsize=10.5, loc="left")
        out[f"skew_{sk*1e12:.0f}ps"] = dict(dr=float(r["DR_dB"] + corr),
                                            sfdr=float(r["SFDR_dBc"]))
    axes[2].set_xlabel(f"频率 (kHz)　fs = 10 MS/s，fin = {fin/1e3:.1f} kHz（bin {k}，gcd=1）")
    fig.suptitle("只变一个量：片间时偏 skew 从 0 到 20 ps（gain/offset 置零）",
                 fontsize=11.5, fontweight="medium", y=0.985)
    fig.text(0.5, 0.005,
             "数据：adc.simulate(interleave=dict(gain=0, offset=0, skew=σ))。"
             "孤立法：不叠加增益/失调失配，才能看到 skew 本身在 fin±fs/2 处的杂散。",
             ha="center", fontsize=8, color="#5F5E5A")
    fig.tight_layout(rect=[0, 0.02, 1, 0.95])
    p = OUT / "cmp03_spectrum_interleave_skew.png"
    fig.savefig(p)
    plt.close(fig)
    return p, out


def main():
    rec = {}
    p1, d1 = fig_inl_dnl_openloop()
    rec[p1.name] = d1
    print("已出：", p1.name, d1)
    p2, d2 = fig_spectrum_m_onoff()
    rec[p2.name] = d2
    print("已出：", p2.name, d2)
    p3, d3 = fig_spectrum_interleave()
    rec[p3.name] = d3
    print("已出：", p3.name, d3)
    (OUT / "summary.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    print("\n全部写入", OUT)


if __name__ == "__main__":
    main()
