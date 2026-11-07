# 模拟部分分层管理清单（MANIFEST）

> 规则：**一个块一个目录，目录内四件套**（`netlist/ sim/ reports/ layout/`）。块的端口以 `spec.md` 为唯一来源，网表端口名必须逐字一致；不一致即视为网表未完成。
> 状态：`SPEC` 只有规格｜`NL` 有网表｜`SIM` 有仿真记录｜`LAY` 有版图｜`SIGN` 已签核。

## 0. 全局约定

| 项 | 约定 |
|:---|:---|
| 网表格式 | Spectre（`.scs`），顶层用 `simulator lang=spectre`；对外交付另导 CDL |
| 器件模型 | `nch5/pch5`（5 V 厚栅）、`nch18/pch18`（1.8 V 薄栅）；由 `netlist/pdk_models.scs` 映射到 SMIC 模型名 |
| 单位电容 | `CUNIT = 27 fF`，全片唯一；DAC1/DAC2/C_INC/replica 必须用同一 `unitcap` 子电路 |
| 电源命名 | `VDD5` / `VDD18` / `VDDIO` / `GND`；块内不出现 `VDD!` 之类全局名 |
| 端口顺序 | 与 `spec.md` 端口表一致，电源/地在最后 |
| 命名 | `X<实例>` 子电路，`M<器件>` MOS，`C<器件>` 电容，`R<器件>` 电阻，`I<器件>` 电流源 |
| 证据 | 每次仿真写 `sim/<run_id>/`，含网表快照、log、波形、结论一行 |

## 1. 块清单（25 块）

| # | 块 | 层级 | 父 | 域 | 网表 | 状态 | 复用来源 | 备注 |
|:--|:---|:---:|:---|:---|:---|:---:|:---|:---|
| 1 | `Sar20bTop` | L0 | — | 混合 | `netlist/Sar20bTop.scs` | NL | — | 两相顶层，36 pad |
| 2 | `BiasGen` | L1 | Sar20bTop | 1.8 V | `BiasGen/netlist/BiasGen.scs` | NL | `Bias`（R1） | bandgap 需自建/外供 |
| 3 | `RefBuffer` | L1 | Sar20bTop | 5 V+1.8 V | `RefBuffer/netlist/RefBuffer.scs` | NL | — | 5 V 主 + 2.5 V 副 |
| 4 | `DynRefBuf` | L1 | Sar20bTop | 5 V | `DynRefBuf/netlist/DynRefBuf.scs` | NL | — | 粗预充 + 300 pF |
| 5 | `RaMux` | L1 | Sar20bTop | 1.8 V | `RaMux/netlist/RaMux.scs` | NL | `TG_8C`（R1） | 旧方案遗留，部分交织不用 |
| 5b | `SliceMux` | L1 | Sar20bTop | 5 V | `SliceMux/netlist/SliceMux.scs` | NL | `TG_5V` | 18:1 选 8 片，偏斜 ≤50 ps |
| 6 | `RingAmp3` | L1 | Sar20bTop | 1.8 V | `RingAmp3/netlist/RingAmp3.scs` | NL | `amp_gainboost`（R2 拓扑） | 三级，共享 |
| 7 | `Sar1Top` | L1 | Sar20bTop | 混合 | `Sar1Top/netlist/Sar1Top.scs` | NL | `PiSAR_2st_8bit`（R2 结构） | 每相一套；采样在 slice 内 |
| 8 | `Sar2Ct` | L1 | Sar20bTop | 1.8 V | `Sar2Ct/netlist/Sar2Ct.scs` | NL | — | 每相一套 |
| 9 | `SwSample5v` | L3 | SdacSlice | 5 V | `SwSample5v/netlist/SwSample5v.scs` | NL | `Bootstrap`（R1） | Ron ≤20 Ω |
| 10 | `SdacPool18` | L1 | Sar20bTop | 5 V | `SdacPool18/netlist/SdacPool18.scs` | NL | — | 8+8+2 |
| 11 | `SdacSlice` | L3 | SdacPool18 | 5 V | `SdacSlice/netlist/SdacSlice.scs` | NL | — | 128×27 fF，7 bit |
| 12 | `Dac1_11b` | L2 | Sar1Top | 5 V | `Dac1_11b/netlist/Dac1_11b.scs` | NL | — | 兼容旧名的包装层，内部=Pool18 |
| 13 | `CmpCoarse4b` | L1 | Sar20bTop | 5 V | `CmpCoarse4b/netlist/CmpCoarse4b.scs` | NL | `comparator4in2`（R1）×15 | 4b flash + 2b SAR |
| 14 | `Cmp1` | L2 | Sar1Top | 5 V | `Cmp1/netlist/Cmp1.scs` | NL | `comparator4in2`（R1） | 一级精比较 |
| 15 | `TriLevelDrv` | L2 | Sar1Top | 5 V | `TriLevelDrv/netlist/TriLevelDrv.scs` | NL | `DYSARcontrl`（R1） | 74 µm 栅驱动 |
| 16 | `CincCouple` | L2 | Sar2Ct | 1.8 V | `CincCouple/netlist/CincCouple.scs` | NL | — | C_INC 1 pF + replica |
| 17 | `Dac2_11b` | L2 | Sar2Ct | 1.8 V | `Dac2_11b/netlist/Dac2_11b.scs` | NL | — | 6+5 分段，1 pF |
| 18 | `Dac2Replica` | L2 | Sar2Ct | 1.8 V | `Dac2Replica/netlist/Dac2Replica.scs` | NL | — | 1:1 复刻 |
| 19 | `Cmp2` | L2 | Sar2Ct | 1.8 V | `Cmp2/netlist/Cmp2.scs` | NL | `comparator_pin`（R1） | 2.36 ns/bit |
| 20 | `CmpQ2` | L2 | Sar1Top | 5 V | `CmpQ2/netlist/CmpQ2.scs` | NL | `comparator4in2`（R1） | 第二量化器，暂不实例化 |
| 21 | `FiaA1` | L2 | RingAmp3 | 1.8 V | `FiaA1/netlist/FiaA1.scs` | NL | — | AZ 输入级 |
| 22 | `AmpA2` | L2 | RingAmp3 | 1.8 V | `AmpA2/netlist/AmpA2.scs` | NL | — | diode-load |
| 23 | `FiaA3` | L2 | RingAmp3 | 1.8 V | `FiaA3/netlist/FiaA3.scs` | NL | — | 输出级 FIA |

## 2. 层次结构（10 MS/s 版）

```
Sar20bTop
├── RefBuffer ── DynRefBuf ── BiasGen
├── Sar1Top_A ──┬── SwSample5v_A
│               ├── SdacPool18_A ── SdacSlice ×9（8 用 + 1 备）
│               ├── CmpCoarse6b_A（63×）
│               ├── Cmp1_A
│               └── TriLevelDrv_A
├── Sar1Top_B（同上，相位 +100 ns）
├── RaMux（A/B 选相）
├── RingAmp3 ── FiaA1 ── AmpA2 ── FiaA3
├── Sar2Ct_A ── CincCouple + Dac2_11b + Dac2Replica + Cmp2
├── Sar2Ct_B（同上）
└── DigitalTop（两相调度、SliceShuffler、SINC2、LMS）
```

> 18 片池按 9+9 分给两个相位（每相 8 用 1 备）；池内 `SLICE_SEL<4:0>` 决定实际映射，备用片可在良率测试后重映射。

## 3. 网表完成度自检（脚本）

```bash
# 端口一致性：spec.md 的端口必须全部出现在网表 subckt 行
python3 scripts/check_ports.py 20b10m/analog
# 层次闭环：每个 X 实例必须有同名 .scs 或声明为外部
python3 scripts/check_hier.py 20b10m/analog/netlist
```

## 3b. 面积（详见 `area_model.md`）

- 按公开 0.18 µm **MIM 1 fF/µm²** 重算：DAC1 0.23、粗量化 0.028（4+2）、core **0.69**、die **1.06**（1030 µm，36 pad，pad 60×60/pitch 90）。
- 要回到 0.53：①粗量化移入跟踪窗 −0.086；②堆叠 MIM 2 fF/µm² −0.084；③去耦 150 pF −0.064；④影子寄存器 −0.017。

## 4. 当前缺口（G2 前必须关）

| # | 缺口 | 影响 | 关法 |
|:--|:---|:---|:---|
| 1 | `pdk_models.scs` 未落地 | 网表不能实跑 | 从 SMIC 018 PDK 抽 `nch5/pch5/nch18/pch18` 映射 |
| 2 | `CmpCoarse6b` 的 63 个比较器失配修调未画 | 极码错码 | 参考侧加 5 bit 修调 DAC |
| 3 | `RingAmp3` 的 AZ 开关时序未与 `ΦAZ 早关 2 ns` 对齐 | 增益误差 | L1 台架扫 AZ 关断时刻 |
| 4 | `SdacSlice` 的 128 单位版图未做共质心 | 7 bit 匹配 | G4 前出单元版图 |
| 5 | `Dac2_11b` 的桥接电容未定值 | INL 台阶 | 按 6+5 分段解桥容，L1 扫 |
