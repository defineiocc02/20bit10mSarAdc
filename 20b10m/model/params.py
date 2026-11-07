# [CODE-INDEX] params.py —— 全局参数（唯一口径）
# 单位：V / A / F / Hz；噪声均为“输入折算 Vrms”。
# 数据来源：kT/C 17.3 µV、RA 24.0、AZ 9.7、Cmp 9.7 来自 Fig.12/预算；
#            ρ=0.61 为由 M_eff 反解的推断值，不是实测；改动前先看 AUDIT.md。
"""参数集中定义：所有实验共用一套口径。"""
from dataclasses import dataclass

@dataclass
class Params:
    fs: float = 10e6          # 输出采样率
    n: int = 16384            # FFT 点数
    fs_diff: float = 10.0     # 差分满量程 Vpp
    amp: float = 4.8          # 差分峰值幅度（略低于 5 V）
    # 输入折算噪声 (Vrms)
    ktc: float = 17.3e-6
    ra_broad: float = 24.0e-6
    ra_az: float = 9.7e-6
    cmp: float = 9.7e-6
    ref: float = 2.9e-6
    # 8× 重复
    M: int = 8
    rho: float = 0.61         # 相邻重复样本相关系数
    # 交织
    n_slices: int = 18
    active: int = 8
    gain_sigma: float = 1e-3  # 片间增益失配
    offset_sigma: float = 0.5e-3
    skew_sigma: float = 1e-12 # 1 ps
    shuffle: bool = True

P = Params()
LSB_TOTAL = P.fs_diff / 2**20.5
LSB2 = (2**2 * P.fs_diff / 2**10) / 2**11   # 19.07 µV
