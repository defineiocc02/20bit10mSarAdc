# [CODE-INDEX] spectrum.py —— 动态指标（规范 §11.1）
#
# 口径：相干采样 + 矩形窗；fin 必须落在整数 bin，否则直接报错（不猜基波）。
# 输出：SNR / SNDR / SFDR(dBc) / THD / ENOB，并给 PSD 积分交叉检查。
# 注意：本模块只做计算，不画图；绘图由 plotting 读已保存数据完成。
"""FFT 指标与 PSD 交叉验证。"""

from __future__ import annotations

import numpy as np


def fft_metrics(x: np.ndarray, fs: float, fin: float, *, n_harm: int = 10,
                strict: bool = True) -> dict:
    """矩形窗相干 FFT 指标。

    DR 不再直接命名信号/噪声比 —— 这里只给 SNR/SNDR；DR 需在 analysis.noise 里
    用固定满量程基准与规定带宽单独算。
    """
    x = np.asarray(x, float)
    n = len(x)
    k_exact = fin * n / fs
    if abs(k_exact - round(k_exact)) > 1e-6:
        msg = (f"fin={fin:.6g} Hz 不在整数 bin（{k_exact:.4f}）：矩形窗会泄漏，"
               f"先吸附到 {round(k_exact)*fs/n:.6g} Hz")
        if strict:
            raise ValueError(msg)
    k0 = int(round(k_exact))

    xc = x - x.mean()
    spec = np.abs(np.fft.rfft(xc)) / (n / 2)
    p = spec ** 2

    def band(k, h=2):
        lo, hi = max(0, k - h), min(len(p) - 1, k + h)
        return float(p[lo:hi + 1].sum())

    psig = band(k0)

    harms, seen = [], {k0}
    for h in range(2, n_harm + 1):
        kh = int(round(h * fin * n / fs))
        kh = kh % n
        if kh > n // 2:
            kh = n - kh           # 折叠到 Nyquist 内
        if 2 < kh < n // 2 and kh not in seen:
            harms.append(kh); seen.add(kh)
    pharm = sum(band(kh) for kh in harms)

    mask = np.ones(len(p), bool)
    mask[:3] = False
    for k in seen:
        mask[max(0, k - 2):min(len(p), k + 3)] = False
    pnoise = float(p[mask].sum())

    q = p.copy(); q[:3] = 0; q[max(0, k0 - 2):k0 + 3] = 0
    kspur = int(np.argmax(q)); pspur = float(q[kspur])

    db = lambda a, b: 10 * np.log10(max(a, 1e-30) / max(b, 1e-30))
    snr = db(psig, pnoise)
    sndr = db(psig, pnoise + pharm)
    sfdr = db(psig, pspur)
    thd = db(pharm, psig)
    enob = (sndr - 1.76) / 6.02

    return dict(snr_db=float(snr), sndr_db=float(sndr), sfdr_dbc=float(sfdr),
                thd_dbc=float(thd), enob_bit=float(enob),
                fin_actual_hz=float(k0 * fs / n), bin=k0,
                spur_bin=int(kspur), n_harm=len(harms), n_fft=n)


def psd_check(x: np.ndarray, fs: float, *, nperseg: int | None = None) -> dict:
    """用 SciPy periodogram 做独立 PSD 积分，与 FFT 路径交叉检查总功率。"""
    from scipy.signal import periodogram
    x = np.asarray(x, float)
    # periodogram 是对整段做一次 FFT，没有 nperseg（那是 welch 的参数）
    f, pxx = periodogram(x - x.mean(), fs=fs, window="boxcar",
                         detrend=False, scaling="density")
    df = f[1] - f[0]
    total_psd = float(np.sum(pxx) * df)          # V^2
    total_time = float(np.mean((x - x.mean()) ** 2))  # V^2（Parseval）
    rel = abs(total_psd - total_time) / max(total_time, 1e-30)
    return dict(total_psd_v2=total_psd, total_time_v2=total_time,
                parseval_rel_err=float(rel), df_hz=float(df))
