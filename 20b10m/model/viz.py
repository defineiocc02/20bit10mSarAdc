"""viz.py —— 出图基础设施（沿用参考库 20b10mtask 的方案）

对齐点：
- 物理尺寸用 mm（146 mm 单栏），不是英寸；
- 中文字体先校验“码”字，再设 family/weight；
- 每张图 title / subtitle / note 三段式；
- 同时出 PNG(300 dpi) + SVG(路径字形) + PDF；
- manifest.json 记录脚本/数据/输出的 SHA256、版本、字体、尺寸。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager

MM = 25.4
WIDTH_MM = 146


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _base_style() -> str:
    font = "Arial"
    try:
        font_manager.findfont(font_manager.FontProperties(family=[font]), fallback_to_default=False)
    except ValueError:
        font = "DejaVu Sans"
    mpl.rcParams.update({
        "font.family": font,
        "font.size": 8,
        "axes.labelsize": 8,
        "axes.titlesize": 8,
        "axes.linewidth": 0.7,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.major.width": 0.7,
        "ytick.major.width": 0.7,
        "grid.linewidth": 0.45,
        "lines.linewidth": 1,
        "path.simplify": False,
        "pdf.fonttype": 42,
        "svg.fonttype": "path",
        "svg.hashsalt": "sar20-10m-model",
        "mathtext.fontset": "dejavusans",
        "savefig.facecolor": "white",
    })
    return font


def chinese_style() -> str:
    """优先 Hiragino Sans GB，其次 PingFang SC；校验“码”字存在。"""
    _base_style()
    for family, weight in (("Hiragino Sans GB", 300), ("PingFang SC", 300)):
        try:
            path = font_manager.findfont(
                font_manager.FontProperties(family=[family], weight=weight),
                fallback_to_default=False,
            )
        except ValueError:
            continue
        if ord("码") not in font_manager.get_font(path).get_charmap():
            continue
        mpl.rcParams.update({
            "font.family": family,
            "font.weight": weight,
            "axes.labelweight": weight,
            "axes.titleweight": weight,
            "axes.unicode_minus": False,
        })
        return family
    raise RuntimeError("需要 Hiragino Sans GB 或 PingFang SC 才能画中文图")


def annotate(fig, title: str, subtitle: str, note: str) -> None:
    fig.text(0.11, 0.975, title, fontsize=10.5, fontweight=600, va="top")
    fig.text(0.11, 0.930, subtitle, fontsize=7.6, va="top")
    fig.text(0.11, 0.015, note, fontsize=6.8, va="bottom")


def save(fig, stem: Path, *, pdf: bool = True) -> list[Path]:
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    outs = []
    png = stem.with_suffix(".png")
    svg = stem.with_suffix(".svg")
    fig.savefig(png, dpi=300)
    fig.savefig(svg, metadata={"Date": None})
    outs += [png, svg]
    if pdf:
        pdfp = stem.with_suffix(".pdf")
        fig.savefig(pdfp, metadata={"CreationDate": None, "ModDate": None})
        outs.append(pdfp)
    return outs


def write_manifest(out_dir: Path, *, script: Path, data: list[Path],
                   outputs: list[Path], dims: list[tuple[int, int]],
                   font: str, extra: dict | None = None) -> Path:
    manifest = {
        "schema": "sar20_10m_model_figures_v1",
        "plot_source": str(script),
        "plot_source_sha256": sha(script),
        "data_source_sha256": {str(p): sha(p) for p in data},
        "matplotlib": mpl.__version__,
        "numpy": np.__version__,
        "font": {"family": font, "checked_glyph": "码"},
        "dimensions_mm": [list(d) for d in dims],
        "output_sha256": {p.name: sha(p) for p in outputs},
    }
    if extra:
        manifest.update(extra)
    path = out_dir / "manifest.json"
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
