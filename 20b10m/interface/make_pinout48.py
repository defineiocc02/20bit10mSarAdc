#!/usr/bin/env python3
"""make_pinout48.py —— QFN-48 6×6 引脚图（20.5 bit / 10 MS/s）"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams["font.family"] = "PingFang SC"
plt.rcParams["axes.unicode_minus"] = False

# 逆时针：左 1-12 上→下；下 13-24 左→右；右 25-36 下→上；上 37-48 右→左
PINS = [
    # left
    ("VINP","A"),("VINN","A"),("VREF5","R"),("VREF2","R"),("VCM","R"),("VREFN","R"),
    ("VDD5A","P"),("VDD5A","P"),("VDD5A","P"),("VSSA","G"),("VSSA","G"),("VSSA","G"),
    # bottom
    ("CLKP","C"),("CLKN","C"),("VDD18A","P"),("VSSA","G"),("VDD18D","P"),("VSSD","G"),
    ("VDDIO","P"),("VSSIO","G"),("VSSD","G"),("VSSA","G"),("SPARE1","T"),("SPARE2","T"),
    # right
    ("DOUTP","D"),("DOUTN","D"),("CLKOUTP","D"),("CLKOUTN","D"),("DRDYP","D"),("DRDYN","D"),
    ("SCLK","S"),("SDI","S"),("SDO","S"),("CS","S"),("CAL_TRIG","S"),("RSTN","S"),
    # top
    ("TEST0","T"),("TEST1","T"),("MON","T"),("DOUT2P","D"),("DOUT2N","D"),("VDD5A","P"),
    ("VSSA","G"),("VDD18A","P"),("VSSD","G"),("VDDIO","P"),("SPARE3","T"),("SPARE4","T"),
]
COLOR = {"A":"#B5D4F4","R":"#CECBF6","P":"#F7C1C1","G":"#D3D1C7","C":"#FAC775",
         "D":"#C0DD97","S":"#9FE1CB","T":"#E5E5E5"}
EDGE = {"A":"#185FA5","R":"#534AB7","P":"#A32D2D","G":"#5F5E5A","C":"#854F0B",
        "D":"#3B6D11","S":"#0F6E56","T":"#888780"}

fig, ax = plt.subplots(figsize=(11, 11))
ax.set_xlim(-0.3, 12.3); ax.set_ylim(0, 12.4); ax.set_aspect("equal"); ax.axis("off")

P0, P1 = 2.6, 9.4          # package 6.8 units = 6 mm
ax.add_patch(Rectangle((P0,P0), P1-P0, P1-P0, facecolor="#F7F7F4", edgecolor="#2C2C2A", lw=1.8))
ax.add_patch(Rectangle((5.2,5.2), 1.6, 1.6, facecolor="#D3D1C7", edgecolor="#888780", lw=0.8))
ax.text(6.0, 6.0, "EP\nVSSA", ha="center", va="center", fontsize=7, color="#2C2C2A")
ax.text(6.0, 4.55, "die 2.0 mm（4 mm²，示意不按比例）", ha="center", va="top", fontsize=7, color="#5F5E5A")

pitch = (P1-P0-0.4)/11
pos = {}
for i in range(12):   pos[i+1]  = (P0, P1-0.2-i*pitch)          # left top->bottom
for i in range(12):   pos[i+13] = (P0+0.2+i*pitch, P0)          # bottom left->right
for i in range(12):   pos[i+25] = (P1, P0+0.2+i*pitch)          # right bottom->top
for i in range(12):   pos[i+37] = (P1-0.2-i*pitch, P1)          # top right->left

for idx,(name,grp) in enumerate(PINS, start=1):
    x,y = pos[idx]
    w,h = (0.34,0.14) if y in (P0,P1) else (0.14,0.34)
    ax.add_patch(Rectangle((x-w/2,y-h/2),w,h, facecolor=COLOR[grp], edgecolor=EDGE[grp], lw=0.8, zorder=3))
    fs=6.2
    if y==P1:      ax.text(x,P1+0.22,name,ha="center",va="bottom",fontsize=fs,rotation=90,color="#2C2C2A"); ax.text(x,P1+0.62,str(idx),ha="center",va="bottom",fontsize=7,color="#2C2C2A")
    elif y==P0:    ax.text(x,P0-0.22,name,ha="center",va="top",fontsize=fs,rotation=90,color="#2C2C2A");    ax.text(x,P0-0.62,str(idx),ha="center",va="top",fontsize=7,color="#2C2C2A")
    elif x==P1:    ax.text(P1+0.22,y,name,ha="left",va="center",fontsize=fs,color="#2C2C2A");                ax.text(P1+0.72,y,str(idx),ha="left",va="center",fontsize=7,color="#2C2C2A")
    else:          ax.text(P0-0.22,y,name,ha="right",va="center",fontsize=fs,color="#2C2C2A");                ax.text(P0-0.72,y,str(idx),ha="right",va="center",fontsize=7,color="#2C2C2A")

ax.text(6.0, 12.05, "SAR20-10M · QFN-48 6×6 mm · 0.5 mm pitch", ha="center", va="center", fontsize=12, color="#1a1a1a")
ax.text(6.0, 11.55, "20.5 bit · 10 MS/s · 29 功能脚 + 19 电源/地", ha="center", va="center", fontsize=9, color="#444441")

legend=[("A","模拟输入"),("R","基准"),("P","电源"),("G","地"),("C","时钟"),("D","LVDS 输出"),("S","SPI/控制"),("T","测试/备用")]
for i,(g,label) in enumerate(legend):
    x=2.0+(i%4)*2.2; y=1.55-(i//4)*0.34
    ax.add_patch(Rectangle((x,y-0.07),0.18,0.14,facecolor=COLOR[g],edgecolor=EDGE[g],lw=0.7))
    ax.text(x+0.24,y,label,ha="left",va="center",fontsize=7,color="#444441")

ax.plot([P0],[P1],marker="o",ms=5,color="#A32D2D",zorder=5)
ax.annotate("PIN 1",xy=(P0,P1),xytext=(0.9,9.0),fontsize=8,color="#A32D2D",
            arrowprops=dict(arrowstyle="-",color="#A32D2D",lw=0.8))

plt.tight_layout()
plt.savefig("pinout_qfn48.png", dpi=220, bbox_inches="tight", facecolor="white")
print("saved pinout_qfn48.png")
