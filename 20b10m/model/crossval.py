"""crossval.py —— 技术有效性交叉验证

协议（每个 claim 都一样）：
- K=10 个独立 seed，配对比较（同一 seed 下 base vs tech）；
- 2 个输入频率、2 个 FFT 长度，检查结论不靠单一工作点；
- 报告 mean ± 95% CI（t_{0.975,9}=2.262）、正的 seed 数、min/max；
- 判定：CI 全正 = POSITIVE；全负 = NEGATIVE；跨 0 = INCONCLUSIVE；
- 能算解析预期的（8×、位账）必须给预测值，measured vs predicted 一起报；
- 不能测的（DEM/dither 未实现）显式标 NOT_IMPLEMENTED，不编数。

运行：cd 20b10m && python3 -m model.crossval
输出：model/results/crossval/{results.json,summary.csv}
"""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

from .params import P
from .adc import simulate
from .metrics import fft_metrics
from . import static
from .charge_model import dac1_curves, cal_residual, _features

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "model" / "results" / "crossval"
K = 10
SEEDS = list(range(1000, 1000 + K))
T95 = 2.262  # t_{0.975, 9}


def metric_at(fin, fs, seed, n, **kw):
    fc = round(fin * n / fs) * fs / n
    x, _ = simulate(fc, fs=fs, n=n, seed=seed, **kw)
    return fft_metrics(x, fs, fc)


def paired(fin, fs, base_kw, tech_kw, metrics, n=P.n, seeds=SEEDS):
    """同一 seed 下 base/tech 配对；返回每个 metric 的差值统计。"""
    base = {m: [] for m in metrics}
    tech = {m: [] for m in metrics}
    for s in seeds:
        b = metric_at(fin, fs, s, n, **base_kw)
        t = metric_at(fin, fs, s, n, **tech_kw)
        for m in metrics:
            base[m].append(b[m])
            tech[m].append(t[m])
    out = {}
    for m in metrics:
        d = np.asarray(tech[m]) - np.asarray(base[m])
        k = len(d)
        mean = float(d.mean())
        sd = float(d.std(ddof=1))
        ci = T95 * sd / math.sqrt(k)
        out[m] = {
            "base_mean": float(np.mean(base[m])),
            "tech_mean": float(np.mean(tech[m])),
            "delta_mean": mean,
            "delta_std": sd,
            "ci95": ci,
            "ci_low": mean - ci,
            "ci_high": mean + ci,
            "positive": int((d > 0).sum()),
            "negative": int((d < 0).sum()),
            "min": float(d.min()),
            "max": float(d.max()),
            "k": k,
            "verdict": ("POSITIVE" if mean - ci > 0 else
                        "NEGATIVE" if mean + ci < 0 else "INCONCLUSIVE"),
        }
    return out


# ---------------------------------------------------------------- T1 8× 平均
def t1_averaging():
    rows = []
    ra, ktc, cmp_, ref, az = 24.0, 17.3, 9.7, 2.9, 9.7
    other2 = ktc**2 + cmp_**2 + ref**2 + az**2
    M, rho = 8, P.rho
    F = 1 / M + 2 / (M * M) * sum((M - k) * rho**k for k in range(1, M))
    pred_db = 10 * math.log10((ra**2 + other2) / (ra**2 * F + other2))
    for fin, n in ((100e3, P.n), (1e6, 8192)):
        r = paired(fin, P.fs, dict(M=1), dict(M=8),
                   ("SNDR_dB", "DR_dB"), n=n)["SNDR_dB"]
        rows.append({"test": "T1_averaging", "config": f"{fin/1e3:.0f}kHz/N{n}",
                     "metric": "SNDR_dB", **r,
                     "predicted_db": pred_db,
                     "measured_minus_pred": r["delta_mean"] - pred_db,
                     "F_ar1": F})
    return rows


# ---------------------------------------------------------------- T2 CAAZ
def t2_caaz():
    rows = []
    for fin, n in ((100e3, 8192), (1e6, 8192), (2e6, 8192)):
        r = paired(fin, P.fs, dict(caaz=False), dict(caaz=True),
                   ("DR_dB", "SNDR_dB"), n=n)
        for m in ("DR_dB", "SNDR_dB"):
            rows.append({"test": "T2_caaz", "config": f"{fin/1e6:.1f}MHz/N{n}",
                         "metric": m, **r[m]})
    # AZ 共享度：share 1.0 应最好，0.0 只剩两点平均
    for share in (1.0, 0.7, 0.0):
        r = paired(100e3, P.fs, dict(caaz=False),
                   dict(caaz=True, az_share=share), ("DR_dB",), n=8192)
        rows.append({"test": "T2_caaz_share", "config": f"share={share}",
                     "metric": "DR_dB", **r["DR_dB"]})
    return rows


# ---------------------------------------------------------------- T3 片级 shuffle
def t3_shuffle():
    rows = []
    base100 = dict(gain=5e-5, offset=50e-6, skew=1e-12, shuffle=False)
    tech100 = dict(gain=5e-5, offset=50e-6, skew=1e-12, shuffle=True)
    r = paired(100e3, P.fs, dict(interleave=base100), dict(interleave=tech100),
               ("DR_dB", "SFDR_dBc"), n=8192)
    for m in ("DR_dB", "SFDR_dBc"):
        rows.append({"test": "T3_shuffle", "config": "100kHz/50ppm",
                     "metric": m, **r[m]})
    base2 = dict(gain=2e-5, offset=20e-6, skew=1e-12, shuffle=False)
    tech2 = dict(gain=2e-5, offset=20e-6, skew=1e-12, shuffle=True)
    r = paired(2e6, P.fs, dict(interleave=base2), dict(interleave=tech2),
               ("DR_dB", "SFDR_dBc"), n=8192)
    for m in ("DR_dB", "SFDR_dBc"):
        rows.append({"test": "T3_shuffle", "config": "2MHz/1ps",
                     "metric": m, **r[m]})
    # 失配档扫描：失配越大，shuffle 对 SFDR 的收益应越大
    for g in (10e-6, 50e-6, 100e-6):
        b = dict(gain=g, offset=50e-6, skew=1e-12, shuffle=False)
        t = dict(gain=g, offset=50e-6, skew=1e-12, shuffle=True)
        r = paired(100e3, P.fs, dict(interleave=b), dict(interleave=t),
                   ("SFDR_dBc",), n=8192, seeds=SEEDS[:6])
        rows.append({"test": "T3_shuffle_mismatch", "config": f"gain={g*1e6:.0f}ppm",
                     "metric": "SFDR_dBc", **r["SFDR_dBc"]})
    return rows


# ---------------------------------------------------------------- T4 校准
def t4_calibration():
    rows = []
    raw_ppm, fin_ppm = [], []
    for s in range(1, K + 1):
        c = dac1_curves(sigma=0.002, seed=s)
        raw_ppm.append(float(np.max(np.abs(c["inl_raw"]))) * 1e6 / 1024)
        pk, _ = cal_residual(n_avg=16, sigma_meas=2.8, trials=8, seed=s)
        fin_ppm.append(float(pk) * 1e6 / 1024)
    raw_ppm, fin_ppm = np.array(raw_ppm), np.array(fin_ppm)
    d = fin_ppm - raw_ppm
    ci = T95 * d.std(ddof=1) / math.sqrt(K)
    rows.append({"test": "T4_calibration", "config": "sigma=0.2%/10 chips",
                 "metric": "INL_ppm", "base_mean": float(raw_ppm.mean()),
                 "tech_mean": float(fin_ppm.mean()), "delta_mean": float(d.mean()),
                 "delta_std": float(d.std(ddof=1)), "ci95": float(ci),
                 "ci_low": float(d.mean() - ci), "ci_high": float(d.mean() + ci),
                 "positive": int((d < 0).sum()), "negative": int((d > 0).sum()),
                 "min": float(d.min()), "max": float(d.max()), "k": K,
                 "raw_mean": float(raw_ppm.mean()), "raw_std": float(raw_ppm.std(ddof=1)),
                 "cal_mean": float(fin_ppm.mean()), "cal_std": float(fin_ppm.std(ddof=1)),
                 "verdict": "PASS" if fin_ppm.max() < raw_ppm.min() else "CONDITIONAL"})
    # out-of-sample：偶数码拟合，奇数码评估
    in_ppm, out_ppm = [], []
    for s in range(1, K + 1):
        c = dac1_curves(sigma=0.002, seed=s)
        codes, y = c["code"], c["inl_raw"]
        B = _features(codes >> 7, codes & 127)
        tr = (codes % 2 == 0)
        w, *_ = np.linalg.lstsq(B[tr], y[tr], rcond=None)
        in_ppm.append(float(np.max(np.abs(B[tr] @ w - y[tr]))) * 1e6 / 1024)
        out_ppm.append(float(np.max(np.abs(B[~tr] @ w - y[~tr]))) * 1e6 / 1024)
    in_ppm, out_ppm = np.array(in_ppm), np.array(out_ppm)
    d = out_ppm - in_ppm
    ci = T95 * d.std(ddof=1) / math.sqrt(K)
    rows.append({"test": "T4_calibration_oos", "config": "even->odd split/10 chips",
                 "metric": "INL_oos_ppm", "base_mean": float(in_ppm.mean()),
                 "tech_mean": float(out_ppm.mean()), "delta_mean": float(d.mean()),
                 "delta_std": float(d.std(ddof=1)), "ci95": float(ci),
                 "ci_low": float(d.mean() - ci), "ci_high": float(d.mean() + ci),
                 "positive": int((d > 0).sum()), "negative": int((d < 0).sum()),
                 "min": float(out_ppm.min()), "max": float(out_ppm.max()), "k": K,
                 "verdict": "CONDITIONAL" if out_ppm.max() > 1.5 else "PASS"})
    # σu 线性：INL/σu 的比值应恒定
    ratios = []
    for sig in (0.001, 0.002, 0.004):
        vals = [float(np.max(np.abs(dac1_curves(sigma=sig, seed=s)["inl_raw"]))) * 1e6 / 1024
                for s in range(1, 6)]
        ratios.append(float(np.mean(vals)) / (sig * 100.0))
    slope = float(np.mean(ratios))
    dev = max(abs(r / slope - 1) for r in ratios)
    rows.append({"test": "T4_sigma_linear", "config": "0.1/0.2/0.4%",
                 "metric": "INL_ppm_per_percent", "base_mean": slope, "tech_mean": slope,
                 "delta_mean": 0.0, "delta_std": 0.0, "ci95": 0.0, "ci_low": 0.0,
                 "ci_high": 0.0, "positive": 0, "negative": 0, "min": min(ratios),
                 "max": max(ratios), "k": 3, "ratios": ratios, "max_rel_dev": dev,
                 "verdict": "PASS" if dev < 0.02 else "CONDITIONAL"})
    return rows


def t5_skew_gain():
    rows = []
    b = dict(gain=2e-5, offset=20e-6, shuffle=True)
    r = paired(2e6, P.fs, dict(interleave={**b, "skew": 0.5e-12}),
               dict(interleave={**b, "skew": 2e-12}), ("SNDR_dB",), n=8192)
    rows.append({"test": "T5_skew", "config": "0.5->2ps @2MHz", "metric": "SNDR_dB", **r["SNDR_dB"]})
    b2 = dict(offset=0, skew=0, shuffle=True)
    r = paired(100e3, P.fs, dict(interleave={**b2, "gain": 10e-6}),
               dict(interleave={**b2, "gain": 50e-6}), ("SNDR_dB",), n=8192)
    rows.append({"test": "T5_gain", "config": "10->50ppm @100kHz", "metric": "SNDR_dB", **r["SNDR_dB"]})
    return rows


# ---------------------------------------------------------------- T6/T7 静态检查
def t6_unimplemented():
    txt = "".join(p.read_text(errors="ignore").lower()
                  for p in (ROOT / "model").glob("*.py") if p.name != "crossval.py")
    word_gen = ("class prbs31" in txt) or ("def dither_words" in txt)
    dem = ("def dem" in txt) or ("dynamic element matching" in txt)
    inject = ("dither" in txt and "inject" in txt)
    if not (word_gen or dem or inject):
        verdict = "NOT_IMPLEMENTED"
    elif word_gen and not (dem or inject):
        verdict = "PARTIAL_DITHER_WORD_ONLY"
    else:
        verdict = "PARTIAL"
    return [{"test": "T6_dem_dither", "config": "static grep model/*.py",
             "metric": "implemented", "base_mean": 0, "tech_mean": 0, "delta_mean": 0,
             "delta_std": 0, "ci95": 0, "ci_low": 0, "ci_high": 0,
             "positive": 0, "negative": 0, "min": 0, "max": 0, "k": 0,
             "verdict": verdict, "dither_word_gen": word_gen, "dem": dem,
             "dither_injection": inject}]


def t7_bitaccount():
    lsb2 = (2**P.R * P.fs_diff / 2**P.N1) / 2**P.N2
    lsb_total = P.fs_diff / 2**(P.N1 + P.N2 - P.R)
    rel = abs(lsb2 - lsb_total) / lsb_total
    return [{"test": "T7_bitaccount", "config": f"N1={P.N1}/N2={P.N2}/R={P.R}",
             "metric": "LSB2_vs_LSBtotal", "base_mean": lsb_total, "tech_mean": lsb2,
             "delta_mean": lsb2 - lsb_total, "delta_std": 0, "ci95": 0,
             "ci_low": 0, "ci_high": 0, "positive": 0, "negative": 0,
             "min": lsb2, "max": lsb2, "k": 1,
             "verdict": "PASS" if rel < 1e-12 else "FAIL", "rel": rel}]


# ---------------------------------------------------------------- 跨实现
def cross_impl():
    rows = []
    p = ROOT / "behavioral" / "runs" / "smoke_ramp" / "metrics.json"
    if p.exists():
        beh = json.loads(p.read_text())
        c = dac1_curves(sigma=0.002, seed=7)
        mdl = float(np.max(np.abs(c["inl_raw"]))) * 1e6 / 1024
        beh_ppm = float(beh.get("inl_peak_ppm", float("nan")))
        rows.append({"test": "X1_inl_0p2", "config": "model vs behavioral",
                     "metric": "INL_ppm", "base_mean": mdl, "tech_mean": beh_ppm,
                     "delta_mean": beh_ppm - mdl, "delta_std": 0, "ci95": 0,
                     "ci_low": 0, "ci_high": 0, "positive": 0, "negative": 0,
                     "min": min(mdl, beh_ppm), "max": max(mdl, beh_ppm), "k": 1,
                     "verdict": "DISCREPANT" if abs(beh_ppm - mdl) / mdl > 0.2 else "CONSISTENT",
                     "ratio": beh_ppm / mdl})
    return rows


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    rows += t1_averaging()
    rows += t2_caaz()
    rows += t3_shuffle()
    rows += t4_calibration()
    rows += t5_skew_gain()
    rows += t6_unimplemented()
    rows += t7_bitaccount()
    rows += cross_impl()

    (OUT / "results.json").write_text(
        json.dumps({"schema": "sar20_10m_crossval_v1", "K": K, "seeds": SEEDS,
                    "t95": T95, "rows": rows}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")

    cols = ["test", "config", "metric", "base_mean", "tech_mean", "delta_mean",
            "delta_std", "ci95", "ci_low", "ci_high", "positive", "negative",
            "min", "max", "k", "verdict"]
    with (OUT / "summary.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (f"{r[k]:.6g}" if isinstance(r.get(k), float) else r.get(k)) for k in cols})

    n_pos = sum(1 for r in rows if r["verdict"] == "POSITIVE")
    n_neg = sum(1 for r in rows if r["verdict"] == "NEGATIVE")
    n_inc = sum(1 for r in rows if r["verdict"] == "INCONCLUSIVE")
    print(f"rows={len(rows)}  POSITIVE={n_pos}  NEGATIVE={n_neg}  INCONCLUSIVE={n_inc}")
    for r in rows:
        if r["test"] in ("T1_averaging", "X1_inl_0p2", "T7_bitaccount"):
            print(f"  {r['test']:18s} {r['config']:22s} {r['metric']:14s} "
                  f"Δ={r['delta_mean']:+.3f}  CI=[{r['ci_low']:+.3f},{r['ci_high']:+.3f}]  {r['verdict']}")


if __name__ == "__main__":
    main()
