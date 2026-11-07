# 模拟网表目录说明（netlist/）

## 1. 结构

```
analog/
├── netlist/                 编译根：common / stub / 时钟接收 / build.scs / tb
│   ├── build.scs            ← 叶子→顶层的 include 顺序（唯一编译入口）
│   ├── common_cells.scs     unitcap / inv / tg / sw / diode
│   ├── digital_stubs.scs    数字块的黑盒端口（G3 前替换）
│   ├── clk_rx.scs           200 MHz 差分接收
│   ├── pdk_models.scs       PDK 模型别名（**G2 前必须填**）
│   ├── check_hier.py        层次/端口自检（不依赖 Spectre）
│   └── tb/Sar20bTop_tb.scs  顶层台架骨架
└── blocks/<Block>/netlist/<Block>.scs   ← 每块一个主网表
```

## 2. 命名与端口规则

- 端口名逐字对齐 `blocks/<Block>/spec.md` 与 `spec/spec_tree_10m.md`；改端口必须同时改三处。
- 电源/地一律显式端口：`VDD5` / `VDD18` / `VDDIO` / `GND`，不用全局 `VDD!`。
- 单位电容只允许 `unitcap`（27 fF）；DAC1/DAC2/C_INC/replica 共用。
- 器件模型只用四个别名：`nch5/pch5/nch18/pch18`。

## 3. 自检

```bash
cd 20b10m/analog/netlist
python3 check_hier.py
# 期望：OK: 所有实例的子电路均已定义，端口数一致
```

## 4. 实跑前置（当前缺）

| # | 缺什么 | 影响 | 谁给 |
|:--|:---|:---|:---|
| 1 | `pdk_models.scs` 的 PDK 路径与四个别名 | MOS 无法解析，网表只能结构检查 | PDK / 版图 |
| 2 | `DigitalTop` 行为模型（Verilog-A） | 顶层没有 PHI_* 驱动，无法 tran | 数字组 |
| 3 | `CmpCoarse6b` 的 5 bit 失调修调 | 极码可能越窗 | 模拟 |
| 4 | `Dac2_11b` 桥容（28 fF 初值） | INL 台阶 | 模拟 L1 |
| 5 | `RingAmp3` 的 CMFB/AZ 实际网络 | 共模漂移 | 模拟 L1 |

## 5. 层次约定

- **不允许**在块网表里 `include` 别的块；统一由 `build.scs` 按顺序 include。
- 新增块：先在 `blocks/<Block>/netlist/` 建 `.scs`，再在 `build.scs` 叶子段插入，最后跑 `check_hier.py`。
- 数字黑盒只允许出现在 `digital_stubs.scs`；块内不得自造数字行为。
