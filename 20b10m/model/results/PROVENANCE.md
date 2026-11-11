# 模型出图来源说明（PROVENANCE）

> 本目录下三个 figure 子目录的图**全部是行为模型输出**，不是硅测、不是前仿、不是论文原图。
> 目录名里的 `measured` / `paper` 是**图风格**，不是数据来源。这一点以前没有写清，容易误读。

| 目录 | 是什么 | 生成脚本 | 数据来源 | 等级 |
|:---|:---|:---|:---|:---:|
| `figures/` | 41 张诊断图（CAAZ / tracking / 交织 / 静态 / 预算） | `model/figures.py` | `model.adc.simulate`、`model.static` | **L1** |
| `figures_paper/` | 14 张"论文风格"重绘图（坐标/版式像论文） | `model/paper_figures.py` | 同上；**不是论文数据** | **L1** |
| `figures_measured/` | 9 张"实测风格"图（频谱/INL/DR/技术排序） | `model/measured_figures.py` | 同上；**不是硅测** | **L1** |
| `figures_plots/` | 5 张早期图（fig1–5） | `model/plots.py` | 同上；部分为旧口径 | **L1（历史）** |

## 规则

1. 任何引用这些图的文档，必须写"模型"或"L1"，不得写"实测/measured/硅上"。
2. 对外汇报/论文只用 `docs/figures/`（带脚注：脚本、N、seed、SSOT 口径、等级、日期）。
3. `figures_measured/` 的目录名保留只为兼容旧链接；新增图不再用 `measured` 命名。
4. 图里的绝对 SNDR/DR/INL 未标定，只能用于技术排序与量级，不能写进数据手册。

## 口径

所有图的位账以 `spec/SSOT.md` 为准（20.00 bit = 10+12−2，G=32）。旧图若标 20.5/11 bit，属历史口径，按 `spec/LEGACY_INDEX.md` 处理。
