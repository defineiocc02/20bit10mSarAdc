# 自查报告：规划、文档与目录（2026-11-07）

> 范围：`20b10m/` 全部内容 + 根目录组织。审查人：本会话助手（非独立第三方）。
> 结论：**规划本身自洽，但文档存在 4 处口径重复、2 处双源，目录未按模拟/数字/规划分层。**
> 已修 6 项，遗留 5 项列在最后。

---

## 1. 内容问题（按严重度）

| # | 问题 | 证据 | 影响 | 处理 |
|:--|:---|:---|:---|:---|
| 1 | **位分配在 4 个文件重复** | `spec/bit_allocation.md`、`plan/plan_10m.md` §6、`plan/interleaving_replan.md` §3、`spec/timing_detail.md` | 改一个数，其余三处漂 | 指定 `spec/bit_allocation.md` 为唯一权威，其余只引用 |
| 2 | **时序在两处重复** | `spec/timing_budget.md`（周期/相位表）与 `spec/timing_detail.md`（子拍/边沿） | 同上 | 已加声明：冲突时以 `timing_detail.md` 为准 |
| 3 | **V1 与 V2 并存未清理** | `analog/blocks/Dac1_11b`（V1 单路）与 `SdacPool18`（V2 交织）同时存在 | 数字组不知道接哪个 | 在 `Dac1_11b/spec.md` 顶部标"V1 基线，不投产" |
| 4 | **两份接口表** | `docs/if/接口契约_模板.csv`（早期示例）与 `spec/interfaces.csv`（实际 298 端口） | 双源，且模板内容与实际不符 | 模板改为指针，不再维护示例数据 |
| 5 | **20b10m 的 G=32 与本计划 G=128 未标隔离** | `plan/repo_integration.md` 表 3 列了两套 | 混用会差 4× | 已在 `plan_10m.md` §3 标"不可混用"，仍需在 bit_allocation 加一句 |
| 6 | **接口无版本/无变更记录** | `interface/` 原先不存在 | 冻结后无法追溯 | 新建 `ANALOG_DIGITAL_IF.md` v0.9-draft，带变更表 |
| 7 | **没有"模拟侧交付物"定义** | block `spec.md` 只有判据 | 谁交什么、交到什么级别不清 | 见 `FILE_LAYOUT.md` §4 |
| 8 | **`interfaces.csv` 缺域标记** | 298 行只有 cell/port/dir/kind/domain/range/note | 无法筛"哪些是模拟块" | 已加 `cell_domain` 列 |
| 9 | **`direction` 枚举无文档** | `in/out/io/pwr` → Verilog `input/output/inout` | 生成脚本隐式映射 | 已写入 `FILE_LAYOUT.md` §5 |

## 2. 目录问题

| # | 问题 | 处理 |
|:--|:---|:---|
| 1 | `20b10m/spec/` 混了规划、规格、分析三类 | 拆出 `plan/`（规划与分析），`spec/` 只放冻结件 |
| 2 | 33 个 block 未分模拟/数字 | 拆成 `analog/blocks/`（22）与 `digital/blocks/`（11） |
| 3 | block 内 `netlist/sim/layout/reports` 只写在 spec 里，没建 | 已为 22 个模拟块建好 |
| 4 | 根目录旧库/新计划/流程混放 | 新增根 `README.md` 指路（见下） |
| 5 | 无 `archive/` | 暂不加，历史版本靠 `snapshots/` 的 tar |

## 3. 已完成的修改

1. `20b10m/` 拆为 `plan/` `spec/` `interface/` `analog/blocks/` `digital/blocks/`；
2. 22 个模拟块建立 `netlist/ sim/ layout/ reports/` 四层；
3. 新增 `interface/ANALOG_DIGITAL_IF.md`（v0.9-draft）+ `analog_digital_if.csv`；
4. `spec/hierarchy.md` 重生成，标注每个模块的 analog/digital 域；
5. `spec/interfaces.csv` 增加 `cell_domain` 列；
6. `docs/if/接口契约_模板.csv` 改为指针；
7. 重整前备份：`snapshots/20b10m_before_reorg_20261107.tar.gz`。

## 4. 遗留（未修，需要决策）

| # | 项 | 为什么没做 | 建议 |
|:--|:---|:---|:---|
| 1 | `timing_budget.md` 与 `timing_detail.md` 合并 | 合并会丢历史表述 | 下次重构时二合一为 `timing.md` |
| 2 | V1 的 `Dac1_11b` 是否删除 | 它还是 P1 基线 | 保留，标注用途 |
| 3 | `interfaces.csv` 仍含 33 个 cell 的全部端口，未标"边界信号" | 需要逐条判断 | 由 `ANALOG_DIGITAL_IF.csv` 承担边界清单 |
| 4 | 无 git | 用户未要求 | 建议 `git init`，OA 库继续用快照 |
| 5 | SKY130 与 180 nm BCD 的后端双轨 | 属数字组范围 | 数字组定 |

## 5. 自查没覆盖到的

- **没有跑过任何仿真**：本文所有"建立/噪声/余量"都是预算推算，证据级别 L0；
- **没有独立复核论文数字**：20.5 bit、28 pF、90 ns、1.7 V 均来自论文文本，未与版图或测试数据交叉；
- **接口时序的数字侧可行性**：200 MHz、相位偏斜 ≤200 ps、`D1_MASK` 位宽，都未经综合验证。
