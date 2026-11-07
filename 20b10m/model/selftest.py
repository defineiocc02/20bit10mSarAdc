# [CODE-INDEX] selftest.py —— 4 项自检
# 运行：python3 -m model.selftest
# 检查：纯正弦 DR、tracking 方差 vs 解析 F、CAAZ AZ 抵消、静态理想 INL。
"""自检：抓建模错误，不依赖外部仿真器。"""
import numpy as np
from .params import P
from .sources import tracking_noise
from .metrics import fft_metrics
from .adc import simulate
from . import static

def check(name, cond, detail=""):
    print(f"[{'PASS' if cond else 'FAIL'}] {name} {detail}")
    return cond

def main():
    ok = True
    # 1) 纯正弦 FFT：DR 应 >120 dB
    t = np.arange(P.n)/P.fs
    fin = round(100e3*P.n/P.fs)*P.fs/P.n
    s = P.amp*np.sin(2*np.pi*fin*t)
    m = fft_metrics(s, P.fs, fin)
    ok &= check("纯正弦 DR", m["DR_dB"] > 120, f"{m['DR_dB']:.1f} dB")

    # 2) tracking 噪声：方差应等于 sigma^2 * F(AR1)
    M, rho, sig = 8, 0.61, 1.0
    rng = np.random.default_rng(1)
    x = tracking_noise(200000, M, rho, sig, rng)
    F = 1/M + 2/(M*M)*sum((M-k)*rho**k for k in range(1, M))
    ok &= check("tracking 方差", abs(x.var()/F - 1) < 0.02, f"emp/F={x.var()/F:.3f}, F={F:.3f}")

    # 3) CAAZ AZ 抵消：只留 AZ，share=1 时输出差应≈0
    rng = np.random.default_rng(2)
    az = rng.normal(0, 1e-3, 20000)
    xe = az[0::2]; xo = az[0::2]           # share=1
    d1 = (xe - xo).std()
    xo2 = az[1::2]                          # share=0
    d0 = (xe - xo2).std()
    ok &= check("CAAZ AZ 抵消", d1 < 1e-12 and d0 > 1e-4, f"share1={d1:.2e}, share0={d0:.2e}")

    # 4) 静态理想权重：INL/DNL 应≈0
    w = 2.0**np.arange(10)
    inl, dnl, _ = static.inl_dnl_v(static.transfer(w))
    ok &= check("静态理想", np.max(np.abs(inl)) < 1e-9 and np.max(np.abs(dnl)) < 1e-9,
                f"INL={np.max(np.abs(inl)):.2e}")

    print("RESULT:", "ALL PASS" if ok else "HAS FAILURE")
    return ok

if __name__ == "__main__":
    main()
