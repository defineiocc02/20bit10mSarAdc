#!/usr/bin/env python3
"""make_output_timing.py —— 24 bit LVDS DDR 输出帧时序图"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams["font.family"] = "PingFang SC"
plt.rcParams["axes.unicode_minus"] = False

fig, ax = plt.subplots(figsize=(11, 5.2))
ax.set_xlim(-55, 215); ax.set_ylim(-0.6, 4.4); ax.axis("off")

def wave(y, color, label):
    ax.text(-52, y+0.22, label.split("\n")[0], ha="left", va="center", fontsize=9, color="#1a1a1a")
    ax.text(-52, y-0.02, label.split("\n")[1], ha="left", va="center", fontsize=7, color="#5F5E5A")

# CLKOUT 200 MHz：周期 5 ns
y = 3.4
xs, ys = [], []
t = 0.0
while t <= 200:
    xs += [t, t, t+2.5, t+2.5]
    ys += [y, y+0.45, y+0.45, y]
    t += 5
ax.plot(xs, ys, color="#854F0B", lw=1.2)
wave(y, "#854F0B", "CLKOUT\n200 MHz")

# DOUT 帧：0-60 ns 24 bit，60-100 空闲，100-160 下一帧
y2 = 1.9
for base in (0, 100):
    ax.add_patch(Rectangle((base, y2), 60, 0.7, facecolor="#C0DD97", edgecolor="#3B6D11", lw=0.8))
    for k in range(0, 24, 4):
        ax.plot([base + k*2.5, base + k*2.5], [y2, y2+0.7], color="#3B6D11", lw=0.4)
        ax.text(base + k*2.5 + 3, y2+0.35, f"D{23-k}", ha="center", va="center", fontsize=7, color="#1a1a1a")
    ax.text(base+60.8, y2+0.35, "idle 40 ns", ha="left", va="center", fontsize=7.5, color="#5F5E5A")
wave(y2, "#3B6D11", "DOUT\n400 Mbit/s")

# DRDY
y3 = 0.6
for base in (0, 100):
    ax.plot([base, base, base+10, base+10], [y3, y3+0.6, y3+0.6, y3], color="#A32D2D", lw=1.4)
    ax.plot([base+10, base+60], [y3, y3], color="#A32D2D", lw=1.4)
wave(y3, "#A32D2D", "DRDY\n10 ns")

# 时间轴
ax.annotate("", xy=(0, -0.35), xytext=(200, -0.35), arrowprops=dict(arrowstyle="<->", color="#5F5E5A", lw=0.9))
for t in (0, 60, 100, 160, 200):
    ax.plot([t, t], [-0.42, -0.28], color="#5F5E5A", lw=0.8)
    ax.text(t, -0.55, f"{t}", ha="center", va="top", fontsize=7.5, color="#5F5E5A")
ax.text(100, -0.85, "时间 (ns)｜帧周期 100 ns（10 MS/s）｜帧长 60 ns（24 bit × 2.5 ns UI）", ha="center", va="top", fontsize=8, color="#5F5E5A")

# 标注
ax.annotate("采样沿 → 帧首 = 120 ns\n（转换 90 + 后处理 20 + 对齐 10）",
            xy=(0, 3.9), xytext=(70, 3.95), fontsize=8, color="#444441",
            arrowprops=dict(arrowstyle="-", color="#888780", lw=0.8))
ax.text(130, 2.9, "帧格式：{VALID, FAULT, DATA[21:0]}\nMSB first；VALID=0 时接收端丢弃",
        fontsize=8, color="#444441", ha="left", va="center")

plt.tight_layout()
plt.savefig("output_timing.png", dpi=220, bbox_inches="tight", facecolor="white")
print("saved output_timing.png")
