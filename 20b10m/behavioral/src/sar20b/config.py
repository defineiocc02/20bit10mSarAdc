# [CODE-INDEX] config.py —— 数值合同 + 架构 profile（唯一口径来源）
#
# 规则（来自维护规范）：
#   - 配置显式传入，不允许模块级可变全局决定实验条件；
#   - 每个数值必须带 source 标签：derived / datasheet / assumed / stress；
#   - profile 决定「物理拓扑」，不决定「非理想参数」，两者分开。
"""数值合同与架构 profile。"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Literal


# ---------------------------------------------------------------- 数值合同

@dataclass(frozen=True)
class NumericalContract:
    """所有码域/电压尺度的唯一定义。任何模块不得自行除 2 的幂。"""

    # ---- 电压尺度（BL-v3 冻结）----
    fs_diff_v: float = 10.0            # 差分满量程 Vpp        [derived: T01 C4]
    vref_p: float = 5.0                # 单侧高参考 V          [derived]
    vref_n: float = 0.0                # 单侧低参考 V
    vcm: float = 2.5                   # 单侧共模 V

    # ---- 位账（BL-v3：10 + 12 − 2 = 20.00）----
    n1: int = 10                       # 一级判决数            [derived: ARCH_DECISION_BLv3]
    n2: int = 12                       # 二级判决数
    n_red: int = 2                     # 冗余位数（DAC2 量程 = 2^n_red · LSB1）

    # ---- 传输码 ----
    n_xfer: int = 22                   # 22 bit offset binary
    xfer_center: int = 1 << 21         # 中心码

    # ---- 物理 ----
    c_unit_f: float = 27e-15           # 单位电容 F            [derived: 1024×27fF=27.648pF]
    n_units_per_side: int = 1024       # 每侧单位数            [derived: 8 片 × 128]
    g_ra: float = 32.0                 # RA 增益               [derived: 1.25Vpp/39mVpp]

    # ---- 采样率 ----
    fs_hz: float = 10e6                # 输出 10 MS/s

    # ---- 派生量（只能读，不能改）----
    @property
    def n_total(self) -> int:
        return self.n1 + self.n2 - self.n_red

    @property
    def lsb1_v(self) -> float:
        """一级 LSB = FS / 2^n1。"""
        return self.fs_diff_v / (2 ** self.n1)

    @property
    def resid_window_pp_v(self) -> float:
        """残差窗口 = 2^n_red · LSB1。"""
        return (2 ** self.n_red) * self.lsb1_v

    @property
    def lsb2_v(self) -> float:
        """二级 LSB 折输入 = 窗口 / 2^n2。"""
        return self.resid_window_pp_v / (2 ** self.n2)

    @property
    def lsb_analysis_v(self) -> float:
        """分析 LSB = FS / 2^n_total。"""
        return self.fs_diff_v / (2 ** self.n_total)

    @property
    def lsb_xfer_v(self) -> float:
        """传输码 LSB = FS / 2^n_xfer。"""
        return self.fs_diff_v / (2 ** self.n_xfer)

    def check(self) -> list[str]:
        """返回不自洽项（空 = 通过）。这是防口径漂移的闸门。"""
        errs = []
        rel = abs(self.lsb2_v - self.lsb_analysis_v) / self.lsb_analysis_v
        if rel > 1e-12:
            errs.append(
                f"位账不自洽：LSB2={self.lsb2_v:.6e} vs LSB_total={self.lsb_analysis_v:.6e}"
                f"（相对差 {rel:.2e}），检查 n1/n2/n_red")
        if self.n_total != 20:
            errs.append(f"总码宽 {self.n_total} != 20（BL-v3 冻结值）")
        return errs


# ---------------------------------------------------------------- profile

ProfileName = Literal["ideal", "native_as_wired", "native_candidate_u3b7"]


@dataclass(frozen=True)
class ArchProfile:
    """架构 profile：只描述「物理上怎么接」，不含任何非理想参数。

    native_as_wired 的 n1_effective 是 **7**，因为当前网表把同一组 D<6:0>
    广播给 18 片（T02 复核）。已知缺陷必须暴露，不许暗中修正。
    """

    name: ProfileName
    n1_effective: int            # 一级实际判决数
    units_per_side: int          # 每侧单位数
    units_per_slice: int         # 每片单位数
    n_slices_active: int         # 每次参与转换的片数
    mapping: str                 # 物理映射方式
    note: str = ""

    @property
    def lsb1_effective_v(self) -> float:
        """按实际判决数算的一级 LSB —— 与合同标称值可能不同。"""
        return 10.0 / (2 ** self.n1_effective)


PROFILES: dict[str, ArchProfile] = {
    "ideal": ArchProfile(
        name="ideal",
        n1_effective=10, units_per_side=1024, units_per_slice=128,
        n_slices_active=8, mapping="binary_3p7",
        note="BL-v3 标称：3 bit unary（8 片）+ 片内 7 bit 二进制 = 1024 码"),

    "native_as_wired": ArchProfile(
        name="native_as_wired",
        n1_effective=7, units_per_side=1024, units_per_slice=128,
        n_slices_active=8, mapping="broadcast_d6_0",
        note="当前网表的真实接法：同一组 D<6:0> 广播给 8 片 → 只有 7 bit 有效，"
             "LSB1 = 78.1 mV。这是缺陷，不是版本选择。"),

    "native_candidate_u3b7": ArchProfile(
        name="native_candidate_u3b7",
        n1_effective=10, units_per_side=1024, units_per_slice=128,
        n_slices_active=8, mapping="u3b7",
        note="候选：c=128H+L，H 片全 128C 接高轨、1 片 7 bit 细分。"
             "要求原固定接 VCM 的第 8 个 1C 改成可切换（未获授权）。"),
}


# ---------------------------------------------------------------- 非理想参数

@dataclass
class NonIdealities:
    """非理想参数。每项带来源标签，工程假设与压力测试分开。"""

    # 噪声（输入折算 Vrms）—— 全部 assumed，来自 Fig.12 读图与既有预算
    ktc_v: float = 17.3e-6
    ra_broad_v: float = 24.0e-6
    cmp_v: float = 9.7e-6
    ref_v: float = 2.9e-6

    # DAC1 单位电容失配（stress 档，不是 PDK 值）
    sigma_u: float = 0.002             # 0.2%  [stress]
    chip_seed: int = 7                 # 固定虚拟芯片

    # 参考
    c_decap_f: float = 300e-12         # [assumed]
    r_buf_ohm: float = 20.0            # [assumed]
    droop_enabled: bool = False

    # DAC 建立
    settle_tau_s: float | None = None  # [assumed]，None = 理想
    t_bit_s: float = 3e-9

    # RA
    a0_db: float | None = None         # None = 无限增益
    ra_tau_s: float | None = None
    ra_t_settle_s: float = 17e-9

    # 8× 重复
    m_rep: int = 1
    rho_rep: float = 0.61              # [stress] 反解值，不是实测
    rep_weight: str = "tri"

    # 开关
    noise_enabled: bool = True

    def sources(self) -> dict[str, str]:
        return {
            "ktc_v": "assumed: Fig.12 读图 + 预算", "ra_broad_v": "assumed: 同上",
            "cmp_v": "assumed: 同上", "ref_v": "assumed: 偏小未含 droop",
            "sigma_u": "stress: 0.2% 压力档，非 PDK", "rho_rep": "stress: 反解值非实测",
            "c_decap_f": "assumed", "r_buf_ohm": "assumed",
            "settle_tau_s": "assumed（None=理想）", "a0_db": "assumed（None=无限）",
        }


# ---------------------------------------------------------------- 组合

@dataclass
class Config:
    """一次实验的完整条件。显式传入，无隐式全局。"""

    contract: NumericalContract = field(default_factory=NumericalContract)
    profile: ArchProfile = field(default_factory=lambda: PROFILES["ideal"])
    nonideal: NonIdealities = field(default_factory=NonIdealities)
    seed: int = 1
    label: str = "default"

    def validate(self) -> list[str]:
        errs = list(self.contract.check())
        if self.profile.name == "native_as_wired" and self.contract.n1 != 10:
            errs.append("native_as_wired 与 n1=10 的合同混用：必须显式说明按 7 bit 复现")
        if self.nonideal.m_rep < 1:
            errs.append("m_rep 必须 ≥1")
        if self.nonideal.rep_weight not in ("tri", "box"):
            errs.append("rep_weight 只能是 tri/box")
        return errs

    def to_dict(self) -> dict:
        d = asdict(self)
        d["contract"]["derived"] = {
            "n_total": self.contract.n_total,
            "lsb1_v": self.contract.lsb1_v,
            "resid_window_pp_v": self.contract.resid_window_pp_v,
            "lsb2_v": self.contract.lsb2_v,
            "lsb_analysis_v": self.contract.lsb_analysis_v,
            "lsb_xfer_v": self.contract.lsb_xfer_v,
        }
        d["nonideal_sources"] = self.nonideal.sources()
        d["profile_lsb1_effective_v"] = self.profile.lsb1_effective_v
        return d


def make_config(profile: str = "ideal", *, label: str | None = None,
                **nonideal_kw) -> Config:
    """构造配置的便捷入口；未知 profile 直接报错。"""
    if profile not in PROFILES:
        raise KeyError(f"未知 profile '{profile}'，可选：{list(PROFILES)}")
    ni = NonIdealities(**nonideal_kw)
    return Config(profile=PROFILES[profile], nonideal=ni,
                  label=label or profile)
