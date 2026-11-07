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
            # 字体回退链：中文字形来自 Hiragino/PingFang，µ、−、± 等拉丁符号回退到 Arial。
            # 只写单一 family 时 matplotlib 不会逐字回退，µ 会变成方框（实测踩过）。
            "font.family": [family, "Arial", "Helvetica", "DejaVu Sans"],
            "font.weight": weight,
            "axes.labelweight": weight,
            "axes.titleweight": weight,
            "axes.unicode_minus": False,
            "mathtext.fontset": "dejavusans",
        })
        return family
    raise RuntimeError("需要 Hiragino Sans GB 或 PingFang SC 才能画中文图")


def annotate(fig, title: str, subtitle: str, note: str) -> None:
    """标题/副标题/脚注按「毫米」定位，而不是图高百分比。

    百分比定位在矮图（74 mm）上会让标题压在副标题上；改成 mm 后各尺寸通用。
    """
    h_mm = fig.get_figheight() * 25.4
    fig.text(0.11, 1 - 1.6/h_mm, title, fontsize=10.5, fontweight=600, va="top")
    fig.text(0.11, 1 - 6.0/h_mm, subtitle, fontsize=7.6, va="top")
    fig.text(0.11, 1.0/h_mm, note, fontsize=6.8, va="bottom")


def _plain_log_axes(fig) -> None:
    """把对数轴的 LogFormatter 换成纯文本刻度。

    LogFormatter 用 mathtext 排 10^{-1}，而 mathtext 的 \\mathdefault 解析不到
    font.family 列表，会打成 dummy glyph（实测一条告警一个方框）。这里统一改成
    「0.01 / 0.1 / 1 / 10 / 1e-3」这种纯文本。
    """
    from matplotlib.ticker import FuncFormatter

    def _fmt(v, _pos):
        if v <= 0:
            return ""
        e = np.log10(v)
        if abs(e - round(e)) > 1e-9:
            return ""
        ee = int(round(e))
        return f"{v:g}" if -2 <= ee <= 3 else f"1e{ee}"

    for ax in fig.axes:
        for axis, scale in ((ax.xaxis, ax.get_xscale()), (ax.yaxis, ax.get_yscale())):
            if scale != "log":
                continue
            if "Log" not in type(axis.get_major_formatter()).__name__:
                continue
            axis.set_major_formatter(FuncFormatter(_fmt))
            axis.set_minor_formatter(FuncFormatter(lambda v, p: ""))


def save(fig, stem: Path, *, pdf: bool = True) -> list[Path]:
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    outs = []
    _plain_log_axes(fig)
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
