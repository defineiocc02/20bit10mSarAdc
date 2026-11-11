# 参考库复用表

> 参考库：`defineiocc02/20bit_SAR_ADC_Behaviour_Verification` 的 `20b10mtask` 分支
> 历史定位：`5094b2e156a7660c85d3bf02bcd6d5a13786377e`（**不是**最新 HEAD 的断言）
> 判定列：直接复用 / 薄适配 / 重新推导 / 仅参考方法 / 不采用

---

## 1. 判定前提

参考库是 **9 bit SADC + 12 bit ADC2（理想）+ 18 片**，目标是 **10 bit DT + 12 bit CT + 18 片**。
位宽、冗余、后级结构都不同，**只有「与架构无关的机制」可以搬**。

---

## 2. 逐项表

| # | 参考文件/符号 | 解决的问题 | 依赖的拓扑/码域 | 目标需要 | 判定 | 接口变化 | 已有证据 | 目标验证 |
|:--|:---|:---|:---|:---|:---|:---|:---|:---|
| 1 | `task1/rtl/slice_scheduler.sv`（约 150 行） | 18 片池的 eligible/stall/有序 ID/样本 ID | 8 片/组、`eligible` 来自模拟释放 | ✅ 需要 | **薄适配** | 5 bit ID 对齐 18 片；`advance` 接 100 ns swap；删 shuffle 分支（片角色冻结） | 本仓已有 Python 等价实现并自检通过（16 片两两交替、坏 2 片不 stall、只剩 7 片全 stall） | Python 逐帧对比 + RTL 定向 tb |
| 2 | `task1/rtl/fig11_dem.sv` | 片内 16C/8C/4C/2C/C 子段轮转 | split RDAC，二维 DEM | ❌ 不需要 | **不采用** | — | 参考库实测：SFDR +6.3 dB 但 **SNDR −2.96 dB** | 若将来评估，按「收益>损失」判 |
| 3 | `task2/rtl/dither_word_gen.sv` | PRBS31 六位字，每样本推 6 次 | 与架构无关 | ❌ 不需要 | **仅参考方法** | — | 本仓用 numpy 版验证：dither 对 SNDR **0.01 dB**（我们 LSB2 = 1 LSB20，无零宽码） | — |
| 4 | `task3/rtl/caaz20_pair.sv` | 偶奇配对 + 共享 AZ 代 | 10 MS/s 原始流 | ⚠️ 可选 | **重新推导** | 若用会降到 5 MS/s | 本仓 Python 复现：AZ 共享残余 0.00、独立 14.33 µV（与参考 14 µV 一致） | 若上 CAAZ 再做 |
| 5 | `task1/evidence/bridge_lms/` | 训练/留出分离、不混训练集 | 与架构无关 | ✅ 需要 | **仅参考方法** | — | — | 本仓 `cal_residual(n_avg)` 已实现有限样本口径，**但缺独立留出集** |
| 6 | `task1/EXPERIMENT_STANDARD.md` | 固定失配池 + 分源随机 + 配对对照 | 与架构无关 | ✅ 需要 | **直接复用（方法）** | — | — | `behavioral/src/sar20b/rng.py` 的 `ChipInstance` + `NoiseStreams` 已照此实现 |
| 7 | `task_reconstruction/` | 定点重构、量化/舍入 | 20 bit signed | ⚠️ 部分 | **仅参考方法** | 目标 22 bit offset binary | — | 本仓 `ReconWeights` 待按 BL-v3 重算 |
| 8 | `task_integration/SPEC.md` | 集成合同、28 项任务表 | 参考架构 | ❌ | **不采用** | — | — | — |
| 9 | `task2/eight/`、`eight_rtl/` | 八片 dither 位图 | 参考 split 阵列 | ❌ | **不采用** | — | — | — |
| 10 | `references/` | ISSCC 2024 9.8 论文/PPT/专利 | — | ✅ | **直接引用** | — | 已核 6 篇专利机制（见 `spec/DROOP_OPTIONS.md` 引专利 [14]） | — |

---

## 3. 不可迁移的三类（明确禁止）

| 类别 | 为什么不能搬 | 例 |
|:---|:---|:---|
| **阵列映射** | 参考是 split RDAC（每片 63+8），目标是 128 单位纯二进制 + 3 bit unary | `fig11_dem.sv` 的 B4 分配 |
| **后级码权** | 参考二级 12 bit 覆盖 ±100 mV（5.12 LSB20 步长），目标覆盖 ±2 LSB1（1.0 LSB20） | `task_reconstruction` 的权重表 |
| **工艺签核** | 参考是 SKY130 数字后端；目标是 180 nm BCD 混合信号 | 参考的 GDS/DRC/STA 结论 |

**另**：参考库的 LMS 是**片外训练 + 片内冻结系数**，不宣称片上存在训练引擎。本仓同样。

---

## 4. 复用代码的来源与许可

| 项 | 状态 |
|:---|:---|
| 参考库 LICENSE | 已存在（`LICENSE`、`NOTICE`），未确认具体条款 |
| 本仓复用的代码 | **目前只有第 1 项的算法逻辑**（Python 重写，未复制源码文本） |
| 若要复制 SV 源码 | 需先确认许可证允许，并在文件头保留原作者与来源 commit |

---

## 5. 一句话

**参考库给了三样东西：调度器的资源所有权模型、实验的配对纪律、以及「哪些技术不值得做」的负结果。**
**它的位权、阵列映射、后级码权、工艺结论一样都不能搬。**
