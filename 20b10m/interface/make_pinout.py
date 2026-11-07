#!/usr/bin/env python3
"""make_pinout.py —— 生成 36 pad 引脚定义图（20.5 bit / 10 MS/s / 180 nm BCD）"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import matplotlib.font_manager as fm

plt.rcParams["font.family"] = "PingFang SC"
plt.rcParams["axes.unicode_minus"] = False

PINS = [
    ("VINP", "模拟输入", "A"), ("VINN", "模拟输入", "A"), ("VREF5", "基准", "R"),
    ("VREF2", "基准", "R"), ("VCM", "基准", "R"), ("VDD5A", "5V 电源", "P"),
    ("VDD5A", "5V 电源", "P"), ("VDD5A", "5V 电源", "P"), ("VSSA", "地", "G"),
    ("VSSA", "地", "G"), ("VSSA", "地", "G"), ("VSSA", "地", "G"),
    ("CLKP", "时钟", "C"), ("CLKN", "时钟", "C"), ("VDD18A", "1.8V 电源", "P"),
    ("VSSD", "地", "G"), ("VDD18D", "1.8V 电源", "P"), ("VSSD", "地", "G"),
    ("VDDIO", "IO 电源", "P"), ("VSSIO", "地", "G"), ("DOUTP", "LVDS 输出", "D"),
    ("DOUTN", "LVDS 输出", "D"), ("DRDYP", "LVDS 输出", "D"), ("DRDYN", "LVDS 输出", "D"),
    ("CLKOUTP", "LVDS 输出", "D"), ("CLKOUTN", "LVDS 输出", "D"), ("SCLK", "SPI", "S"),
    ("SDI", "SPI", "S"), ("SDO", "SPI", "S"), ("CS", "SPI", "S"),
    ("CAL_TRIG", "校准", "S"), ("RSTN", "复位", "S"), ("TEST0", "测试", "T"),
    ("TEST1", "测试", "T"), ("MON", "观测", "T"), ("SPARE", "备用", "T"),
]
COLOR = {"A": "#B5D4F4", "R": "#CECBF6", "P": "#F7C1C1", "G": "#D3D1C7",
         "C": "#FAC775", "D": "#C0DD97", "S": "#9FE1CB", "T": "#E5E5E5"}
EDGE = {"A": "#185FA5", "R": "#534AB7", "P": "#A32D2D", "G": "#5F5E5A",
        "C": "#854F0B", "D": "#3B6D11", "S": "#0F6E56", "T": "#888780"}

fig, ax = plt.subplots(figsize=(10.5, 10.5))
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.set_aspect("equal"); ax.axis("off")

D0, D1 = 2.0, 8.0          # die 边界
ax.add_patch(Rectangle((D0, D0), D1-D0, D1-D0, facecolor="#FAFAF8", edgecolor="#2C2C2A", lw=1.8))
C0 = D0 + 0.45
ax.add_patch(Rectangle((C0, C0), D1-D0-0.9, D1-D0-0.9, facecolor="none",
                       edgecolor="#B4B2A9", lw=0.8, ls="--"))

pos = {}
span = (D1 - D0 - 0.5) / 8
for i in range(9):
    pos[i+1]  = (D0 + 0.25 + i*span, D1)
    pos[i+10] = (D1, D1 - 0.25 - i*span)
    pos[i+19] = (D1 - 0.25 - i*span, D0)
    pos[i+28] = (D0, D0 + 0.25 + i*span)

for idx, (name, desc, grp) in enumerate(PINS, start=1):
    x, y = pos[idx]
    w, h = (0.46, 0.16) if y in (D0, D1) else (0.16, 0.46)
    ax.add_patch(Rectangle((x-w/2, y-h/2), w, h, facecolor=COLOR[grp],
                           edgecolor=EDGE[grp], lw=0.9, zorder=3))
    fs = 6.6
    if y == D1:                       # 上边：名称在内侧竖排，编号在外侧
        ax.text(x, D1+0.30, name, ha="center", va="bottom", fontsize=fs, rotation=90, color="#2C2C2A")
        ax.text(x, D1+0.78, str(idx), ha="center", va="bottom", fontsize=7.5, color="#2C2C2A")
    elif y == D0:                     # 下边
        ax.text(x, D0-0.30, name, ha="center", va="top", fontsize=fs, rotation=90, color="#2C2C2A")
        ax.text(x, D0-0.78, str(idx), ha="center", va="top", fontsize=7.5, color="#2C2C2A")
    elif x == D1:                     # 右边
        ax.text(D1+0.28, y, name, ha="left", va="center", fontsize=fs, color="#2C2C2A")
        ax.text(D1+0.80, y, str(idx), ha="left", va="center", fontsize=7.5, color="#2C2C2A")
    else:                             # 左边
        ax.text(D0-0.28, y, name, ha="right", va="center", fontsize=fs, color="#2C2C2A")
        ax.text(D0-0.80, y, str(idx), ha="right", va="center", fontsize=7.5, color="#2C2C2A")

# 中心信息
ax.text(5.0, 6.55, "SAR20-10M", ha="center", va="center", fontsize=22, color="#2C2C2A")
ax.text(5.0, 6.05, "20.5 bit · 10 MS/s（2×5 MS/s 交织）", ha="center", va="center", fontsize=11.5, color="#444441")
ax.text(5.0, 5.62, "180 nm BCD · 36 pad（60×60 µm / pitch 90）· 差分 10 Vpp", ha="center", va="center", fontsize=9.5, color="#5F5E5A")
ax.text(5.0, 5.18, "核心 830×830 µm ｜ 裸片 1030×1030 µm ≈ 1.06 mm²", ha="center", va="center", fontsize=8.5, color="#5F5E5A")
ax.text(5.0, 4.72, "上：模拟输入/基准/5V　下：LVDS + SPI + 测试", ha="center", va="center", fontsize=8, color="#5F5E5A")
ax.text(5.0, 4.42, "左：SPI/复位/测试　　右：时钟/1.8V/地", ha="center", va="center", fontsize=8, color="#5F5E5A")

legend = [("A", "模拟输入"), ("R", "基准"), ("P", "电源"), ("G", "地"),
          ("C", "时钟"), ("D", "LVDS 输出"), ("S", "SPI/控制"), ("T", "测试/备用")]
for i, (g, label) in enumerate(legend):
    x = 2.55 + (i % 4) * 1.30; y = 3.55 - (i // 4) * 0.34
    ax.add_patch(Rectangle((x, y-0.08), 0.18, 0.16, facecolor=COLOR[g], edgecolor=EDGE[g], lw=0.7))
    ax.text(x+0.24, y, label, ha="left", va="center", fontsize=7.2, color="#444441")

# 1 脚标记
ax.plot([D0], [D1], marker="o", ms=5, color="#A32D2D", zorder=5)
ax.annotate("PIN 1", xy=(D0, D1), xytext=(D0-0.95, D1+0.95), fontsize=8, color="#A32D2D",
            arrowprops=dict(arrowstyle="-", color="#A32D2D", lw=0.8))

plt.tight_layout()
plt.savefig("pinout_36pad.png", dpi=220, bbox_inches="tight", facecolor="white")
print("saved pinout_36pad.png")
