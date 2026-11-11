"""SAR20-10M 架构参数（唯一来源，冻结版 v1）

每条都标了来源：ARCH=spec/ARCH_V2.md、DER=推导、ASSUME=假设（未仿）。
改这里之前先看 arch/README.md 的"改动规则"。
"""
from __future__ import annotations

from dataclasses import dataclass, field

# ---------- 物理常数 ----------
K_B = 1.380649e-23
T_AMB = 300.0


@dataclass(frozen=True)
class Arch:
    # ---- 量程与位账 ----
    fs_pp: float = 10.0          # 差分满量程 Vpp            [ARCH §6]
    n1_bits: int = 10            # 一级有效位                [ARCH D-03]
    n1_decisions: int = 10       # 4b flash + 2b SAR + 4b fine[ARCH D-03]
    n2_bits: int = 11            # 二级位数                  [ARCH D-04]
    m_repeat: int = 8            # 8 次重复读                [ARCH D-10]
    redundancy_bits: float = 2.0 # 冗余                      [ARCH §6]
    out_bits: int = 22           # 输出字长                  [ARCH D-07]
    frame_bits: int = 24         # {VALID,FAULT,DATA[21:0]}

    # ---- 电容与增益 ----
    cu_f: float = 27e-15         # 单位电容                  [ARCH D-02]
    slices_total: int = 18       # 18 片池                   [ARCH D-01]
    slices_active: int = 8       # 每拍 8 片                 [ARCH D-01]
    units_per_slice: int = 128   # 片内 128 单位             [ARCH D-02]
    c_inc_f: float = 864e-15     # C_INC = 32 单位           [ARCH D-11]
    c_br_f: float = 28e-15       # 桥接电容（保留网表值）     [裁决 2026-11-08]
    a_ra: float = 32.0           # RA 电压增益（由 C_FB 定）  [ARCH D-11]

    # ---- 时序（200 MHz，20 tick/帧）----
    t_clk_ns: float = 5.0
    ticks_per_frame: int = 20
    phi_c0_ticks: int = 2        # cnt 0-1   → 10 ns
    phi_c1_ticks: int = 3        # cnt 2-4   → 15 ns
    phi_ra_ticks: int = 5        # cnt 5-9   → 25 ns
    phi_c2_ticks: int = 8        # cnt 10-17 → 40 ns

    # ---- 电路时序（未仿，[ASSUME]）----
    t_flash_ns: float = 3.0      # 4b flash 建立
    t_cmp1_ns: float = 2.36      # 一级单次判决（含 DAC1 建立）
    t_cmp2_ns: float = 0.6       # 二级单次判决（U2，未仿）
    t_dac2_settle_ns: float = 0.9
    t_sar2_logic_ns: float = 0.3
    t_beats_target_ns: float = 2.0   # 19 拍统一 2 ns  [ARCH §5.2]

    # ---- 噪声（输入折算 Vrms，[ARCH §10]）----
    cs_pf: float = 28.0          # 采样电容/侧
    ra_broadband_uv: float = 24.0  # RA 宽带，平均前
    ra_az_uv: float = 9.7
    cmp_uv: float = 9.7          # 比较器（U3：口径未定）
    ref_uv: float = 2.9
    tau_ra_ns: float = 2.5       # RA 噪声相关时间（U1，未仿）
    dt_beat_ns: float = 2.0      # 重复读间隔 = 判决拍 [ARCH D-09]
    jitter_ps: float = 1.0       # 验收值
    noise_target_uv: float = 26.5  # 论文反推总预算
    dr_target_db: float = 102.5

    # ---- 校准 ----
    coef_slots: int = 160
    coef_independent: int = 142  # 去掉 18 个共线片权   [ARCH D-05]
    sigma_unit: float = 0.002    # 单位电容相对失配（0.2%）
    cal_meas_noise_lsb: float = 2.8
    cal_avg_n: int = 16

    # ---- 派生量（只读）----
    def __post_init__(self):
        pass

    # 位账
    @property
    def resolution_bits(self) -> float:
        return self.n1_bits + self.n2_bits - self.redundancy_bits + 0.5 * __import__("math").log2(self.m_repeat)

    @property
    def lsb1_v(self) -> float:
        return self.fs_pp / 2 ** self.n1_bits

    @property
    def residual_span_v(self) -> float:
        return 2 ** self.redundancy_bits * self.lsb1_v

    @property
    def lsb2_v(self) -> float:
        return self.residual_span_v / 2 ** self.n2_bits

    @property
    def lsb_total_v(self) -> float:
        import math
        return self.lsb2_v / math.sqrt(self.m_repeat)

    @property
    def lsb_out_v(self) -> float:
        return self.fs_pp / 2 ** self.out_bits

    # 电容
    @property
    def c_dac1_f(self) -> float:
        return self.slices_active * self.units_per_slice * self.cu_f

    @property
    def c_dac2_array_f(self) -> float:
        """DAC2 主阵 32 单位（含 dummy）"""
        return 32 * self.cu_f

    @property
    def c_br_effective_f(self) -> float:
        """桥接串联子阵后的等效容（子阵 64 单位）"""
        cs = 64 * self.cu_f
        return self.c_br_f * cs / (self.c_br_f + cs)

    @property
    def c_dac2_eff_f(self) -> float:
        return self.c_dac2_array_f + self.c_br_effective_f

    @property
    def k_inc(self) -> float:
        return self.c_inc_f / (self.c_inc_f + self.c_dac2_eff_f)

    # ρ：相邻重复读的相关系数（AR(1)，Δt/τ）
    def rho(self, dt_ns: float | None = None) -> float:
        import math
        dt = self.dt_beat_ns if dt_ns is None else dt_ns
        return math.exp(-dt / self.tau_ra_ns)


ARCH = Arch()
