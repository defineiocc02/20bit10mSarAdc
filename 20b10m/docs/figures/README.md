# 效果图与来源（docs/figures）

> 规则：**图上每个效果数字必须带标签，图下必须有脚注。** 没有来源的图不进这个目录。
> 生成：`python3 -m model.crossval && python3 -m model.figures_ssot`（2026-11-12）。
> 统计：动态图 10 seeds、误差棒 = 95% CI（t=2.262）；图用 seed 2000–2009，crossval 用 1000–1009，**互为独立复现**。
> 口径：`spec/SSOT.md`（20.00 bit = 10+12−2，G=32，相位 10/15/20/45）。

---

## 1. 图、问题与判定

| 图 | 回答的问题 | 数据来源（可复现） | 等级 | 关键数字 | 判定 |
|:---|:---|:---|:---:|:---|:---|
| `f0_architecture.svg` | 结构是什么、哪些是 target / as-wired | `analog/blocks/*/netlist/*.scs` + SSOT | **L0** | 10+12−2；27.648 pF；864 fF；5+6 | 结构事实 |
| `f1_spectrum` | 100 kHz 的 SNDR/DR/SFDR | `model.adc.simulate` + FFT，N=16384，seed=11 | **L1** | SNDR 101.9；DR 102.0；SFDR 130.5 | 单点示例 |
| `f2_averaging` | 8× 重复值多少 dB | `model.adc.simulate`，M 扫描，10 seeds | **L1** | **+1.68 dB** | **VALIDATED**（预测 1.714） |
| `f3_shuffle` | 片级随机选片换到什么 | `model.adc.simulate`，10 seeds | **L1** | SFDR **+17.1 dBc**；DR −1.7（方向不稳） | SFDR **VALIDATED**；DR **NOT VALIDATED** |
| `f4_inl_dnl` | 0.2% 失配的 INL/DNL 与校准残差 | `charge_model` + `_features` 有限样本拟合，seed 7 + 10 chips | **L1** | INL 17.8→0.54 ppm；DNL 0.0235→0.00073 LSB1；失码 0→0；OOS 1.87 ppm | **CONDITIONAL**（OOS 超 1.5） |
| `f5_skew_gain` | 交织 skew / 增益失配的代价 | `model.adc.simulate`，10 seeds | **L1** | −1.5 dB / −5.1 dB | **VALIDATED（退化）** |
| `f6_crossval` | 哪些效果统计显著 | `model.crossval`，K=10 | **L1** | 见报告 | 森林图 + INL 三口径 |
| `f7_dem_dither` | DEM 与 dither 各自贡献什么 | `model.tech_effects`，K=10 | **L1** | DEM：INL 3.6×/DNL 2.8×；dither：INL 1.08×/DNL 4.6×；both：4.4×/13.8× | DEM 管 INL / dither 管 DNL |

> 判定口径：动态 Δ 的 95% CI 全正 → POSITIVE；全负 → NEGATIVE；跨 0 → INCONCLUSIVE。
> 校准：cal_max < raw_min → PASS；否则 CONDITIONAL。跨实现差异 >20% → DISCREPANT。

---

## 2. 脚注格式（每张图都有）

```
来源: model/figures_ssot.py · 数据: <函数> · N=<点数> · seeds=<种子>
口径: SSOT 20.00 bit (10+12−2) · G=32 · 等级: L1 行为模型（非前仿/非硅测） · 2026-11-12
说明: <这张图不能声称什么>
```

- `[模型]`：`model/` 或 `behavioral/` 的行为级输出；
- `[论文]`：论文/讲稿原文数字，注明页码；
- `[估算]`：面积/功耗/版图量级，不是仿真。

---

## 2.1 DEM 与 dither 分开看（f7）

| 机制 | INL | DNL | 每样本噪声 | 说明 |
|:---|:---|:---|:---|:---|
| DEM（8 态片级） | **22.9 → 6.3 LSB20（3.6×）** | **24.0 → 8.5 LSB20（2.8×）** | 0.12 ppm | 主要平均片内二进制比例误差 |
| dither（码域 D=2） | **22.9 → 21.1 LSB20（1.08×）** | **24.0 → 5.2 LSB20（4.6×）** | 0.03 ppm | 平均相邻码台阶，INL 几乎不变 |
| DEM+dither | **22.9 → 5.2 LSB20（4.4×）** | **24.0 → 1.7 LSB20（13.8×）** | 0.11 ppm | 互补 |

> 口径：1 LSB20 = 0.954 ppm FS；1 LSB1 = 1024 LSB20。
> 这是**模型层面**的贡献，不是网表/RTL 已实现；采样态 dither（OPEN-3）与单位级 DEM（OPEN-5）仍未做。

## 3. 口径差异（**必须看**）

| 项 | 图 / crossval | 旧说法 | 为什么 |
|:---|:---|:---|:---|
| 8× 重复 | **+1.69 dB**（均匀权，10 seeds） | +1.86 dB（三角权，`behavioral`） | 重复权不同；两者都标"模型" |
| 片级 shuffle SFDR | **+17~22 dBc**（两段 seed 都正） | +21.2 dBc | 工作点/失配档不同，趋势一致 |
| 片级 shuffle DR | **+0.9 dB（1000 段）vs −1.7 dB（2000 段）** | −1.0 dB | **方向翻转**；不能引用 |
| 校准 | **INL 0.54 ppm、DNL 0.00073 LSB1（有限样本）/ 1.87 ppm（OOS）** | 0.3 ppm | 估计器不同；OOS 才是泛化 |
| skew 0.5→2 ps | **−1.44 dB** | −2.0 dB | 2 seeds 是抽样误差；10 seeds 才稳 |
| gain 10→50 ppm | **−5.58 dB** | −5.0 dB | 同上 |

规则：**同一张图只用一个 estimator**；跨图比较必须先对齐 seeds、N、失配档、重复权。

---

## 4. 重新生成

```bash
cd 20b10m
python3 -m model.crossval         # ~30 s；results.json + summary.csv
python3 -m model.figures_ssot     # 6 张图 + manifest.json
```

字体：`Hiragino Sans GB` / `PingFang SC`（`model/viz.py` 校验“码”字）。
输出：146 mm 宽，PNG 300 dpi，SVG 路径字形，PDF 可选。
