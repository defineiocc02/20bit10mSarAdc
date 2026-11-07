# 文件存放规范

> 一句话：**规划在 `plan/`，冻结规格在 `spec/`，接口在 `interface/`，实现按 `analog|digital` 分家，历史靠 `snapshots/`。**

---

## 1. 目录总览

```
pipelinedsar工作站/
├── README.md                  项目总入口（旧库/新计划/流程各在哪）
├── STATUS.md                  唯一状态源
├── cds.lib                    Virtuoso 库映射
├── docs/                      团队流程（规范、交付流程、模板）
├── snapshots/                 OA 库与阶段快照（tar + sha256）
├── Pipe_SAR/                  旧 65 nm 库（只读参考，不再改）
├── Pipe_SAR_attic_20261107/   旧库移出件
└── 20b10m/                    新计划
    ├── README.md
    ├── plan/                  规划与分析（可改，不冻结）
    ├── spec/                  冻结规格（改要变更单）
    ├── interface/             模拟↔数字接口（给数字组）
    ├── review/                审查报告
    ├── analog/blocks/<Cell>/  22 个模拟块
    ├── digital/blocks/<Cell>/ 11 个数字块
    ├── verilog/               端口桩（由 spec/interfaces.csv 生成）
    ├── skill/                 建库脚本
    └── docs/                  导入步骤
```

## 2. 每个 block 的内部结构

```
analog/blocks/<Cell>/
├── spec.md        端口、参数、判据、文件位置（唯一说明）
├── netlist/       导出的 CDL / 网表（G2 起）
├── sim/           每次仿真一个 run_id 子目录
│   └── <YYYYMMDD>_<purpose>_v<n>/
│       ├── run.md         仿真运行记录
│       ├── config/        模型、参数、.scs
│       ├── raw/           psf（不入库，可删）
│       └── result/        csv + 图 + 结论
├── layout/        GDS、DRC/LVS 报告（G4 起）
└── reports/       单元报告、评审记录
```

数字块只有 `spec.md`（其余由数字组按自己的流程组织）。

## 3. 放哪张表

| 文件类型 | 位置 | 命名 |
|:---|:---|:---|
| 规划/分析 | `plan/` | `<主题>.md`，不编号 |
| 冻结规格 | `spec/` | `architecture.md`、`bit_allocation.md`、`timing.md`、`hierarchy.md`、`interfaces.csv` |
| 接口 | `interface/` | `ANALOG_DIGITAL_IF.md` + `analog_digital_if.csv` |
| 审查 | `review/` | `<YYYYMMDD>_<主题>.md` |
| 仿真记录 | `analog/blocks/<Cell>/sim/<run_id>/run.md` | 见 `docs/templates/仿真运行记录.md` |
| 网表 | `analog/blocks/<Cell>/netlist/` | `<Cell>_<快照tag>.cdl` |
| 版图 | `analog/blocks/<Cell>/layout/` | `<Cell>_<版本>.gds` + `drc_<日期>.rpt` |
| 报告 | `analog/blocks/<Cell>/reports/` | `L<级别>_<内容>_<日期>.md` |

## 4. 模拟侧交付物（每个 block 在 G2 必须交）

| # | 交付 | 判据 | 级别 |
|:--|:---|:---|:---:|
| 1 | `spec.md` 更新到"已实现"（端口与接口规范一致） | 逐条对照 `ANALOG_DIGITAL_IF.md` | — |
| 2 | 网表（CDL） | 能独立 netlist，无悬空 | L0 |
| 3 | 单元仿真 `run.md` | 过 block spec 的验收判据 | L1 |
| 4 | 噪声/角点（若该块有噪声指标） | 用 `tran noise` 或 pnoise | L3 |
| 5 | 交接单 | `docs/templates/模块交接单.md`，写清"未验证项" | — |

**没交第 3 项就不算 G2 通过**；只交 spec 不算交付。

## 5. 枚举与映射

| 字段 | 取值 | 含义 |
|:---|:---|:---|
| `interfaces.csv:dir` | `in` / `out` / `io` / `pwr` | 从 cell 角度 |
| Verilog 生成 | `in→input`、`out→output`、`io→inout`、`pwr→inout` | 仅用于生成 pin |
| `interfaces.csv:kind` | `analog` / `digital` / `power` | 电气类型 |
| `interfaces.csv:domain` | `5V` / `1.8V` | 电压域 |
| `interfaces.csv:cell_domain` | `analog` / `digital` | 属于哪一组 |
| 接口 CSV `direction` | `d2a` / `a2d` / `ext->both` / `d2a`（状态） | 数字↔模拟方向 |

## 6. 生命周期

```
草案(draft) ──评审──► 冻结(frozen) ──变更单──► 修订(rev N)
   │                      │
   └─ 放 plan/            └─ 放 spec/，带版本号与变更记录
```

- `plan/` 下的文件可以随时改，不用变更单；
- `spec/` 与 `interface/` 冻结后，改动必须走 `docs/templates/变更单.md`；
- 每个 Gate 打一次快照：`scripts/snapshot.sh <gate>_<tag>`。

## 7. 不入库 / 要清理

| 内容 | 处理 |
|:---|:---|
| `raw/` 下的 psf | 只留 result，raw 可删 |
| PDK | 不进仓库，只记版本与路径 |
| GDS 大文件 | 走快照，不进 git |
| `*.oa-`、`*.bak` | 不入库 |
| 临时脚本 | 放 `/tmp`，任务结束清理 |
