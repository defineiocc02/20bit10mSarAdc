# [CODE-INDEX] pipeline.py —— 唯一端到端装配入口
#
# 规范要求（§6.2）：
#   - 每次试探必须更新实际 CDAC 命令、计算剩余电压，再由比较器判决；
#   - 不能把输入直接 round 为 n1 位然后补造 SAR 记录；
#   - 理想量化器只作 oracle，必须单独标注，不进入声称物理闭环的路径。
#
# 本文件实现：采样 → hold → SAR1 逐位（真实底板切换 + 电荷求解）→ 残差
#             → ADC2（当前 = ideal_proxy，明确标注）→ 重构 → 22 bit 传输码
"""端到端装配：一个样本走一遍。"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..config import Config
from ..contracts import SampleContext, FrameResult, FAULTS
from ..rng import ChipInstance, NoiseStreams
from .charge import DiffCdac, binary_weights


def profile_weights(profile: str, n_units: int, n_bits: int):
    """返回 (判决位权重 MSB 在前, termination 单位数)。

    真实拓扑：每侧 1024 单位 = 1..512（10 位和 1023）+ 1 个 termination。
    termination 固定接低轨，不参与判决 —— 它让总电容恰为 1024，保证 LSB 精确。

    native_as_wired（7 判决）：8 片同码并联，权重 = 8×[1..64]，termination = 8。
    """
    n_active = 8
    if profile == "native_as_wired":
        per = binary_weights(n_units // n_active)             # 每片 128 -> [1..64] + term
        bits = per[:n_bits] * n_active
        term = int(per[n_bits:].sum()) * n_active if len(per) > n_bits else 0
        return bits[::-1], term
    full = binary_weights(n_units)                            # [1..512, term]
    bits = full[:n_bits]
    term = int(full[n_bits:].sum()) if len(full) > n_bits else 0
    return bits[::-1], term


@dataclass
class Outcome:
    ctx: SampleContext
    trace: list = field(default_factory=list)
    v_resid_v: float = 0.0
    overload: bool = False


class Pipeline:
    """一条转换链：一片差分 CDAC + SAR1 + ADC2(proxy) + 重构。"""

    def __init__(self, cfg: Config, chip: ChipInstance | None = None,
                 streams: NoiseStreams | None = None):
        errs = cfg.validate()
        if errs:
            raise ValueError("配置非法：" + "；".join(errs))
        self.cfg = cfg
        c = cfg.contract
        self.chip = chip or ChipInstance(
            n_units=c.n_units_per_side, sigma_u=cfg.nonideal.sigma_u,
            seed=cfg.nonideal.chip_seed)
        self.streams = streams or NoiseStreams(cfg.seed)

        self.n1 = cfg.profile.n1_effective
        self.weights, self.term_units = profile_weights(
            cfg.profile.name, c.n_units_per_side, self.n1)
        if len(self.weights) != self.n1:
            raise ValueError(f"权重数 {len(self.weights)} 与 profile n1={self.n1} 不符")

        # 单位 → 位 的掩码（MSB 在前）；termination 单位留在末尾不切换
        self.bit_masks = []
        start = 0
        for w in self.weights:
            m = np.zeros(c.n_units_per_side, bool)
            m[start:start + int(w)] = True
            self.bit_masks.append(m)
            start += int(w)
        if start + self.term_units != c.n_units_per_side:
            raise ValueError(
                f"位权 {start} + termination {self.term_units} != 每侧 {c.n_units_per_side}")

        caps = self.chip.caps(c.c_unit_f)
        self.cdac = DiffCdac(caps, caps.copy(), c.vref_p, c.vref_n, c.vcm)
        self.lsb1_eff = c.fs_diff_v / (2 ** self.n1)
        self._tol = 1e-9          # 1 nV 判决容差，远小于 LSB，只为吸收浮点抖动

    # ---------------------------------------------------------------- 一次转换

    def convert(self, vin_p: float, vin_n: float, sid: int = 0,
                trace: bool = False) -> Outcome:
        """差分输入 -> 单侧码域 x = (vp-vn)/2 + VCM，再走单端 CDAC 逐位。

        拓扑说明：CDAC 是「底板加权平均」型 ——
            采样时底板 = x，顶板浮空后 V_top = x；
            转换开始把所有底板切到 VGND，此时 V_top = 0；
            逐位试 VREF，V_top = Σ(b_i·w_i·VREF)/C_tot 就是 DAC 输出；
            判据 V_top >= x 则保留（DAC 还没超过输入）。
            残差 = x − V_top（DAC 超过输入时为负）。
        """
        c = self.cfg.contract
        x = (vin_p - vin_n) / 2.0 + c.vcm
        x = float(np.clip(x, 0.0, c.vref_p))
        ctx = SampleContext(sample_id=sid, architecture_profile=self.cfg.profile.name)
        tr = []

        def ev(kind, **kv):
            if trace:
                tr.append(dict(sid=sid, kind=kind, **kv))

        # ---- 采样 + hold ----
        self.cdac.sample(x, c.vcm)
        self.cdac.hold()
        ev("sample", x=x)
        ctx.v_top_init_v = x

        # ---- 全部底板切到 VGND（转换起点）----
        allmask = np.ones(c.n_units_per_side, bool)
        self.cdac.switch_units("P", allmask, "VGND", x, c.vcm)
        ev("reset_bottom", vtop=self.cdac.vtop_p)

        # ---- SAR1 逐位 ----
        code = 0
        for b, mask in enumerate(self.bit_masks):
            self.cdac.switch_units("P", mask, "VREF", x, c.vcm)
            v = self.cdac.vtop_p
            ev("trial", bit=b, vdac=v)
            # 判据：DAC 已经**超过**输入才撤销（严格大于 + 浮点容差）。
            # 用 >= 会把「恰好落在码边界」的点错误地归到下一档，d1 少 1、残差顶满格。
            if v > x + self._tol:
                self.cdac.switch_units("P", mask, "VGND", x, c.vcm)   # 撤销
                ev("revert", bit=b)
            else:
                code |= (1 << (self.n1 - 1 - b))
                ev("keep", bit=b, vdac=v)

        # ---- 残差：x − DAC ----
        v_dac = self.cdac.vtop_p
        resid = x - v_dac
        ctx.d1_raw = code
        ctx.v_resid_v = resid

        half_win = c.resid_window_pp_v / 4.0      # 单侧窗口 = 差分窗口的一半
        if abs(resid) > half_win:
            ctx.valid = False
            ctx.fault_reason = FAULTS["RESID_OVERLOAD"]

        # ---- ADC2（ideal_proxy）----
        rel = float(np.clip(resid / half_win, -1.0, 1.0))
        d2 = int(round((rel + 1.0) * 0.5 * (2 ** c.n2)))
        d2 = int(np.clip(d2, 0, 2 ** c.n2 - 1))
        ctx.d2_raw = d2

        # ---- 重构 ----
        raw = code * (2 ** (c.n2 - c.n_red)) + (d2 - 2 ** (c.n2 - 1))
        code_x = int(np.clip(raw, 0, 2 ** c.n_total - 1))
        ctx.code_xfer = code_x << (c.n_xfer - c.n_total)
        ev("done", code=code_x, d2=d2)

        return Outcome(ctx=ctx, trace=tr, v_resid_v=resid,
                       overload=(ctx.fault_reason is not None))

    # ---------------------------------------------------------------- 批量

    def run(self, vin_p: np.ndarray, vin_n: np.ndarray, trace_ids=()) -> list[Outcome]:
        out = []
        for i in range(len(vin_p)):
            out.append(self.convert(float(vin_p[i]), float(vin_n[i]), sid=i,
                                    trace=(i in trace_ids)))
        return out

    def codes(self, outcomes: list[Outcome]) -> np.ndarray:
        return np.array([o.ctx.code_xfer for o in outcomes], dtype=np.int64)


def make_pipeline(profile: str = "ideal", *, seed: int = 1, **ni_kw) -> Pipeline:
    from ..config import make_config
    cfg = make_config(profile, **ni_kw)
    cfg.seed = seed
    return Pipeline(cfg)
