#!/usr/bin/env python3
"""make_floorplan.py —— 10 MS/s floorplan（die 1030 µm / core 830 µm，MIM 1 fF/µm²）"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch

plt.rcParams["font.family"] = "PingFang SC"
plt.rcParams["axes.unicode_minus"] = False

DIE = 1030.0
C0, C1 = 100.0, 930.0

fig, ax = plt.subplots(figsize=(10.2, 10.2))
ax.set_xlim(-70, DIE + 70); ax.set_ylim(-70, DIE + 70)
ax.set_aspect("equal"); ax.axis("off")

ax.add_patch(Rectangle((0, 0), DIE, DIE, facecolor="#FCFCFA", edgecolor="#2C2C2A", lw=2.0))
ax.add_patch(Rectangle((C0, C0), C1-C0, C1-C0, facecolor="none", edgecolor="#888780", lw=1.0, ls="--"))

def block(x0, y0, x1, y1, name, spec, fc, ec, fs=9.5, area=None):
    ax.add_patch(Rectangle((x0, y0), x1-x0, y1-y0, facecolor=fc, edgecolor=ec,
                           lw=1.2, alpha=0.88, zorder=3))
    cx, cy, h = (x0+x1)/2, (y0+y1)/2, y1-y0
    ax.text(cx, cy + (12 if h > 80 else 0), name, ha="center", va="center",
            fontsize=fs, color="#1a1a1a", zorder=4, weight="bold")
    if spec:
        ax.text(cx, cy - (14 if h > 80 else 0), spec, ha="center", va="center",
                fontsize=7.2, color="#333333", zorder=4)
    if area:
        ax.text(x1-5, y1-7, area, ha="right", va="top", fontsize=6.4, color="#555555", zorder=4)

block(105, 520, 405, 905, "DAC1-A（9×SdacSlice）", "62 pF/侧 · 1 fF/µm² MIM\n含 7 位开关 + 自举采样", "#CECBF6", "#534AB7", area="0.130 mm²")
block(425, 520, 725, 905, "DAC1-B（9×SdacSlice）", "相位 +100 ns\n同 A 相", "#CECBF6", "#534AB7", area="0.130 mm²")

block(105, 405, 375, 505, "CmpCoarse4b + 2b SAR", "15 cmp + 2 步", "#FAC775", "#854F0B", fs=8.5, area="0.028 mm²")
block(390, 405, 550, 505, "RefBuffer", "DynRefBuf · 5 V/2.5 V", "#F7C1C1", "#A32D2D", fs=8.5, area="0.026 mm²")
block(565, 405, 725, 505, "去耦 360 pF", "MOS 2.35 fF/µm²", "#F7C1C1", "#A32D2D", area="0.153 mm²")

block(355, 290, 475, 390, "RaMux + RingAmp3", "共享 RA\nZout 300 Ω", "#9FE1CB", "#0F6E56", area="0.016")

block(105, 250, 265, 385, "Sar2Ct-A", "C_INC+DAC2+rep.\n11 bit + 8×", "#B5D4F4", "#185FA5", area="0.010 mm²")
block(565, 250, 725, 385, "Sar2Ct-B", "C_INC+DAC2+rep.\n11 bit + 8×", "#B5D4F4", "#185FA5", area="0.010 mm²")

block(125, 110, 705, 230, "DigitalTop", "两相调度 / SliceShuffler / SINC2 / LMS / 帧打包 + LVDS", "#C0DD97", "#3B6D11", fs=9.5, area="0.100 mm²")

for x, name, col, fc in [(330, "VINP/N", "#185FA5", "#B5D4F4"), (515, "CLKP/N", "#854F0B", "#FAC775")]:
    yy = DIE if name.startswith("VIN") else 0
    ax.add_patch(Rectangle((x-22, yy-9), 44, 18, facecolor=fc, edgecolor=col, lw=0.8, zorder=5))
    ax.text(x, yy+22 if yy else yy-26, name, ha="center", va="center", fontsize=7.4, color=col)

def arr(x0, y0, x1, y1, color="#444441"):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=13,
                                 color=color, lw=1.1, zorder=6))

arr(255, 520, 255, 505, "#534AB7")
arr(565, 520, 565, 505, "#534AB7")
arr(355, 405, 380, 390, "#185FA5")
arr(415, 290, 320, 250, "#0F6E56")
arr(415, 290, 565, 250, "#0F6E56")
arr(415, 230, 415, 250, "#3B6D11")

ax.annotate("", xy=(0, -42), xytext=(DIE, -42), arrowprops=dict(arrowstyle="<->", color="#5F5E5A", lw=0.9))
ax.text(DIE/2, -57, "1030 µm（die，pad 60×60 / pitch 90）", ha="center", va="top", fontsize=8, color="#5F5E5A")
ax.annotate("", xy=(C0, 960), xytext=(C1, 960), arrowprops=dict(arrowstyle="<->", color="#888780", lw=0.9))
ax.text((C0+C1)/2, 972, "830 µm（core，0.69 mm² @1 fF/µm²）", ha="center", va="bottom", fontsize=8, color="#5F5E5A")

ax.text(DIE/2, DIE+42, "SAR20-10M Floorplan（2×5 MS/s，MIM 1 fF/µm² 基准）",
        ha="center", va="bottom", fontsize=11.5, color="#1a1a1a")

plt.tight_layout()
plt.savefig("floorplan_10m.png", dpi=220, bbox_inches="tight", facecolor="white")
print("saved floorplan_10m.png")
