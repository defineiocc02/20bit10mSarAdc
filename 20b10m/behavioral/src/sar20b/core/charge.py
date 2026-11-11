# [CODE-INDEX] charge.py —— 差分 CDAC 的节点电荷模型
#
# 规则（维护规范 §6.1）：
#   - 每片 P/N 的电容失配、寄生、采样状态在同一次仿真中持久；
#   - 采样初始化与每次底板切换前后的状态都要能取到；
#   - 底板互斥：VIN / VREF / VGND / VCM 不得同时导通两组；
#   - 单位电荷计数与节点电压求解是两条独立路径，互不调用。
"""差分 CDAC：电荷守恒 + 底板命令。"""

from __future__ import annotations

import numpy as np


class DiffCdac:
    """一片差分 CDAC（P/N 各 n_units 个单位电容）。

    顶板（top plate）浮空后电荷守恒：
        V_top_new = V_top_init + Σ_i [C_i · (V_bot_i_new − V_bot_i_init)] / C_total

    底板（bottom plate）由命令决定接 VIN / VREF / VGND / VCM。
    """

    LEVELS = ("VIN", "VREF", "VGND", "VCM")

    def __init__(self, caps_p: np.ndarray, caps_n: np.ndarray,
                 vref_p: float, vref_n: float, vcm: float, c_par_f: float = 0.0):
        if caps_p.shape != caps_n.shape:
            raise ValueError("P/N 电容数组必须等长")
        self.cap_p = np.asarray(caps_p, float)
        self.cap_n = np.asarray(caps_n, float)
        self.n = len(self.cap_p)
        self.vref_p, self.vref_n, self.vcm = vref_p, vref_n, vcm
        self.c_par = float(c_par_f)

        self.bot_p = np.full(self.n, "VIN", dtype=object)
        self.bot_n = np.full(self.n, "VIN", dtype=object)
        self.vtop_p = 0.0
        self.vtop_n = 0.0
        self._sampled = False
        self._vhold_p = 0.0
        self._vhold_n = 0.0

    # ---- 电平映射 ----
    def _level_v(self, name: str, vin_p: float = 0.0, vin_n: float = 0.0) -> float:
        if name == "VREF":
            return self.vref_p
        if name == "VGND":
            return self.vref_n
        if name == "VCM":
            return self.vcm
        if name == "VIN":
            return vin_p          # 调用方按 P/N 传入对应输入
        raise ValueError(f"未知底板电平 {name}")

    def _v_bot_array(self, side: str, vin_p: float, vin_n: float) -> np.ndarray:
        names = self.bot_p if side == "P" else self.bot_n
        vin = vin_p if side == "P" else vin_n
        out = np.empty(self.n)
        for i, nm in enumerate(names):
            out[i] = self._level_v(nm, vin, vin)
        return out

    # ---- 采样 ----
    def sample(self, vin_p: float, vin_n: float):
        """采样相：所有底板接对应输入，顶板跟随。"""
        self.bot_p[:] = "VIN"
        self.bot_n[:] = "VIN"
        self.vtop_p = vin_p
        self.vtop_n = vin_n
        self._vhold_p, self._vhold_n = vin_p, vin_n
        self._sampled = True

    def hold(self):
        """进入转换：顶板浮空，记下底板初值与顶板初值。"""
        if not self._sampled:
            raise RuntimeError("未采样就 hold")
        self._vbot0_p = self._v_bot_array("P", self._vhold_p, self._vhold_n)
        self._vbot0_n = self._v_bot_array("N", self._vhold_p, self._vhold_n)
        self._ctot_p = self.cap_p.sum() + self.c_par
        self._ctot_n = self.cap_n.sum() + self.c_par

    # ---- 底板切换 ----
    def set_bottom(self, side: str, units: np.ndarray, level: str):
        """把指定单位集合的底板接到 level。units 是布尔掩码。"""
        if level not in self.LEVELS:
            raise ValueError(f"非法底板电平 {level}")
        names = self.bot_p if side == "P" else self.bot_n
        names[np.asarray(units, bool)] = level

    def switch_units(self, side: str, units: np.ndarray, level: str,
                     vin_p: float, vin_n: float):
        """把指定单位切到 level，并**增量**更新顶板电压（O(该位单位数)）。"""
        if level not in self.LEVELS:
            raise ValueError(f"非法底板电平 {level}")
        names = self.bot_p if side == "P" else self.bot_n
        caps = self.cap_p if side == "P" else self.cap_n
        ctot = self._ctot_p if side == "P" else self._ctot_n
        sel = np.asarray(units, bool)
        vin = vin_p if side == "P" else vin_n
        vmap = {"VREF": self.vref_p, "VGND": self.vref_n, "VCM": self.vcm, "VIN": vin}
        v_new = vmap[level]
        old = names[sel]
        dv = np.array([v_new - vmap[o] for o in old])
        dq = float(np.sum(caps[sel] * dv))
        names[sel] = level
        if side == "P":
            self.vtop_p += dq / ctot
        else:
            self.vtop_n += dq / ctot

    def diff(self) -> float:
        """当前差分顶板电压 V_top,P − V_top,N。"""
        return self.vtop_p - self.vtop_n

    def check_conflict(self) -> list[str]:
        """互斥检查：一个单位只能接一个电平，这里按『底板命令是否有空』判定。"""
        errs = []
        for side, names in (("P", self.bot_p), ("N", self.bot_n)):
            bad = [i for i, nm in enumerate(names) if nm not in self.LEVELS]
            if bad:
                errs.append(f"{side} 侧单位 {bad[:5]} 底板电平非法")
        return errs

    # ---- 节点电压求解 ----
    def vtop(self, side: str, vin_p: float, vin_n: float) -> float:
        """按电荷守恒求当前顶板电压（独立求解路径，不查表）。"""
        if side == "P":
            caps, v0, vbot0, ctot = self.cap_p, self.vtop_p, self._vbot0_p, self._ctot_p
        else:
            caps, v0, vbot0, ctot = self.cap_n, self.vtop_n, self._vbot0_n, self._ctot_n
        vbot1 = self._v_bot_array(side, vin_p, vin_n)
        dq = float(np.sum(caps * (vbot1 - vbot0)))
        return v0 + dq / ctot

    def unit_charge_count(self, side: str) -> float:
        """单位电荷计数（独立路径，用于与电压求解交叉检查）。"""
        names = self.bot_p if side == "P" else self.bot_n
        caps = self.cap_p if side == "P" else self.cap_n
        # 以 VGND 为参考的电荷量
        q = 0.0
        for i, nm in enumerate(names):
            if nm == "VREF":
                q += caps[i] * (self.vref_p - self.vref_n)
            elif nm == "VCM":
                q += caps[i] * (self.vcm - self.vref_n)
        return q


def binary_weights(n_units: int) -> np.ndarray:
    """把 n_units 拆成 1,2,4,... 的位权（最高位在最后）。"""
    w = []
    left = n_units
    i = 0
    while left > 0:
        take = min(1 << i, left)
        w.append(take)
        left -= take
        i += 1
    return np.array(w, dtype=int)
