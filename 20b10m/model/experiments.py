# [CODE-INDEX] experiments.py —— 全部实验入口
# 运行：cd 20b10m && python3 -m model.experiments
# 输出：model/results/results.json 与 report.md
# 覆盖：CAAZ（含 AZ 共享度）、M 扫描、部分交织（skew/失配/洗牌/增益）、静态 INL/DNL。
"""跑全部实验：CAAZ、交织、M 扫描、静态 INL/DNL。"""
import json, os
import numpy as np
from .params import P
from .adc import simulate
from .metrics import fft_metrics
from . import static

OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)

def avg_metric(fin, fs, seeds=4, **kw):
    rows = []
    n = P.n
    fin_c = round(fin*n/fs)*fs/n          # 相干采样：把 fin 吸到整数 bin
    for s in range(seeds):
        x, _ = simulate(fin_c, fs=fs, seed=100+s, **kw)
        rows.append(fft_metrics(x, fs, fin_c))
    return {k: float(np.mean([r[k] for r in rows])) for k in ("DR_dB","SNDR_dB","SFDR_dBc")}

def exp_caaz():
    out = []
    for fin in (100e3, 1e6, 2e6):
        base = avg_metric(fin, P.fs, caaz=False)
        caaz = avg_metric(fin, P.fs, caaz=True)
        out.append({"fin": fin, **{f"base_{k}":v for k,v in base.items()},
                    **{f"caaz_{k}":v for k,v in caaz.items()},
                    "dDR": caaz["DR_dB"]-base["DR_dB"],
                    "dSNDR": caaz["SNDR_dB"]-base["SNDR_dB"]})
    return out

def exp_caaz_az():
    out = []
    for share in (1.0, 0.7, 0.0):
        m = avg_metric(100e3, P.fs, caaz=True, az_share=share, seeds=4)
        out.append({"az_share": share, **m})
    base = avg_metric(100e3, P.fs, caaz=False, seeds=4)
    for r in out:
        r["dDR_vs_base"] = r["DR_dB"] - base["DR_dB"]
    return {"base": base, "rows": out}

def exp_tracking():
    out = []
    for M in (1,2,4,8):
        m = avg_metric(100e3, P.fs, M=M, seeds=3)
        out.append({"M": M, **m})
    return out

def exp_interleave():
    out = []
    # 5 MS/s 单通道基线
    base5 = avg_metric(100e3, 5e6, seeds=3)
    out.append({"case":"5MS/s single", **base5})
    # 10 MS/s 理想交织
    ideal = avg_metric(100e3, 10e6, seeds=3,
                       interleave=dict(gain=0, offset=0, skew=0))
    out.append({"case":"10MS/s ideal", **ideal})
    for skew in (0.5e-12, 1e-12, 2e-12, 4e-12):
        m = avg_metric(100e3, 10e6, seeds=3,
                       interleave=dict(gain=2e-5, offset=20e-6, skew=skew, shuffle=True))
        out.append({"case":f"10MS/s skew={skew*1e12:.1f}ps", "skew_ps":skew*1e12, **m})
    # 2 MHz 下扫 skew（100 kHz 时斜率太小，看不出）
    for skew in (0.5e-12, 1e-12, 2e-12):
        m = avg_metric(2e6, 10e6, seeds=3,
                       interleave=dict(gain=2e-5, offset=20e-6, skew=skew, shuffle=True))
        out.append({"case":f"10MS/s 2MHz skew={skew*1e12:.1f}ps", "skew_ps":skew*1e12, **m})
    # 不洗牌 vs 洗牌（100 kHz，失配为主）
    for sh in (False, True):
        m = avg_metric(100e3, 10e6, seeds=3,
                       interleave=dict(gain=5e-5, offset=50e-6, skew=1e-12, shuffle=sh))
        out.append({"case":f"10MS/s shuffle={sh}", "shuffle":sh, **m})
    # 2 MHz、1 ps skew 下洗牌对 SFDR 的影响
    for sh in (False, True):
        m = avg_metric(2e6, 10e6, seeds=3,
                       interleave=dict(gain=2e-5, offset=20e-6, skew=1e-12, shuffle=sh))
        out.append({"case":f"10MS/s 2MHz skew=1ps shuffle={sh}", "shuffle":sh, **m})
    # 增益失配扫描（100 kHz）
    for g in (1e-5, 5e-5, 1e-4):
        m = avg_metric(100e3, 10e6, seeds=3,
                       interleave=dict(gain=g, offset=0, skew=0, shuffle=True))
        out.append({"case":f"10MS/s gain={g*1e6:.0f}ppm", "gain_ppm":g*1e6, **m})
    return out

def exp_static():
    rows = []
    for sig in (0.001, 0.002, 0.004):
        rows.append(static.run(bits=10, unit_sigma=sig, seed=7))
    return rows

def exp_static_pools(n_pools=8, sigma=0.002):
    """多失配池扫描：把「单池一个数」变成分布（对齐 20b10mtask 的多制造 seed 纪律）。

    - 每个池独立 seed = 100+i、同 sigma；片选择仍取池内前 8 片（与 dac1_curves 一致）。
    - 同时报两种 INL 口径：best_fit（对码回归）与 endpoint（首尾连线）。
      两口径必须同时出现，否则跨文档比较会混用（REFERENCE_AUDIT §1-8）。
    - 只读地复用 dac1_curves，不改变 exp_static 的既有口径与数字。
    """
    from .charge_model import Pool, dac1_curves, LSB1
    out = []
    for i in range(n_pools):
        c = dac1_curves(pool=Pool.make(sigma=sigma, seed=100 + i))
        v = c["v"]; codes = c["code"].astype(float)
        A = np.stack([np.ones_like(codes), codes], axis=1)
        fit, *_ = np.linalg.lstsq(A, v, rcond=None)
        slope = (v[-1] - v[0]) / (codes[-1] - codes[0])
        inl_bf = (v - A @ fit) / LSB1
        inl_ep = (v - (v[0] + slope * (codes - codes[0]))) / LSB1
        dnl_bf = np.diff(v) / fit[1] - 1.0
        dnl_ep = np.diff(v) / slope - 1.0
        to_ppm = 1e6 / 2**10
        out.append({
            "seed": 100 + i,
            "inl_bf_ppm": float(np.max(np.abs(inl_bf)) * to_ppm),
            "inl_ep_ppm": float(np.max(np.abs(inl_ep)) * to_ppm),
            "dnl_bf_lsb": float(np.max(np.abs(dnl_bf))),
            "dnl_ep_lsb": float(np.max(np.abs(dnl_ep))),
            "mean_dnl_bf": float(dnl_bf.mean()),
            "mean_dnl_ep": float(dnl_ep.mean()),
        })
    return out

def main():
    res = {
        "caaz": exp_caaz(),
        "caaz_az": exp_caaz_az(),
        "tracking": exp_tracking(),
        "interleave": exp_interleave(),
        "static": exp_static(),
    }
    with open(os.path.join(OUT,"results.json"),"w") as f:
        json.dump(res,f,indent=2)
    # markdown
    L=["# Python 行为级模型结果",""]
    L.append("## CAAZ（10 MS/s 输出，raw 20 MS/s）")
    L.append("| fin | 基线 DR | CAAZ DR | ΔDR | 基线 SNDR | CAAZ SNDR | ΔSNDR |")
    L.append("|---:|---:|---:|---:|---:|---:|---:|")
    for r in res["caaz"]:
        L.append(f"| {r['fin']/1e3:.0f} kHz | {r['base_DR_dB']:.2f} | {r['caaz_DR_dB']:.2f} | {r['dDR']:+.2f} | {r['base_SNDR_dB']:.2f} | {r['caaz_SNDR_dB']:.2f} | {r['dSNDR']:+.2f} |")
    L.append("")
    L.append("## CAAZ 的 AZ 共享程度（100 kHz）")
    L.append("| az_share | DR | Δ vs 基线 |")
    L.append("|---:|---:|---:|")
    for r in res["caaz_az"]["rows"]:
        L.append(f"| {r['az_share']:.1f} | {r['DR_dB']:.2f} | {r['dDR_vs_base']:+.2f} |")
    L.append("")
    L.append("## 8× 重复（M 扫描）")
    L.append("| M | DR | SNDR | SFDR |")
    L.append("|---:|---:|---:|---:|")
    for r in res["tracking"]:
        L.append(f"| {r['M']} | {r['DR_dB']:.2f} | {r['SNDR_dB']:.2f} | {r['SFDR_dBc']:.2f} |")
    L.append("")
    L.append("## 部分交织（10 MS/s，18 片池）")
    L.append("| 场景 | DR | SNDR | SFDR |")
    L.append("|---|---:|---:|---:|")
    for r in res["interleave"]:
        L.append(f"| {r['case']} | {r['DR_dB']:.2f} | {r['SNDR_dB']:.2f} | {r['SFDR_dBc']:.2f} |")
    L.append("")
    L.append("## 静态 DAC1（10 bit，单位电容失配）")
    L.append("| σu | DNL raw | INL raw | DNL cal | INL cal | INL raw ppm | INL cal ppm |")
    L.append("|---:|---:|---:|---:|---:|---:|---:|")
    for r in res["static"]:
        L.append(f"| {r['unit_sigma']*100:.1f}% | {r['dnl_raw_lsb']:.3f} | {r['inl_raw_lsb']:.3f} | {r['dnl_cal_lsb']:.3f} | {r['inl_cal_lsb']:.3f} | {r['inl_raw_ppm']:.1f} | {r['inl_cal_ppm']:.1f} |")
    open(os.path.join(OUT,"report.md"),"w").write("\n".join(L)+"\n")
    print("\n".join(L))

if __name__ == "__main__":
    main()
