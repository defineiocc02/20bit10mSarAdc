# 代码索引（SAR20-10M）

> 所有入口文件开头都有 `[CODE-INDEX]` 注释块：作用、端口、时序、单位、假设。
> 先看这三个：`analog/blocks/Sar20bTop/netlist/Sar20bTop.scs`、`digital/DigitalTop.sv`、`model/adc.py`。

## 1. 目录

```
20b10m/
├── analog/
│   ├── netlist/
│   │   ├── build.scs              # 编译根（叶子→顶层 include 顺序）
│   │   ├── common_cells.scs       # unitcap/inv/tg/sw/diode
│   │   ├── digital_stubs.scs      # 数字黑盒端口（与 RTL 26/26 对齐）
│   │   ├── clk_rx.scs             # 200 MHz 差分接收
│   │   ├── pdk_models.scs         # PDK 别名（待填）
│   │   └── check_hier.py          # 层次/端口自检
│   └── blocks/<Block>/netlist/    # 每块一个 .scs
├── digital/
│   ├── DigitalTop.sv              # 单链数字顶层
│   ├── SliceSched.sv              # 18 片 8+8+2 调度
│   ├── Sar1Ctrl.sv                # 4b flash + 2b SAR + 5b
│   ├── Sar2Ctrl.sv                # 11b + 8×
│   ├── Sinc2.sv                   # CoI 累加
│   ├── ReconWeights.sv            # 冻结系数重构（非片上 LMS）
│   ├── FramePack.sv               # 24 bit 帧 + FIFO
│   ├── SerLvds.sv                 # 400 Mbit/s DDR
│   ├── tb_DigitalTop.sv           # 烟测
│   └── README.md                  # 模块表/时序/待接
└── model/
    ├── params.py                  # 唯一参数口径
    ├── sources.py                 # 噪声/失配源
    ├── adc.py                     # CAAZ/tracking/交织
    ├── static.py                  # DNL/INL
    ├── metrics.py                 # FFT 指标
    ├── experiments.py             # 全部实验入口
    ├── selftest.py                # 4 项自检
    ├── AUDIT.md                   # 来源/假设/错误/可信度
    └── results/                   # results.json + report.md
```

## 2. 模拟网表（Spectre）

| 文件 | 行数 | 作用 |
|:---|:---:|:---|
| `analog/blocks/Sar20bTop/netlist/Sar20bTop.scs` | 48 | 顶层：单链 + 18 片池 + SliceMux + RA + CT2 + 数字 |
| `analog/blocks/SdacPool18/netlist/SdacPool18.scs` | 41 | 18 片独立 slice，`ACQ<i>/CONV<i>/EN<i>` + 独立顶板 |
| `analog/blocks/SliceMux/netlist/SliceMux.scs` | 48 | 18:1 顶板选通，8 片同时导通 |
| `analog/blocks/CmpCoarse4b/netlist/CmpCoarse4b.scs` | 40 | 15 cmp + 16 段梯，4 bit 粗量化 |
| `analog/blocks/SdacSlice/netlist/SdacSlice.scs` | 98 | 128×27 fF，片内 7 bit |
| `analog/blocks/Sar1Top/netlist/Sar1Top.scs` | 16 | 比较器 + 三电平驱动 + SAR1 逻辑壳 |
| `analog/blocks/Sar2Ct/netlist/Sar2Ct.scs` | 30 | C_INC + DAC2 + replica + Cmp2 |
| `analog/blocks/RingAmp3/netlist/RingAmp3.scs` | 28 | 三级 ring amp（单套） |
| `analog/netlist/build.scs` | 40 | 编译根；按叶子→顶层 include |
| `analog/netlist/digital_stubs.scs` | 24 | 数字黑盒；与 `DigitalTop.sv` 26 端口一致 |

其余：`SwSample5v`、`Cmp1/Cmp2`、`Dac2_11b/Dac2Replica`、`RefBuffer/DynRefBuf/BiasGen`、`TriLevelDrv`、`FiaA1/AmpA2/FiaA3` 都在各自 `blocks/<Block>/netlist/`。

## 3. 数字 RTL（SystemVerilog）

| 文件 | 行数 | 作用 | 备注 |
|:---|:---:|:---|:---|
| `digital/DigitalTop.sv` | 102 | 单链顶层：帧计数/相位/后处理/输出 | 26 端口与模拟 stub 逐字一致 |
| `digital/SliceSched.sv` | 48 | 18 片 8+8+2，`base+8 mod 18` | 轮换，非 LFSR/DEM |
| `digital/Sar1Ctrl.sv` | 67 | 4b flash + 2b SAR + 5b | 行为级，非 bit-exact |
| `digital/Sar2Ctrl.sv` | 47 | 11b + 8× 重复 | 未建模亚稳态/建立 |
| `digital/Sinc2.sv` | 46 | 8 拍 CoI 累加，26 bit | 均匀权，非三角 CoI |
| `digital/ReconWeights.sv` | 29 | 冻结系数重构，22 bit | **不是片上 LMS** |
| `digital/FramePack.sv` | 48 | 24 bit 帧 + 16 深 FIFO | `{VALID,FAULT,DATA}` |
| `digital/SerLvds.sv` | 77 | 400 Mbit/s DDR | 双沿 always，综合换 ODDR |
| `digital/tb_DigitalTop.sv` | 34 | 200 MHz 烟测 | 需 iverilog |

## 4. Python 模型

| 文件 | 行数 | 作用 |
|:---|:---:|:---|
| `model/params.py` | 33 | 唯一参数：fs/噪声/ρ/M/交织误差 |
| `model/sources.py` | 39 | AR(1)、tracking 噪声、DAC 权重、slice 失配 |
| `model/adc.py` | 73 | CAAZ/tracking/部分交织/量化 |
| `model/static.py` | 46 | DAC1 DNL/INL + 校准上界 |
| `model/metrics.py` | 44 | FFT：DR/SNDR/SFDR/THD |
| `model/experiments.py` | 139 | 全部实验，写 results/ |
| `model/selftest.py` | 51 | 4 项自检 |
| `model/viz.py` | — | 出图基础设施：mm/字体/PNG+SVG+PDF/manifest |
| `model/plots.py` | — | 5 张图：CAAZ/M/交织/INL-DNL/频谱 |
| `model/PLOT_DESIGN.md` | — | 借什么/丢什么/样式合同 |
| `model/AUDIT.md` | — | 来源/假设/错误/可信度 |
| `model/results/figures/` | — | 15 个图件 + manifest.json + README |

## 5. 运行

```bash
cd 20b10m
# 模拟
python3 analog/netlist/check_hier.py        # 220 实例/39 子电路，端口一致
python3 analog/netlist/check_ports.py       # 数模 26/26 端口
# 数字（需 iverilog）
cd digital && make lint && make sim
# Python
cd 20b10m && python3 -m model.selftest      # 4 项自检
python3 -m model.experiments               # 生成 results/
```

## 6. 注释规范与已知 stub

- **模拟**：`// [CODE-INDEX]` 头 + 端口逐字对齐 `spec.md`；单位 V/F/Ω；模型名 `nch5/pch5/nch18/pch18`。
- **数字**：`// [CODE-INDEX]` 头 + 时序表；端口与 `digital_stubs.scs` 一致。
- **Python**：`# [CODE-INDEX]` 头；每个函数写明输入/输出与假设；`AUDIT.md` 记录已知错误。

**尚未接死的三处**：
1. `Sar1Ctrl`/`Sar2Ctrl` 未替换 `SarLogic1/2_stub`；
2. `ReconWeights` 仍是名义权重，48 系数 SPI 未接；
3. `pdk_models.scs` 未填 SMIC 别名，模拟只能结构检查。
