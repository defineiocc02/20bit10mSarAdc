"""figures.py —— 32+ 张模型图（每张回答一个技术有效性问题）

沿用 20b10mtask 的出图方案：146 mm、Hiragino Sans GB、PNG+SVG+PDF、manifest。
运行：cd 20b10m && python3 -m model.figures
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .params import P, LSB_TOTAL, LSB2
from .adc import simulate
from .metrics import fft_metrics
from . import static, viz

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "model/results"
OUT = RES / "figures"
BASE, CAAZ, WARN, GOOD, NEUTRAL = "#626C75", "#0072B2", "#D55E00", "#009E73", "#333333"
MM = viz.MM
W = 146


def canvas(h=80, w=W, left=0.12, right=0.97, top=0.78, bottom=0.20):
    fig, ax = plt.subplots(figsize=(w / MM, h / MM))
    fig.subplots_adjust(left=left, right=right, top=top, bottom=bottom)
    return fig, ax


def metric(fin, fs, caaz=False, seeds=2, **kw):
    n = P.n
    fc = round(fin * n / fs) * fs / n
    rows = []
    for s in range(seeds):
        x, _ = simulate(fc, fs=fs, caaz=caaz, seed=500 + s, **kw)
        rows.append(fft_metrics(x, fs, fc))
    return {k: float(np.mean([r[k] for r in rows])) for k in ("DR_dB", "SNDR_dB", "SFDR_dBc")}


def spectrum(fin, fs, caaz=False, interleave=None, seed=11):
    n = P.n
    fc = round(fin * n / fs) * fs / n
    x, _ = simulate(fc, fs=fs, caaz=caaz, interleave=interleave, seed=seed)
    spec = np.abs(np.fft.rfft(x - x.mean())) / (n / 2)
    p = spec**2
    k = 51
    sm = np.convolve(p, np.ones(k) / k, mode="same")
    db = 10 * np.log10(np.maximum(sm / (P.fs_diff / 2) ** 2, 1e-24))
    return np.fft.rfftfreq(n, 1 / fs) / 1e6, db


def _res():
    return json.loads((RES / "results.json").read_text(encoding="utf-8"))


# ---------------- A. CAAZ ----------------
def f01(D):
    rows = D["res"]["caaz"]
    fin = np.array([r["fin"] / 1e3 for r in rows]); b = np.array([r["base_DR_dB"] for r in rows]); c = np.array([r["caaz_DR_dB"] for r in rows])
    fig, ax = canvas(78)
    ax.plot(fin, b, "o-", color=BASE, ms=3, label="无 CAAZ"); ax.plot(fin, c, "s-", color=CAAZ, ms=3, label="CAAZ")
    for x, y0, y1 in zip(fin, b, c): ax.annotate(f"{y1-y0:+.2f} dB", (x, y1), textcoords="offset points", xytext=(0, 6), ha="center", fontsize=6.2, color=CAAZ)
    ax.set(xscale="log", xlabel="输入频率（kHz）", ylabel="DR（dB）", xticks=[100, 1000, 2000], xticklabels=["0.1", "1", "2"]); ax.grid(alpha=.26); ax.legend(frameon=False, fontsize=6.6, loc="lower left")
    viz.annotate(fig, "CAAZ 的频率响应：10 MS/s 输出 / 20 MS/s raw", "100 kHz +3.58 dB；2 MHz +3.14 dB，sinc 开始衰落", "模型值，未标定，不可签核；数据 results.json。")
    return fig, (W, 78)


def f02(D):
    rows = D["res"]["caaz_az"]["rows"]; x = [r["az_share"] for r in rows]; y = [r["DR_dB"] for r in rows]
    fig, ax = canvas(76)
    ax.bar(range(len(x)), y, color=[BASE, "#3E8FC4", CAAZ][:len(x)], width=.58)
    for i, v in enumerate(y): ax.text(i, v + .03, f"{v:.2f}", ha="center", va="bottom", fontsize=6.6)
    ax.set(xticks=range(len(x)), xticklabels=[f"{v:.1f}" for v in x], xlabel="AZ 共享度 az_share", ylabel="DR（dB）", ylim=(min(y)-0.4, max(y)+0.25)); ax.grid(alpha=.26, axis="y")
    viz.annotate(fig, "CAAZ 的独家作用：AZ 共享度扫描", "az_share=1 共享同一 AZ 代；0 等于不做 CAAZ，只剩两点平均", "100 kHz、10 MS/s；数据 results.json。")
    return fig, (W, 76)


def f03(D):
    s = np.linspace(.05, .45, 200); gain = 10*np.log10(1/(1-s))
    fig, ax = canvas(76)
    ax.plot(s*100, gain, color=CAAZ, lw=1.2)
    for x, lab in ((13, "我们 13%"), (18, "模型 18%"), (26, "论文 26%")):
        ax.axvline(x, color=BASE, ls=":", lw=.7); ax.text(x+.4, .3, lab, fontsize=6.2, color=BASE)
    ax.set(xlabel="AZ 项占噪声功率（%）", ylabel="CAAZ 独家增益（dB）", xlim=(5,45)); ax.grid(alpha=.26)
    viz.annotate(fig, "CAAZ 独家增益 = AZ 份额的函数", "10log10(1/(1−s))；我们 AZ 只占 13–18%，所以只有 0.6–0.9 dB", "解析式；论文 26% 对应 1.3 dB。")
    return fig, (W, 76)


def f04(D):
    p1 = [metric(f, 5e6, caaz=True, seeds=2)["DR_dB"] - metric(f, 5e6, caaz=False, seeds=2)["DR_dB"] for f in (100e3, 1e6, 2e6)]
    p2 = [metric(f, 10e6, caaz=True, seeds=2)["DR_dB"] - metric(f, 10e6, caaz=False, seeds=2)["DR_dB"] for f in (100e3, 1e6, 2e6)]
    fig, ax = canvas(78); xx = np.arange(3)
    ax.bar(xx-.18, p1, .34, color=BASE, label="P1 5 MS/s 输出（raw 10M）")
    ax.bar(xx+.18, p2, .34, color=CAAZ, label="P2 10 MS/s 输出（raw 20M）")
    ax.set(xticks=xx, xticklabels=["0.1 MHz", "1 MHz", "2 MHz"], ylabel="ΔDR（dB）", ylim=(0,4.6)); ax.grid(alpha=.26, axis="y"); ax.legend(frameon=False, fontsize=6.2, loc="upper right")
    viz.annotate(fig, "CAAZ 的速率代价：P1 vs P2", "P1 2 MHz 只剩 +1.77 dB；P2 2 MHz 仍有 +3.14 dB", "CAAZ 需要 raw 速率翻倍；模型值。")
    return fig, (W, 78)


def f05(D):
    f = np.linspace(0, 5e6, 500)
    fig, ax = canvas(76)
    for raw, c in ((10e6, BASE), (20e6, CAAZ), (40e6, GOOD)):
        ax.plot(f/1e6, 20*np.log10(np.abs(np.cos(np.pi*f/(2*raw)))+1e-12), color=c, lw=1.1, label=f"raw {raw/1e6:g} MHz")
    ax.set(xlabel="输入频率（MHz）", ylabel="两点平均的 sinc 衰落（dB）", xlim=(0,5), ylim=(-4,0.2)); ax.grid(alpha=.26); ax.legend(frameon=False, fontsize=6.4, loc="lower left")
    viz.annotate(fig, "CAAZ 的 sinc 衰落：raw 速率决定高频可用性", "P1 raw 10M 在 2 MHz 已 −1.84 dB；P2 raw 20M 只 −0.44 dB", "解析式 |cos(πf/(2fs_raw))|。")
    return fig, (W, 76)


def f06(D):
    items = ["kT/C", "RA 宽带", "RA AZ", "Cmp", "Ref"]
    base = [P.ktc, P.ra_broad, P.ra_az, P.cmp, P.ref]
    caaz = [P.ktc/np.sqrt(2), P.ra_broad/np.sqrt(2), 0.0, P.cmp/np.sqrt(2), P.ref/np.sqrt(2)]
    fig, ax = canvas(80); x = np.arange(2); bottom = np.zeros(2); colors = ["#B5D4F4", "#7FB3D5", "#F5B7B1", "#C39BD3", "#A9DFBF"]
    for name, b, c, col in zip(items, base, caaz, colors):
        ax.bar(x, [b*1e6, c*1e6], .5, bottom=bottom, color=col, edgecolor="white", lw=.4, label=name)
        bottom += np.array([b*1e6, c*1e6])
    ax.set(xticks=x, xticklabels=["无 CAAZ", "CAAZ"], ylabel="输入折算噪声（μVrms）"); ax.grid(alpha=.26, axis="y"); ax.legend(frameon=False, fontsize=6, ncol=3, loc="upper right")
    viz.annotate(fig, "CAAZ 到底消哪一项：噪声预算分解", "AZ 项归零；其余独立项只按 √2 平均（3 dB）", "按参数表 RSS 近似；不是逐源仿真分解。")
    return fig, (W, 80)


def f07(D):
    fig, ax = canvas(80)
    for caaz, c, lab in ((False, BASE, "无 CAAZ"), (True, CAAZ, "CAAZ")):
        f, db = spectrum(100e3, 10e6, caaz=caaz); ax.plot(f[1:], db[1:], lw=.8, color=c, label=lab)
    ax.set(xlim=(0,5), ylim=(-160,5), xlabel="频率（MHz）", ylabel="幅度（dBFS）"); ax.grid(alpha=.24); ax.legend(frameon=False, fontsize=6.6, loc="upper right")
    viz.annotate(fig, "输出频谱：CAAZ 开关对比", "100.1 kHz、10 MS/s、16384 点相干采样、51 bin 平滑", "绝对噪底为模型值，未标定。")
    return fig, (W, 80)


# ---------------- B. tracking ----------------
def f08(D):
    rows = D["res"]["tracking"]; M = np.array([r["M"] for r in rows]); dr = np.array([r["DR_dB"] for r in rows])
    fig, ax = canvas(76); ax.plot(M, dr, "o-", color=CAAZ, ms=3)
    ax.annotate(f"M=1→8：{dr[-1]-dr[0]:+.2f} dB", (M[-1], dr[-1]), textcoords="offset points", xytext=(-6, 10), ha="right", fontsize=6.8, color=CAAZ)
    ax.set(xscale="log", xlabel="重复次数 M", ylabel="DR（dB）", xticks=M, xticklabels=[str(m) for m in M]); ax.grid(alpha=.26)
    viz.annotate(fig, "8× tracking 的有效平均：只有 +1.7 dB", "ρ=0.61 的 AR(1) 相关噪声；不是理论 4 dB", "ρ 未实测，属推断值。")
    return fig, (W, 76)


def f09(D):
    rho = np.linspace(0, .95, 200); fig, ax = canvas(78)
    for M, c in ((2, BASE), (4, CAAZ), (8, GOOD)):
        F = 1/M + 2/(M*M)*sum((M-k)*rho**k for k in range(1, M))
        ax.plot(rho, 10*np.log10(1/F), color=c, lw=1.1, label=f"M={M}")
    ax.set(xlabel="相邻重复样本相关系数 ρ", ylabel="平均增益（dB）", xlim=(0,.95)); ax.grid(alpha=.26); ax.legend(frameon=False, fontsize=6.6)
    viz.annotate(fig, "相关噪声的平均上限：ρ 决定能拿多少 dB", "M=8 在 ρ=0.61 时只有 4.05 dB（RA 单独），整机更少", "等权平均解析式；SINC2 三角权会略有差异。")
    return fig, (W, 78)


def f10(D):
    vals = [0.2, 0.4, 0.61, 0.8]; y = [metric(100e3, 10e6, rho=r, seeds=2)["DR_dB"] for r in vals]
    fig, ax = canvas(76); ax.plot(np.array(vals), y, "o-", color=CAAZ, ms=3)
    ax.set(xlabel="ρ", ylabel="DR（dB）", xlim=(.15,.85)); ax.grid(alpha=.26)
    viz.annotate(fig, "ρ 扫描：RA 带宽越宽，8× 越有效", "ρ 从 0.8 降到 0.2，DR 提升约 4 dB", "模型值；ρ 需由 RA 噪声 PSD 实测。")
    return fig, (W, 76)


def f11(D):
    k = np.arange(0, 9); fig, ax = canvas(74)
    for rho, c in ((.3, BASE), (.61, CAAZ), (.9, WARN)):
        ax.plot(k, rho**k, "o-", color=c, ms=2.5, lw=1, label=f"ρ={rho}")
    ax.set(xlabel="重复间隔（样本）", ylabel="归一化自相关", ylim=(-.05,1.05)); ax.grid(alpha=.26); ax.legend(frameon=False, fontsize=6.4)
    viz.annotate(fig, "重复读之间的相关：AR(1) 假设", "ρ=0.61 时第 2 次读仍有 0.37 相关；这就是平均拿不满的原因", "模型假设；实际 PSD 可能双极点。")
    return fig, (W, 74)


def f12(D):
    fig, ax = canvas(76)
    Ms = np.array([1,2,4,8]);
    for rho, c in ((.3, BASE), (.61, CAAZ), (.9, WARN)):
        g = []
        for M in Ms:
            f = 1/M + 2/(M*M)*sum((M-k)*rho**k for k in range(1, M)); g.append(10*np.log10(1/f))
        ax.plot(Ms, g, "o-", color=c, ms=3, label=f"ρ={rho}")
    ax.set(xscale="log", xlabel="M", ylabel="RA 噪声平均增益（dB）", xticks=Ms, xticklabels=[str(m) for m in Ms]); ax.minorticks_off(); ax.grid(alpha=.26); ax.legend(frameon=False, fontsize=6.4)
    viz.annotate(fig, "M 的边际收益：越往后越小", "ρ=0.61 时 M=1→8 只有 4.05 dB，M=8→16 只多 1.4 dB", "解析式；整机 DR 还要被不可平均项稀释。")
    return fig, (W, 76)


def f13(D):
    cases = [("track off / CAAZ off", False, False), ("track on / CAAZ off", True, False),
             ("track off / CAAZ on", False, True), ("track on / CAAZ on", True, True)]
    vals = [metric(100e3, 10e6, caaz=c, M=(8 if t else 1), seeds=2)["DR_dB"] for _, t, c in cases]
    fig, ax = canvas(78); x = np.arange(4)
    ax.bar(x, vals, .55, color=[BASE, "#3E8FC4", "#7FB3D5", CAAZ]); ax.set(xticks=x, xticklabels=["T−/C−","T+/C−","T−/C+","T+/C+"], ylabel="DR（dB）", ylim=(min(vals)-.8, max(vals)+.4)); ax.grid(alpha=.26, axis="y")
    for i, v in enumerate(vals): ax.text(i, v+.08, f"{v:.2f}", ha="center", fontsize=6.2)
    viz.annotate(fig, "tracking 与 CAAZ 能叠加吗", "两者作用在不同噪声项：tracking 平均 RA 宽带，CAAZ 消 AZ；合起来仍受 kT/C 地板限制", "模型值；CAAZ 的 sinc 未在此图扣除。")
    return fig, (W, 78)


# ---------------- C. interleaving ----------------
def f14(D):
    fig, ax = canvas(78); names = ["5 MS/s\n单通道", "10 MS/s\n全通道交织", "10 MS/s\n部分交织"]
    area = [1.0, 2.0, 1.25]; win = [110, 10, 100]
    ax.bar(np.arange(3), area, .55, color=[BASE, WARN, CAAZ])
    for i, (a, w) in enumerate(zip(area, win)): ax.text(i, a+.04, f"面积 ×{a:g}\n采样窗 {w} ns", ha="center", fontsize=6.2)
    ax.set(xticks=range(3), xticklabels=names, ylabel="相对面积（×）", ylim=(0,2.4)); ax.grid(alpha=.26, axis="y")
    viz.annotate(fig, "为什么必须是“部分交织”而不是全通道", "全通道 10 MS/s 每通道只剩 10 ns 采样窗，且面积/功耗翻倍；部分交织只复制 DAC，仍保 100 ns", "面积按 DAC/RA/CT2 估算；采样窗为架构值。")
    return fig, (W, 78)


def f15(D):
    rows = [r for r in D["res"]["interleave"] if "2MHz skew" in r["case"] and "shuffle" not in r["case"]]
    x = [r["skew_ps"] for r in rows]; dr = [r["DR_dB"] for r in rows]; sf = [r["SFDR_dBc"] for r in rows]
    fig, ax = canvas(80); ax.plot(x, dr, "o-", color=CAAZ, ms=3, label="DR"); ax.plot(x, sf, "s--", color=WARN, ms=3, label="SFDR")
    ax.set(xlabel="片间 skew（ps）", ylabel="dB", xticks=x, xticklabels=[f"{v:g}" for v in x]); ax.grid(alpha=.26); ax.legend(frameon=False, fontsize=6.4, loc="center right")
    viz.annotate(fig, "skew 是部分交织的头号杀手", "2 MHz、2 ps：DR 掉约 4.3 dB；预算必须 ≤1 ps", "一阶 skew 模型；未含采样网络带宽。")
    return fig, (W, 80)


def f16(D):
    rows = [r for r in D["res"]["interleave"] if "2MHz skew" in r["case"] and "shuffle" not in r["case"]]
    x = [r["skew_ps"] for r in rows]; dr = [r["DR_dB"] for r in rows]
    fig, ax = canvas(76); ax.plot(x, dr, "o-", color=CAAZ, ms=3); ax.set(xlabel="片间 skew（ps）", ylabel="DR（dB）", xticks=x, xticklabels=[f"{v:g}" for v in x]); ax.grid(alpha=.26)
    viz.annotate(fig, "skew 对 DR 的斜率", "0.5→2 ps 掉约 2.3 dB；再往上会更快", "模型值；用于定版图等长预算。")
    return fig, (W, 76)


def f17(D):
    rows = [r for r in D["res"]["interleave"] if "gain=" in r["case"]]
    g = [0] + [r["gain_ppm"] for r in rows]; dr = [metric(100e3, 10e6, interleave=dict(gain=0, offset=0, skew=0), seeds=2)["DR_dB"]] + [r["DR_dB"] for r in rows]
    fig, ax = canvas(78); ax.plot(g, dr, "o-", color=CAAZ, ms=3); ax.set(xlabel="片间增益失配（ppm）", ylabel="DR（dB）"); ax.grid(alpha=.26)
    viz.annotate(fig, "增益失配：50 ppm 就掉 6 dB", "每片增益校准必须打到 ≤10 ppm，否则交织没有意义", "模型值；失配为随机、8 片平均。")
    return fig, (W, 78)


def f18(D):
    offs = [0, 20, 50, 100]; y = [metric(100e3, 10e6, interleave=dict(gain=0, offset=o*1e-6, skew=0), seeds=2)["DR_dB"] for o in offs]
    fig, ax = canvas(76); ax.plot(offs, y, "o-", color=CAAZ, ms=3); ax.set(xlabel="片间失调失配（μV）", ylabel="DR（dB）"); ax.grid(alpha=.26)
    viz.annotate(fig, "失调失配：20 μV 还能接受，100 μV 就崩", "失调是直流项，可用每片失调系数校准；不洗牌会出 fs/2 杂散", "模型值；未画杂散位置。")
    return fig, (W, 76)


def f19(D):
    rows = [r for r in D["res"]["interleave"] if r["case"] in ("10MS/s shuffle=False", "10MS/s shuffle=True")]
    labels = ["不洗牌", "洗牌"]; dr = [r["DR_dB"] for r in rows]; sf = [r["SFDR_dBc"] for r in rows]
    fig, ax = canvas(78); xx = np.arange(2); ax.bar(xx-.18, dr, .34, color=CAAZ, label="DR"); ax.bar(xx+.18, sf, .34, color=WARN, label="SFDR")
    ax.set(xticks=xx, xticklabels=labels, ylabel="dB", ylim=(80,135)); ax.grid(alpha=.26, axis="y"); ax.legend(frameon=False, fontsize=6.4, loc="upper left", ncol=2)
    viz.annotate(fig, "洗牌把杂散换成噪声：SFDR 106→126", "不洗牌 DR 98.6 / SFDR 107.5；洗牌 DR 96.5 / SFDR 126.3", "100 kHz、失配 50 ppm + 50 μV + 1 ps。")
    return fig, (W, 78)


def f20(D):
    fig, ax = canvas(82)
    for sk, c, lab in ((0, BASE, "skew 0"), (2e-12, WARN, "skew 2 ps")):
        f, db = spectrum(2e6, 10e6, interleave=dict(gain=2e-5, offset=20e-6, skew=sk, shuffle=False)); ax.plot(f[1:], db[1:], lw=.7, color=c, label=lab)
    ax.set(xlim=(0,5), ylim=(-150,5), xlabel="频率（MHz）", ylabel="幅度（dBFS）"); ax.grid(alpha=.25); ax.legend(frameon=False, fontsize=6.4, loc="upper right")
    viz.annotate(fig, "skew 的杂散落在哪：2 MHz 输入", "不洗牌时，片间 skew 在 fs/2±fin 附近出离散杂散", "模型值；51 bin 平滑，杂散幅度会被压低。")
    return fig, (W, 82)


def f21(D):
    # 18 slices x 18 swaps, role map
    base = 0; mat = np.zeros((18, 18))
    for t in range(18):
        b = (base + 8*t) % 18
        conv = [(b+k) % 18 for k in range(8)]; acq = [(b+8+k) % 18 for k in range(8)]
        for i in conv: mat[i, t] = 2
        for i in acq: mat[i, t] = 1
    fig, ax = plt.subplots(figsize=(W/MM, 92/MM)); fig.subplots_adjust(left=.14,right=.97,top=.76,bottom=.16)
    ax.imshow(mat, aspect="auto", cmap=matplotlib.colors.ListedColormap(["#F2F2F2", "#B5D4F4", "#534AB7"]), interpolation="nearest")
    ax.set(xlabel="换相序号（每 100 ns）", ylabel="slice 编号", yticks=range(0,18,2)); ax.grid(alpha=.2, color="white", lw=.4)
    viz.annotate(fig, "18 片池的角色调度：8 转换 + 8 采样 + 2 备", "深色=转换、浅色=采样、灰=备用；base 每次 +8 mod 18，9 次覆盖全部", "调度为轮换，不是 LFSR/DEM；实际洗牌另加。")
    return fig, (W, 92)


def f22(D):
    conv = np.zeros(18); acq = np.zeros(18); base = 0
    for t in range(18):
        b = (base + 8*t) % 18
        for k in range(8): conv[(b+k)%18] += 1; acq[(b+8+k)%18] += 1
    fig, ax = canvas(76); x = np.arange(18); ax.bar(x-.18, conv, .34, color=CAAZ, label="转换"); ax.bar(x+.18, acq, .34, color="#7FB3D5", label="采样")
    ax.set(xlabel="slice 编号", ylabel="使用次数（18 次换相）", xticks=range(0,18,2)); ax.grid(alpha=.26, axis="y"); ax.legend(frameon=False, fontsize=6.4)
    viz.annotate(fig, "每片的使用次数：轮换是否公平", "base+8 mod 18 的 9 次循环让每片转换/采样次数接近相等", "模型调度；未含备用片替换。")
    return fig, (W, 76)


# ---------------- D. static ----------------
def f23(D):
    c = D["curves"]; code = c["code"]; fig, ax = canvas(86)
    ax.step(code, c["inl_raw"], where="post", color=BASE, lw=.8, label="校准前"); ax.step(code, c["inl_cal"], where="post", color=CAAZ, lw=.9, label="位权校准后")
    ax.set(xlabel="DAC1 码（10 bit）", ylabel="INL（LSB1）"); ax.grid(alpha=.26); ax.legend(frameon=False, fontsize=6.6, loc="upper right")
    viz.annotate(fig, "DAC1 INL：校准前 16.4 ppm → 0.3 ppm", "σu=0.2%，8 unary 片 × 128 单位；校准只扣位权项", "1024 码逐码；不是 20.5 bit 系统 INL。残差由测量噪声决定（n=16）。")
    return fig, (W, 86)


def f24(D):
    c = D["curves"]; code = c["code"][1:]; fig, ax = canvas(82)
    ax.step(code, c["dnl_raw"], where="post", color=BASE, lw=.7, label="校准前"); ax.step(code, c["dnl_cal"], where="post", color=CAAZ, lw=.8, label="位权校准后")
    ax.set(xlabel="DAC1 码（10 bit）", ylabel="DNL（LSB1）"); ax.grid(alpha=.26); ax.legend(frameon=False, fontsize=6.6, loc="upper right")
    viz.annotate(fig, "DAC1 DNL：失配在进位处出尖峰", "校准后尖峰被位权项吸收；剩余为有限样本残差（±0.6 ppm）", "逐码 DNL；20.5 bit 下不可直接测。")
    return fig, (W, 82)


def f25(D):
    rows = D["res"]["static"]; x = np.arange(len(rows)); raw = [r["inl_raw_ppm"] for r in rows]; cal = [r["inl_cal_ppm"] for r in rows]
    fig, ax = canvas(78); ax.bar(x-.18, raw, .34, color=BASE, label="校准前"); ax.bar(x+.18, cal, .34, color=CAAZ, label="校准后")
    ax.set(xticks=x, xticklabels=[f"{r['unit_sigma']*100:.1f}%" for r in rows], xlabel="单位电容 σu", ylabel="INL（ppm FS）"); ax.grid(alpha=.26, axis="y"); ax.legend(frameon=False, fontsize=6.4)
    viz.annotate(fig, "单位电容失配 vs 校准后 INL", "σu 0.1/0.2/0.4% 校准前 8/16/33 ppm，校准后都约 0.3 ppm", "模型值；校准后残差与 σu 无关——它由测量噪声（∝1/√n）决定。")
    return fig, (W, 78)


def f26(D):
    bits = np.array([12,14,16,18,20,24]); res = 1e6 / 2**bits
    fig, ax = canvas(76); ax.semilogy(bits, res, "o-", color=CAAZ, ms=3)
    ax.axhline(1.5, color=WARN, ls="--", lw=.8); ax.text(12.2, 1.8, "论文 1.5 ppm", fontsize=6.2, color=WARN)
    ax.set(xlabel="系数位宽（bit）", ylabel="校准残差上界（ppm）"); ax.grid(alpha=.26, which="both")
    viz.annotate(fig, "系数位宽够不够：14 bit 就溢出", "14 bit 有符号只到 ±8191，MSB 半组 Q4 要 ±8192；24 bit 残差 0.06 ppm", "按权重满量程估算，不是 LMS 仿真。")
    return fig, (W, 76)


def f27(D):
    c = D["curves"]; fig, ax = canvas(76)
    bins = np.linspace(-.018,.018,73); ax.hist(c["dnl_raw"], bins=bins, color=BASE, alpha=.55, label="校准前"); ax.hist(c["dnl_cal"], bins=bins, color=CAAZ, alpha=.55, label="校准后")
    ax.set(xlabel="DNL（LSB1）", ylabel="码数"); ax.grid(alpha=.26); ax.legend(frameon=False, fontsize=6.4)
    viz.annotate(fig, "DNL 分布：校准把尖峰收回到 0 附近", "校准前尾部到 ±0.0145 LSB1（14 ppm）；校准后只剩 ±0.0006 LSB1", "1024 码直方图。")
    return fig, (W, 76)


def f28(D):
    g = np.linspace(0, 3, 100); inl = 0.5*g**2
    fig, ax = canvas(74); ax.plot(g, inl, color=CAAZ, lw=1.2); ax.set(xlabel="片上温度梯度（K/mm）", ylabel="附加 INL（ppm）"); ax.grid(alpha=.26)
    viz.annotate(fig, "热梯度不是主风险，但会毁校准", "1 K/mm 约 0.5 ppm；3 K/mm 到 4.5 ppm，已超预算", "二次近似，系数为估算；需版图质心重合。")
    return fig, (W, 74)


def f29(D):
    n = np.array([1e3, 3e3, 1e4, 3e4, 1e5]); res = 40/np.sqrt(n)
    fig, ax = canvas(74); ax.loglog(n, res, "o-", color=CAAZ, ms=3); ax.set(xlabel="校准点数", ylabel="LMS 残差（ppm）"); ax.grid(alpha=.26, which="both")
    viz.annotate(fig, "校准点数：1e4 点约 0.4 ppm", "残差按 1/√N 收敛；1e4 点 @10 MS/s 约 1 ms", "经验模型；未含噪声/失配相关性。")
    return fig, (W, 74)


# ---------------- E. noise / ref / jitter ----------------
def f30(D):
    items = ["kT/C", "RA 宽带", "RA AZ", "Cmp", "Ref"]; vals = [P.ktc, P.ra_broad/np.sqrt(2.5), P.ra_az, P.cmp, P.ref]
    fig, ax = canvas(78); x = np.arange(len(items))
    ax.bar(x, np.array(vals)*1e6, .55, color=[ "#B5D4F4","#7FB3D5","#F5B7B1","#C39BD3","#A9DFBF"])
    ax.set(xticks=x, xticklabels=items, ylabel="输入折算噪声（μVrms）"); ax.grid(alpha=.26, axis="y")
    viz.annotate(fig, "整机噪声预算：RA 宽带仍是最大项", "kT/C 17.3、RA 平均后约 15、AZ 9.7、Cmp 9.7、Ref 2.9", "按参数表；RSS 约 26.5 μV，对应 DR 102.5。")
    return fig, (W, 78)


def f31(D):
    cs = np.array([14,28,56])*1e-12; ktc = np.sqrt(2*1.38e-23*300/cs)
    other = np.sqrt(np.sum(np.array([P.ra_broad/np.sqrt(2.5), P.ra_az, P.cmp, P.ref])**2))
    dr = 20*np.log10((P.fs_diff/2/np.sqrt(2))/np.sqrt(ktc**2+other**2))
    fig, ax = canvas(76); ax.plot(cs*1e12, dr, "o-", color=CAAZ, ms=3); ax.set(xlabel="采样电容（pF/侧）", ylabel="DR（dB）"); ax.grid(alpha=.26)
    viz.annotate(fig, "加大采样电容的边际收益：28→56 pF 只 +0.6 dB", "kT/C 已只占 27%；翻倍电容救不了 DR，反而加输入电流", "解析式；其他噪声取固定值。")
    return fig, (W, 76)


def f32(D):
    st = np.linspace(.2, 2.0, 100)*1e-12; f = 2e6; A = P.fs_diff/2
    ej = A*2*np.pi*f*st/np.sqrt(2); en = 26.5e-6
    sndr = 20*np.log10((A/np.sqrt(2))/np.sqrt(ej**2+en**2))
    fig, ax = canvas(76); ax.plot(st*1e12, sndr, color=CAAZ, lw=1.2); ax.axvline(1.0, color=WARN, ls="--", lw=.8); ax.text(1.05, sndr.min()+2, "1 ps 验收", fontsize=6.2, color=WARN)
    ax.set(xlabel="采样时钟抖动 σt（ps）", ylabel="2 MHz SNDR 上限（dB）"); ax.grid(alpha=.26)
    viz.annotate(fig, "2 MHz 的抖动天花板：1 ps 就是 95.7 dB", "σt=1 ps 时抖动 44.4 μV；0.5 ps 才能到 97.5 dB", "解析式；未含开关非线性。")
    return fig, (W, 76)


def f33(D):
    c = np.array([150,300,400,600,1000])*1e-12; droop = 69e-12/c*1e3
    fig, ax = canvas(76); ax.plot(c*1e12, droop, "o-", color=CAAZ, ms=3); ax.set(xlabel="片上去耦 Cdec（pF）", ylabel="瞬时 droop（mV）"); ax.grid(alpha=.26)
    viz.annotate(fig, "去耦不是越大越好：300–400 pF 是拐点", "1 nF 只能把 droop 从 230 降到 69 mV，却要 0.43 mm²", "Q=69 pC 的估算；未含 R_buf 补回。")
    return fig, (W, 76)


def f34(D):
    t = np.linspace(0, 5e-9, 500); target = .5*LSB_TOTAL
    fig, ax = canvas(76)
    for ron, c in ((20, BASE), (32, CAAZ), (52, WARN)):
        tau = ron*28e-12; err = 1.25*np.exp(-t/tau)*1e3
        ax.semilogy(t*1e9, np.maximum(err, 1e-6), color=c, lw=1, label=f"Ron={ron} Ω")
    ax.axhline(target*1e3, color=NEUTRAL, ls=":", lw=.8); ax.text(0.05, target*1e3*1.3, "0.5 LSB1", fontsize=6.2)
    ax.set(xlabel="时间（ns）", ylabel="DAC1 建立误差（mV）", ylim=(1e-4,1e3)); ax.grid(alpha=.26, which="both"); ax.legend(frameon=False, fontsize=6.2)
    viz.annotate(fig, "DAC1 粗装载：Ron 32 Ω 是硬上限", "52 Ω 在 ss 角 9.5 ns，超 ΦC0；32 Ω 留 0.5 ns", "τ=Ron·C_eq 的简化；实际 C_eq 随码变。")
    return fig, (W, 76)


def f35(D):
    d = np.linspace(0, 5, 100); inl = 0.3*d
    fig, ax = canvas(74); ax.plot(d, inl, color=CAAZ, lw=1.2); ax.set(xlabel="参考 droop（LSB1）", ylabel="码相关 INL（ppm）"); ax.grid(alpha=.26)
    viz.annotate(fig, "参考 droop 直接变成码相关 INL", "droop 1 LSB1 约 0.3 ppm；要守 1.5 ppm，droop 必须 <5 LSB1", "线性近似；实际与码型/回流有关。")
    return fig, (W, 74)


# ---------------- F. system ----------------
def f36(D):
    phases = ["ΦC0", "ΦC1", "ΦRA", "ΦC2-SAR", "REP", "GUARD"]; dur = [7.5,15,25,27.5,10,5]; cols = ["#B5D4F4","#9FE1CB","#FAC775","#CECBF6","#A9DFBF","#D3D1C7"]
    fig, ax = plt.subplots(figsize=(W/MM, 70/MM)); fig.subplots_adjust(left=.13,right=.97,top=.76,bottom=.24)
    left = 0
    for p, d, c in zip(phases, dur, cols):
        ax.barh(0, d, left=left, color=c, edgecolor="white", height=.55); ax.text(left+d/2, 0, f"{p}\n{d:g}", ha="center", va="center", fontsize=6.2); left += d
    ax.set(xlim=(0,90), ylim=(-.6,.6), xlabel="时间（ns）", yticks=[]); ax.grid(alpha=.25, axis="x")
    viz.annotate(fig, "90 ns 单相帧：ΦC2 是硬核", "7.5 + 15 + 25 + 27.5 + 10 + 5 = 90 ns；部分交织每 100 ns 重复一次", "标称值；ss 角余量见时序表。")
    return fig, (W, 70)


def f37(D):
    items = ["RA", "参考", "数字", "其他"]; vals = [0.80,1.0,1.15,0.35]
    fig, ax = canvas(74); ax.bar(items, vals, .5, color=["#9FE1CB","#F7C1C1","#C0DD97","#D3D1C7"])
    ax.set(ylabel="core 功耗（mW）", ylim=(0,1.5)); ax.grid(alpha=.26, axis="y")
    for i, v in enumerate(vals): ax.text(i, v+.03, f"{v:.2f}", ha="center", fontsize=6.4)
    viz.annotate(fig, "core 功耗分配：约 3.3 mW", "RA 0.8 + 参考 1.0 + 数字 1.15 + 其他 0.35；不含 I/O", "估算值；与论文 3.57 mW 同口径。")
    return fig, (W, 74)


def f38(D):
    items = ["DAC1", "SliceMux", "去耦", "数字", "CT2+RA", "其他"]; vals = [0.45,0.11,0.44,0.315,0.221,0.7]
    fig, ax = canvas(78); ax.barh(items[::-1], vals[::-1], color=["#D3D1C7","#9FE1CB","#C0DD97","#F7C1C1","#B5D4F4","#CECBF6"])
    ax.set(xlabel="面积（mm²）"); ax.grid(alpha=.26, axis="x")
    viz.annotate(fig, "4 mm² 版面积分配（宽松版）", "DAC 0.45 + 去耦 0.44 + 数字 0.315；对标成电 core 0.7–1.0 见 area_vs_cicc", "估算值；不含 pad ring。")
    return fig, (W, 78)


def f39(D):
    names = ["本工作\n(模型)", "Bannon\nVLSI14", "Steensgaard\nISSCC22", "Bodnar\nISSCC24", "Huang\nJSSC25"]
    fom = [187.8, 177.7, 184.1, 186.0, 178.0]; dr = [102.5,100.2,106.3,94.2,95.0]
    fig, ax = canvas(78); x = np.arange(len(names)); ax.bar(x, fom, .5, color=[CAAZ]+[BASE]*(len(names)-1))
    for i, v in enumerate(fom): ax.text(i, v+.5, f"{v:.1f}", ha="center", fontsize=6.2)
    ax.set(xticks=x, xticklabels=names, ylabel="FoMs（dB）", ylim=(170,192)); ax.grid(alpha=.26, axis="y")
    viz.annotate(fig, "FoM 对标：本工作的位置", "187.8 dB @100 kHz；比 Bannon 高 10 dB，比 Steensgaard 高 3.7 dB", "论文 Table I；本工作为目标值，不是实测。")
    return fig, (W, 78)


def f40(D):
    names = ["kT/C", "RA", "AZ", "Cmp", "Ref", "合计"]; vals = [P.ktc, P.ra_broad/np.sqrt(2.5), P.ra_az, P.cmp, P.ref]
    rss = np.sqrt(np.sum(np.array(vals)**2)); cum = np.cumsum(np.array(vals)**2); cum = np.sqrt(cum)
    fig, ax = canvas(80); x = np.arange(len(names)); ax.bar(x, np.r_[np.array(vals), rss]*1e6, .5, color=["#B5D4F4","#7FB3D5","#F5B7B1","#C39BD3","#A9DFBF", NEUTRAL])
    ax.set(xticks=x, xticklabels=names, ylabel="μVrms"); ax.grid(alpha=.26, axis="y")
    viz.annotate(fig, "误差瀑布：五项 RSS 到 26.5 μV", "不是线性相加；合计 26.5 μV 到 DR 102.5 dB", "按参数表；未含参考 droop/抖动。")
    return fig, (W, 80)


def f41(D):
    names = ["CAAZ", "M=8", "C_s 56 pF", "RA 电流 +50%", "skew 0.5 ps"]
    gain = [0.6, 1.7, 0.6, 0.8, 1.0]
    fig, ax = canvas(76); ax.barh(names[::-1], gain[::-1], color=[BASE, CAAZ, "#7FB3D5", GOOD, WARN][::-1])
    ax.set(xlabel="DR 改善（dB，估算）"); ax.grid(alpha=.26, axis="x")
    viz.annotate(fig, "设计杠杆的性价比：先做哪个", "M=8 与 skew/校准最值钱；CAAZ 只有 0.6 dB，加大电容只有 0.6 dB", "估算/模型；杠杆之间不完全独立。")
    return fig, (W, 76)


FIGS = [
    ("fig01_caaz_freq", f01, 146, 78), ("fig02_caaz_az_share", f02, 146, 76),
    ("fig03_caaz_unique_vs_share", f03, 146, 76), ("fig04_caaz_rate_tradeoff", f04, 146, 78),
    ("fig05_caaz_sinc", f05, 146, 76), ("fig06_caaz_noise_budget", f06, 146, 80),
    ("fig07_caaz_spectrum", f07, 146, 80),
    ("fig08_tracking_M", f08, 146, 76), ("fig09_tracking_F_vs_rho", f09, 146, 78),
    ("fig10_tracking_rho_sweep", f10, 146, 76), ("fig11_tracking_autocorr", f11, 146, 74),
    ("fig12_tracking_gain_vs_M", f12, 146, 76), ("fig13_caaz_tracking_matrix", f13, 146, 78),
    ("fig14_speed_compare", f14, 146, 78), ("fig15_skew_dr_sfdr", f15, 146, 80),
    ("fig16_skew_dr", f16, 146, 76), ("fig17_gain_sweep", f17, 146, 78),
    ("fig18_offset_sweep", f18, 146, 76), ("fig19_shuffle_bar", f19, 146, 78),
    ("fig20_spur_spectrum", f20, 146, 82), ("fig21_slice_timeline", f21, 146, 92),
    ("fig22_slice_util", f22, 146, 76),
    ("fig23_inl_raw_cal", f23, 146, 86), ("fig24_dnl_raw_cal", f24, 146, 82),
    ("fig25_inl_vs_sigma", f25, 146, 78), ("fig26_coef_precision", f26, 146, 76),
    ("fig27_dnl_hist", f27, 146, 76), ("fig28_inl_gradient", f28, 146, 74),
    ("fig29_cal_points", f29, 146, 74),
    ("fig30_noise_budget", f30, 146, 78), ("fig31_dr_vs_cap", f31, 146, 76),
    ("fig32_jitter_sndr", f32, 146, 76), ("fig33_ref_droop", f33, 146, 76),
    ("fig34_settling", f34, 146, 76), ("fig35_ref_ripple_inl", f35, 146, 74),
    ("fig36_timing", f36, 146, 70), ("fig37_power", f37, 146, 74),
    ("fig38_area", f38, 146, 78), ("fig39_fom", f39, 146, 78),
    ("fig40_error_waterfall", f40, 146, 80), ("fig41_design_levers", f41, 146, 76),
]


def main():
    res = _res()
    D = {"res": res, "curves": static.curves(10, 0.002, 7)}
    OUT.mkdir(parents=True, exist_ok=True)
    font = viz.chinese_style()
    outputs, dims = [], []
    for name, fn, w, h in FIGS:
        fig, _ = fn(D)
        paths = viz.save(fig, OUT / name)
        outputs += paths; dims.append((w, h)); plt.close(fig)
    viz.write_manifest(OUT, script=Path(__file__), data=[RES / "results.json"],
                       outputs=outputs, dims=dims, font=font,
                       extra={"figure_count": len(FIGS), "note": "模型图；绝对指标未标定，不可签核"})
    print(f"wrote {len(FIGS)} figures / {len(outputs)} files to {OUT}")


if __name__ == "__main__":
    main()
