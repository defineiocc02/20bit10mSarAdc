# [CODE-INDEX] contracts.py —— 样本身份与结果合同
#
# 规范要求：每笔必须能定位「哪一笔、哪一步」，且原码延迟返回时只能用该笔冻结上下文。
"""样本身份、帧结果、故障。"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class SampleContext:
    """一笔转换的完整身份。缺字段不如显式置 None，不许默认值冒充已知。"""

    sample_id: int
    reset_epoch: int = 0
    t_sample_s: float = 0.0                # 真实采样时刻（不是输出到达时刻）
    t_done_s: float | None = None
    t_emit_s: float | None = None

    # 物理归属
    slice_ids: tuple[int, ...] = ()
    sample_commands: dict[str, Any] = field(default_factory=dict)
    conversion_commands: dict[str, Any] = field(default_factory=dict)

    # 码域
    d1_raw: int | None = None              # 一级原码（n1 位）
    d1_norm: int | None = None             # 规范化码（服务架构 profile）
    d2_raw: int | None = None              # 二级原码（n2 位）
    dt: int | None = None                  # 重复码（m_rep 位）

    # 残差与中间量（便于逐笔追踪）
    v_resid_v: float | None = None
    v_top_init_v: float | None = None

    # 配置与校准
    architecture_profile: str = "ideal"
    calibration_generation: int = 0

    # 结果
    code_xfer: int | None = None            # 22 bit offset binary
    valid: bool = True
    fault_reason: str | None = None

    def to_row(self) -> dict:
        d = asdict(self)
        d["slice_ids"] = list(self.slice_ids)
        return d


@dataclass
class FrameResult:
    """一帧（一个样本）的结果 + 可选的追踪。"""

    ctx: SampleContext
    trace: list[dict] = field(default_factory=list)

    def add_event(self, t_s: float, kind: str, **kv):
        self.trace.append(dict(t=t_s, kind=kind, **kv))


FAULTS = {
    "NONE": None,
    "RESID_OVERLOAD": "残差超出 DAC2 窗口",
    "REF_DROOP": "参考跌落超阈值",
    "TIMEOUT": "判决未在截止时间内完成",
    "MAPPING_CONFLICT": "底板命令出现非法导通组合",
    "SATURATED": "重构码饱和",
}
