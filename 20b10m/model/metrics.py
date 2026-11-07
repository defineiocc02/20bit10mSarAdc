# [CODE-INDEX] metrics.py —— FFT 指标（DR/SNDR/SFDR/THD）
# 口径：相干采样 + 矩形窗；fin 必须落在整数 bin（avg_metric 里已吸）。
# 信号功率取基波 ±2 bin；噪声去掉 DC/基波/前 10 次谐波；SFDR 取最大非基波峰。
"""FFT 指标：DR / SNDR / SFDR / THD。相干采样 + 矩形窗。"""
import numpy as np

def fft_metrics(x, fs, fin, n_harm=10, strict=True):
    """矩形窗 FFT 指标。strict=True 时强制 fin 落在整数 bin。

    矩形窗没有旁瓣抑制：fin 偏 0.25 bin 时 SNDR 会从 102 dB 掉到十几 dB
    （审计实测 13.76 dB），所以相干性是硬前置条件，不能靠调用方自觉。
    """
    x = np.asarray(x, float)
    n = len(x)
    k_exact = fin * n / fs
    if abs(k_exact - round(k_exact)) > 1e-9:
        if strict:
            raise ValueError(
                f"fin={fin:.6g} Hz 不在整数 bin（{k_exact:.4f} bin）：矩形窗会泄漏，"
                f"请先吸附到 {round(k_exact)*fs/n:.6g} Hz")
    x = x - x.mean()
    w = np.ones(n)
    spec = np.abs(np.fft.rfft(w * x)) / (n / 2)
    p = spec**2
    k0 = int(round(fin * n / fs))
    def band(k, h=2):
        lo, hi = max(0, k-h), min(len(p)-1, k+h)
        return p[lo:hi+1].sum()
    psig = band(k0)
    # 谐波
    harms = []
    for h in range(2, n_harm+1):
        kh = int(round(h * fin * n / fs))
        if kh < len(p)-2:
            harms.append(kh)
    pharm = sum(band(kh) for kh in harms)
    # 噪声：去掉 DC、基波、谐波
    mask = np.ones(len(p), bool)
    mask[:3] = False
    for k in [k0] + harms:
        mask[max(0,k-2):min(len(p),k+3)] = False
    pnoise = p[mask].sum()
    # SFDR：除基波外的最大峰
    q = p.copy(); q[:3] = 0; q[max(0,k0-2):k0+3] = 0
    kspur = int(np.argmax(q)); pspur = q[kspur]
    db = lambda a, b: 10*np.log10(max(a,1e-30)/max(b,1e-30))
    return {
        "DR_dB": db(psig, pnoise),
        "SNDR_dB": db(psig, pnoise + pharm),
        "SFDR_dBc": db(psig, pspur),
        "THD_dBc": db(pharm, psig),
        "fin_actual": k0 * fs / n,
        "spur_bin": kspur,
        "psig": psig,
    }
