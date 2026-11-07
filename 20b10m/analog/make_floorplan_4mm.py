#!/usr/bin/env python3
"""make_floorplan_4mm.py —— 4 mm² 部分交织 floorplan（成电 die photo + ADI RDAC 切片）"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

plt.rcParams["font.family"] = "PingFang SC"
plt.rcParams["axes.unicode_minus"] = False

DIE_W, DIE_H = 2200.0, 1800.0
C0X, C1X = 100.0, 2100.0
C0Y, C1Y = 100.0, 1700.0

fig, ax = plt.subplots(figsize=(11.5, 9.6))
ax.set_xlim(-60, DIE_W + 60); ax.set_ylim(-60, DIE_H + 90)
ax.set_aspect("equal"); ax.axis("off")

ax.add_patch(Rectangle((0, 0), DIE_W, DIE_H, facecolor="#FCFCFA", edgecolor="#2C2C2A", lw=2.2))
ax.add_patch(Rectangle((C0X, C0Y), C1X-C0X, C1Y-C0Y, facecolor="none", edgecolor="#888780", lw=1.0, ls="--"))

def block(x0, y0, x1, y1, name, spec, fc, ec, fs=9.5, area=None):
    ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, facecolor=fc, edgecolor=ec,
                           lw=1.2, alpha=0.9, zorder=3))
    cx, cy, h = (x0+x1)/2, (y0+y1)/2, y1-y0
    dy = 45 if h > 260 else (22 if h >= 100 else 0)
    ax.text(cx, cy + dy, name, ha="center", va="center", fontsize=fs,
            color="#1a1a1a", zorder=4, weight="bold")
    if spec:
        ax.text(cx, cy - dy, spec, ha="center", va="center",
                fontsize=7.4, color="#333333", zorder=4)
    if area:
        ax.text(x1-6, y1-8, area, ha="right", va="top", fontsize=6.6, color="#555555", zorder=4)

block(150, 1200, 850, 1520, "DAC1-P（18 slices）", "9 列 × 2 排，3.456 pF/片\n8 用 + 1 备", "#CECBF6", "#534AB7", fs=9.2, area="0.224 mm²")
block(950, 1200, 1650, 1520, "DAC1-N（18 slices）", "与 P 镜像\n角色每 100 ns 交换", "#CECBF6", "#534AB7", fs=9.2, area="0.224 mm²")

block(1700, 1300, 1980, 1520, "Coarse ADC", "4b flash + 2b SAR\n15 cmp", "#FAC775", "#854F0B", fs=8.4, area="0.062")

block(150, 1050, 1650, 1170, "SliceMux 18:1", "8 片汇流到 RA；偏斜 ≤50 ps", "#EEEDFE", "#534AB7", fs=9.0, area="0.180")

block(800, 800, 1100, 1000, "RA（单套）", "三级 ring amp，Zout 300 Ω", "#9FE1CB", "#0F6E56", fs=9.0, area="0.060")

block(800, 560, 1100, 780, "CT2 + DAC2 + Replica", "C_INC 1 pF；11 bit + 8×", "#B5D4F4", "#185FA5", fs=8.6, area="0.070")

block(1750, 800, 1980, 1150, "Reference Buffers", "5 V + 2.5 V\nRout ≤20 Ω", "#F7C1C1", "#A32D2D", fs=8.4, area="0.081")
block(1750, 300, 1980, 760, "去耦 1.0 nF", "VREF 主去耦\n（右侧近回流）", "#F7C1C1", "#A32D2D", fs=8.0, area="0.106")

block(150, 550, 400, 1000, "ClkRx + BiasGen", "200 MHz 接收\n偏置/共模", "#FAC775", "#854F0B", fs=8.2, area="0.112")
block(450, 560, 740, 1000, "去耦 bank-L", "VCM / 预充", "#F7C1C1", "#A32D2D", fs=7.8, area="0.128")

block(400, 200, 1400, 500, "DigitalTop（单套）", "调度 / SliceShuffler / SINC2 / 冻结系数重构 / 帧打包 / LVDS",
      "#C0DD97", "#3B6D11", fs=9.4, area="0.300 mm²")
block(1500, 200, 1700, 500, "测试/观测", "MON 8:1\n探针", "#E5E5E5", "#888780", fs=8.0, area="0.060")

for i in range(12):
    t = 175 + i*150
    for (x, y) in [(t, 30), (DIE_W-30, t), (t, DIE_H-30), (30, t)]:
        ax.add_patch(Rectangle((x-30, y-30), 60, 60, facecolor="#D3D1C7",
                               edgecolor="#888780", lw=0.4, zorder=5))

def arr(x0, y0, x1, y1, color="#444441"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=14,
                                 color=color, lw=1.2, zorder=6))

arr(500, 1200, 500, 1170, "#534AB7")
arr(1200, 1200, 1200, 1170, "#534AB7")
arr(900, 1050, 900, 1000, "#534AB7")
arr(950, 800, 950, 780, "#0F6E56")
arr(950, 560, 950, 500, "#3B6D11")
arr(1750, 950, 1100, 950, "#A32D2D")

ax.annotate("", xy=(0, -40), xytext=(DIE_W, -40), arrowprops=dict(arrowstyle="<->", color="#5F5E5A", lw=0.9))
ax.text(DIE_W/2, -55, "2200 µm（die，3.96 mm²）· 48 pad · 60×60 / pitch 150", ha="center", va="top", fontsize=8.8, color="#5F5E5A")
ax.text(DIE_W/2, 1840, "SAR20-10M · 4 mm² 部分交织（成电堆叠 + ADI RDAC 切片）",
        ha="center", va="bottom", fontsize=12.5, color="#1a1a1a")

plt.tight_layout()
plt.savefig("floorplan_4mm.png", dpi=220, bbox_inches="tight", facecolor="white")
print("saved floorplan_4mm.png")
