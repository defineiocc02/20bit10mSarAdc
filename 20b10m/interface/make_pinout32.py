#!/usr/bin/env python3
"""make_pinout32.py —— QFN-32 5×5 引脚图（精简版）"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

plt.rcParams["font.family"] = "PingFang SC"
plt.rcParams["axes.unicode_minus"] = False

# 逆时针：左 1-8 上→下；下 9-16 左→右；右 17-24 下→上；上 25-32 右→左
PINS = [
    ("VINP","A"),("VINN","A"),("VREF5","R"),("VREF2","R"),("VCM","R"),("VREFN","R"),("VDD5A","P"),("VSSA","G"),
    ("CLKP","C"),("CLKN","C"),("VDD18A","P"),("VSSA","G"),("VDD18D","P"),("VSSD","G"),("VDDIO","P"),("VSSIO","G"),
    ("DOUTP","D"),("DOUTN","D"),("CLKOUTP","D"),("CLKOUTN","D"),("DRDYP","D"),("DRDYN","D"),("SCLK","S"),("SDI","S"),
    ("SDO","S"),("CS","S"),("RSTN","S"),("MON","T"),("VDD5A","P"),("VSSA","G"),("VSSD","G"),("VSSA","G"),
]
COLOR = {"A":"#B5D4F4","R":"#CECBF6","P":"#F7C1C1","G":"#D3D1C7","C":"#FAC775",
         "D":"#C0DD97","S":"#9FE1CB","T":"#E5E5E5"}
EDGE = {"A":"#185FA5","R":"#534AB7","P":"#A32D2D","G":"#5F5E5A","C":"#854F0B",
        "D":"#3B6D11","S":"#0F6E56","T":"#888780"}

fig, ax = plt.subplots(figsize=(10.2, 10.2))
ax.set_xlim(-0.3, 12.6); ax.set_ylim(0, 12.4); ax.set_aspect("equal"); ax.axis("off")

P0, P1 = 3.1, 8.9           # 5.8 units = 5 mm
ax.add_patch(Rectangle((P0,P0), P1-P0, P1-P0, facecolor="#F7F7F4", edgecolor="#2C2C2A", lw=1.8))
ax.add_patch(Rectangle((5.3,5.3), 1.4, 1.4, facecolor="#D3D1C7", edgecolor="#888780", lw=0.8))
ax.text(6.0, 6.0, "EP\nVSSA", ha="center", va="center", fontsize=7, color="#2C2C2A")
ax.text(6.0, 4.75, "die 1.03 mm（示意，不按比例）", ha="center", va="top", fontsize=7, color="#5F5E5A")

pitch = (P1-P0-0.4)/7
pos = {}
for i in range(8):   pos[i+1]  = (P0, P1-0.2-i*pitch)
for i in range(8):   pos[i+9]  = (P0+0.2+i*pitch, P0)
for i in range(8):   pos[i+17] = (P1, P0+0.2+i*pitch)
for i in range(8):   pos[i+25] = (P1-0.2-i*pitch, P1)

for idx,(name,grp) in enumerate(PINS, start=1):
    x,y = pos[idx]
    w,h = (0.38,0.16) if y in (P0,P1) else (0.16,0.38)
    ax.add_patch(Rectangle((x-w/2,y-h/2),w,h, facecolor=COLOR[grp], edgecolor=EDGE[grp], lw=0.8, zorder=3))
    fs=7.0
    if y==P1:      ax.text(x,P1+0.24,name,ha="center",va="bottom",fontsize=fs,rotation=90,color="#2C2C2A"); ax.text(x,P1+0.72,str(idx),ha="center",va="bottom",fontsize=8,color="#2C2C2A")
    elif y==P0:    ax.text(x,P0-0.24,name,ha="center",va="top",fontsize=fs,rotation=90,color="#2C2C2A");    ax.text(x,P0-0.72,str(idx),ha="center",va="top",fontsize=8,color="#2C2C2A")
    elif x==P1:    ax.text(P1+0.24,y,name,ha="left",va="center",fontsize=fs,color="#2C2C2A");                ax.text(P1+1.02,y,str(idx),ha="left",va="center",fontsize=8,color="#2C2C2A")
    else:          ax.text(P0-0.24,y,name,ha="right",va="center",fontsize=fs,color="#2C2C2A");                ax.text(P0-0.86,y,str(idx),ha="right",va="center",fontsize=8,color="#2C2C2A")

ax.text(6.0, 12.05, "SAR20-10M · QFN-32 5×5 mm · 0.5 mm pitch（精简版）", ha="center", va="center", fontsize=12, color="#1a1a1a")
ax.text(6.0, 11.55, "20.5 bit · 10 MS/s · 20 功能脚 + 12 电源/地", ha="center", va="center", fontsize=9, color="#444441")

legend=[("A","模拟输入"),("R","基准"),("P","电源"),("G","地"),("C","时钟"),("D","LVDS 输出"),("S","SPI/控制"),("T","测试/观测")]
for i,(g,label) in enumerate(legend):
    x=2.0+(i%4)*2.2; y=1.55-(i//4)*0.34
    ax.add_patch(Rectangle((x,y-0.07),0.18,0.14,facecolor=COLOR[g],edgecolor=EDGE[g],lw=0.7))
    ax.text(x+0.24,y,label,ha="left",va="center",fontsize=7,color="#444441")

ax.plot([P0],[P1],marker="o",ms=5,color="#A32D2D",zorder=5)
ax.annotate("PIN 1",xy=(P0,P1),xytext=(1.0,8.9),fontsize=8,color="#A32D2D",
            arrowprops=dict(arrowstyle="-",color="#A32D2D",lw=0.8))

plt.tight_layout()
plt.savefig("pinout_qfn32.png", dpi=220, bbox_inches="tight", facecolor="white")
print("saved pinout_qfn32.png")
