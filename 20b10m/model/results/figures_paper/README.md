# 论文测试风格图（14 张）

> 生成：`python3 -m model.paper_figures`｜清单：`manifest.json`。
> 全部由模型生成；绝对指标未标定，不可当实测签核。

![100 kHz 频谱](paper01_spectrum_100k.png)

**paper01｜100 kHz 输出频谱。** 10 MS/s、16384 点相干采样；SNDR/SFDR/DR 标注。

![2 MHz 频谱](paper02_spectrum_2m.png)

**paper02｜2 MHz 输出频谱。** 模型未注入抖动，故 SNDR 偏高；2 MHz 绝对指标不可作验收。

![DR 曲线](paper03_dr_curve.png)

**paper03｜SNDR/SNR vs 输入幅度。** 低幅度进入噪声底；DR 由 26.5 µV 决定。

![SNDR vs 频率](paper04_sndr_vs_fin.png)

**paper04｜SNDR vs 输入频率。** 6 k / 100 k / 2 M 三个目标点。

![INL](paper05_inl_20b.png)

**paper05｜INL（20 位风格）。** 模型合成的位权+非位权残差；±1.5 ppm 量级。

![DNL](paper06_dnl_20b.png)

**paper06｜DNL（20 位风格）。** ±0.4 ppm 量级；逐码 DNL 受噪声平滑。

![噪声分解](paper07_noise_breakdown.png)

**paper07｜噪声分解。** sampling 27.4%、RA amp 52.9%、AZ 8.6%、other 8.6%。

![CAAZ 频谱](paper08_caaz_spectrum.png)

**paper08｜CAAZ 开关频谱。** 100 kHz；ΔDR +3.58 dB（含 3 dB 通用平均）。

![M 扫描](paper09_m_sweep.png)

**paper09｜8× tracking 的 M 扫描。** M=1→8 +1.71 dB。

![skew 频谱](paper10_skew_spectrum.png)

**paper10｜交织 skew 的杂散。** 2 MHz、不洗牌；fs/2±fin 附近抬起。

![功耗](paper11_power.png)

**paper11｜功耗分解。** core 约 3.27 mW；论文 3.57 mW 同口径。

![FoM](paper12_fom.png)

**paper12｜FoM 对标。** 目标 187.8 dB。

![直方图](paper13_histogram.png)

**paper13｜输出码分布。** 噪声底 26.5 µV。

![温度](paper14_temp.png)

**paper14｜SNDR vs 温度。** 经验漂移模型；不是 PVT 仿真。

---

设计取舍见 [PLOT_DESIGN.md](../../PLOT_DESIGN.md)；诊断图见 [`../figures/README.md`](../figures/README.md)。
