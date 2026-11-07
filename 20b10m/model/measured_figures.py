"""measured_figures.py —— 按 20b10mtask 的频谱/INL-DNL 画法重做

对齐参考：
- `task2/eight/plots.py::_spectra`：2×2 面板、单音谱线、杂散圆点、SNDR/SFDR 框、146×111 mm。
- `task1/experiments/full20_linearity_plots.py::_linearity/_band`：3×2、每 1024 码 min/max 包络、
  中码放大、OFF/ON 双色、146×155 mm。

运行：cd 20b10m && python3 -m model.measured_figures
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

from .params import P
from .adc import simulate
from .metrics import fft_metrics
from . import static, viz
from .charge_model import dac1_curves

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "model/results"
OUT = RES / "figures_measured"
OFF, ON, WARN = "#626C75", "#0072B2", "#D55E00"
W, MM = 146, viz.MM
N_FFT = 65536
N_CODES = 1 << 20
STEP = 1024
LSB20_PPM = 1e6 / 2**20          # 1 LSB20 = 0.9537 ppm FS



def _plain_ticks(ax, axis="x", vals=None, fmt="{:g}"):
    """对数轴用固定刻度 + 纯文本标签：避免 mathtext 的 10^{-1} 走 \\mathdefault
    找不到字形（实测会打出一串 dummy glyph 告警）。"""
    vals = list(vals)
    labels = [fmt.format(v) for v in vals]
    if axis == "x":
        ax.set_xticks(vals); ax.set_xticklabels(labels)
    else:
        ax.set_yticks(vals); ax.set_yticklabels(labels)
    ax.minorticks_off()


def _spectrum(fin, fs=10e6, caaz=False, seed=11, dac_inl=None):
    n = N_FFT
    fc = round(fin * n / fs) * fs / n
    x, _ = simulate(fc, fs=fs, n=n, caaz=caaz, seed=seed, dac_inl=dac_inl)
    spec = np.abs(np.fft.rfft(x - x.mean())) / (n / 2)
    p = spec**2
    k0 = int(round(fc * n / fs))
    q = p.copy(); q[:4] = 0; q[max(0, k0 - 3):k0 + 4] = 0
    kspur = int(np.argmax(q))
    db = 20 * np.log10(np.maximum(spec / (P.fs_diff / 2), 1e-12))
    m = fft_metrics(x, fs, fc)
    return np.fft.rfftfreq(n, 1 / fs) / 1e6, db, kspur, m


def spec_grid(D):
    """DAC1 静态 INL 未校准 / 每段校准后，两个输入频率。"""
    got = {}
    fig, axes = plt.subplots(2, 2, figsize=(W / MM, 111 / MM), sharex=True, sharey=True)
    fig.subplots_adjust(left=.112, right=.975, top=.79, bottom=.17, hspace=.55, wspace=.2)
    cols = ((100e3, "100 kHz"), (2e6, "2 MHz"))
    rows = (("raw", "未校准（DAC1 INL 16.4 ppm）", WARN),
            ("cal", "每段权校准后（残余 0.29 ppm）", ON))
    for row, (inl, arm, col_) in enumerate(rows):
        for col, (fin, lab) in enumerate(cols):
            f, db, kspur, m = _spectrum(fin, dac_inl=inl)
            got[(inl, fin)] = m
            ax = axes[row, col]
            ax.plot(f, db, lw=.45, color=col_)
            ax.plot(f[kspur], db[kspur], "o", ms=2.8, color=col_, mec="white", mew=.35)
            ax.set(title=f"{arm}｜{lab}", xlim=(0, 5), ylim=(-176, 2))
            txt = (f"SNDR {m['SNDR_dB']:.1f} dB\nSFDR {m['SFDR_dBc']:.1f} dBc" if inl == "raw"
                   else f"SNDR {m['SNDR_dB']:.1f} dB\nSFDR：模型无失真项")
            ax.text(.97, .90, txt, transform=ax.transAxes, ha="right", va="top", fontsize=6.4,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=.85, pad=1.0))
            ax.grid(alpha=.23)
        axes[row, 0].set_ylabel("幅度（dBFS）")
    for ax in axes[1]:
        ax.set_xlabel("频率（MHz）")
    viz.annotate(fig, "DAC1 静态误差对输出频谱的影响",
                 "10 MS/s、65536 点相干采样、矩形窗；圆点为最大杂散",
                 f"模型生成：未校准 SNDR {got[('raw',100e3)]['SNDR_dB']:.1f} dB／SFDR {got[('raw',100e3)]['SFDR_dBc']:.1f} dBc，"
                 f"校准后回到噪声底 {got[('cal',100e3)]['SNDR_dB']:.1f} dB。\n"
                 "校准后残余为噪声型（不产生杂散），故 SFDR 高估；实测受基准建立/电荷注入限制，预期 100–110 dBc。")
    return fig, (W, 111)


def caaz_grid(D):
    """CAAZ 开/关：左=2 MHz 处的谱叠加，右=噪声底差值随频率。"""
    fig, axes = plt.subplots(1, 2, figsize=(W / MM, 80 / MM))
    fig.subplots_adjust(left=.105, right=.975, top=.70, bottom=.235, wspace=.32)
    ax = axes[0]
    for caaz, c, tag in ((False, OFF, "CAAZ off"), (True, ON, "CAAZ on")):
        f, db, kspur, m = _spectrum(2e6, caaz=caaz, dac_inl="cal")
        ax.plot(f, db, lw=.40, color=c, alpha=.85, label=f"{tag}：SNDR {m['SNDR_dB']:.1f} dB")
    ax.set(title="2 MHz 输入：噪声底叠加", xlim=(0, 5), ylim=(-172, -120))
    ax.legend(fontsize=5.8, loc="upper left", handlelength=1.2, frameon=True,
              framealpha=.9, edgecolor="none", borderpad=.25)
    ax.set_ylabel("幅度（dBFS）"); ax.set_xlabel("频率（MHz）"); ax.grid(alpha=.23)
    # 右：逐 bin 差，滑动中值平滑
    ax = axes[1]
    for fin, c, lab in ((100e3, OFF, "100 kHz"), (2e6, ON, "2 MHz")):
        _, d0, _, _ = _spectrum(fin, caaz=False, dac_inl="cal")
        _, d1, _, _ = _spectrum(fin, caaz=True, dac_inl="cal")
        d = d0 - d1
        k = 401
        sm = np.convolve(d, np.ones(k)/k, mode="same")[k:-k]
        fq = np.fft.rfftfreq(N_FFT, 1/10e6)[k:-k] / 1e6
        ax.plot(fq, sm, lw=.9, color=c, label=f"{lab}（均值 {sm[200:-200].mean():+.2f} dB）")
    ax.set(title="噪声底改善量", xlabel="频率（MHz）", ylabel="CAAZ off − on（dB）",
           xlim=(0, 5), ylim=(2.1, 5.6))
    ax.grid(alpha=.23)
    ax.legend(fontsize=5.8, loc="lower center", ncol=2, handlelength=1.1, frameon=True,
              framealpha=.92, edgecolor="none", borderpad=.25)
    viz.annotate(fig, "CAAZ 的净收益：噪声底压低多少",
                 "同一随机种子、同一输入；逐 bin 相减后 401 点滑动中值",
                 "含 3 dB 通用平均；独家 AZ 抵消只有 0.61 dB —— 宣传值不能全算在 CAAZ 头上。")
    return fig, (W, 80)


def cal_sweep(D):
    """把 DAC1 INL 按比例压下去，看 SNDR/SFDR 怎么回到噪声底 —— 校准精度的设计规则。"""
    from .charge_model import inl_profile
    codes, prof = inl_profile("raw")
    peak0 = float(np.max(np.abs(prof))) * 1e6 / P.fs_diff
    scales = np.array([1.0, .5, .3, .2, .1, .05, .02, .01, .003])
    snr, sfdr, res = [], [], []
    for s in scales:
        _, _, _, m = _spectrum(100e3, dac_inl=(codes, prof * s))
        snr.append(m["SNDR_dB"]); sfdr.append(m["SFDR_dBc"]); res.append(peak0 * s)
    _, _, _, m0 = _spectrum(100e3, dac_inl=None)
    fig, ax = plt.subplots(figsize=(W / MM, 84 / MM))
    fig.subplots_adjust(left=.115, right=.965, top=.78, bottom=.20)
    ax.semilogx(res, sfdr, "o-", ms=2.6, lw=.9, color=OFF, label="SFDR（dBc）")
    ax.semilogx(res, snr, "s-", ms=2.4, lw=.9, color=ON, label="SNDR（dB）")
    ax.axhline(m0["SNDR_dB"], color=ON, lw=.6, ls=":", alpha=.8)
    ax.axhline(m0["SFDR_dBc"], color=OFF, lw=.6, ls=":", alpha=.8)
    ax.text(res[-1]/1.15, m0["SNDR_dB"] + .5, f"噪声底 {m0['SNDR_dB']:.1f} dB（零 INL）",
            fontsize=5.8, color=ON, ha="left", va="bottom")
    ax.set(xlabel="DAC1 残余 INL（ppm FS，峰值）", ylabel="dB", xlim=(res[-1]/1.3, res[0]*1.3))
    _plain_ticks(ax, "x", [16, 8, 4, 2, 1, .5, .25, .1, .05])
    ax.grid(alpha=.23, which="both"); ax.legend(frameon=False, fontsize=6.4, loc="lower left")
    viz.annotate(fig, "校准精度的设计规则：残余 INL 要压到多少",
                 f"横轴为峰值残余 INL；点线是零 INL 的噪声底（SNDR {m0['SNDR_dB']:.1f}／SFDR {m0['SFDR_dBc']:.0f}）",
                 "判据：残余 ≤1.5 ppm → SNDR 在噪声底 0.5 dB 内；≤0.5 ppm → SFDR ≥128 dBc，不再是瓶颈。")
    return fig, (W, 84)


def _linearity_arrays(n_avg=16):
    """DAC1 10 bit 电荷域曲线；INL/DNL 换到 ppm FS。

    校准后用「有限样本」残差（每码平均 n_avg 次、单次 σ=2.8 LSB20），
    而不是理想的 0 —— 理想 0 是特征张成的数学假象，不可对外声称。
    """
    from .charge_model import cal_residual
    c = dac1_curves()
    ppm = 1e6 / 1024.0          # 1 LSB1 = 976.56 ppm FS
    pk, env = cal_residual(n_avg=n_avg)
    rng = np.random.default_rng(101)
    signed_env = np.where(rng.random(1024) < .5, -1.0, 1.0) * env
    # 校准后剩下的就是残差本身（拟合权重减真权重），不是 raw 再加残差
    inl_cal = signed_env - signed_env.mean()
    dnl_cal = np.diff(np.arange(1024) + inl_cal) - 1.0
    return (c["code"], c["inl_raw"]*ppm, inl_cal*ppm,
            c["dnl_raw"]*ppm, dnl_cal*ppm, pk*ppm)


def inl_dnl_20b(D):
    code, inl_raw, inl_cal, dnl_raw, dnl_cal, pk_cal = _linearity_arrays()
    signed = code - 512
    fig, axes = plt.subplots(3, 2, figsize=(W / MM, 155 / MM))
    fig.subplots_adjust(left=.115, right=.972, top=.845, bottom=.125, hspace=.80, wspace=.34)
    cols = ((False, "未校准", WARN), (True, f"校准后（n=16，残差 {pk_cal:.2f} ppm）", ON))
    for col, (cal, label, color) in enumerate(cols):
        dnl = dnl_cal if cal else dnl_raw
        inl = inl_cal if cal else inl_raw
        a0, a1 = axes[0, col], axes[1, col]
        a0.step(signed[1:], dnl, where="post", color=color, lw=.7)
        a1.step(signed, inl, where="post", color=color, lw=.7)
        a0.set(title=label)
        # 数值塞进面板内，避免标题被右边框裁掉
        a0.text(.03, .95, f"DNL [{dnl.min():+.2f}, {dnl.max():+.2f}] ppm",
                transform=a0.transAxes, ha="left", va="top", fontsize=6.2, color=color,
                bbox=dict(facecolor="white", edgecolor="none", alpha=.88, pad=1.0))
        a1.set(title=f"峰值 |INL| = {np.max(np.abs(inl)):.2f} ppm")
        for a, y in ((a0, dnl), (a1, inl)):     # 每列独立纵轴，否则校准后是一根零线
            lo, hi = float(np.min(y)), float(np.max(y)); pad = .10*(hi-lo+1e-12)
            a.set(ylim=(lo-pad, hi+pad))
    # 第三行左：中码 32 码放大，两条曲线叠画
    mid, zoom = 512, np.arange(-16, 17)
    axes[2, 0].step(zoom, dnl_raw[mid + zoom - 1], where="post", color=WARN, lw=.8, label="未校准")
    axes[2, 0].step(zoom, dnl_cal[mid + zoom - 1], where="post", color=ON, lw=.9, label="校准后")
    axes[2, 0].set(xlim=(-16, 16), xticks=[-16, -8, 0, 8, 16], xlabel="相对中码（码）")
    axes[2, 0].legend(handles=[plt.Line2D([], [], color=WARN, lw=.9, label="未校准"),
                               plt.Line2D([], [], color=ON, lw=1.1, label="校准后")],
                      frameon=True, framealpha=.9, edgecolor="none",
                      fontsize=5.8, loc="upper left", handlelength=1.1, borderpad=.25)
    # 第三行右：残差 vs 每码平均次数（校准精度的设计规则）
    ns = np.array([1, 4, 16, 64, 256, 1024, 4096])
    pks = [_linearity_arrays(n)[5] for n in ns]
    axes[2, 1].loglog(ns, pks, "o-", ms=2.8, lw=.9, color=ON, label="模型（σ=2.8 LSB20）")
    axes[2, 1].loglog(ns, pks[0]/np.sqrt(ns/ns[0]), ":", lw=.8, color=OFF, label="1/√n 参考")
    axes[2, 1].axhline(1.5, color=WARN, lw=.7, ls="--")
    axes[2, 1].text(4300, 1.62, "1.5 ppm：SNDR 落入噪声底 0.5 dB 内",
                    fontsize=5.8, color=WARN, ha="right", va="bottom")
    axes[2, 1].set(xlabel="每码平均次数 n", ylabel="峰值残余 INL（ppm FS）")
    _plain_ticks(axes[2, 1], "x", [1, 4, 16, 64, 256, 1024, 4096])
    _plain_ticks(axes[2, 1], "y", [.05, .1, .2, .5, 1, 2])
    axes[2, 1].legend(frameon=False, fontsize=6.0, loc="lower left")
    for row, ylab in ((0, "DNL（ppm FS）"), (1, "INL（ppm FS）")):
        axes[row, 0].set_ylabel(ylab)
    axes[2, 0].set_ylabel("DNL（ppm FS）")
    for ax in axes.flat:
        ax.grid(alpha=.26, which="both")
    viz.annotate(fig, "DAC1 10 bit 电荷域 DNL／INL（8 unary 片 × 128 单位，σu=0.2%）",
                 "上两行：全 1024 码；左下：中码 ±16 码放大；右下：校准残余随平均次数的收敛",
                 "只含电容失配。校准残余由测量噪声决定（∝1/√n），不是算法极限；"
                 "实际还受寄生/电荷注入/基准建立限制，模型未含，故不给绝对 INL 承诺。")
    return fig, (W, 155)


def dr_curve(D):
    """SNDR vs 输入幅度：三条曲线说明"失真限制"与"校准把它修掉"。"""
    amps = np.arange(-60, 1, 5)
    fc = round(100e3*N_FFT/10e6)*10e6/N_FFT     # 必须相干，否则泄漏把 DR 打崩
    cfgs = ((None, OFF, "理想（无静态误差）"), ("raw", WARN, "未校准 DAC1"),
            ("cal", ON, "校准后"))
    curves = {}
    for tag, _c, _lab in cfgs:
        ys = []
        for a in amps:
            old = P.amp; P.amp = 4.8*10**(a/20)
            try:
                m = fft_metrics(simulate(fc, fs=10e6, n=N_FFT, seed=21, dac_inl=tag)[0], 10e6, fc)
            finally:
                P.amp = old
            ys.append(m["SNDR_dB"])
        curves[tag] = np.array(ys)
    fig, ax = plt.subplots(figsize=(W/MM, 90/MM))
    fig.subplots_adjust(left=.115, right=.965, top=.775, bottom=.19)
    for tag, c, lab in cfgs:
        ax.plot(amps, curves[tag], "o-", ms=2.4, lw=.9, color=c, label=lab)
    ax.set(xlabel="输入幅度（dBFS）", ylabel="SNDR（dB）", xlim=(-60, 10))
    ax.grid(alpha=.23); ax.legend(frameon=False, fontsize=6.2, loc="lower right")
    # 满量程处的差值直接用竖线标出来，比拉一条跨图的箭头干净
    gap = curves["cal"][-1] - curves["raw"][-1]
    ax.plot([0, 0], [curves["raw"][-1], curves["cal"][-1]], color=WARN, lw=.9)
    ax.text(1.2, (curves["raw"][-1] + curves["cal"][-1])/2, f"{gap:.1f} dB",
            color=WARN, fontsize=6.2, va="center")
    ax.text(1.2, curves["raw"][-1] - 2.2, "未校准", color=WARN, fontsize=5.8, va="center")
    viz.annotate(fig, "SNDR vs 输入幅度：校准把顶端的塌陷抬平",
                 "未校准在大信号端被 DAC1 静态非线性压住；校准后一路到 0 dBFS 都是噪声底",
                 "模型无抖动/无建立误差，高频与满量程端仍偏乐观；DR 取满量程 SNDR。")
    return fig, (W, 90)


def sndr_fin(D):
    """SNDR vs 输入频率：时钟抖动是高频端的唯一下降机制。"""
    fins = [6e3, 30e3, 100e3, 300e3, 1e6, 2e6, 3e6]
    res = {}
    for jt, c, lab in ((0.0, OFF, "理想时钟"), (1e-12, ON, "σt = 1 ps")):
        ys = []
        for f in fins:
            fc = round(f*N_FFT/10e6)*10e6/N_FFT
            ys.append(fft_metrics(simulate(fc, fs=10e6, n=N_FFT, seed=31,
                                           dac_inl="cal", jitter=jt)[0], 10e6, fc)["SNDR_dB"])
        res[lab] = np.array(ys)
        ax = None
    fig, ax = plt.subplots(figsize=(W/MM, 86/MM))
    fig.subplots_adjust(left=.115, right=.965, top=.775, bottom=.195)
    for jt, c, lab in ((0.0, OFF, "理想时钟"), (1e-12, ON, "σt = 1 ps")):
        ax.semilogx(np.array(fins)/1e3, res[lab], "o-", ms=2.6, lw=.9, color=c, label=lab)
    ax.ticklabel_format(axis="y", useOffset=False)
    ax.set(xlabel="输入频率（kHz）", ylabel="SNDR（dB）")
    ax.grid(alpha=.23, which="both"); ax.legend(frameon=False, fontsize=6.2, loc="lower left")
    _plain_ticks(ax, "x", [6, 30, 100, 300, 1000, 2000])
    ax.text(6, res["σt = 1 ps"][0] - 2.6,
            f"2 MHz 处抖动限制 {20*np.log10(1/(2*np.pi*2e6*1e-12)):.1f} dB",
            fontsize=6.0, color=ON)
    viz.annotate(fig, "SNDR vs 输入频率：抖动决定高频端",
                 "理想时钟下 SNDR 与频率无关；加 1 ps 抖动后按 20log(2πfσt) 滚降",
                 "模型只含抖动，未含采样网络带宽/RA 建立；实测高频还会再低一些。")
    return fig, (W, 86)


def noise_breakdown(D):
    """噪声功率分解：基线 / 8× tracking / +CAAZ，三档都归一化到 100%。"""
    import numpy as np
    sig = np.array([P.ktc, P.ra_broad, P.ra_az, np.hypot(P.cmp, P.ref)])
    names = ["采样 kT/C", "RA 宽带", "RA AZ", "比较器+基准"]
    cols = ["#B5D4F4", "#7FB3D5", "#F5B7B1", "#C3B1E1"]
    F = 0.393                     # AR(1) 下 8× 平均的残留功率比（selftest 实测）
    caaz_avg = 0.5                # 两点平均：全部噪声功率减半
    caaz_az = 1 / 10**(0.58/10)   # AZ 抵消的独家收益 0.58 dB
    stage = [sig**2,
             np.array([sig[0]**2, sig[1]**2*F, sig[2]**2, sig[3]**2]),
             np.array([sig[0]**2*caaz_avg, sig[1]**2*F*caaz_avg,
                       sig[2]**2*caaz_az*caaz_avg, sig[3]**2*caaz_avg])]
    fig, ax = plt.subplots(figsize=(W/MM, 92/MM))
    fig.subplots_adjust(left=.115, right=.965, top=.755, bottom=.20)
    x = np.arange(3); bottom = np.zeros(3)
    for k, (n, c) in enumerate(zip(names, cols)):
        v = np.array([100*st[k]/st.sum() for st in stage])
        ax.bar(x, v, .5, bottom=bottom, color=c, edgecolor="white", lw=.5, label=n)
        for i, (vv, bb) in enumerate(zip(v, bottom)):
            if vv > 6:
                ax.text(i, bb+vv/2, f"{vv:.0f}", ha="center", va="center", fontsize=6.2)
        bottom += v
    tot = np.array([np.sqrt(st.sum()) for st in stage])   # V
    ax.set(xticks=x, xticklabels=["基线", "8× tracking", "+CAAZ"],
           ylabel="噪声功率占比（%，归一化）", ylim=(0, 108))
    ax.grid(alpha=.23, axis="y"); ax.legend(frameon=False, fontsize=6.2, ncol=4,
                                            loc="upper center", bbox_to_anchor=(.5, 1.14))
    viz.annotate(fig, "噪声分解：做完 tracking 之后，kT/C 变成第一项",
                 f"输入折算噪声 {tot[0]*1e6:.1f} → {tot[1]*1e6:.1f} → {tot[2]*1e6:.1f} µV；"
                 f"对应 SNDR {20*np.log10(3.536/tot[0]):.1f} → "
                 f"{20*np.log10(3.536/tot[1]):.1f} → {20*np.log10(3.536/tot[2]):.1f} dB",
                 "RA 宽带按 AR(1) 残留 0.393 折；CAAZ 按两点平均 ×0.5 再加 AZ 独家 0.58 dB。\n"
                 "结论：tracking 之后该加 C_s，而不是继续堆平均次数。")
    return fig, (W, 92)


def _cal_gain():
    _, _, _, m0 = _spectrum(100e3, dac_inl="raw")
    _, _, _, m1 = _spectrum(100e3, dac_inl="cal")
    return m1["SNDR_dB"] - m0["SNDR_dB"], m0["SNDR_dB"], m1["SNDR_dB"]


def tech_rank(D):
    dcal, s0, s1 = _cal_gain()
    tech=[(f"DAC1 位权校准（SNDR {s0:.1f}→{s1:.1f}）",dcal,3),
          ("级间增益校准 50→10 ppm",4.89,2),("CAAZ（10 MS/s 输出）",3.58,5),
          ("skew ≤0.5 ps（2 MHz）",1.72,3),("8× tracking",1.71,3),
          ("C_s 28→56 pF",0.99,4),("CAAZ 独家（AZ 抵消）",0.61,5),
          ("RA 电流 +50%（ρ 0.61→0.45）",0.40,4),("交织 5→10 MS/s",0.0,2),
          ("洗牌（SFDR +18.8 dB）",-2.09,1)]
    tech=sorted(tech,key=lambda x:x[1])
    names=[t[0] for t in tech]; vals=[t[1] for t in tech]
    fig,ax=plt.subplots(figsize=(W/MM,105/MM)); fig.subplots_adjust(left=.46,right=.965,top=.80,bottom=.16)
    colors=[WARN if v<-0.5 else (OFF if abs(v)<.05 else ON) for v in vals]
    ax.barh(names,vals,color=colors,height=.58)
    for i,v in enumerate(vals):
        ax.text(v+(.08 if v>=0 else -.08),i,f"{v:+.2f}",va="center",ha="left" if v>=0 else "right",fontsize=6.2)
    ax.axvline(0,color="#333333",lw=.6); ax.set(xlabel="ΔSNDR（dB，100 kHz / 10 MS/s）",xlim=(-3.2,8.6)); ax.grid(alpha=.22,axis="x")
    viz.annotate(fig,"各技术的有效性：ΔSNDR 排序",
                 "校准类收益最大（它决定误差预算而不是噪声）；CAAZ 次之；交织换速率不换精度",
                 "ΔSNDR 来自模型；CAAZ 含 3 dB 通用平均，独家仅 0.61 dB；洗牌 DR 略降但 SFDR +18.8 dB。")
    return fig,(W,105)


def tech_matrix(D):
    dcal, _s0, _s1 = _cal_gain()
    pts=[("DAC1 位权校准",dcal,3),("增益校准",4.89,2),("CAAZ",3.58,5),("skew",1.72,3),
         ("tracking",1.71,3),("C_s 56pF",0.99,4),("CAAZ 独家",0.61,5),("RA 电流",0.40,4),
         ("交织",0.0,1.5),("洗牌",-2.09,1)]
    fig,ax=plt.subplots(figsize=(W/MM,92/MM)); fig.subplots_adjust(left=.12,right=.965,top=.78,bottom=.18)
    for name,y,x in pts:
        ax.scatter(x,y,s=40,color=(WARN if y<-.5 else (OFF if abs(y)<.05 else ON)),zorder=3)
        ax.annotate(name,(x,y),textcoords="offset points",xytext=(5,4),fontsize=6.0)
    ax.axhline(0,color="#333333",lw=.6); ax.set(xlabel="实施代价（1 低 → 5 高）",ylabel="ΔSNDR（dB）",xlim=(.5,5.6),ylim=(-2.8,8.4)); ax.grid(alpha=.22)
    viz.annotate(fig,"技术取舍：收益 vs 代价","左上=高性价比（位权校准、级间增益校准）；右上=高收益高代价（CAAZ）；右下=负收益（洗牌 DR）",
                 "代价为 1–5 的主观分级；交织的收益在速率不在精度，见 TECH_EFFECTIVENESS.md。")
    return fig,(W,92)


FIGS=[("measured01_spectra",spec_grid,146,111),("measured02_inl_dnl",inl_dnl_20b,146,155),
      ("measured03_dr_curve",dr_curve,146,88),("measured04_sndr_fin",sndr_fin,146,84),
      ("measured05_noise_breakdown",noise_breakdown,146,88),
      ("measured06_tech_rank",tech_rank,146,105),("measured07_tech_matrix",tech_matrix,146,92),
      ("measured08_caaz_spectra",caaz_grid,146,74),("measured09_cal_rule",cal_sweep,146,84)]


def main():
    res=json.loads((RES/"results.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True,exist_ok=True); font=viz.chinese_style(); outs=[]; dims=[]
    for name,fn,w,h in FIGS:
        fig,_=fn({"res":res}); paths=viz.save(fig,OUT/name); outs+=paths; dims.append((w,h)); plt.close(fig)
    viz.write_manifest(OUT,script=Path(__file__),data=[RES/"results.json"],outputs=outs,dims=dims,font=font,
                       extra={"figure_count":len(FIGS),"note":"按 20b10mtask 的 _spectra/_linearity 画法；模型生成"})
    print(f"wrote {len(FIGS)} measured figures / {len(outs)} files")


if __name__=="__main__":
    main()
