# 工程组织计划（SAR20-10M）

> 目标：180 nm BCD，20.5 bit / 10 MS/s 两级 SAR；CICC 2026 单相 90 ns 帧 + ADI ISSCC2024 9.8 式**部分交织**（只交织 DAC1 的 18 片池）。
> 原则：**先模型、再网表、再版图**；每一层都有可复核判据；绝对指标未硅测前不得签核。

## 1. 范围与路线

| 阶段 | 内容 | 状态 |
|:---|:---|:---|
| P0 | 文献/专利基线、位账、预算 | 完成（`plan/master_plan_20b5m.md`） |
| P1 | 单相 5 MS/s 基线（论文原样） | 规格/网表/模型已搭，未仿真 |
| **P2** | **10 MS/s 部分交织（当前目标）** | 架构/网表/RTL/模型已搭，未前仿 |
| P3 | 换一级结构（ADI 式 sDAC+RDAC follower） | 不在本项目 |

## 2. 工作分解（WBS）

| WP | 名称 | 主要内容 | 交付物 | 负责角色 | Gate |
|:--|:---|:---|:---|:---|:---:|
| WP1 | 行为模型 | CAAZ/tracking/交织/静态/噪声/出图 | `model/`、`results.json`、55 张图 | 严收敛 + 何权衡 | G1 |
| WP2 | 架构与规格 | 位账、90 ns 帧、18 片池、面积/floorplan、引脚 | `plan/`、`spec/`、`interface/` | 秦校准 | G0/G1 |
| WP3 | 模拟前端 | 采样、DAC 池、SliceMux、粗量化、RA、CT2、参考 | 25 块 `spec.md` + Spectre 网表 | 秦校准 + 甄低噪 | G2 |
| WP4 | 数字后端 | 调度、SAR1/2 控制、SINC2、冻结重构、帧打包、LVDS | `digital/*.sv` + 断言/覆盖率 | 陆时序 | G2/G3 |
| WP5 | 版图 | 4 mm²/1.06 mm² floorplan、匹配、电源地、PEX | GDS、DRC/LVS、寄生预算 | 郝匹配 | G4 |
| WP6 | 验证与测试 | L0–L5 分层、PVT/MC、硅测方案 | `phase2_verification.md`、测试计划 | 严收敛 | G3–G6 |
| WP7 | 仓库与证据 | 目录规范、图 manifest、快照、变更单 | 本仓库、`manifest.json`、`CODE_INDEX.md` | 何权衡 | 持续 |

## 3. 里程碑与判据

| Gate | 交付 | 通过判据 | 证据 |
|:---|:---|:---|:---:|
| **G0 规格冻结** | 位账、FS、G、C_INC、90 ns 帧、引脚 | 所有数字单一来源；旧 `bit_allocation.md` 作废 | L0 |
| **G1 架构/模型** | 行为模型 + 架构裁决 | CAAZ/tracking/交织趋势可复现；F(M)、skew、校准曲线有判据 | L1 |
| **G2 模块设计** | 25 模拟块 + 数字 RTL | 每块 spec 可测；网表端口一致；单元仿真过判据 | L1–L2 |
| **G3 系统前仿** | 顶层 tran/tran noise | DR 102.0–103.5；SNDR ≥97@100k；90 ns 闭合 | L2 |
| **G4 版图** | GDS + DRC/LVS/天线 | DRC/LVS 零错；关键节点寄生在预算内 | L4 |
| **G5 后仿** | RCC 后仿 | 相对前仿 DR −1.0 dB、SNDR −1.5 dB、INL ≤1.8 ppm | L4 |
| **G6 硅测** | 测试芯片 + 测试计划 | DR ≥101.5；SNDR ≥98@100k；M=1/8、CAAZ on/off 可复现 | L5 |

## 4. 交付树（与 `spec/hierarchy.md` 对应）

```
Sar20bTop
├── RefBuffer / DynRefBuf / BiasGen
├── SdacPool18（18×SdacSlice）
├── SliceMux（18:1，选 8）
├── Sar1Top（Cmp1 + TriLevelBank11 + SarLogic1）
├── CmpCoarse4b（15 cmp）
├── RingAmp3（FiaA1/AmpA2/FiaA3）
├── Sar2Ct（CincCouple/Dac2_11b/Dac2Replica/Cmp2/SarLogic2）
└── DigitalTop（PhaseGen/SliceSched/Sar1Ctrl/Sar2Ctrl/Sinc2/ReconWeights/FramePack/SerLvds）
```

## 5. 角色与协作

| 角色 | 负责 | 不负责 |
|:---|:---|:---|
| 何权衡（主理人） | 裁决、基线、报告、仓库 | 不代写专业结论 |
| 秦校准（架构） | 位账、预算、时序架构、校准策略 | 晶体管尺寸 |
| 甄低噪（模拟） | 比较器/RA/参考/自举/偏置 | 架构选型 |
| 陆时序（数字） | RTL、调度、后处理、低功耗 | 模拟接口电平 |
| 郝匹配（版图） | 匹配、寄生、电源地、DRC/LVS | 电路尺寸 |
| 严收敛（验证） | 分层仿真、PVT/MC、指标口径、硅测 | 改电路 |
| PL（用户） | 参数确认、流片/封装决策、资源 | — |

## 6. 进度（按月，从 G0 起）

| 月 | 目标 |
|:--:|:---|
| M0 | G0 冻结：位账/FS/G/引脚/面积口径；模型自检 |
| M1 | G1：模型定稿；模拟 25 块网表 L0；数字 RTL 骨架 |
| M2 | G2：关键块 L1（采样/DAC 单片/RA/Cmp/参考）；数字 lint/烟测 |
| M3 | G3：系统前仿；时序 ss 角闭合；参考/抖动模型补齐 |
| M4 | G4：版图 floorplan → 关键块版图；DRC/LVS |
| M5 | G5：RCC 后仿、PVT/MC；测试芯片流片 |
| M6 | G6：硅测 bring-up、频谱/INL/DR、报告 |

## 7. 仓库与证据规范

- **单一规格源**：`spec/spec_tree_10m.md` + `plan/arch_10m.md`；旧 `bit_allocation.md` 已作废。
- **代码索引**：`CODE_INDEX.md`；每个入口文件头有 `[CODE-INDEX]` 注释。
- **图件**：`model/results/figures/`（41 张诊断）与 `figures_paper/`（14 张论文风格）；各带 `manifest.json`（脚本/数据/输出 SHA256、字体、尺寸）。
- **出图规范**：146 mm、Hiragino Sans GB、PNG 300 dpi + SVG(path) + PDF；见 `model/PLOT_DESIGN.md`。
- **证据等级**：L0 静态 / L1 行为/单元 / L2 前仿 / L3 后仿 / L4 PVT/MC / L5 硅测；报告必须标级。
- **提交**：一次提交一个主题；不提交 `__pycache__`、原始 psf、未脱敏数据。

## 8. 风险 top 5

| # | 风险 | 触发 | 缓解 |
|:--|:---|:---|:---|
| 1 | 18:1 SliceMux 偏斜/电荷注入 | 片间 >50 ps | 对称树、等长、dummy、先断后合 |
| 2 | 参考 droop/回流 | 比较时刻 >2.44 mV | 1 nF 片上 + 封装 1 µF + R_buf ≤20 Ω |
| 3 | PDK MIM 密度只有 1 fF/µm² | core >0.8 | 2 fF/µm² 堆叠 / 4+2 粗量化 / 去耦 150 pF |
| 4 | 2 MHz 抖动 | σt >1 ps | 外部时钟、独立 LDO/pad、0.5 ps 目标 |
| 5 | 数字/模拟耦合 | 固定码 INL 变 >0.5 LSB | 分区、guard ring、独立电源、末次翻转 ≥8 ns |

## 9. 当前状态与下一步

**已完成**：位账/预算/架构裁决；25 块模拟 spec + 28 个 Spectre 网表（220 实例）；9 个数字 RTL 文件（26 端口对齐）；Python 模型（4 项自检全过）；55 张图 + manifest。

**下一步（按顺序）**：
1. 填 `pdk_models.scs`，跑 `check_hier` + L0；
2. 把 `Sar1Ctrl/Sar2Ctrl` 接进两个数字 stub；
3. 跑 kT/C 标定台 + S6 τ_top PZ；
4. 关键块 L1：`SwSample5v`、`SdacSlice`、`RingAmp3`、`Cmp1`；
5. G2 评审后再开版图。
