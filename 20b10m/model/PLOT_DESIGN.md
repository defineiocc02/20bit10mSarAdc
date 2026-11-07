# 出图方案：从 `20b10mtask` 借什么、丢什么

> 参考仓库：`defineiocc02/20bit_SAR_ADC_Behaviour_Verification`，分支 `20b10mtask`。
> 具体对照文件：
> - `task2/figures/README.md`、`task2/figures/manifest.json`
> - `task1/experiments/full20_linearity_plots.py`（`_style/_chinese_style/_save`）
> - `task2/eight/plots.py`（`_annotate/_band`、双栏对比）
>
> 结论：**保留它的“图件即交付物”治理方式（mm 尺寸、中文字体校验、PNG+SVG+PDF、manifest+哈希、三段式标题），丢掉它的跨模块硬耦合与过度分图。**

## 1. 值得保留的（精华）

| # | 做法 | 为什么保留 | 我们的落地 |
|:--|:---|:---|:---|
| 1 | **图件 manifest + SHA256**（脚本、数据、输出、字体、版本） | 图能追溯到哪份数据、哪版脚本；改图不会“说不清” | `model/viz.py:write_manifest`，自动写 `results/figures/manifest.json` |
| 2 | **物理尺寸 mm**（146 mm 单栏） | 与论文栏宽一致，字号/线宽不靠“看起来差不多” | `WIDTH_MM=146`，每图 `dimensions_mm` 入 manifest |
| 3 | **中文字体校验**（查“码”字，不靠 fallback） | 避免图上出现方框；字体本身也是交付质量 | `chinese_style()`：Hiragino Sans GB → PingFang SC，校验 charmap |
| 4 | **title / subtitle / note 三段式** | 图能脱离正文单独阅读；note 写口径与限制 | `viz.annotate()`，位置 0.975/0.930/0.015 |
| 5 | **PNG(300 dpi)+SVG(path)+PDF** | 网页/Word/LaTeX 三处都能用；SVG 字形转路径不依赖字体 | `viz.save()`，`svg.fonttype=path`、`metadata Date=None` |
| 6 | **克制的双色语义**（OFF `#626C75`、ON `#0072B2`） | 开关/基线对比不靠彩虹色；黑白打印仍可辨 | 全图统一 `BASE/CAAZ/WARN/GOOD` |
| 7 | **grid alpha、ticks in、8 pt 字号** | 与参考库图并排不违和 | `viz._base_style()` 逐项对齐 |
| 8 | **图注链接数据/脚本/证据** | 读者能自己复核 | `figures/README.md` 每图带脚本与数据路径 |

## 2. 丢掉的（糟粕）

| # | 参考库做法 | 问题 | 我们的替代 |
|:--|:---|:---|:---|
| 1 | 图脚本 `from task1.experiments... import _chinese_style` | 跨包硬耦合，换目录就跑不起来 | `viz.py` 自包含；`plots.py` 只依赖 `model/` |
| 2 | 图脚本直接 import 实验内部（`linearity()`、`ROOT`） | 图与实验版本绑死，无法单独重画 | 只读 `results/results.json` + `static.curves()`，接口稳定 |
| 3 | 每张图配 `_envelope.csv`、多档 zoom、PDF 全出 | 文件爆炸，评审时不知道看哪张 | 5 张主图，固定命名；PDF 只给主图 |
| 4 | 754,319 个内码的逐码数组进图脚本 | 内存/时间大，且 20.5 bit 逐码 DNL 本身不可测 | DAC1 10 bit 的 1024 码逐码曲线 + 系统段级说明 |
| 5 | manifest 手工维护哈希 | 容易过期，反而不可信 | `write_manifest` 从实际输出自动算 |
| 6 | 图内大量 `ax.text` 绝对坐标 | 改尺寸就错位 | 统一 `annotate()` 与 `subplots_adjust` |
| 7 | 所有图都出 SVG+PDF+PNG | 冗余；网页只需要 PNG/SVG | 主图三格式，调试图不出 PDF |

## 3. 我们的图（55 张：41 诊断 + 14 论文风格）

- 诊断图 `results/figures/`：CAAZ（7）、tracking（6）、交织（9）、静态（7）、噪声/参考/抖动（6）、系统（6）。
- 论文测试风格 `results/figures_paper/`：频谱、DR 曲线、SNDR-f、INL/DNL、噪声分解、CAAZ、M 扫、skew 频谱、功耗、FoM、直方图、温度。


| 图 | 回答什么 | 关键标注 |
|:---|:---|:---|
| `fig01_caaz_freq` | CAAZ 到底值多少 dB、随频率怎么掉 | 100 kHz +3.58、2 MHz +3.14；注明“含 3 dB 通用平均” |
| `fig08_tracking_M` | 8× 重复为什么只有 +1.7 dB | ρ=0.61；标注 M=1→8 |
| `fig15_skew_dr_sfdr` | 部分交织卡在哪：skew 还是失配/洗牌 | 2 MHz skew 扫描；洗牌把 SFDR 106→126 |
| `fig23_inl_raw_cal` | 校准前后 INL/DNL；校准吃不掉什么 | σu=0.2%、1.5 ppm 非位权残差；raw 38.6→cal 1.8 ppm |
| `fig07_caaz_spectrum` | CAAZ 在频域的样子 | 1–4 MHz 噪声底差 3.69 dB（101 bin 平滑） |

## 4. 样式合同（写死在 `viz.py`）

| 项 | 值 |
|:---|:---|
| 单栏宽 | **146 mm** |
| 字号 | 正文/轴 8 pt；标题 10.5 pt；副标题 7.6 pt；脚注 6.8 pt |
| 线宽 | 轴 0.7；网格 0.45；曲线 1.0 |
| 刻度 | 朝内，major width 0.7 |
| 字体 | Hiragino Sans GB（weight 300），校验“码”；缺失则 PingFang SC |
| 颜色 | 基线 `#626C75`、CAAZ `#0072B2`、警示 `#D55E00`、改善 `#009E73` |
| 输出 | PNG 300 dpi + SVG（字形转路径）+ PDF（主图） |
| 元数据 | `svg.hashsalt="sar20-10m-model"`，日期清空 |

## 5. 取舍说明

1. **为什么不做“每图一个 CSV + 多 zoom”**：我们的数据是 1024 码/5 组实验，不是 75 万码；多 zoom 只会增加评审负担。逐码曲线一张足够。
2. **为什么图只读 `results.json`**：把“算”和“画”解耦；重画不需要重跑 6 秒实验，也不会因为实验内部改名而崩。
3. **为什么 manifest 自动生成**：手工哈希在参考库里是治理手段，但容易过期；自动生成更可信。
4. **为什么保留 PDF**：LaTeX 报告要用矢量；但只给 5 张主图，不给调试图。
5. **为什么图里写“未标定，不可签核”**：绝对 DR 依赖未实测的 ρ/噪声分配；图只能支持相对结论。

## 6. 复现

```bash
cd 20b10m
python3 -m model.experiments     # 生成 results.json / report.md
python3 -m model.plots           # 生成 15 个图件 + manifest.json
python3 -m model.selftest        # 4 项自检
```

图件目录：`model/results/figures/`；清单：`manifest.json`；图注：`README.md`。
