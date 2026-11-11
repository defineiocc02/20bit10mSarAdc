# [CODE-INDEX] params.py —— 全局参数（唯一口径）
# 单位：V / A / F / Hz；噪声均为"输入折算 Vrms"。
# 数据来源：kT/C 17.3 µV、RA 24.0、AZ 9.7、Cmp 9.7 来自 Fig.12/预算；
#            ρ=0.61 为由 M_eff 反解的推断值，不是实测；改动前先看 AUDIT.md。
# 位账：BL-v3 冻结为 10 + 12 − 2 = 20.00 bit（见 spec/ARCH_DECISION_BLv3.md）。
#       改 N1/N2/R 会自动重算 LSB 并做自洽检查，防止口径漂移。
"""参数集中定义：所有实验共用一套口径。"""
from dataclasses import dataclass

@dataclass
class Params:
    fs: float = 10e6          # 输出采样率
    n: int = 16384            # FFT 点数
    fs_diff: float = 10.0     # 差分满量程 Vpp
    amp: float = 4.8          # 差分峰值幅度（略低于 5 V）
    # ---- 位账（唯一来源：spec/ARCH_DECISION_BLv3.md）----
    N1: int = 10              # 一级判决数（4b flash + 2b SAR + 4b fine）
    N2: int = 12              # 二级判决数（DAC2）
    R: int = 2                # 冗余位数：DAC2 量程 = 2^R · LSB1
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
    gain_sigma: float = 1e-3  # 片间增益失配（dataclass 默认；实验里会被覆盖）
    offset_sigma: float = 0.5e-3
    skew_sigma: float = 1e-12 # 1 ps
    shuffle: bool = True      # True=片间随机选片；BL-v3 已判定取消，实验须显式关掉

P = Params()

# ---- 由位账推导的 LSB（不要再硬编码）----
N_TOTAL = P.N1 + P.N2 - P.R
LSB1 = P.fs_diff / 2**P.N1                      # 一级 LSB
LSB_TOTAL = P.fs_diff / 2**N_TOTAL              # 系统 LSB（20.00 bit）
LSB2 = (2**P.R * P.fs_diff / 2**P.N1) / 2**P.N2 # 二级 LSB 折输入

# 自洽检查：只有当 N1 + N2 - R 正确时，二级最低位才等于系统最低位。
# 这条断言是"防口径漂移"的闸门 —— 改任何位账参数，这里先报。
_rel = abs(LSB2 - LSB_TOTAL) / LSB_TOTAL
if _rel > 1e-12:
    raise AssertionError(
        f"位账不自洽：LSB2={LSB2:.6e} V, LSB_total={LSB_TOTAL:.6e} V, "
        f"相对差 {_rel:.2e}。检查 N1/N2/R 是否与 ARCH_DECISION_BLv3 一致。")

# 历史口径（2026-11-08 前，仅供对照，不得用于新结论）：
#   LSB_TOTAL = fs_diff / 2^20.5 = 6.743 µV   （8× 平均折 1.5 bit，口径混算）
#   LSB2      = (4·fs_diff/2^10) / 2^11 = 19.073 µV
