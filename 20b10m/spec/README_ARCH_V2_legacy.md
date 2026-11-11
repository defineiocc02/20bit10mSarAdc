# SAR20-10M —— 20.5 bit / 10 MS/s 两级 SAR（部分交织，180 nm BCD）

> **目标**：复现 CICC 2026 成电 20.5 bit / 5 MS/s 两级 SAR（CT 二级 + tracking averaging），并用 **ADI ISSCC2024 9.8 式部分交织** 做到 **10 MS/s**：只交织 DAC1 的 18 片池，量化器/RA/CT2/参考/数字全部单套共享。
> **状态**：G0 规格骨架 + 行为模型 + 模拟网表 + 数字 RTL；**没有硅测**，绝对指标不可签核。

## 1. 一句话架构

```
VIN → 18 片 DAC1 池（8 转换 + 8 采样 + 2 备）
    → SliceMux(18:1，选 8 片) → RA → CT2(C_INC+DAC2+replica) → DigitalTop → LVDS
```

- 单相帧 **90 ns**：ΦC0 7.5 / ΦC1 15 / ΦRA 25 / ΦC2 37.5 / guard 5。
- 转换链每 **100 ns** 跑一帧；slice 角色每 100 ns 交换，每片周期 200 ns（采样 100 + 转换 90 + 空闲 10）。
- 位账：**20.5 = 10 + 11 + 1.5(8×) − 2(冗余)**；G=32；FS=10 Vpp 差分；28 pF/侧/样本。

## 2. 关键数字（冻结口径）

| 项 | 值 |
|:---|:---|
| 分辨率 / 速率 | 20.5 bit / 10 MS/s |
| 输入 / 采样电容 | 差分 10 Vpp；28 pF/侧/样本（8×3.456 pF） |
| LSB1 / LSB2 / LSB_total | 9.766 mV / 19.07 µV / 6.744 µV |
| 粗量化 | 4b flash（15 cmp）+ 2b SAR，6.5 ns |
| RA | 单套；24.0 µV；Zout 300 Ω；1.7 V 摆幅 |
| CT2 | 单套；C_INC 1 pF；11 bit + 8× |
| 时钟 | 外部 200 MHz 差分，无 PLL；σt 1.0 ps 验收 / 0.5 ps 目标 |
| 输出 | 22 bit 无符号；LVDS DDR 400 Mbit/s；24 bit 帧 |
| 功耗 / 面积 | core ≈3.5–3.8 mW；4 mm² 宽松版 / 1.06 mm² 对标版 |
| 封装 / 引脚 | QFN-48 6×6；48 pad（29 功能 + 19 电源/地） |

## 3. 目录

```
20b10m/
├── README.md              本文件
├── HANDOVER.md            交接文档（接手先读：现状/缺陷/下一步）
├── CODE_INDEX.md          代码索引
├── TECH_EFFECTIVENESS.md  各技术有效性对比（结论总表）
├── FILE_LAYOUT.md         文件存放规范
├── plan/                  规划、架构裁决、面积/floorplan、SPEC 主文档
├── spec/                  层次、端口、位分配、时序、10M 规格表
├── interface/             模拟↔数字接口、引脚定义、输出协议
├── analog/blocks/         25 个模拟块：spec.md + netlist/ sim/ reports/ layout/
│   └── netlist/           build.scs（编译根）、common_cells.scs、digital_stubs.scs、pdk_models.scs
├── digital/               DigitalTop / SliceSched / Sar1Ctrl / Sar2Ctrl / Sinc2 / ReconWeights / FramePack / SerLvds
├── model/                 Python 行为模型（CAAZ / tracking / 交织 / 静态 / 出图）
│   ├── results/           results.json、report.md
│   ├── results/figures/   41 张诊断图 + manifest.json
│   ├── results/figures_paper/   14 张论文测试风格图 + manifest.json
│   └── results/figures_measured/ 9 张实测风格图（频谱/INL-DNL/DR/技术排序）
├── verilog/               端口桩
├── skill/                 建库脚本
└── docs/                  导入步骤、流程模板
```

## 4. 先看什么

| 想了解 | 文件 |
|:---|:---|
| 接手这个项目 | `HANDOVER.md`（30 秒摘要 → P0 缺陷 → 里程碑） |
| 代码在哪、怎么读 | `CODE_INDEX.md` |
| 架构裁决与预算 | `plan/master_plan_20b5m.md`、`plan/arch_10m.md`、`plan/coarse_quant_decision.md` |
| 10M 逐块规格 | `spec/spec_tree_10m.md` |
| 面积对标成电 | `analog/area_vs_cicc.md` |
| 内部 floorplan | `analog/floorplan_4mm.md`、`floorplan_4mm.png` |
| 走线规则 | `analog/routing_plan.md` |
| 各技术到底值多少 dB | `TECH_EFFECTIVENESS.md` |
| 模型可信度 | `model/AUDIT.md`、`model/REFERENCE_AUDIT.md` |
| 校准链路缺口 | `digital/CALIBRATION_GAP.md` |
| 出图规范 | `model/PLOT_DESIGN.md` |
| 引脚/输出接口 | `interface/PINOUT_QFN48.md`、`interface/OUTPUT_IF_10M.md` |

## 5. 模型结论（可复现）

| 问题 | 结论 | 图 |
|:---|:---|:---|
| DAC1 校准有用吗 | 不校准 SNDR **94.5 dB / SFDR 103.5 dBc**，校准后回到噪声底 **101.8 dB**（+7.3 dB）；残余 INL 0.3 ppm | `measured01/02/09`、`fig23–27` |
| 交织能提速吗 | 理想 10 MS/s 与 5 MS/s 同 DR（101.87 dB）→ 交织只换速率；2 MHz、2 ps skew 掉 1.5 dB；增益 50 ppm 掉 5.4 dB | `fig14–20` |
| CAAZ 有用吗 | 100 kHz **+3.62 dB**、2 MHz +3.18；其中 3.04 dB 是通用两点平均，AZ 抵消只 **+0.58 dB** | `measured08`、`fig01/02/03/07` |
| 8× 平均有多少 | M=1→8 只有 **+1.67 dB**（ρ=0.61），不是 4.5 dB | `fig08–13` |
| 洗牌值不值 | DR −1.0 dB，SFDR **+21.2 dBc**（103.7→124.9） | `fig17–19` |
| 面积该多大 | 对标成电 core **0.70–1.0**、die 0.95–1.25；4 mm² 是宽松版 | `fig38`、`area_vs_cicc.md` |

**注意**：绝对 DR/SNDR/INL 为模型值，未标定，不能当签核；模型缺参考建立/抖动/亚稳态/DAC 建立，实测 SFDR 预期 100–110 dBc。
详见 `TECH_EFFECTIVENESS.md`（含"能声称/不能声称"清单）与 `model/REFERENCE_AUDIT.md`（与参考实现的逐点对照）。

## 6. 快速运行

```bash
cd 20b10m
# 模型
python3 -m model.selftest        # 4 项自检
python3 -m model.experiments     # results.json / report.md
python3 -m model.figures          # 41 张诊断图 + manifest
python3 -m model.paper_figures    # 14 张论文风格图 + manifest
# 模拟网表
python3 analog/netlist/check_hier.py
python3 analog/netlist/check_ports.py
# 数字（需 iverilog/verilator）
cd digital && make lint && make sim
```

## 7. 当前缺口

1. `pdk_models.scs` 未填 SMIC 别名，模拟只能结构检查。
2. `Sar1Ctrl/Sar2Ctrl` 未替换两个数字 stub。
3. `ReconWeights` 仍是名义权重，48 系数 SPI 未接。
4. 模型缺参考纹波、抖动、比较器亚稳态、DAC 建立。
5. 版图未开始；floorplan 只是约束图。

## 8. 证据等级

L0 静态 → L1 行为/单元 → L2 前仿 → L3 后仿 → L4 PVT/MC → L5 硅测。**任何“20.5 bit 精度”“102.5 dB 已复现”只有 L5 才能写。**
