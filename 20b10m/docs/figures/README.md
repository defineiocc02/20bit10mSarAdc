# 效果图与来源（docs/figures）

> 规则：**图上每个效果数字必须带标签，图下必须有脚注。** 没有来源的图不进这个目录。
> 生成：`python3 -m model.figures_ssot`（2026-11-11）；清单与 SHA：`manifest.json`。
> 口径：`spec/SSOT.md`（20.00 bit = 10+12−2，G=32，相位 10/15/20/45）。

---

## 1. 图与问题

| 图 | 回答的问题 | 数据来源（可复现） | 证据等级 | 关键数字 | **不能声称** |
|:---|:---|:---|:---:|:---|:---|
| `f0_architecture.svg` | 结构是什么、哪些是 target / as-wired | `analog/blocks/*/netlist/*.scs` 逐行 + `spec/SSOT.md` | **L0 结构** | 10+12−2；27.648 pF；864 fF；5+6 | 不是仿真，不是版图 |
| `f1_spectrum` | 100 kHz 输入的 SNDR/DR/SFDR | `model.adc.simulate` + `model.metrics.fft_metrics`，N=16384，seed=11 | **L1 行为模型** | SNDR 101.9 dB；DR 102.0 dB；SFDR 130.5 dBc | 不是硅测，不是前仿；绝对数未标定 |
| `f2_averaging` | 8× LSB 重复值多少 dB | `model.adc.simulate`，M=1/2/4/8，2 seeds/点 | **L1 行为模型** | +1.71 dB（M=1→8，均匀权） | 不能写成论文复现；论文 p.47 是 +2 dB |
| `f3_shuffle` | 片级随机选片换到什么 | `model.adc.simulate`，interleave（gain 50 ppm / offset 50 µV / skew 1 ps），2 seeds/点 | **L1 行为模型** | DR −1.4 dB，SFDR +20.6 dBc | **不是 CDAC 单位级 DEM**；不能引用为 DEM 收益 |
| `f4_inl` | 0.2% 单位失配的 INL 与校准残差 | `model.static.curves` → `charge_model.dac1_curves`，1024 码，seed=7 | **L1 行为模型** | INL 16.4 → 0.30 ppm FS | 不是论文实测；σu=0.2% 是 stress 档 |
| `f5_skew_gain` | 交织 skew / 增益失配的代价 | `model.adc.simulate` + `slice_errors`，2 seeds/点 | **L1 行为模型** | 2 ps → −2.0 dB；50 ppm → −5.0 dB（10→50 ppm） | skew/增益幅度是 stress 假设，不是封装实测 |

---

## 2. 脚注格式（每张图都有）

```
来源: model/figures_ssot.py · 数据: <函数> · N=<点数> · seed=<种子>
口径: SSOT 20.00 bit (10+12−2) · G=32 · 等级: L1 行为模型（非前仿/非硅测） · 2026-11-11
说明: <这张图不能声称什么>
```

- `[模型]`：`model/` 或 `behavioral/` 的行为级输出；
- `[论文]`：论文/讲稿原文数字，注明页码；
- `[估算]`：面积/功耗/版图量级，不是仿真。

---

## 3. 已知的口径差异（不掩盖）

| 项 | 本图 | 别处 | 为什么不同 |
|:---|:---|:---|:---|
| 8× 重复 | **+1.71 dB**（均匀权） | README §3：+1.86 dB（三角权，`behavioral`） | 重复权不同（boxcar vs triangular），不是矛盾 |
| 片级 shuffle | **−1.4 dB / +20.6 dBc**（50 ppm，2 seeds） | 旧 README：−1.0 dB / +21.2 dBc | 失配档与 seed 数不同；趋势一致 |
| 频谱 SNDR | **101.9 dB**（N=16384） | 旧 README：101.84 dB | 同量级，四舍五入/seed 差异 |

> 规则：**同一张图只用一个 estimator**；跨图比较必须先对齐 N、seed、失配档、重复权。

---

## 4. 重新生成

```bash
cd 20b10m
python3 -m model.figures_ssot          # 出 PNG/SVG/PDF + manifest.json
```

字体：`Hiragino Sans GB` / `PingFang SC`（`model/viz.py` 会校验“码”字）。
输出：146 mm 宽，PNG 300 dpi，SVG 路径字形，PDF 可选。
