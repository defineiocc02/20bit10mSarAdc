"""charge_model.py —— DAC1 电荷域静态模型（对齐 20b10mtask 的 ChargePool 思路）

参考库 `task2/eight/model.py::ChargePool` 的做法：
  - 用实际单位电容（含失配）算每片增益与底板权重；
  - 残差写成 affine：r = gain·(x−Vlow) − base；
  - 校准用位权/段权拟合，残差是拟合吃不掉的部分。
这里只做 DAC1 的 10 bit 段级（8 个 unary 片 × 128 单位），不是 20.5 bit 全系统。

单位：F / V / LSB1。
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

C_UNIT = 27e-15
UNITS = 128
NSLICE = 18
ACTIVE = 8
VREF, VGND, VCM = 5.0, 0.0, 2.5
FS_DIFF = 10.0
LSB1 = FS_DIFF / 1024.0


@dataclass
class Pool:
    caps: list[np.ndarray]       # 每片 128 个单位电容
    cp: float                    # 顶板对地寄生（全局，不按片）

    @classmethod
    def make(cls, sigma=0.002, cp=0.0, seed=7):
        rng = np.random.default_rng(seed)
        caps = [np.maximum(1e-18, C_UNIT * (1 + rng.normal(0, sigma, UNITS))) for _ in range(NSLICE)]
        return cls(caps, cp)


def _vtop(caps: np.ndarray, bits: int, full=False, vref=VREF, vgnd=VGND, cp=0.0, vin=0.0):
    """7 bit 二进制 + 1 个 termination；full=True 时 128 个单位全接 VREF。

    127 个单位按 1,2,4,...,64 分组；第 128 个单位在 full 时接 VREF、否则 VGND。
    这样 8 片 ×128 = 1024 个码，段边界不会少 1 个 LSB。
    """
    bit_of_unit = np.zeros(127, dtype=np.int8)
    start = 0
    for i in range(7):
        n = 1 << i
        bit_of_unit[start:start+n] = i
        start += n
    bot = np.where(((bits >> bit_of_unit) & 1).astype(bool), vref, vgnd)
    c = caps[:127]
    ctot = caps.sum() + cp
    num = (c * (bot - vin)).sum() + caps[127] * ((vref if full else vgnd) - vin)
    return vin + num / ctot


def dac1_curves(pool: Pool | None = None, sigma=0.002, cp=0.0, seed=7):
    """返回 0..1023 的差分输出、INL/DNL（raw）与位权校准残差。"""
    pool = pool or Pool.make(sigma=sigma, cp=cp, seed=seed)
    codes = np.arange(1024)
    v = np.empty(1024)
    for k in codes:
        seg, low = int(k >> 7), int(k & 127)
        vp = 0.0; vn = 0.0
        for j in range(ACTIVE):
            # P：j<seg 全 VREF；j==seg 按 low 二进制；j>seg 全 VGND
            if j < seg:
                vp += _vtop(pool.caps[j], 127, full=True, cp=pool.cp)
            elif j == seg:
                vp += _vtop(pool.caps[j], low, cp=pool.cp)
            else:
                vp += _vtop(pool.caps[j], 0, cp=pool.cp)
            # N：互补码 1023-k
            kn = 1023 - k; segn, lown = int(kn >> 7), int(kn & 127)
            if j < segn:
                vn += _vtop(pool.caps[j], 127, full=True, cp=pool.cp)
            elif j == segn:
                vn += _vtop(pool.caps[j], lown, cp=pool.cp)
            else:
                vn += _vtop(pool.caps[j], 0, cp=pool.cp)
        v[k] = (vp - vn) / ACTIVE
    # 端点/最佳直线拟合后再算 INL（去掉 dummy 引起的固定失调/增益）
    A = np.stack([np.ones(1024), codes], axis=1)
    fit, *_ = np.linalg.lstsq(A, v, rcond=None)
    v_fit = A @ fit
    inl_raw = (v - v_fit) / LSB1
    # DNL 必须用同一条拟合直线的斜率归一，否则 mean(DNL)≠0、与 INL 口径不自洽
    # （审计 REFERENCE_AUDIT.md §1-8：用标称 LSB1 时 mean(DNL)=+2.23 ppm）
    lsb_fit = fit[1]
    dnl_raw = np.diff(v) / lsb_fit - 1.0

    # 校准：把 INL 投影到位权特征上，扣掉可校准部分；残差=特征吃不掉的
    seg = codes >> 7
    low = codes & 127
    Bg = [np.ones(1024)]
    Bg += [((seg >= j + 1).astype(float)) for j in range(7)]
    Bg += [(((low >> i) & 1).astype(float)) for i in range(7)]
    Bg = np.stack(Bg, axis=1)
    cg, *_ = np.linalg.lstsq(Bg, inl_raw, rcond=None)
    inl_global = inl_raw - Bg @ cg

    Bp = [np.ones(1024)]
    Bp += [((seg == j).astype(float)) for j in range(8)]
    for j in range(8):
        for i in range(7):
            Bp.append((((seg == j) & (((low >> i) & 1) == 1)).astype(float)))
    Bp = np.stack(Bp, axis=1)
    cp, *_ = np.linalg.lstsq(Bp, inl_raw, rcond=None)
    inl_cal = inl_raw - Bp @ cp
    dnl_cal = np.diff(codes + inl_cal) - 1.0
    v_cal = v_fit + inl_cal * LSB1
    return {"code": codes, "v": v, "v_cal": v_cal, "inl_global": inl_global,
            "inl_raw": inl_raw, "dnl_raw": dnl_raw,
            "inl_cal": inl_cal, "dnl_cal": dnl_cal}


def _features(seg, low):
    """65 个特征：1 常量 + 8 段增益 + 8×7 段内位权。"""
    B = [np.ones(len(seg))]
    B += [((seg == j).astype(float)) for j in range(8)]
    for j in range(8):
        for i in range(7):
            B.append((((seg == j) & (((low >> i) & 1) == 1)).astype(float)))
    return np.stack(B, axis=1)


def cal_residual(n_avg=64, sigma_meas=2.8, trials=8, pool=None, seed=7):
    """有限样本校准残差：每码平均 n_avg 次、单次测量噪声 sigma_meas[LSB20]。

    物理含义：片外 LMS/最小二乘用实测码值估权重，估不准的部分留下来。
    LS 是线性的，残差 = 特征空间对测量噪声的投影，因此 ∝ sigma/sqrt(n)。
    返回 (峰值残差[LSB1], 曲线数组[LSB1])，曲线为 trials 的 RMS 包络。

    单位换算：inl_raw 以 LSB1 计（1 LSB1 = 1024 LSB20），故噪声也先折到 LSB1。
    """
    c = dac1_curves(pool=pool, seed=seed)
    codes, inl = c["code"], c["inl_raw"]
    seg, low = codes >> 7, codes & 127
    B = _features(seg, low)
    rng = np.random.default_rng(seed + 1000)
    sig1 = sigma_meas / 1024.0
    curves = []
    for _ in range(trials):
        y = inl + rng.normal(0, sig1 / np.sqrt(n_avg), len(inl))
        w, *_ = np.linalg.lstsq(B, y, rcond=None)
        # 残差 = 拟合值减真值（校准后剩下的）
        curves.append(B @ w - inl)
    curves = np.array(curves)
    env = np.sqrt((curves**2).mean(axis=0))
    return float(np.max(np.abs(curves))), env


def inl_profile(which="raw", n_avg=64, pool=None, seed=7):
    """输入折算的静态误差曲线（伏特），供时域模型注入。

    which="raw"：未校准；
    which="cal"：校准后——用有限样本残差（n_avg 次平均），不是数学上的 0。
                 理想 0 只在「INL 完全由位权误差张成且权重估得无限准」时成立，不可当结果。
    """
    c = dac1_curves(pool=pool, seed=seed)
    if which == "cal":
        _pk, env = cal_residual(n_avg=n_avg, pool=pool, seed=seed)
        rng = np.random.default_rng(seed + 55)
        sign = np.where(rng.random(len(env)) < .5, -1.0, 1.0)
        return c["code"], (sign * env) * LSB1
    return c["code"], c["inl_raw"] * LSB1


if __name__ == "__main__":
    c = dac1_curves()
    print("raw INL ppm", np.max(np.abs(c["inl_raw"])) * 1e6 / 1024)
    print("cal INL ppm", np.max(np.abs(c["inl_cal"])) * 1e6 / 1024, "(特征张成，应≈0)")
    for n in (1, 16, 64, 256, 4096):
        pk, _ = cal_residual(n_avg=n)
        print(f"n_avg={n:5d}  residual peak {pk*1e6/1024:6.2f} ppm  ({pk:.2f} LSB1)")
