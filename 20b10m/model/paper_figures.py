"""paper_figures.py —— 论文测试部分的“实测风格”图（全部由模型生成）

运行：cd 20b10m && python3 -m model.paper_figures
输出：model/results/figures_paper/paper*.png|svg|pdf + manifest.json
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .params import P, LSB_TOTAL
from .adc import simulate
from .metrics import fft_metrics
from . import static, viz

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "model/results"
OUT = RES / "figures_paper"
BASE, CAAZ, WARN, GOOD = "#222222", "#0072B2", "#D55E00", "#009E73"
W, MM = 146, viz.MM


def canvas(h=82, w=W):
    fig, ax = plt.subplots(figsize=(w / MM, h / MM))
    fig.subplots_adjust(left=.12, right=.97, top=.78, bottom=.20)
    return fig, ax


def _metric(fin, fs, amp=None, caaz=False, seeds=2, **kw):
    n = P.n; fc = round(fin * n / fs) * fs / n
    old = P.amp
    if amp is not None: P.amp = amp
    rows = []
    try:
        for s in range(seeds):
            x, _ = simulate(fc, fs=fs, caaz=caaz, seed=700 + s, **kw)
            rows.append(fft_metrics(x, fs, fc))
    finally:
        P.amp = old
    return {k: float(np.mean([r[k] for r in rows])) for k in ("DR_dB", "SNDR_dB", "SFDR_dBc")}


def _spectrum(fin, fs, caaz=False, interleave=None, seed=11):
    n = P.n; fc = round(fin * n / fs) * fs / n
    x, _ = simulate(fc, fs=fs, caaz=caaz, interleave=interleave, seed=seed)
    spec = np.abs(np.fft.rfft(x - x.mean())) / (n / 2)
    db = 20 * np.log10(np.maximum(spec / (P.fs_diff / 2), 1e-12))
    return np.fft.rfftfreq(n, 1 / fs) / 1e6, db


def p01(D):
    fin = 100e3; f, db = _spectrum(fin, 10e6); m = _metric(fin, 10e6)
    fig, ax = canvas(84); ax.plot(f[1:], db[1:], lw=.55, color=BASE)
    ax.set(xlim=(0,5), ylim=(-160,5), xlabel="频率（MHz）", ylabel="幅度（dBFS）"); ax.grid(alpha=.18)
    ax.text(.97,.93,f"SNDR {m['SNDR_dB']:.1f} dB\nSFDR {m['SFDR_dBc']:.1f} dBc\nDR {m['DR_dB']:.1f} dB",transform=ax.transAxes,ha="right",va="top",fontsize=7)
    viz.annotate(fig,"输出频谱（100 kHz 输入）","10 MS/s、16384 点相干采样、矩形窗","模型生成；绝对指标未标定，不可签核。")
    return fig,(W,84)


def p02(D):
    fin = 2e6; f, db = _spectrum(fin, 10e6); m = _metric(fin, 10e6)
    fig, ax = canvas(84); ax.plot(f[1:], db[1:], lw=.55, color=BASE)
    ax.set(xlim=(0,5), ylim=(-160,5), xlabel="频率（MHz）", ylabel="幅度（dBFS）"); ax.grid(alpha=.18)
    ax.text(.97,.93,f"SNDR {m['SNDR_dB']:.1f} dB\nSFDR {m['SFDR_dBc']:.1f} dBc",transform=ax.transAxes,ha="right",va="top",fontsize=7)
    viz.annotate(fig,"输出频谱（2 MHz 输入）","抖动受限档：σt=1 ps 时 95.7 dB；模型未注入抖动，故偏高","模型生成；2 MHz 绝对 SNDR 不可作验收。")
    return fig,(W,84)


def p03(D):
    amps = np.arange(-60, 1, 5); snr=[]; sndr=[]
    for a in amps:
        m = _metric(100e3, 10e6, amp=4.8*10**(a/20), seeds=2); snr.append(m["DR_dB"]); sndr.append(m["SNDR_dB"])
    fig, ax = canvas(84); ax.plot(amps, snr, "o-", color=BASE, ms=2.5, lw=.9, label="SNR"); ax.plot(amps, sndr, "s-", color=CAAZ, ms=2.2, lw=.9, label="SNDR")
    ax.set(xlabel="输入幅度（dBFS）", ylabel="dB", xlim=(-60,2)); ax.grid(alpha=.2); ax.legend(frameon=False, fontsize=6.6, loc="lower right")
    viz.annotate(fig,"SNDR/SNR vs 输入幅度（DR 曲线）","低幅度进入噪声底；DR 由 26.5 µV 噪声决定","模型生成；未含参考/抖动非理想。")
    return fig,(W,84)


def p04(D):
    fins = [6e3, 100e3, 1e6, 2e6]; s = [_metric(f, 10e6)["SNDR_dB"] for f in fins]
    fig, ax = canvas(82); ax.plot(np.array(fins)/1e3, s, "o-", color=BASE, ms=3, lw=.9)
    ax.set(xscale="log", xlabel="输入频率（kHz）", ylabel="SNDR（dB）"); ax.grid(alpha=.22, which="both")
    for x,y in zip(np.array(fins)/1e3, s): ax.annotate(f"{y:.1f}", (x,y), textcoords="offset points", xytext=(0,6), ha="center", fontsize=6.2)
    viz.annotate(fig,"SNDR vs 输入频率","6 kHz 100.5 / 100 kHz 99.4 / 2 MHz 95.7（目标）","模型值；高频受抖动/开关非线性限制，图中未注入。")
    return fig,(W,82)


def p05(D):
    n = 4096; code = np.linspace(0, 2**20-1, n); rng = np.random.default_rng(3)
    inl = 1.5*(0.55*np.sin(2*np.pi*3*code/2**20+0.4)+0.30*np.sin(2*np.pi*17*code/2**20+1.1)+0.15*rng.normal(0,1,n))
    fig, ax = canvas(84); ax.plot(code/1e3, inl, lw=.45, color=BASE)
    ax.axhspan(-1.5,1.5,color=CAAZ,alpha=.08,linewidth=0)
    ax.set(xlabel="20 位输出码（k）", ylabel="INL（ppm FS）", ylim=(-2.2,2.2)); ax.grid(alpha=.2)
    viz.annotate(fig,"INL：校准后 ±1.5 ppm 量级","模型合成的 20 位 INL（位权+非位权残差）；不是 10 bit DAC1 逐码","示意/模型曲线；真实 INL 需硅测码密度。")
    return fig,(W,84)


def p06(D):
    n = 4096; code = np.linspace(0, 2**20-1, n); rng = np.random.default_rng(4)
    dnl = 0.25*rng.normal(0,1,n) + 0.10*np.sin(2*np.pi*31*code/2**20)
    fig, ax = canvas(80); ax.plot(code/1e3, dnl, lw=.4, color=BASE)
    ax.axhspan(-0.4,0.4,color=GOOD,alpha=.08,linewidth=0)
    ax.set(xlabel="20 位输出码（k）", ylabel="DNL（ppm FS）", ylim=(-1.0,1.0)); ax.grid(alpha=.2)
    viz.annotate(fig,"DNL：±0.4 ppm 量级","模型合成；20.5 bit 逐码 DNL 受噪声平滑，不能直接测","示意/模型曲线。")
    return fig,(W,80)


def p07(D):
    labels = ["sampling", "RA amp", "RA AZ", "other"]; before = [27.4, 52.9, 8.6, 8.6]; after = [27.4, 52.9/5, 8.6, 8.6]
    fig, ax = canvas(84); x = np.arange(2); bottom = np.zeros(2)
    for lab, b, a, c in zip(labels, before, after, ["#B5D4F4","#7FB3D5","#F5B7B1","#C3B1E1"]):
        ax.bar(x, [b,a], .45, bottom=bottom, color=c, edgecolor="white", lw=.4, label=lab); bottom += np.array([b,a])
    ax.set(xticks=x, xticklabels=["before tracking","after tracking"], ylabel="噪声功率占比（%）", ylim=(0,110)); ax.grid(alpha=.2, axis="y"); ax.legend(frameon=False, fontsize=6.2, ncol=2, loc="upper right")
    viz.annotate(fig,"噪声分解：RA 放大相是主导项","sampling 27.4%、RA amp 52.9%、RA AZ 8.6%、other 8.6%","按 Fig.12 条带/预算；after 按 −80% 功率（论文口径）。")
    return fig,(W,84)


def p08(D):
    fin = 100e3; fig, ax = canvas(84)
    for caaz, c, lab in ((False, BASE, "CAAZ off"), (True, CAAZ, "CAAZ on")):
        f, db = _spectrum(fin, 10e6, caaz=caaz); ax.plot(f[1:], db[1:], lw=.55, color=c, label=lab)
    ax.set(xlim=(0,5), ylim=(-160,5), xlabel="频率（MHz）", ylabel="幅度（dBFS）"); ax.grid(alpha=.18); ax.legend(frameon=False, fontsize=6.6, loc="upper right")
    viz.annotate(fig,"CAAZ 开关的频谱对比","100 kHz；模型 ΔDR +3.58 dB（含 3 dB 通用平均）","模型值；AZ 共享假设理想。")
    return fig,(W,84)


def p09(D):
    M = [1,2,4,8]; s = [_metric(100e3,10e6, M=m)["DR_dB"] for m in M]
    fig, ax = canvas(80); ax.plot(M,s,"o-",color=BASE,ms=3,lw=.9)
    for x,y in zip(M,s): ax.annotate(f"{y:.1f}",(x,y),textcoords="offset points",xytext=(0,6),ha="center",fontsize=6.2)
    ax.set(xscale="log", xlabel="M", ylabel="DR（dB）", xticks=M, xticklabels=[str(m) for m in M]); ax.minorticks_off(); ax.grid(alpha=.22)
    viz.annotate(fig,"8× tracking 的 M 扫描","M=1→8 实测模型 +1.71 dB；不是 4 dB","模型值；ρ=0.61 未实测。")
    return fig,(W,80)


def p10(D):
    fig, ax = canvas(84)
    for sk,c,lab in ((0,BASE,"skew 0"),(2e-12,WARN,"skew 2 ps")):
        f,db = _spectrum(2e6,10e6,interleave=dict(gain=2e-5,offset=20e-6,skew=sk,shuffle=False)); ax.plot(f[1:],db[1:],lw=.55,color=c,label=lab)
    ax.set(xlim=(0,5), ylim=(-150,5), xlabel="频率（MHz）", ylabel="幅度（dBFS）"); ax.grid(alpha=.18); ax.legend(frameon=False, fontsize=6.6, loc="upper right")
    viz.annotate(fig,"交织 skew 的杂散","2 MHz 输入、不洗牌；skew 2 ps 时 fs/2±fin 附近杂散抬起","模型值；51 bin 平滑会压低窄杂散。")
    return fig,(W,84)


def p11(D):
    items = ["RA","Reference","Digital","Other"]; vals=[0.80,0.98,1.15,0.34]
    fig, ax = canvas(80); ax.bar(items, vals, .5, color=["#9FE1CB","#F7C1C1","#C0DD97","#D3D1C7"])
    ax.set(ylabel="功耗（mW）", ylim=(0,1.4)); ax.grid(alpha=.22, axis="y")
    for i,v in enumerate(vals): ax.text(i,v+.03,f"{v:.2f}",ha="center",fontsize=6.4)
    viz.annotate(fig,"功耗分解：core 约 3.27 mW","论文 3.57 mW（RA 797 / 参考 980 / 数字 1455 / 其他 340 µW）","估算；不含 I/O。")
    return fig,(W,80)


def p12(D):
    names=["This work","Bannon14","Steensgaard22","Bodnar24","Huang25"]; fom=[187.8,177.7,184.1,186.0,178.0]
    fig, ax = canvas(80); ax.bar(names,fom, .5, color=[CAAZ]+[BASE]*4)
    for i,v in enumerate(fom): ax.text(i,v+.4,f"{v:.1f}",ha="center",fontsize=6.2)
    ax.set(ylabel="FoMs（dB）", ylim=(170,192)); ax.grid(alpha=.22, axis="y")
    viz.annotate(fig,"FoM 对标（论文 Table I）","本工作目标 187.8 dB @100 kHz；不是实测","论文值/目标值。")
    return fig,(W,80)


def p13(D):
    x,_=simulate(100e3, fs=10e6, seed=5)
    fig, ax = canvas(80); ax.hist(x*1e6, bins=160, color=BASE, alpha=.8)
    ax.set(xlabel="输出（µV）", ylabel="样本数"); ax.grid(alpha=.22, axis="y")
    viz.annotate(fig,"输出码分布：噪声底 26.5 µV","100 kHz 正弦、10 MS/s；直方图宽度对应 DR 102.5 dB","模型值；未标定。")
    return fig,(W,80)


def p14(D):
    T=np.linspace(-40,125,80); s=99.4-0.004*(T-27)-1.2e-5*(T-27)**2
    fig, ax = canvas(78); ax.plot(T,s,color=BASE,lw=1.1); ax.set(xlabel="温度（℃）", ylabel="SNDR（dB）"); ax.grid(alpha=.22)
    viz.annotate(fig,"SNDR vs 温度（模型）","27℃ 99.4 dB；−40/125℃ 约 −0.6/−0.5 dB","经验漂移模型；不是 PVT 仿真。")
    return fig,(W,78)


PAPERS=[("paper01_spectrum_100k",p01,146,84),("paper02_spectrum_2m",p02,146,84),
        ("paper03_dr_curve",p03,146,84),("paper04_sndr_vs_fin",p04,146,82),
        ("paper05_inl_20b",p05,146,84),("paper06_dnl_20b",p06,146,80),
        ("paper07_noise_breakdown",p07,146,84),("paper08_caaz_spectrum",p08,146,84),
        ("paper09_m_sweep",p09,146,80),("paper10_skew_spectrum",p10,146,84),
        ("paper11_power",p11,146,80),("paper12_fom",p12,146,80),
        ("paper13_histogram",p13,146,80),("paper14_temp",p14,146,78)]


def main():
    res=json.loads((RES/"results.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True,exist_ok=True); font=viz.chinese_style(); outs=[]; dims=[]
    for name,fn,w,h in PAPERS:
        fig,_=fn({"res":res}); paths=viz.save(fig,OUT/name); outs+=paths; dims.append((w,h)); plt.close(fig)
    viz.write_manifest(OUT,script=Path(__file__),data=[RES/"results.json"],outputs=outs,dims=dims,font=font,
                       extra={"figure_count":len(PAPERS),"note":"论文测试风格图；模型生成，绝对指标未标定"})
    print(f"wrote {len(PAPERS)} paper figures / {len(outs)} files")


if __name__=="__main__":
    main()
