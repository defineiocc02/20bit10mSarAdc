# [CODE-INDEX] rng.py —— 固定虚拟芯片与分源随机流
#
# 规则（维护规范 §8）：
#   - 制造失配「只发生一次」，全仿真持久；不得每笔重抽；
#   - 噪声/失配/dither/调度种子各自独立编号，开关一个机制不打乱其他流；
#   - 不使用 hash() 或全局 RNG 的调用次数决定结果。
"""随机源：固定失配池 + SeedSequence 分源。"""

from __future__ import annotations

import numpy as np


class ChipInstance:
    """一颗固定虚拟芯片：单位电容失配只抽一次。"""

    def __init__(self, n_units: int, sigma_u: float, seed: int):
        self.n_units = n_units
        self.sigma_u = sigma_u
        self.seed = seed
        ss = np.random.SeedSequence(entropy=seed, spawn_key=(1,))   # 源 1 = 制造失配
        rng = np.random.default_rng(ss)
        self.unit_rel = rng.normal(0.0, sigma_u, n_units)           # 相对偏差数组
        self.unit_scale = 1.0 + self.unit_rel

    def caps(self, c_unit: float) -> np.ndarray:
        return c_unit * self.unit_scale

    def summary(self) -> dict:
        return dict(n_units=self.n_units, sigma_u=self.sigma_u, seed=self.seed,
                    rel_rms=float(np.std(self.unit_rel)),
                    rel_max=float(np.max(np.abs(self.unit_rel))))


class NoiseStreams:
    """按用途分开的随机流。同一 chip/sample 身份可重放。"""

    def __init__(self, seed: int):
        self.seed = seed
        self._rng = {}
        for name, key in (("ktc", 2), ("cmp", 3), ("ref", 4),
                          ("ra", 5), ("dither", 6), ("meta", 7)):
            ss = np.random.SeedSequence(entropy=seed, spawn_key=(key,))
            self._rng[name] = np.random.default_rng(ss)

    def normal(self, name: str, n: int, sigma: float) -> np.ndarray:
        """取 n 个样本的噪声。同名多次调用会顺序推进 —— 同一 chip seed 下可重放。"""
        if sigma == 0.0:
            return np.zeros(n)
        return self._rng[name].normal(0.0, sigma, n)

    def uniform(self, name: str, n: int, lo: float, hi: float) -> np.ndarray:
        return self._rng[name].uniform(lo, hi, n)

    def ar1(self, name: str, n: int, m: int, rho: float, sigma: float) -> np.ndarray:
        """n 个样本 × m 次重复读的 AR(1) 序列（相关方向是重复序号）。"""
        if sigma == 0.0:
            return np.zeros((n, m))
        out = np.empty((n, m))
        out[:, 0] = self._rng[name].normal(0.0, sigma, n)
        w_sigma = sigma * np.sqrt(max(1e-12, 1.0 - rho * rho))
        for k in range(1, m):
            out[:, k] = rho * out[:, k - 1] + self._rng[name].normal(0.0, w_sigma, n)
        return out
