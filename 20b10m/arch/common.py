"""公共数据结构：一条检查记录。"""
from __future__ import annotations

from dataclasses import dataclass, asdict

PASS, WARN, FAIL = "PASS", "WARN", "FAIL"


@dataclass
class Check:
    cid: str
    item: str
    value: str
    target: str
    verdict: str
    note: str = ""

    def as_dict(self) -> dict:
        return asdict(self)
