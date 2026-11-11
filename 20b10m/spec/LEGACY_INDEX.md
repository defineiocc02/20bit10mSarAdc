# 历史文件索引（LEGACY INDEX）

> 目的：把"不能作为设计输入"的文件一次列清，避免读者在旧数字里再迷路。
> **活口径只有 `spec/SSOT.md`**；本页列出的文件只作演进证据/审计快照。

---

## 1. 活文件（可以作为设计输入）

| 类别 | 文件 |
|:---|:---|
| 唯一口径 | `spec/SSOT.md`、`spec/params.yaml` |
| 顶层说明 | `README.md`（20b10m）、`STATUS.md`（工作区） |
| 接口 | `interface/ANALOG_DIGITAL_IF.md`、`interface/DIGITAL_ARCH.md`、`interface/analog_digital_if.csv`、`interface/OUTPUT_IF_10M.md`、`interface/PINOUT_QFN48.md` |
| 块规格 | `analog/blocks/*/spec.md`（Dac1 除外，见下） |
| 网表 | `analog/blocks/*/netlist/*.scs`、`analog/netlist/*.scs` |
| RTL | `digital/*.sv`、`digital/README.md` |
| 模型 | `behavioral/`、`model/params.py` |
| 闸门 | `tools/check_ssot.py`、`tools/check_consistency.py`、`analog/netlist/check_hier.py`、`analog/netlist/check_ports.py` |

---

## 2. 历史文件（**不得作为设计输入**）

### 2.1 已加横幅

| 文件 | 为什么历史 |
|:---|:---|
| `spec/ARCH_V2.md` | V2 架构；D-04 的 DAC2 11 bit、ΦC2 40 ns 已被 BL-v3/SSOT 取代 |
| `spec/bit_allocation.md` | 20.5 bit / 11+12−2.5 / 5 Vpp，整份作废 |
| `analog/BLOCK_CONTRACTS.md` | 2026-11-08 网表审计快照；1039/11 bit/28 pF 是当时实测 |
| `analog/blocks/Dac1_11b/spec.md` | V1 legacy，已被 `SdacPool18/SdacSlice` 取代 |

### 2.2 未加横幅，但按历史读

| 文件/目录 | 说明 |
|:---|:---|
| `spec/hierarchy.md` | 旧层次树（三代口径混用） |
| `spec/spec_tree_10m.md` | 10M 逐块规格，含旧 11 bit/40 ns |
| `spec/INTERFACES_V2.md` | 旧接口表；活表是 `interface/analog_digital_if.csv` |
| `spec/interfaces.csv` | 旧端口表（Sar1Top 还带 VINP/PHI_S）；活表同上 |
| `spec/ARCH_REVIEW.md`、`spec/ADR-001_ARCH_DECISION.md` | 架构演进证据 |
| `spec/TASKS_ARCH_V2_legacy.md`、`spec/README_ARCH_V2_legacy.md` | 明确标 legacy |
| `plan/*` | 规划过程；数字随版本变，不作口径 |
| `review/*`（除 `20261111_unify_log.md`、`20261111_cdac_if_dem_dither.md`） | 评审快照 |
| `HANDOVER.md`、`STATE.md`、`TASKS.md`、`PLAN.md`、`TECH_EFFECTIVENESS.md` | 状态/结论快照 |
| `verification/PLAN.md` | 验证计划旧稿 |
| `model/`（除 `params.py`） | 旧 10+11 模型与 41+14+9 张图；结论按 SSOT 重算后才可用 |
| `arch/` | 旧架构计算包（`bitaccount.py`/`noise.py`），含 20.5 口径 |
| `verilog/20b10m_skeleton.v` | 旧端口桩；活 RTL 在 `digital/` |
| `docs/导入步骤.md` | 导入流程，数字无关 |
| `analog/LAYOUT_PLAN.md`、`analog/PDK_FILL.md` | 版图/PDK 旧计划 |
| `skill/create_lib.il` | 建库脚本，与口径无关 |

---

## 3. 规则

1. 引用历史文件时必须写 `[历史]`，并同时给出 SSOT 编号。
2. 任何新文档只引 `spec/SSOT.md`，不引 `ARCH_V2.md` / `bit_allocation.md`。
3. `tools/check_ssot.py` 只扫活文件；历史文件不进闸门，但也不得被新文档引用为口径。
4. 若要把某个历史文件"复活"，先改 `spec/SSOT.md` 并把它移出本索引。

---

## 4. 有效性结论（不是文件，是口径）

- 技术有效性以 `model/results/crossval/summary.csv` 为准（K=10 seeds，95% CI）。
- 报告：`review/20261112_crossval.md`；图：`docs/figures/f6_crossval.png`。
- 单 seed / 2 seeds 的点估计只能当示例；与 crossval 冲突时以 crossval 为准。
