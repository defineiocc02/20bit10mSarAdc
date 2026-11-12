"""tech_effects.py —— DEM 与 dither 的独立贡献（共顶板电荷模型）

为什么单独建这个模块：
- `charge_model.dac1_curves` 把每片顶板电压各自归一化再平均，**片间总容失配被抵消**，
  只留下片内二进制电容的比例误差；它适合校准/INL 的主模型，但不适合评估 DEM。
- 这里用**共顶板**电荷分享：8 片的 1024 个单位电容接在同一顶板，
  V_top = Σ C_i·V_bot_i / C_total。片间总容失配与片内比例误差都进来。

三个可分别开关的机制：
- DEM：8 个循环置换，改变「哪片当二进制片 / 哪些片满量程」；
- dither：码域整数 dither，码 c→c+d，数字端减 d·LSB1；D=1/2/4/8；
- both：两者同时平均。

输出（每个 case）：INL 峰值（ppm FS）、DNL 峰值（LSB1）、每样本状态间 RMS 噪声（ppm）。
注意：INL/DNL 是**跨状态平均后**的静态指标；每样本噪声是代价，不能只看平均值。

运行：cd 20b10m && python3 -m model.tech_effects
输出：model/results/dem_dither.json
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

from .charge_model import Pool, LSB1, VREF

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "model" / "results" / "dem_dither.json"
ACTIVE = 8


def _bit_order():
    b = np.zeros(127, dtype=np.int8)
    st = 0
    for i in range(7):
        n = 1 << i
        b[st:st + n] = i
        st += n
    return b


BIT_ORDER = _bit_order()


class Top:
    """预计算每片 full / binary 的电荷，_top 只做 8 次加法。"""

    def __init__(self, pool: Pool):
        caps = np.concatenate(pool.caps[:ACTIVE])
        self.ctot = float(caps.sum())
        self.slice_sum = np.array([float(pool.caps[j].sum()) for j in range(ACTIVE)])
        self.binq = np.zeros((ACTIVE, 128), float)
        for j in range(ACTIVE):
            c = pool.caps[j][:127]
            for b in range(128):
                self.binq[j, b] = float((c * ((b >> BIT_ORDER) & 1)).sum())

    def v(self, code: int, perm) -> float:
        k, low = code >> 7, code & 127
        total = 0.0
        for j in range(ACTIVE):
            pj = perm[j]
            if j < k:
                total += self.slice_sum[pj]
            elif j == k:
                total += self.binq[pj, low]
        return total / self.ctot * VREF


def _inl_dnl(v, codes):
    A = np.stack([np.ones(len(codes)), codes], axis=1)
    fit, *_ = np.linalg.lstsq(A, v, rcond=None)
    inl = (v - A @ fit) / LSB1
    dnl = np.diff(v) / fit[1] - 1.0
    return inl, dnl


def effect(top: Top, perms, dvals, codes):
    states = []
    for c in codes:
        vals = [top.v(c + d, p) - top.v(1023 - (c + d), p) - d * LSB1
                for p in perms for d in dvals]
        states.append(vals)
    M = np.asarray(states)
    v = M.mean(axis=1)
    inl, dnl = _inl_dnl(v, codes)
    noise = math.sqrt(float(np.mean(M.var(axis=1, ddof=1)))) * 1e6 / 1024
    return (float(np.max(np.abs(inl))) * 1e6 / 1024,
            float(np.max(np.abs(dnl))),
            noise,
            int((dnl <= -1).sum()))


def ident():
    return tuple(range(ACTIVE))


def dem_perms():
    return [tuple((j + s) % ACTIVE for j in range(ACTIVE)) for s in range(ACTIVE)]


def _cases(full=True):
    yield "raw", [ident()], [0]
    yield "DEM", dem_perms(), [0]
    for D in ((1, 2, 4, 8) if full else (2,)):
        ds = list(range(-D, D + 1))
        yield f"dither_D{D}", [ident()], ds
        yield f"DEM+dither_D{D}", dem_perms(), ds


def _codes(D=8):
    return np.arange(D, 1024 - D)


def one_chip(seed: int, full=True):
    top = Top(Pool.make(sigma=0.002, seed=seed))
    codes = _codes(8 if full else 2)
    return {name: effect(top, perms, ds, codes) for name, perms, ds in _cases(full)}


def multi_chip(K: int = 10):
    rows = []
    for s in range(1, K + 1):
        r = one_chip(s, full=False)
        r["seed"] = s
        rows.append(r)
    agg = {}
    for name in rows[0]:
        if name == "seed":
            continue
        arr = np.array([r[name][:3] for r in rows], float)
        agg[name] = {"mean": arr.mean(axis=0).tolist(),
                     "std": arr.std(axis=0, ddof=1).tolist(),
                     "missing_total": int(sum(r[name][3] for r in rows))}
    return rows, agg


def main() -> None:
    seed7 = one_chip(7, full=True)
    rows, agg = multi_chip(10)
    base = np.array(agg["raw"]["mean"])
    for v in agg.values():
        v["inl_ratio"] = float(base[0] / v["mean"][0]) if v["mean"][0] > 0 else float("inf")
        v["dnl_ratio"] = float(base[1] / v["mean"][1]) if v["mean"][1] > 0 else float("inf")
    payload = {
        "schema": "sar20_10m_dem_dither_v1",
        "date": "2026-11-12",
        "model": "common-top charge sharing; 8 slices; sigma_u=0.2%; 1024 codes",
        "seed7": {k: {"inl_ppm": v[0], "dnl_lsb1": v[1], "noise_ppm": v[2], "missing": v[3]}
                  for k, v in seed7.items()},
        "chips": {"K": 10, "rows": rows, "agg": agg},
        "notes": [
            "INL/DNL 是跨状态平均后的静态指标；noise_ppm 是每样本状态间 RMS，是代价",
            "DEM=8 个循环置换；dither=码域整数 dither，数字扣除；不是采样态电荷注入",
            "共顶板模型包含片间总容失配，与 charge_model 的逐片归一口径不同",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{'case':22s} {'INLppm':>8s} {'DNLlsb1':>9s} {'noise':>7s} {'INLx':>6s} {'DNLx':>6s}")
    for name, v in agg.items():
        print(f"{name:22s} {v['mean'][0]:8.2f} {v['mean'][1]:9.5f} {v['mean'][2]:7.3f} "
              f"{v['inl_ratio']:6.2f} {v['dnl_ratio']:6.2f}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
