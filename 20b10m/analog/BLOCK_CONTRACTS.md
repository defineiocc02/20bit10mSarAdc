# 模拟块契约（BLOCK_CONTRACTS）

> ⚠️ **2026-11-08 审计快照，不是现行口径。** 端口/位宽以 `spec/SSOT.md` 为准；
> 本文的 1039 / 11 bit / 28 pF 等数字是当时网表的实测，保留作缺陷证据。

> 基线：**BL-v1-draft**（`spec/ARCH_V2.md`）
> 口径生效：2026-11-08 ｜ 作者：analog-circuit-designer-2（任务 T02）
> **端口唯一来源 = 网表 `subckt` 行**（本轮显式改口径：`MANIFEST.md:3` 的"端口以 spec.md 为唯一来源"与实现现状相反，见 §4-C6）
> 证据标签：`[NL]` 网表逐字 ｜ `[SPEC]` blocks/*/spec.md ｜ `[ARCH]` spec/ARCH_V2.md ｜ `[PLAN]` plan/*.md ｜ `[RUN]` 本轮实跑命令

---

## 0. 全局核账（先看这 6 个数）

| # | 量 | 值 | 来源 |
|:--|:---|:---|:---|
| 1 | 块目录数 | **24** | `ls analog/blocks/` → 24 个目录 [`RUN`] |
| 2 | 目录里有网表的 | **23**（缺 `Dac1_11b`） | `blocks/Dac1_11b/netlist/` 是空目录 [`RUN`] |
| 3 | 在用 / legacy | **21 / 3**（legacy = `RaMux`、`CmpQ2`、`Dac1_11b`） | `ARCH_V2.md:172`。网表可追溯的只有 **20** 块：`SwSample5v` 虽"在用"但 **0 个 X 实例**（见 C7） |
| 4 | 编译单元 | files=28, subckts=39, instances=220 | `python3 netlist/check_hier.py` 输出 [`RUN`] |
| 5 | 器件语句（未展开） | **M=105 / R=33 / C=33** | 正则统计 28 个 .scs [`RUN`] |
| 6 | 有仿真/版图记录的块 | **0**（24 个 `sim/ reports/ layout/` 全是空目录） | `find blocks -path '*/sim/*'` 计数 0 [`RUN`] |

> `MANIFEST.md:18` 写"块清单（**25 块**）"，但该表实际只有 24 行（#1–#23 + #5b）。**25 是笔误**，见 C5。
> `check_hier.py` 的 "OK" **只证明实例引用的 subckt 存在、token 数相等**（`check_hier.py:68`），不展开总线、不查未驱动网络 → 不等于可仿真。见 §5-D16。

---

## 1. 总表

列说明：
- **层级**：L0 顶层 / L1 壳 / L2 子块 / L3 叶子 / *infra* 编译期共用单元
- **域**：`5V` 仅 5 V 供电与厚栅 ｜ `1.8V` 仅 1.8 V 供电 ｜ `混合` 两者都有，或 1.8 V 供电但挂 5 V 信号
- **端口数**：`token/展开位`（总线按位展开；`token` 即 subckt 行端口个数）
- **状态**：SPEC 仅规格 ｜ NL 有网表 ｜ SIM 有仿真记录 ｜ LAY 有版图 —— **全项目无 SIM / LAY**

| # | 块 | 层级 | 父（网表实际） | 父（spec.md 声称） | 域 | 在用 | 端口数 | 供电端口 | 关键指标（一条） | 状态 |
|:--|:---|:---:|:---|:---|:---:|:---:|:---:|:---|:---|:---:|
| 1 | `Sar20bTop` | L0 | — | — | 混合 | 在用 | 18/39 | VDD5 VDD18 VDDIO | 22 bit 输出 / 10 MS/s / DR 102.5 dB [`ARCH:19`] | NL |
| 2 | `BiasGen` | L1 | Sar20bTop | Sar20bTop | 1.8V | 在用 | 9/9 | VDD18 | 总电流 <200 µA，PVT <20% [`SPEC`] | NL |
| 3 | `RefBuffer` | L1 | Sar20bTop | Sar20bTop | 5V | 在用 | 6/6 | VDD5 | R_out ≤20 Ω、噪声 ≤2.9 µV、400–500 µW [`NL:3`] | NL |
| 4 | `DynRefBuf` | L1 | Sar20bTop | Sar20bTop | 5V | 在用 | 7/7 | VDD5 | 300 pF 去耦 + R_buf 20 Ω [`NL:3,15`] | NL |
| 5 | `SdacPool18` | L1 | Sar20bTop | Sar1Top* | 5V | 在用 | 14/105 | VDD5 | 18×3.456 pF，8 转换+8 采样+2 备 [`NL:3`] | NL |
| 6 | `SdacSlice` | L2 | SdacPool18 | SdacPool18 | 5V | 在用 | 14/20 | VDD5 | 3.456 pF = 128×27 fF，片内 7b [`NL:1`] | NL |
| 7 | `SwSample5v` | L3 | **（无实例）** | SdacSlice [`ARCH:143`] | 混合 | 在用（挂空） | 7/7 | VDD5 (+VDD18 预留) | Ron ≤20 Ω [`SPEC`] | NL |
| 8 | `SliceMux` | L1 | Sar20bTop | Sar20bTop | 5V | 在用 | 8/76 | VDD5 | Ron ≤20 Ω/片，片间偏斜 ≤50 ps [`SPEC`] | NL |
| 9 | `CmpCoarse4b` | L1 | Sar20bTop | Sar20bTop | 混合 | 在用 | 8/22 | VDD18 | 15 cmp，2.0 ns，±0.5 LSB4=±8 LSB1 [`NL:2`] | NL |
| 10 | `Sar1Top` | L1 | Sar20bTop | Sar20bTop | 混合 | 在用 | 16/50 | VDD5 VDD18 | ΦC0 10 ns + ΦC1 15 ns 内 6 次判决 [`ARCH:216`] | NL |
| 11 | `Cmp1` | L2 | Sar1Top | Sar1Top | 混合 | 在用 | 7/7 | VDD18 | 判决 <1.5 ns，失调 <1 LSB1 [`SPEC`] | NL |
| 12 | `TriLevelDrv` | L2 | Sar1Top（经 `TriLevelBank11`） | Sar1Top | 5V | 在用 | 8/8 | VDD5 | 74 µm 栅驱动能力 [`NL:3`] | NL |
| 13 | `RingAmp3` | L1 | Sar20bTop | Sar20bTop | 1.8V | 在用 | 14/14 | VDD18 | G=32，1.25 Vpp，Zout 300 Ω，CL=4 pF [`ARCH:266`] | NL |
| 14 | `FiaA1` | L2 | RingAmp3 | RingAmp3 | 1.8V | 在用 | 9/9 | VDD18 | 增益 >20 dB，带宽 >500 MHz [`SPEC`] | NL |
| 15 | `AmpA2` | L2 | RingAmp3 | RingAmp3 | 1.8V | 在用 | 8/8 | VDD18 | 增益 >10 dB，极点 >1 GHz [`SPEC`] | NL |
| 16 | `FiaA3` | L2 | RingAmp3 | RingAmp3 | 1.8V | 在用 | 9/9 | VDD18 | 摆幅 1.7 V，建立 <20 ns [`SPEC`] | NL |
| 17 | `Sar2Ct` | L1 | Sar20bTop | Sar20bTop | 1.8V | 在用 | 12/29 | VDD18 | 11 bit + 8× 重复，19 拍 = 38 ns ≤ 40 ns [`ARCH:45`] | NL |
| 18 | `CincCouple` | L2 | Sar2Ct | Sar2Ct | 1.8V | 在用 | 10/20 | VDD18 | C_INC 1.0 pF/侧（37×27 fF）[`NL:8`] | NL |
| 19 | `Dac2_11b` | L2 | Sar2Ct + Dac2Replica | Sar2Ct | 1.8V | 在用 | 7/17 | VDD18 | 11b = 5b 主阵 + 桥 + 6b 子阵，顶板 ≈0.89 pF [`NL:2`] | NL |
| 20 | `Dac2Replica` | L2 | **CincCouple**（非 Sar2Ct） | Sar2Ct | 1.8V | 在用 | 7/17 | VDD18 | 与 Dac2_11b 1:1，失配 <1% [`SPEC`] | NL |
| 21 | `Cmp2` | L2 | Sar2Ct | Sar2Ct | 1.8V | 在用 | 7/7 | VDD18 | 判决 <1 ns [`SPEC`] / 2.36 ns/bit [`MANIFEST:41`] **互斥** | NL |
| 22 | `RaMux` | L1 | **（无实例）** | Sar20bTop | 1.8V | **legacy** | 9/9 | VDD18 | Ron <50 Ω，寄生 <5 fF [`SPEC`] | NL |
| 23 | `CmpQ2` | L2 | **（无实例）** | Sar1Top | 混合 | **legacy** | 7/7 | VDD18 | 与主量化器同构，返回采样 <1 ns [`SPEC`] | NL |
| 24 | `Dac1_11b` | L2 | **（无实例、无网表）** | Sar1Top | 5V | **legacy** | — | — | 1039×27 fF（旧口径）[`SPEC`] | **SPEC** |

`*` `SdacPool18/spec.md:3` 写父 = `Sar1Top`；网表实际由 `Sar20bTop` 直接实例化（`Sar20bTop.scs:24`），`Sar1Top` 里没有它。以网表为准。
`†` 层级按实际深度校正：`SdacPool18` = L1（顶的子）、`SdacSlice` = L2、`SwSample5v` = L3。`MANIFEST.md:33` 把 `SdacSlice` 标成 L3（跳过 L2），与 `SPEC` 表自己的 L1→L3 缺口矛盾，此处按 `<`ARCH_V2.md:141-143`>` 的三级树校正。

### 1.1 infra（编译期共用单元，不是块目录）

| 名字 | 文件:行 | 端口数 | 域 | 说明 |
|:---|:---|:---:|:---:|:---|
| `ClkRx` | `netlist/clk_rx.scs:6` | 5 | 1.8V | CLKP CLKN → CLK200，Rterm 100 Ω |
| `unitcap` | `netlist/common_cells.scs:9` | 2 | — | CUNIT=27 f（`common_cells.scs:5`） |
| `inv18` / `inv5` | `common_cells.scs:14` / `:20` | 4 / 4 | 1.8 / 5 | — |
| `tg5` / `tg18` | `common_cells.scs:26` / `:32` | 6 / 6 | 5 / 1.8 | 带 `params: wn/wp` |
| `sw5` / `diode18` / `cm_sense` | `common_cells.scs:38/:43/:48` | 5 / 3 / 3 | 5 / 1.8 / — | `cm_sense` 仅台架 |
| `SarLogic1_stub` | `netlist/digital_stubs.scs:4` | 10/44 | 1.8V | **空壳**，无行为 |
| `SarLogic2_stub` | `digital_stubs.scs:7` | 8/25 | 1.8V | **空壳** |
| `DigitalTop_stub` | `digital_stubs.scs:11` | 2/39（4 行续行） | 1.8V | **空壳** |

> 三个数字 stub 的 `subckt` 体内**没有任何语句** → 顶层所有 `PHI_*` / `SEL` / `ACQ` / `CONV` / `EN` 永远是未驱动网络。这是 `Sar20bTop_tb.scs` 不能跑 tran 的第一原因（`tb/Sar20bTop_tb.scs:2` 自己也承认）。

---

## 2. 逐块端口契约（从网表 `subckt` 行逐字抽取）

> 格式：`序号 端口名` 按 subckt 行**原顺序**列出。方向列是从实例连接推断的（网表没有方向信息），标 `?` 表示网表内部看不出唯一方向。
> 与 spec.md 不一致的块 → 该小节末"⚠"行，汇总见 §3。

### 2.1 `Sar20bTop`（L0，`blocks/Sar20bTop/netlist/Sar20bTop.scs:15`）
```
 1 VINP   2 VINN   3 VREFP   4 VREFN   5 VREF2   6 VCM
 7 CLKP   8 CLKN   9 RSTN   10 CAL_EN  11 IREF
12 DOUT<21:0>   13 DOUT_RDY   14 MON
15 VDD5  16 VDD18  17 VDDIO  18 GND
```
18 token / 39 位。实例（`:18-45`）：`ClkRx`、`RefBuffer`、`DynRefBuf`、`BiasGen`、`SdacPool18`、`SliceMux`、`Sar1Top`、`CmpCoarse4b`、`RingAmp3`、`Sar2Ct`、`DigitalTop_stub`。
⚠ 与 spec 差异：新增 `VREF2` / `IREF` / `VDDIO`；`CLK`→`CLKP`+`CLKN`；`DOUT<20:0>`(21b) → `DOUT<21:0>`(22b)；`MON<7:0>` → `MON`（标量）。**网表 `:45` 又给 `DigitalTop_stub` 接 `MON<7:0>`**（与标量端口 `MON` 不是同一网络）→ 见 D1。

### 2.2 `Sar1Top`（L1，`Sar1Top.scs:5`）
```
 1 VTOPP  2 VTOPN  3 VREF   4 VCM   5 VGND
 6 COARSE<14:0>   7 PHI_C0   8 PHI_C1
 9 D1<10:0>  10 SAMN<10:0>  11 CMPP  12 CMPN  13 DONE1
14 VDD5  15 VDD18  16 GND
```
16 token / 50 位。实例（`:6-8`）：`Cmp1`、`TriLevelBank11`、`SarLogic1_stub`。
⚠ 差异极大（见 §4-C7）：**没有** `VINP/VINN`（采样在 slice 内）、没有 `PHI_S/PHI_RA`、没有 `VRESP/VRESN`、没有 `D1_RDY`（改 `DONE1`）；`VREFP`+`VREFN` 合并成单端 `VREF`；**新增** `COARSE<14:0>`/`SAMN<10:0>`/`CMPP`/`CMPN`；端口顺序把 `VTOPP/VTOPN` 提到第 1 位。
⚠ `:7` `Xdrv ... OUT<10:0>` 接 `SEG<10:0>`，`SEG` 无任何消费者 → 见 D14。

### 2.3 `Sar2Ct`（L1，`Sar2Ct.scs:6`）
```
 1 VRESP  2 VRESN  3 VREFP2  4 VREFN2  5 VCM
 6 PHI_RA  7 PHI_C2
 8 D2<10:0>  9 DT<7:0>  10 DONE2
11 VDD18  12 GND
```
12 token / 29 位。实例（`:8-18`）：`CincCouple`、`Dac2_11b`、`Cmp2`、`SarLogic2_stub`。
⚠ `D2<11:0>`(12b) → `D2<10:0>`(11b)：**网表对，spec 错**（`ARCH_V2.md:40` D-04 冻结 11 bit）。`Dac2_12b` 名已不存在。

### 2.4 `SdacPool18`（L1，`SdacPool18.scs:13`）
```
 1 VINP   2 VINN   3 VREFP   4 VREFN   5 VCM   6 VGND
 7 D<6:0>          （7 位）
 8 ACQ<17:0>   9 CONV<17:0>  10 EN<17:0>
11 VTOPP<17:0>  12 VTOPN<17:0>
13 VDD5  14 GND
```
14 token / 105 位。实例：`SdacSlice` ×18（`:15-49`，逐片展开，无 generate）。
⚠ 与 spec **完全不同**：spec 的 `PHI_ACQ<1:0>`/`PHI_CONV<1:0>`/`D1<10:0>`/`SLICE_SEL<4:0>` 在网表里全不存在。**`D<6:0>` 只有 7 位，而 `Sar20bTop.scs:24` 给它接 `D1<6:0>`（截断 11 位码的高 4 位）**，跨片 unary 高 3 bit 无处承载 → 见 D13。

### 2.5 `SdacSlice`（L2，`SdacSlice.scs:95`）
```
 1 VINP   2 VINN   3 VREFP   4 VREFN   5 VCM   6 VGND
 7 D<6:0>          （7 位）
 8 PHI_ACQ  9 PHI_CONV  10 EN
11 VTOPP  12 VTOPN  13 VDD5  14 GND
```
14 token / 20 位。内部：`sdac_half` ×2（`:96-97`，P/N 侧镜像），`sdac_half:19` 内 8 个电容 27f…1728f + Cdum 27f = **3456 f = 128×27 f**。
⚠ spec 的 `DIN<13:0>`(14b) → 网表 `D<6:0>`(7b)；spec 无 `EN`、无 `VTOPP/VTOPN`。
⚠ 电容是**写死数值**，未用 `unitcap` → 违反 `MANIFEST.md:12` / `netlist/README.md:22`（见 §5-D12）。
⚠ **只有两电平**：`sdac_half` 每位的底板开关只到 `VREFP`/`VREFN`（`:32-33` 等），`VCM` 只在 `EN=0` 时整列接（`:85-91`）→ spec.md 的"三电平(VREF/VCM/VGND)"未实现（见 §5-D18）。

### 2.6 `SwSample5v`（L3，`SwSample5v.scs:6`）
```
 1 VIN   2 VOUT   3 PHI_S   4 CKS   5 VDD5   6 VDD18   7 GND
```
7/7，与 spec **完全一致**。**但全 28 个 .scs 里 0 个 X 实例引用它**（只有 `build.scs:14` include 与 `tb/tb_SwSample5v.scs:13`）→ 见 C7/D2。

### 2.7 `SliceMux`（L1，`SliceMux.scs:12`）
```
 1 VTOPP<17:0>  2 VTOPN<17:0>  3 SEL<17:0>  4 SELB<17:0>
 5 VOUTP  6 VOUTN  7 VDD5  8 GND
```
8 token / 76 位。36 个 `tg5 wn=40u wp=80u`（`:13-48`）。与 spec **完全一致**（spec 把 `VDD5/GND` 合写）。

### 2.8 `CmpCoarse4b`（L1，`CmpCoarse4b.scs:12`）
```
 1 VINP  2 VINN  3 VREFP  4 VREFN  5 PHI_C0  6 D<14:0>  7 VDD18  8 GND
```
8 token / 22 位。16 个 1 kΩ 电阻梯（`:13-29`，R0–R16）+ **15 个 `Cmp1`**（`:30-44`，Xc0–Xc14）→ 温度计 15 位。
⚠ spec 端口表把 `VINP/VINN`、`VREFP/VREFN`、`VDD18/GND` 合写成一格，展开后**逐 port 一致**；但 spec 把域标成 `5V` 而供电只有 `VDD18`（实际是"1.8 V 供电 + 5 V 输入"的混合域）。

### 2.9 `Cmp1` / `Cmp2` / `CmpQ2`（L2，`Cmp1.scs:6` / `Cmp2.scs:5` / `CmpQ2.scs:5`）
```
 1 VINP  2 VINN  3 CLK  4 OUTP  5 OUTN  6 VDD18  7 GND
```
三者端口**同构**，7/7，与各 spec **完全一致**。
- `Cmp1` 用 `nch5` 输入对（`:10-11`）+ `nch18` 再生 → 混合域（spec 标 5V 正确）。
- `Cmp2`/`CmpQ2` 全 `nch18/pch18` → 1.8V（`CmpQ2.scs:10-11` 也是 nch5，实际混合）。
⚠ **`Cmp1`/`Cmp2` 都没有 `*_READY` 输出**，而 `ARCH_V2.md:343`（A3）要求"模拟侧必须给 `CMP1_READY/CMP2_READY` 4 相握手脉冲"——这是**当前端口表的最大缺口**，不加则 ΦC2 无法实现（见 §4-C9）。

### 2.10 `TriLevelDrv` / `TriLevelBank11`（`TriLevelDrv.scs:6` / `:36`）
```
TriLevelDrv     : 1 VREF  2 VCM  3 VGND  4 VIN  5 SAMN  6 OUT  7 VDD5  8 GND    (8)
TriLevelBank11  : 1 VREF  2 VCM  3 VGND  4 D<10:0>  5 SAMN<10:0>  6 OUT<10:0>  7 VDD5  8 GND  (8/38)
```
`TriLevelBank11` 内含 `TriLevelDrv` ×11（`:37-47`）。
⚠ spec 端口是 `VREF VCM VGND VIN SAM- PI NI OUT VDD5 VDD18`（10 个）→ 网表**删掉 `PI`/`NI`/`VDD18`、`SAM-` 改名 `SAMN`**。

### 2.11 `RingAmp3`（L1，`RingAmp3.scs:7`）
```
 1 VINP  2 VINN  3 VOUTP  4 VOUTN  5 VCM
 6 PHI_RA  7 PHI_AZ  8 EN
 9 VBP  10 VBN  11 VCP  12 VCN
13 VDD18  14 GND
```
14/14。内含 `FiaA1`(`:9`)、`AmpA2`(`:18`)、`FiaA3`(`:21`)，级间 1 pF + 1 GΩ 弱定义共模（`:12-15`）。
⚠ spec 只有 10 个端口，**网表多出 `VBP/VBN/VCP/VCN` 四个偏置端口** → spec 漏写。见 D8（`Mpd` 无效开关）。

### 2.12 `FiaA1` / `AmpA2` / `FiaA3`（`FiaA1.scs:6` / `AmpA2.scs:5` / `FiaA3.scs:6`）
```
FiaA1 : VINP VINN VOUTP VOUTN VBP VBN PHI_AZ VDD18 GND                        (9)
AmpA2 : VINP VINN VOUTP VOUTN VBP VBN VDD18 GND                               (8)
FiaA3 : VINP VINN VOUTP VOUTN VCP VCN PHI_RA VDD18 GND                        (9)
```
三者与各自 spec **完全一致**。
⚠ `FiaA1:20-21` 用 `PHI_AZB` 但无驱动（无端口/无反相器）→ D7。
⚠ `FiaA3` 的 `VCP/VCN` 端口**零器件连接**（`:8-11` 全部栅极只接 VINP/VINN）→ D9。

### 2.13 `CincCouple`（L2，`CincCouple.scs:7`）
```
 1 VINP  2 VINN  3 VOUTP  4 VOUTN  5 VCM
 6 D2<10:0>  7 PHI_RA  8 PHI_RST
 9 VDD18  10 GND
```
10 token / 20 位。`Cip/Cin` **1.0 pF 理想电容**（`:9-10`，非 `unitcap`；1.0 p/27 f = **37.037 单位**，版图需取 37 单位 = 999 f），`tg18` 复位 ×2，`Dac2Replica` ×1（`:17`），`Crep/Cren` 1.0 pF（`:18-19`）。详见 §3.1-T02b。
⚠ spec 端口 `VREPP/VREPN/D2<11:0>` + 无 `PHI_RA/PHI_RST` → 网表用 `VCM` 顶掉 `VREPP/VREPN`，**replica 的参考因此被钉在 VCM**（`:17` 接 `VCM VCM VCM`）→ 见 D4/D5。
⚠ spec 的 C_INC 初值是 **864 f**（`CincCouple/spec.md:22`），网表是 **1000 f**，差 **+15.7%** → 见 X22/§3.1-T02b。

### 2.14 `Dac2_11b` / `Dac2Replica`（`Dac2_11b.scs:7` / `Dac2Replica.scs:6`）
```
 1 DIN<10:0>  2 VREFP  3 VREFN  4 VCM  5 VTOP  6 VDD18  7 GND
```
7 token / 17 位（两者同构）。主阵（VTOP 侧）= 432+216+108+54+27+27(dum) = **864 f = 32 C_u**；子阵（SUB 侧）= 864+432+216+108+54+27+27(dum) = **1728 f = 64 C_u**；桥 `Cbr = 28 f`（`:35`）。`Dac2Replica` 只含 `Xcore → Dac2_11b`（`:7`）。
⚠ 桥容 28 f 对 11 bit **只偏 +2.1%（安全侧），不是错 2×**；布局建议的 55.7 f 会让 DAC2 掉到 10 bit → 见 §3.1-T02a（含手算表）。
⚠ 目录名 `Dac2_11b` 而 `blocks/Dac2_11b/spec.md:1` 标题是 **`Dac2_12b`**、端口 `DIN<11:0>`、"12 bit" → 网表对（`ARCH_V2.md:40`），spec 是旧稿。
⚠ **`Dac2_11b` 无 `RST` 端口**，但 12 个复位 TG（`:55-65`）的栅极接 `RST/RSTB` → **悬空**，见 D3。

### 2.15 `RaMux`（L1，legacy，`RaMux.scs:6`）
```
 1 VINA_P  2 VINA_N  3 VINB_P  4 VINB_N  5 PHI_SEL  6 VOUTP  7 VOUTN  8 VDD18  9 GND
```
9/9，与 spec **完全一致**。⚠ `PHI_SELB`（`:9,11,14,16`）无驱动，注释 `:18` 说"由数字域给"，但**端口表里没有** → legacy 块，不修。
⚠ 域：spec 标 `1.8V`，但它是 `VTOPP` 顶板（0–5 V）的选择开关 → 实际是混合域，且用 `pch18/nch18` 过 5 V 信号**耐压不足**（这也是它被淘汰的物理原因之一，`ARCH_V2.md:169`）。

### 2.16 `RefBuffer`（L1，`RefBuffer.scs:6`）
```
 1 VREF_IN  2 VREFP  3 VREFN  4 VCM  5 VDD5  6 GND
```
6/6。⚠ spec 有 10 个端口：**网表缺 `VREFP2`/`VREFN2`（1.8 V 副参考）和 `EN`**。而 `Sar2Ct.scs:39` 的 `VREFP2` 是从顶层 `VREF2` 直接给的、`VREFN2` 接 `VREFN`（5 V 参考！）→ 1.8 V 二级用的是 5 V 参考脚，见 D11。

### 2.17 `DynRefBuf`（L1，`DynRefBuf.scs:6`）
```
 1 REF_IN  2 VREFP_PRE  3 VREFP_OUT  4 VREFN_OUT  5 PRE  6 VDD5  7 GND
```
7/7。⚠ spec 端口是 `REF_IN VREFP_PRE SEL EN VREFP_OUT VREFN_OUT VDD5 GND`（8 个）→ 网表**合并 `SEL`/`EN` 成单 `PRE`，且顺序不同**。`PREB`（`:12`）无驱动 → D6。

### 2.18 `BiasGen`（L1，`BiasGen.scs:6`）
```
 1 IREF  2 EN  3 VBP1  4 VBP2  5 VBN1  6 VBN2  7 VCM_OUT  8 VDD18  9 GND
```
9/9，与 spec **完全一致**。⚠ 但电路不成立：`VBP1` 没有灌流路径、`VCM_OUT` = 100k/100k 分压 = VDD18/2 = **0.9 V 而非 2.5 V**、`Men` 不控任何支路 → D10。

### 2.19 `Dac1_11b`（L2，legacy）
**无网表。** `blocks/Dac1_11b/netlist/` 为空目录。不能给出端口契约——**只能给 spec 的 14 个端口，标注"未实现"**：
`VINP VINN VREFP VREFN VCM VGND D1<10:0> PHI_S PHI_C1 VTOPP VTOPN VDD5 VDD18 GND`（`Dac1_11b/spec.md:11-24`）。
⚠ `MANIFEST.md:34` 写"兼容旧名的包装层，内部=Pool18" → 与"空目录"矛盾；状态应为 **SPEC**，不是 NL。

---

## 3. 冲突表（网表 vs blocks/*/spec.md，逐条）

**裁决口径：一律以网表为准（本轮），spec.md 视为待改文档。不悄悄二选一——下表全部列出，改哪边由 team-lead 派单。**

| # | 块 | spec.md 说 | 网表实际 | 差异类型 | 后果 |
|:--|:---|:---|:---|:---|:---|
| X1 | `Sar20bTop` | `CLK` 5 MHz，`DOUT<20:0>` 21b，`MON<7:0>`，无 VREF2/IREF/VDDIO | `CLKP/CLKN` 200 MHz 差分，`DOUT<21:0>` 22b，`MON` 标量，有 VREF2/IREF/VDDIO | 改名+加宽+新增 | 台架端口对不上；`interfaces.csv` 已作废（`ARCH_V2.md:328`） |
| X2 | `Sar20bTop` | 5 MS/s（`Sar20bTop/spec.md:4,27`） | 10 MS/s（`ARCH_V2.md` 全篇 / `Sar20bTop.scs:2`） | 数值 | 采样率口径 |
| X3 | `Sar1Top` | 11 端口含 VINP/VINN/PHI_S/PHI_RA/VRESP/VRESN/VREFP/VREFN/D1_RDY | 16 端口含 COARSE/SAMN/CMPP/CMPN/DONE1、单端 VREF | 结构重写 | 一级壳边界改了：采样在 slice 内 |
| X4 | `Sar1Top` | 转换窗 90 ns（`spec.md:32`） | ΦC0 10 + ΦC1 15 + ΦRA 25 + ΦC2 40（`ARCH_V2.md:216`） | 口径 | 90 ns 是整帧，不是一级窗 |
| X5 | `Sar2Ct` | `D2<11:0>` 12b，子块 `Dac2_12b` | `D2<10:0>` 11b，`Dac2_11b` | 位宽 | 20 拍 40 ns 零余量 → 必须 11b（D-04） |
| X6 | `Sar2Ct` | "20 周期在 40 ns 内"（`spec.md:37`） | 19 拍 = 38 ns（`ARCH_V2.md:45`） | 数值 | 2 ns/拍 |
| X7 | `SdacPool18` | `PHI_ACQ<1:0> PHI_CONV<1:0> D1<10:0> SLICE_SEL<4:0>`，父=Sar1Top | `D<6:0> ACQ<17:0> CONV<17:0> EN<17:0> VTOPP/N<17:0>`，父=Sar20bTop | 完全重写 | 洗牌/DEM 没有端口承载 |
| X8 | `SdacSlice` | `DIN<13:0>` 14b，无 EN/VTOP | `D<6:0>` 7b + `EN` + `VTOPP/VTOPN` | 位宽+新增 | 池内 7b、跨片 3b unary |
| X9 | `CmpCoarse4b` | 域 = 5V | 供电仅 `VDD18`，输入 5 V | 域标错 | 电源域划分表要改 |
| X10 | `TriLevelDrv` | `SAM- PI NI VDD18`（10 端口） | `SAMN`，无 PI/NI/VDD18（8 端口） | 删除+改名 | 数字侧译码接口变了 |
| X11 | `RingAmp3` | 10 端口（无偏置） | 14 端口（+VBP VBN VCP VCN） | 新增 | spec 漏写偏置 |
| X12 | `CincCouple` | `VREPP VREPN D2<11:0>` | `VCM PHI_RA PHI_RST D2<10:0>` | 结构+位宽 | replica 参考被 VCM 顶掉 |
| X13 | `Dac2_11b` | 标题 `Dac2_12b`、`DIN<11:0>`、12 bit | `Dac2_11b`、`DIN<10:0>`、11 bit | 位宽+命名 | 目录名与 spec 标题不一致 |
| X14 | `Dac2Replica` | `DIN<11:0>` | `DIN<10:0>` | 位宽 | 同上 |
| X15 | `RefBuffer` | 10 端口（含 VREFP2/VREFN2/EN） | 6 端口 | 删除 | 1.8 V 副参考没有缓冲器 |
| X16 | `DynRefBuf` | `SEL EN`（8 端口） | 单 `PRE`（7 端口），顺序不同 | 合并+顺序 | 台架激励要按网表重写 |
| X17 | `Dac1_11b` | 14 端口 | 无网表 | 未实现 | 状态 SPEC |
| X18 | `Cmp2` | 判决 <1 ns | 2.36 ns/bit（`MANIFEST.md:41`），与 19 拍 38 ns 冲突（`ARCH_V2.md:45` D-09） | 数值互斥 | **全芯片最紧的一段**，未仿 |
| X19 | 全局 | 端口顺序"电源/地在最后"（`MANIFEST.md:14`） | `Sar1Top` 把 `VTOPP/VTOPN` 放第 1，`Sar20bTop` 把 `DOUT` 夹在电源前 | 顺序 | 网表内部一致（都是电源/地最后）✓，只是与"信号顺序"约定无关 |
| X20 | `Sar1Top` / `SdacSlice` | "三电平(VREF/VCM/VGND)"（`Sar1Top/spec.md:32`） | 每位只有 VREFP/VREFN 两路；`TriLevelDrv` 输出悬空 | 功能缺失 | DAC1 实际两电平 → 面积/线性度/`TriLevelDrv` 全要重估（D18） |
| X21 | `Dac2_11b` 桥容 | **未定值**（`Dac2_11b/spec.md:20` 只写 "C_unit 待定"；`MANIFEST.md:89` "未定值"；`netlist/README.md:40` "28 fF 初值"） | **28 fF**（`Dac2_11b.scs:35`） | 未定 vs 已填 | 见 §3.1-T02a：28 f 对 11 bit 只偏 +2.1%，**不是 2× 错** |
| X22 | `CincCouple` C_INC | **864 fF**（"建议先按 32×27fF=864fF 试"，`CincCouple/spec.md:22`） | **1.0 pF** 理想（`CincCouple.scs:9-10`），非 `unitcap` 整数倍 | 数值三方不一 | 见 §3.1-T02b：spec 864 / 网表 1000 / 布局 999 / ARCH 1000 |
| X23 | 级间增益 `G` | `ARCH_V2.md:18` **G = 32**（RA 电压增益） | 网表**无任何元件定义 G**；电容比 8×3456 f/999 f = **27.68**，只在无源共享假设下才等于 G | 定义冲突 | 见 §3.1-T02b：两者不是同一量，不可互换 |

---

## 3.1 数值核对（team-lead 追加项 T02-a / T02-b）

> 两条都来自 `analog/LAYOUT_PLAN.md:180-209`。**我不改网表**，只做"网表实际值 / spec 值 / 差异 / 影响"四列核对，并把算术全部写出来供复核。
> 复核用脚本（纯算术，无仿真）：电荷守恒解，未做任何器件级假设。

### T02-a `Dac2_11b` 桥接电容 `Cbr`：**网表 28 fF，不是"错 2×"，而是偏 +2.1%**

| 列 | 内容 |
|:---|:---|
| **网表实际值** | `Cbr (VTOP SUB) capacitor c=28f` —— **28 fF**（`Dac2_11b.scs:35`，注释 `:3` "桥容 28 fF 为初值，L1 必须按 INL 台阶重解"） |
| **spec.md 值** | **无值**。`Dac2_11b/spec.md:20` 只有 "C_unit 待定"；`MANIFEST.md:89` "`Dac2_11b` 的桥接电容未定值"；`netlist/README.md:40` "桥容（28 fF 初值）"；`ARCH_V2.md` 不提桥容 |
| **差异** | 网表 **28 fF** ｜ 布局 `LAYOUT_PLAN.md:194` **55.7 fF**（= 64/31 × 27）｜ 11 bit 要求的理论值 **27.43 fF**（= 1728/63）。三者最大差 **2.03×** |
| **影响** | 按 28 f 做：DAC2 增益 **+2.1%**，仍然 11 bit，曲线连续、不缺码，误差进桥接校准系数（D-05 已给"1 桥接"系数）。按 55.7 f 做：DAC2 只有 **10 bit**，位账 20.5 → 19.5，**直接掉 1 bit**。 |

**手算复核（可逐行复算）**

```
主阵（VTOP 侧，Dac2_11b.scs:19-34）
  432 + 216 + 108 + 54 + 27 (Cm0..Cm4) + 27 (Cmdum) = 864 fF = 32 C_u
子阵（SUB 侧，Dac2_11b.scs:36-54）
  864 + 432 + 216 + 108 + 54 + 27 (Cs0..Cs5) + 27 (Csdum) = 1728 fF = 64 C_u

11 bit 的充要条件：64 个子 LSB 恰好铺满 1 个主 LSB（32 单位 × 64 = 2048 码）
  → 子LSB/主LSB = 1/64   （不是 1/32；1/32 才是"1 bit 重叠 = 10 bit"）

电荷守恒（不是简单分压，主阵 864 fF 是负载）：
  令 Cm=864, Cs=1728, Cb=Cbr，单位 27 f 在 SUB 侧翻转
  分母 D = Cm·Cs + Cb·(Cm+Cs)
  子步 ΔV_sub = 27·Cb / D
  主步 ΔV_main = 27 / (Cm + Cb·Cs/(Cb+Cs))
  比值 R = ΔV_sub/ΔV_main ；总码数 = 32 / R
```

| `Cbr` | 子 LSB / 主 LSB | 子阵覆盖（主 LSB） | 总码数 | 有效位 | 判定 |
|:---:|:---:|:---:|:---:|:---:|:---|
| 27.0 f（恰好 1 C_u） | 1/65.00 | **0.985** | 2080 | 11.02* | 覆盖 <1 → **1.5% 缺口，约 30 个码不可达（这才是"断开"）** |
| **27.43 f（理论值）** | **1/64.07** | **0.999** | **2050** | **11.00** | 正好 |
| **28.0 f（网表现值）** | 1/62.71 | **1.021** | 2007 | 10.97 | 轻微重叠（+2.1%），**不缺码**，安全侧 |
| 55.7 f（布局建议） | 1/32.02 | **1.999** | 1025 | **10.00** | 重叠 1 整位 → **浪费 1 bit** |

`*` 27.0 f 一行的 "11.02" 只是"分辨率等效"（32×65=2080 格），其中 1.5% 是空档，实际可用码 ≈2020 < 2048。

**"50% 传输曲线是否断开"——要分两条，别混：**
1. **子阵内部**的 32C_u / 64C_u = **50%** 分压：这是子阵自身二进制的性质（`Cs0=864` 占 `1728` 的一半），**与 Cbr 完全无关**，28 f 下仍然是 50%，**不断开**。
2. **桥的电压传输比** `Cbr/(Cbr+S)`：理想 = 1/64 = **1.5625%**；28 f 给 **1.5947%**（+2.1%）；55.7 f 给 **3.125%**（+100%）。被改的是这一条。
3. **"断开"（缺码）的真实判据**是"子阵覆盖 < 1 主 LSB"：28 f → 1.021（重叠，不断开）；恰好 1 C_u=27 f → 0.985（**这才是会断开的那一侧**）；55.7 f → 2.0（重叠一整位）。
   → **28 f 落在"宁重叠不缺码"的安全侧**，可以不改；若要与理论值对齐，取 **27.43 f ≈ 1.016 C_u**。

> ⚠ **与 `LAYOUT_PLAN.md:191-196` 的结论相反**：他们要求"SUB 子阵 MSB 折到 VTOP 必须等于 VTOP 的 LSB"，这条要求本身对应**"1 bit 重叠"→ 10 bit**（32 单位主阵 + 64 单位子阵 → 1024 码）。而 `Dac2_11b.scs:1`（"5 bit 主阵 32 单位 + 6 bit 子阵 64 单位"）、`ARCH_V2.md:40`（D-04 冻结 11 bit）、`:56`（LSB1/LSB2 = 512 = 2^9）都要求 **11 bit**。按 32×64=2048 的单位数，正确条件必然是 α = 1/64。
> **若按布局的 55.7 f 投片，DAC2 只有 10 bit**；若按 33 finger = 55.69 f 实现，等于把上述错误固化到版图。**建议 layout 侧把 §4.3 的 33 finger 目标改为 ≈27.4 fF（16.2 个 1.6875 fF finger，或 1 C_u + 微调）**。我不改 `LAYOUT_PLAN.md`，已于同日直接告知 `layout-design-expert`。

### T02-b `C_INC`：**网表 1.0 pF 不是 CUNIT 整数倍；四份文档四个值**

| 列 | 内容 |
|:---|:---|
| **网表实际值** | `Cip (VINP VOUTP) capacitor c=1.0p`、`Cin (VINN VOUTN) c=1.0p`（`CincCouple.scs:9-10`）；replica 侧 `Crep/Cren c=1.0p`（`:18-19`）。**4 个 1.0 pF，全是理想 `capacitor`，没有一个 `unitcap` 实例** |
| **spec 值** | **864 fF**（"C_INC=待定（建议先按 32×27fF=864fF 试）"，`CincCouple/spec.md:22`） |
| **其它口径** | 布局 `LAYOUT_PLAN.md:205-206` 取 **37 单位 = 999 fF（−0.1%）**；`ARCH_V2.md:17` 写 **1 pF** 并冻结 |
| **差异** | 1000 f（网表）/ 864 f（spec）/ 999 f（布局）/ 1000 f（ARCH）。`1000/27 = 37.037`，**不是整数**；`37×27 = 999`（−0.1%）；`38×27 = 1026`（+2.6%） |
| **影响** | ①**失配/PVT**：1.0 p 用理想电容 → 与 27 fF 单位电容**没有任何工艺相关性**，`MANIFEST.md:12` 的"CUNIT 全片唯一、DAC1/DAC2/C_INC/replica 必须共用 `unitcap`"在网表层面**完全未落实**（同类问题已记为 D12，此处扩展到 4 个块：`SdacSlice`/`Dac2_11b`/`Dac2Replica`/`CincCouple`）。②**数值**：spec 的 864 f 与网表 1000 f 差 **+15.7%**，任何按 864 f 算的分压/噪声都错 16%。③**增益**：见下。 |

**关于"G 到底是 27.68 还是 32"——两者不是同一个量，不能互相替代**

| 量 | 值 | 定义 | 由什么决定 | 网表里有没有 |
|:---|:---:|:---|:---|:---:|
| RA 电压增益 | **32**（30.1 dB） | `RingAmp3` 的输出/输入电压比 | gm × 负载（`RingAmp3.scs:9-21` 三级），**与任何电容比无关** | 有（目标值，未仿） |
| 池总容 / C_INC | 27.648 p / 0.999 p = **27.68**（用 1.000 p 则 27.65） | 8 片 × 3.456 pF ÷ C_INC | 电容值 | **只在"无源电荷共享"架构里等于级间增益**；本网表 RA 是有源放大，**不存在这个增益** |
| C_INC 对 DAC2 顶板的分压 | 1.0/(1.0+0.8916) = **0.5287**（−5.5 dB） | 串联耦合电容与 DAC2 顶板电容的分压 | `CincCouple.scs:9-10` + `Dac2_11b.scs` 顶板总容 891.6 fF | **有**（这是网表里唯一成立的"电容比分压"） |

- `ARCH_V2.md:58` 写"DAC2 节点 625 mVpp = 1.25 Vpp ÷ 2（C_INC 1 pF 与 DAC2 1 pF 分压）"→ 实测顶板 **0.8916 pF**，分压应为 **0.5287**（比 0.5 高 5.7%）→ DAC2 节点实际 ≈ **0.661 Vpp**，不是 625 mVpp。
- 若把 27.68 当成 G 写进摆幅预算：39.06 mV × 27.68 = **1.081 V**，与 `ARCH_V2.md:18` 的 1.25 V 设计点冲突 14%；且 RA 是电压放大器，其输出摆幅由电源/负载决定，**不由电容比决定**。
- **建议**：`ARCH_V2.md` 把"G"拆成两个符号——`A_RA`（=32，电压增益，`RingAmp3` 的验收指标）与 `k_INC`（=0.529，C_INC↔DAC2 分压）。位账里的 39.06 mV × 32 = 1.25 V 只对 `A_RA` 成立；DAC2 侧的 LSB 必须额外乘 `k_INC`。

---

## 3.2 对 ARCH D-11 三条裁决的应答（`sar-adc-architect`，含 U1/U2/U3）

> 应答口径：**只报网表实读值与可复算的算术**；凡需要前仿才能给的，写"缺仿真"，不给猜测值。

### 3.2.1 D-11 第 1 条（G 由 C_FB 设定）——**确认缺陷，但"864 fF 是反馈还是串联"的答案是"都不是"**

| 问 | 答（网表实读） | 证据 |
|:---|:---|:---|
| 864 fF 在闭环里是反馈电容吗？ | **否。全项目没有任何 864 fF 的电容靠近 RA**。`RingAmp3.scs` 内只有级间 AC 耦合 `C1p/C1n = 1.0 pF`（`:12-13`）+ 两颗 1 GΩ 弱定义共模（`:14-15`），**没有反馈网络、没有虚拟地、没有 C_FB** | `RingAmp3.scs:7-25` |
| 是纯串联耦合吗？ | **也不是**。串联耦合的是 `CincCouple` 的 `Cip/Cin = 1.0 pF`（`CincCouple.scs:9-10`），它在 RA **之后**、DAC2 之前，与 G 无关 | `CincCouple.scs:9-10` |
| 那 864 fF 在哪？ | **只在 `Dac2_11b` 的顶板主阵**：432+216+108+54+27+27dum = 864 fF = 32 C_u（`Dac2_11b.scs:19-34`）。它与 RA 之间隔着 `CincCouple` 的 1 pF（网表）/ 864 fF（D-11 后） | 同左 |
| RA 现在是开环还是闭环？ | **完全开环**：三级级联（`FiaA1→AmpA2→FiaA3`，`:9,18,21`），无 β 网络；`EN` 的断电开关是无效器件（D8） | `RingAmp3.scs:9-24` |

**结论**：D-11 的"G = C_DAC1/C_FB = 1024/32 = 32.000"是**新拓扑要求，不是编号问题**，网表侧要新增三样东西，缺一不可：
1. `VTOP`→RA 输入之间的**虚拟地开关**（ΦRA 期间闭合；`SliceMux` 的 `VOUTP/VOUTN` 现在直连 `RingAmp3` 输入，`Sar20bTop.scs:36`）；
2. **C_FB = 864 fF × 2**（P/N 各一，32 单位）跨接在 RA 输入与输出之间；
3. ΦRA 期间 **8 片 slice 的底板电压保持**（`SdacSlice.scs` 目前只有 ACQ/CONV 两个相，没有"保持"相）。

**一个必须先解决的接口冲突**：闭环后 `VTOP` 在 ΦRA 期间是虚拟地（≈定值），而 `CmpCoarse4b`（`Sar20bTop.scs:33`）与 `Cmp1`（`Sar1Top.scs:6`）**都直接读顶板**。二者只在 ΦC0/ΦC1 工作、ΦRA 期间不需要顶板，所以**时序上可以共存**，但必须在契约里写死："ΦRA 期间 CMP1/CmpCoarse4b 的 `CLK` 保持低"，否则闭环会把判决节点钳死。→ 记入 Q9。

### 3.2.2 D-11 第 2 条（C_INC 1.0 pF → 864 fF）——**接受，但"严格 ÷2"不成立，实际 0.492**

| 列 | 内容 |
|:---|:---|
| 网表现值 | **1.0 pF**（`CincCouple.scs:9-10`）+ replica 侧 **1.0 pF**（`:18-19`），全理想电容、无 `unitcap` 实例 |
| 裁决值 | **864 fF = 32 C_u**（`ARCH_V2.md:20,298`；`CincCouple/spec.md:22` 恰好也建议 864 fF） |
| 我的确认 | ✅ 接受。理由与 D-11 一致：1000/27 = 37.037 非整数；864 = 32 整数单位；spec 与 ARCH 至此统一 |
| **一处需更正** | D-11 写"C_INC/(C_INC+C_DAC2) = **0.500**，DAC2 节点 625 mVpp"。**C_DAC2 顶板不是 864 fF，而是 864 + 桥的串联等效**：<br>·Cbr=55.7 → 串联 53.96 → 顶板 **918.0 fF** → 分压 **0.4848** → 节点 **606 mVpp**<br>·Cbr=27.4 → 串联 26.97 → 顶板 **891.0 fF** → 分压 **0.4923** → 节点 **615 mVpp**<br>→ 无论哪种桥容都到不了 0.500，"严格 ÷2 / 625 mV"高估 **1.6–3.0%**。LSB2 = 305 µV 也随之偏 1.6–3%（可被 D2 权重系数吸收，但不能写成"严格"） |
| 另一处 | `ARCH_V2.md:300` 说"全片只有两种电容值（1024 / 32 单位）"——**实际是四种**：DAC1 1024 u、DAC2 子阵 **64 u**、C_FB/C_INC/DAC2 主阵 32 u、桥 **非整数**（55.7 f = 2.06 u 或 27.4 f = 1.02 u）。桥无论取哪个值都不是整数单位，只能 finger 级拼 → "unitcap 全片唯一"对桥**天然不适用** |

### 3.2.3 D-11 第 3 条（桥容 28 → 55.7 fF）——**不同意：55.7 才是把 LSB2 翻倍到 610 µV 的那个值**

**先给结论**：网表 **28 fF** 对 11 bit 只偏 **+2.1%**；**55.7 fF 才会让 DAC2 退到 10 bit、LSB2 翻倍到 610 µV、位账退到 19.5**。D-11 把因果记反了。

**推导（3 行）**
```
6+5 分段要得到 2048 码，子阵必须"铺满 1 个主 LSB"（不是"MSB 等于 1 个主 LSB"）：
  32 主单位 × 64 子码 = 2048 ✓
  ⇒ 子LSB/主LSB = 1/64  ⇒ 子阵 MSB = 0.5 主 LSB
  故  (32C_u)·C_b/(64C_u+C_b) = 0.5·C_u  ⇒  63·C_b = 32·C_u  ⇒  C_b = 27.43 fF
D-11 写的是 "= 1·C_u"（把 0.5 写成 1）⇒ C_b 翻倍 55.7 fF ⇒ 子阵步长翻倍
```

**数值表（电荷守恒，含主阵 864 fF 负载；`Cb/(Cb+Cs)` 的简单分压不适用）**

| `Cbr` | 子LSB/主LSB | 子阵覆盖 | 有效位 | 子 LSB 折算到 DAC2 节点 | 判定 |
|:---:|:---:|:---:|:---:|:---:|:---|
| 27.0 f（1 C_u） | 1/65.00 | 0.985 | 11.02* | 296 µV | 1.5% 缺口（约 30 码不可达） |
| **27.43 f（=1728/63）** | **1/64.07** | **0.999** | **11.00** | **305 µV** ✓ | 正好 |
| **28.0 f（网表现值）** | 1/62.71 | **1.021** | 10.97 | **311 µV（+2.1%）** | **安全侧：重叠，不缺码** |
| **55.7 f（D-11 建议）** | 1/32.02 | **1.999** | **10.00** | **610 µV（×2）** | **= D-11 自己写的失效模式** |

`*` 27.0 f 行的"11.02"只是分辨率等效格数（32×65=2080），其中 1.5% 是空档。

**"中点是 50% 还是断开"——分三条，别混**
1. **子阵内部** 864/1728 = **50%**：子阵自身的二进制分压，**与 Cbr 无关**，任何 Cbr 下都是 50%，断不开。
2. **桥的传输比** `Cbr/(Cbr+S)`：理想 **1.5625%**（=1/64）；28 f → **1.5947%**（+2.1%）；55.7 f → **3.125%**（+100%）。被改的是这一条，不是"中点"。
3. **"断开"（缺码）的唯一判据**是"子阵覆盖 < 1 个主 LSB"：28 f 覆盖 1.021 → **不断**；恰好 1 C_u=27 f 覆盖 0.985 → **才断**（缺 1.5%）。

**为什么两个人都算成 2×**：`(32C_u)·C_b/(64C_u+C_b)` 恒等式右边应当是 **0.5 C_u**（子阵 MSB = 半个主 LSB），写成 `1·C_u` 就得到 2 倍。同理"折算权重 0.502 → 只覆盖半个 LSB"是把**子阵 MSB 的比例**当成了**子阵总覆盖**；总覆盖 = 2 × 0.502 × 63/64 ≈ **1.02 个 LSB**。

**唯一需要我认的**：28 f 与理想 27.43 f 差 **+2.1%**，会让 DAC2 增益偏大 2.1%（D-05 的"1 个桥接系数"正好吸收它）。若要精确，取 **27.43 f**（比 1 C_u 多 1.6%），不要取 55.7 f。

**请仲裁的唯一问题**：DAC2 的 11 bit 是"**5+6 无重叠**"（→ Cbr ≈ 27.4 f）还是"**5+6 带 1 bit 重叠**"（→ Cbr = 55.7 f，实际 10 bit）？`Dac2_11b.scs:1` 写"5 bit 主阵（32 单位）+ 桥 + 6 bit 子阵（64 单位）"，32×64 = 2048 = 2^11，指向**无重叠**；`ARCH_V2.md:69` 说"LSB2 = 305 µV 不变"，也只有在 Cbr=27.4 时成立。

### 3.2.4 U1 / U2 / U3 —— **三条都需要前仿，当前给不出数；只报"文档矛盾"与"最小实验"**

| # | 问题 | 能不能答 | 网表/文档现状 | 我的答复 | 要出数必须先有 |
|:--|:---|:---:|:---|:---|:---|
| **U2** | `Cmp2` 判决是 0.6 ns 还是 2.36 ns/bit？ | ❌ 无仿真 | 三个互斥值：`Cmp2/spec.md:32` "**<1 ns**"；`MANIFEST.md:41` "**2.36 ns/bit**"；`ARCH_V2.md:45` 假设 "**≤0.6 ns（未仿）**"。网表只给尺寸（`Cmp2.scs:6-12`，输入对 16 µm、尾 12 µm），**无模型就无法算** | **无法回答**。只能给最坏情形的后果：按 2.36 ns/bit → 19×2.36 = **44.8 ns > 40 ns，ΦC2 不闭合**（缺口 4.8 ns）。**计划值必须按 2.36 做预案**（M 8→6 或砍 ΦC0），直到前仿。另有独立阻塞：`Cmp2` 没有 `READY` 输出（C9），自定时方案**在接口上还不存在** | PDK（P0）+ `tran` 阶跃过驱台架 → 测 t_dec(ΔVin, CLK 沿) |
| **U3** | `Cmp1` 噪声 366 µV 是 1:1 还是 ÷G？ | ⚠ 折算口径能答，数值不能 | **口径：1:1 正确**——`Cmp1` 的输入就是顶板（`Sar1Top.scs:6` 把 `VTOPP/VTOPN` 直连 `Cmp1`），中间没有任何衰减；"÷G = 11.4 µV"只有在比较器接在 RA 输出（即 `Cmp2`）时才成立。**数值：366 µV 是网表注释里的占位值**（`Cmp1.scs:9` "w/l 待 L1 按噪声 366 µV@顶板 调"），**从未仿真** | **两个数不可能同时成立**：若 366 µV 真是输入折算值，它就是整机 26.5 µV 的 **13.8 倍**，20.5 bit 直接不成立；同时 366 µV = 0.0375 LSB1，对"判决 0.5 LSB1"够用，说明它更像**单次判决的比较器总噪声**而不是"输入等效噪声预算项"。→ 在 pnoise 出来前，**不要把 366 µV 写进噪声表**，标 `【未验证】` | PDK + `pnoise`（采样保持态，BW 按 1/(2·t_dec)） |
| **U1** | τ_RA（闭环噪声带宽） | ❌ **当前拓扑下这个量不存在** | RA 是开环三级（`RingAmp3.scs:9-21`），共模靠 1 GΩ 弱定义（`:14-15`），`EN` 开关是无效器件（D8）。**开环没有"闭环噪声带宽"，τ_RA 无从定义** | **问题前提要先改**：D-11 第 1 条把 RA 改成闭环后，τ 才存在，且由 C_FB 与环路 β·gm 决定。**建议顺序：先落 C_FB 拓扑 → 再跑 `tran noise`/`pnoise` 取 τ → 最后定 ρ**。现在直接问 τ_RA 会得到一个测不出来的数 | D-11 拓扑落地（C_FB+虚拟地+保持相）+ PDK |

> 一句话给 ARCH：**U2 是最急，但它和 U1/U3 一样卡在同一个前置条件——PDK P0 的 4 条映射**（`PDK_FILL.md` §2）。在 `pdk_models.scs` 落地前，这三条的任何数字都只能是文献借用，不能进预算。

### 3.2.5 参考 buffer（300 pF 不拆分）——**接受，且网表本来就符合**

| 项 | 裁决 | 网表现状 | 差什么 |
|:---|:---|:---|:---|
| 去耦 | lumped 200–300 pF 贴总线 + 每片 3–6 pF 旁路 | `Cdec = 300 pF` 单点（`DynRefBuf.scs:8`）+ `Cdec2 = 60 pF`（`:9`）→ **与裁决一致，是 lumped**；"每片 3~6 pF 旁路"**没有**（`SdacSlice.scs` 无旁路电容） | 补 18 处 3–6 pF 旁路（改网表，本轮不做） |
| 等阻支路 | 18 条支路等阻 ±5% | 只有一颗 `Rd = 20 Ω`（`DynRefBuf.scs:15`）串在 `REF_IN→VREFP_OUT`，**没有 18 条支路**，也没有星点 | 需新增 star + 18×R_buf 拓扑 |
| 判据 | 粗位 ≤8 LSB1 / 细位 ≤0.5 LSB1 | 旧判据"≤0.5 mV"只在 `routing_plan.md` | 采纳新判据（属验证组） |
| 阻塞 | — | `PREB` 无驱动（D6）、`VREFN_OUT` 无直流通路（D19） | 先修这两个，buffer 才跑得起来 |

---

## 4. 裁决（C1–C9）

### C1 — 粗量化：**`CmpCoarse4b`，15 个比较器。`CmpCoarse6b` / 63 cmp 作废。**
- 实现证据：`CmpCoarse4b.scs:30-44` 恰好 15 个 `Xc0..Xc14 → Cmp1`；`:12` 输出 `D<14:0>` = 15 位温度计；`Sar20bTop.scs:33` 实例化它（不是 6b）。
- 架构证据：`ARCH_V2.md:44`（D-08，"15 = 2^4−1，**确认（且 ΦC0 依赖它）**"）；`ARCH_V2.md:332`（"`MANIFEST.md` §2 … `CmpCoarse6b(63)` 作废"）。
- 决策记录：`plan/coarse_quant_decision.md:3`（"63 个比较器降到 15 个，面积 0.086→0.028"）、`:44`（"`CmpCoarse6b` 改成 `CmpCoarse4b`（15 cmp）"）。
- 面积侧一致：`analog/area_model.md:34` 按"15/63 × 0.086"计。
- **结论**：`CmpCoarse6b` 目录不存在、网表不存在、从未实例化。15 cmp 是唯一实现，也是唯一闭合 ΦC0 的方案（flash 3.0 + 2×2.36 = 7.7 ns ≤ 10 ns）。
- **待同步的旧文档（不在我权限内，需派单）**：`MANIFEST.md:54,86`、`netlist/README.md:39`、`analog/REUSE_MAP.md:17`、`plan/phase2_digital.md:152,169`（数字侧仍按 `TH[62:0]`）、`plan/phase2_layout.md:402`（"63×10 fF = 0.63 pF"）。**数字侧 63 版接口是活的上游风险**，见 §7-Q1。

### C2 — `RaMux`：**legacy，不实例化。**
`Sar20bTop.scs` 只实例化 `SliceMux`（`:28`），28 个 .scs 里 `RaMux` 的 X 实例 **0 次**（仅 `build.scs:17` include）。`ARCH_V2.md:169`"不实例化（保留目录，标注 legacy）：`RaMux`（部分交织后不需要）"。`MANIFEST.md:26` 也写"旧方案遗留，部分交织不用"。
→ 保留文件，`build.scs` 可继续 include（不影响编译），但**不能作为在用的相选网络**。

### C3 — `CmpQ2`：**legacy，不实例化。**
X 实例 0 次（`CmpQ2.scs` 之外无任何引用）。`ARCH_V2.md:169`"`CmpQ2`（第二量化器，时序未定）"；`MANIFEST.md:42`"暂不实例化"。

### C4 — `Dac1_11b`：**legacy，不实例化，且无网表（状态 SPEC）。**
`blocks/Dac1_11b/netlist/` 空；X 实例 0 次；`ARCH_V2.md:169`"`Dac1_11b`（`SdacPool18` 的旧名包装）"。
→ 但 `MANIFEST.md:34` 声称"包装层，内部=Pool18" → **与空目录矛盾**。若真要保留"包装层"语义，需要一个 1 行的 `Xcore ... SdacPool18` 网表；**本轮不建**（不属我的写入权限，且会把 legacy 变成在用）。

### C5 — 块数 = **24 个目录 / 21 在用 + 3 legacy**，`MANIFEST.md` 的 "25 块" 是笔误。
`ls analog/blocks/` = 24；`ARCH_V2.md:172`"模拟 24 个目录 = **21 个在用** + 3 个 legacy"；`MANIFEST.md:18` 标题 25 但表体只有 24 行（#1–#23 + #5b）。**21/3 的划分与 ARCH 一致，但与网表实例化状态差 1 块**：`SwSample5v` 属"在用"却在网表里挂空（C7），所以从顶层能追溯到的只有 20 块。

### C6 — 端口权威：**本轮起以网表 `subckt` 行为准**，`MANIFEST.md:3` 的原规则（"spec.md 为唯一来源、不一致即网表未完成"）**表述反了**。
现证据：23 个块里有 **17 个** 网表与 spec.md 不一致，且其中 `Sar1Top`/`SdacPool18`/`CincCouple` 是结构性重写——不可能"17 个网表全都没完成而 spec 全对"；同时 `ARCH_V2.md`（唯一权威）与网表在 D-03/D-04 这些**位宽判决**上是一致的（`D1<10:0>`、`D2<10:0>`、`COARSE<14:0>`、`DOUT<21:0>`）。
→ 建议改为："端口以网表为准；spec.md 与本表冲突时，`blocks/<B>/spec.md` 必须在本轮内改齐，否则视为过期文档"。

### C7 — `SwSample5v` 是**在用块，但网表里挂空**（结构缺口 G-NL1）。
`ARCH_V2.md:143` 明确 `SdacSlice └── SwSample5v ×18`；`ARCH_V2.md:69` 框图 `VINP/VINN ──► [SwSample5v ×18] ──► [SdacSlice ×18]`。
但 `SdacSlice.scs` 的 `sdac_half:31-33` 用 `Xa0 (VIN b0 ACQ ACQB ...)` 把 `VIN` **直接**当采样开关输入——`SdacSlice` 只把 `VINP/VINN` 当端口引进来，**没有 `SwSample5v` 实例**；`SwSample5v` 也没有 `CKS` 驱动源（顶层没有 `CKS` 网络）。
→ 二选一，必须由架构/模拟共同裁决：
  (a) `SdacSlice` 内插 `SwSample5v`（需新增 `CKS`/`PHI_S` 端口，切片端口再加 2~3 个）；
  (b) 明确"切片内 `tg5` 即采样开关，`SwSample5v` 只用于 V1 单路路径"→ 则 `SwSample5v` 也应进 legacy 名单（24→22 在用 + 4 legacy）。
**我倾向 (a)**（`ARCH_V2.md` 是三处一致的口径，且 Ron ≤20 Ω 的指标只有自举能做）。但这会改端口，不能由我单方面改网表。

### C8 — `Sar1Top` 不含采样开关、端口是顶板 `VTOPP/VTOPN` 入 —— **网表对，spec 错**。
`ARCH_V2.md:146`"`Sar1Top` [analog] 一级壳（**不含采样开关**）"；`Sar1Top.scs:5` 首两个端口就是 `VTOPP/VTOPN`。与 X3 一致。

### C9 — `Cmp1`/`Cmp2` 缺 `READY` 输出 = **本轮最硬的契约缺口**。
`ARCH_V2.md:343`（A3）："**必须给，且是 4 相握手脉冲（START↑→READY↑→START↓→READY↓）**……不给 = ΦC2 无法实现 = 二级必须降到 6–7 bit（位账 20.5 作废）"。
现状：`Cmp1.scs:6` / `Cmp2.scs:5` 都有自己的 `CLK` 输入和 `OUTP/OUTN`，**没有 `READY`**。RTL 侧 `Sar1Ctrl.sv`/`Sar2Ctrl.sv` 也没有握手（`ARCH_V2.md:44` D-08 备注："flash 与 Cmp1 的握手在 RTL 里**不存在**"）。
→ 契约需要在两侧同时加端口。**模拟侧我建议**：`Cmp1`/`Cmp2` 增加 `RDY`（开漏或推挽，1.8 V 域），由再生完成的最后一个节点取反得到；`CmpCoarse4b` 增加 `COARSE_STROBE`/`COARSE_READY`（D-08 同一条要求）。**本轮不改进网表**（不属写入权限），只在此登记为端口级 TODO。

---

## 5. 网表级缺陷清单（可复现，不是"要优化"，是"跑不了/算错"）

> 全部为**结构/连接**问题，未涉及任何器件参数；每条都可用 `grep` 复现。修复都要改网表 → 本轮**只登记不修**。

| # | 位置 | 现象 | 影响 | 严重度 |
|:--|:---|:---|:---|:---:|
| D1 | `Sar20bTop.scs:15` vs `:45` | 顶层端口是标量 `MON`，`Xdig` 接 `MON<7:0>` | 仿真器视为两个不同网络；`MON` 悬空 | 中 |
| D2 | 全 28 文件 | `SwSample5v` 的 X 实例 **0 个** | 采样网络缺一级（见 C7） | **高** |
| D3 | `Dac2_11b.scs:55-65` | 12 个 `tg18` 栅极接 `RST/RSTB`，subckt **无 `RST` 端口** | 12 个复位开关永不导通 → DAC2 无法复位 | **高** |
| D4 | `CincCouple.scs:17-19` | `Xrep` 的 `VREFP/VREFN` 全接 `VCM`；`Crep/Cren` 都从 `VREPP` 到 `VOUTP`/`VOUTN` | replica 输出无信号、注入为共模 → kickback 抵消不成立 | **高** |
| D5 | `CincCouple.scs:7` | 无 `VREPP/VREPN` 端口（spec 有） | replica 拿不到真参考 | 中 |
| D6 | `DynRefBuf.scs:12` | 用 `PREB`，无端口/无反相器 | 预充开关的 PMOS 栅悬空 → 预充靠碰运气 | **高** |
| D7 | `FiaA1.scs:20-21` | 用 `PHI_AZB`，无端口/无反相器 | AZ 开关 PMOS 栅悬空 → AZ 不工作 | **高** |
| D8 | `RingAmp3.scs:24` | `Mpd (VDD18 EN VDD18 VDD18) pch18`：源/衬/栅/漏四个端点中三个都是 `VDD18` | 不构成开关，`EN` 不断电 | 中 |
| D9 | `FiaA3.scs:8-11` | `VCP/VCN` 端口零器件连接 | 端口悬空，偏置不起作用 | 中 |
| D10 | `BiasGen.scs:8-18` | `VBP1` 无灌流路径；`VCM_OUT` = 100k/100k 分压 = 0.9 V；`Men` 不控任何支路 | 偏置/共模全错；`VCM` 给 0.9 V 会让全链偏 | **高** |
| D11 | `RefBuffer.scs:23` | `VCM` 由 PMOS 源随产生，栅在 2.5 V → `VCM ≈ 2.5 + \|Vgs\|`（约 3 V 量级，**需仿真确认**）；且缺 `VREFP2/VREFN2/EN` | `VCM` 不等于 2.5 V；`Sar2Ct.scs:39` 的 `VREFN2` 还接的是 5 V 的 `VREFN` | **高** |
| D12 | `SdacSlice.scs:20-27`、`Dac2_11b.scs:19-54`、`Dac2Replica`（全继承）、`CincCouple.scs:9-10,18-19` | 电容全部写死数值（27f…1728f、1.0p），**4 个块、0 个 `unitcap` 实例** | 违反 `MANIFEST.md:12`/`README.md:22`；失配/温漂无工艺相关性；且 1.0 pF = 37.037 单位，不能用 27 fF 整数表示 → §3.1-T02b | **高** |
| D13 | `SdacPool18.scs:15-49` | 18 片共享同一 `D<6:0>`；`Sar20bTop.scs:24` 只接 `D1<6:0>` | 跨片 unary 高 3 bit 未实现，`D1[10:7]` 丢失 | **高** |
| D14 | `Sar1Top.scs:7` | `Xdrv` 的 `OUT<10:0>` → `SEG<10:0>`，`SEG` 无消费者 | 三电平驱动输出没接到任何电容底板（DAC1 在 slice 内，靠 `D1` 走数字路径）→ 接口归属未定 | **高** |
| D15 | `tb/tb_Cmp1.scs:3-4`、`tb_SdacSlice.scs:3-4`、`tb_SwSample5v.scs:3-4` | include 路径 `../../../netlist/…`、`../../<B>/…` **实测全部 MISS**（应为 `../common_cells.scs`、`../blocks/<B>/netlist/<B>.scs`） | 三个台架当前 **0 个能跑** | **高** |
| D16 | `tb/tb_SdacSlice.scs:24` | 给 `SdacSlice` 传 **20 个节点**，端口只有 **14 个**（多了 1 个 `vdd5`、少了 `EN`，且 `VCM` 写成裸数字 `2.5`） | 该台架即使修好 include 也过不了端口检查 | **高** |
| D17 | `check_hier.py:68` | 只比较 token 数、不展开总线、不查未驱动网络 | 上面 D1/D6/D7/D9 全部"通过" → **`OK` 不能当可仿真证据** | 中 |
| D18 | `SdacSlice.scs:31-33,85-91` + `Sar1Top.scs:7` | 每位底板只有 `VREFP`/`VREFN` 两路 TG（`Xr0/Xg0…`），`VCM` 只在 `EN=0` 时经 `sw5` 接整列底板；`TriLevelDrv` 的输出 `SEG<10:0>` 无消费者 | **spec 的"三电平（VREF/VCM/VGND）"在网表里没有落点**：DAC1 实际是两电平，`TriLevelDrv` 是悬空块 | **高** |
| D19 | `DynRefBuf.scs:9` | `VREFN_OUT` 只挂一个 `Cdec2`，无任何直流通路（`Rd` 只接 `VREFP_OUT`） | `VREFN_OUT` 是浮空 DC 节点；且顶层 `Xdyn` 引出后无人使用（`Sar20bTop.scs:20` vs `:24`） | 中 |

---

## 6. 每块"跑第一个 testbench 还缺什么"

> 三列口径：**缺模型** = `pdk_models.scs` 里要有的别名（详见 `PDK_FILL.md`）；**缺激励** = 台架需要的源/码源/时钟；**缺判据** = spec 有指标但没定义怎么测（meas 语句/角点/样本数）。
> "可开工" = 修完 D-列缺陷 + 填完 P0 模型后能不能当天出第一个波形。

| 序 | 块 | 缺模型 | 缺激励 | 缺判据 | 阻塞缺陷 | 可开工 |
|:--:|:---|:---|:---|:---|:---|:---:|
| 1 | `inv18`/`inv5`/`tg5`/`tg18`/`sw5`/`diode18` | nch5 pch5 nch18 pch18 | VDD + 阶跃 | 无（单元级只验 Vth/Ron 方向） | — | ✅ 先做（模型自检） |
| 2 | `Cmp1` | nch5 nch18 pch18 | `CLK` 5 ns、`VINP/VINN` 差模扫描 | 失调 <1 LSB1、判决 <1.5 ns、噪声 <50 µV（**没有 meas，只有文字**）；缺 `RDY`（C9） | 台架 include 路径（D15） | ✅ 修 D15 后 |
| 3 | `Cmp2` | nch18 pch18 | `CLK` 2 ns、差模扫描 | 判决 <1 ns 与 2.36 ns/bit **互斥**（X18）→ 先测再定 | 台架不存在（需新建） | ✅ |
| 4 | `SwSample5v` | nch5 pch5 | `CKS`/`PHI_S` 不重叠两相、`VIN` 1 MHz 2.4 V 幅 | Ron ≤20 Ω（`Itest` 已在 `:16`，但 `I=0` 测不出 Ron）、电荷注入 <0.1 LSB1 | D15 路径 | ✅ 修 D15 后 |
| 5 | `SdacSlice` | nch5 pch5 | 7 位码源 + `PHI_ACQ`/`PHI_CONV`/`EN` | 权重误差 <0.5 LSB1、单调性（7b 扫 128 码） | D15+D16（台架节点数错）+ D12 + D18（无三电平） | ⚠ 先修台架 |
| 6 | `Dac2_11b` | nch18 pch18 | 11 位码源 + `RST`（**缺端口 D3**） | 权重误差 <0.5 LSB2；桥容 28 fF 待解（`MANIFEST.md:89`） | D3 | ⚠ 先补 RST |
| 7 | `Dac2Replica` | nch18 pch18 | 同 DAC2 码源 | 与 DAC2 失配 <1%（**怎么测没定义**：DC 对比还是瞬态？） | 无（依赖 DAC2 先修） | ⚠ 依赖 #6 |
| 8 | `CincCouple` | nch18 pch18 | `PHI_RA`/`PHI_RST` + 11 位码 | 顶板扰动 <0.5 LSB2 | D4 D5（replica 拓扑未成立） | ❌ 需先定拓扑 |
| 9 | `RingAmp3`（含 FiaA1/AmpA2/FiaA3） | nch18 pch18 | `PHI_AZ`（早关 2 ns）、`PHI_RA`、`EN`、4 pF 负载 | G=32、1.25 Vpp、Zout 300 Ω、建立 <25 ns | D7 D8 D9 | ❌ 需先修 D7/D8 |
| 10 | `CmpCoarse4b` | nch5 nch18 pch18 | 16 段梯 + 5 V 差模扫描 + `PHI_C0` | 16 个边界码不越细窗、极码无气泡、失调 ≤0.25 粗 LSB | 15 个 `Cmp1` 的失调修调**根本没画**（`ARCH_V2.md:188`） | ⚠ 可跑理想失调版 |
| 11 | `SliceMux` | nch5 pch5 | 18 路独立源 + `SEL/SELB<17:0>` | Ron ≤20 Ω、片间偏斜 ≤50 ps（**没 meas 定义**）、先断后合 | 无 | ✅ |
| 12 | `SdacPool18` | nch5 pch5 | `ACQ/CONV/EN<17:0>` 18 相时序 + 7b 码 | 两相增益失配 <1e-4 | D13（unary 未实现） | ⚠ 只能验 18 片同码 |
| 13 | `BiasGen` | nch18 pch18 | `IREF` 10 µA + `EN` | PVT 电流变化 <20%、`VCM_OUT` = 2.5 V | D10（电路不成立） | ❌ 需重画 |
| 14 | `RefBuffer` | pch5 nch5 | `VREF_IN` 5 V + 负载阶跃 | R_out ≤20 Ω、噪声 ≤2.9 µV、纹波 <2 µV | D11 | ❌ 需重画 |
| 15 | `DynRefBuf` | pch5 nch5 | `PRE`/`PREB`（D6） | 参考纹波 <2 µV、20b 建立 | D6 | ❌ 先补反相 |
| 16 | `TriLevelDrv` | nch5 pch5 | `D<10:0>`/`SAMN<10:0>` 全 3 态组合 | 建立误差 <0.1 LSB、驱动 74 µm 栅 | D14（输出没接负载） | ⚠ 可单独测 |
| 17 | `ClkRx` | nch18 pch18 | 200 MHz 差分 ±0.3 V | 抖动 ≤0.3 ps（**pnoise 台架不存在**） | 无 | ✅ |
| 18 | `Sar1Top` | 上面全部 | `COARSE` 由数字给 + 三 stub 行为 | 余差建立 0.5 LSB2、INL <2 LSB | D14 + stub 空壳 | ❌ |
| 19 | `Sar2Ct` | 上面全部 | `D2/DT` 由 stub 给 | kickback <1 LSB2、19 拍 38 ns | D3 + stub 空壳 | ❌ |
| 20 | `Sar20bTop` | 全部 + `DigitalTop` 行为模型 | **全部 PHI_\* 由 DigitalTop 驱动** | 整链 SNDR/DR | stub 空壳（`digital_stubs.scs:11` 体是空的）+ D1 | ❌ |

### 6.1 可开工顺序（按依赖，不按块号）

```
第 0 步（无块依赖，1 个台架、半天）
  PDK_FILL 自检台架 → 4 个器件 DC/DC-sweep，确认 nch5/pch5/nch18/pch18 全部解析
  判据：4 条 IV 曲线 + 打印 Vth/Von，无 "unknown model"

第 1 步（纯标准单元 + 最短路径）
  inv18 → inv5 → tg5/tg18 → sw5      （每个 1 个 tb，验 Ron/翻转点）

第 2 步（叶子，互不依赖，可并行）
  Cmp1        [修 D15]                ← 最快出"真"数字
  Cmp2        [新建 tb]
  SliceMux    [新建 tb]               ← 36 个 tg5，只需 DC + 瞬态
  SwSample5v  [修 D15]
  ClkRx       [新建 tb]

第 3 步（叶子，需先补端口/连接）
  Dac2_11b    [补 RST 端口 → D3]；桥容先冻结（28 f 或 27.43 f，见 Q5）
  BiasGen     [重画 D10]  ┐ 这两块是"改电路"不是"跑仿真"
  RefBuffer   [重画 D11]  ┘
  FiaA1/AmpA2/FiaA3 → RingAmp3  [补 PHI_AZB/EN/D9；若走 D-11 闭环则需再加 C_FB×2 + 虚拟地 + 保持相]
  TriLevelDrv [D14 接假负载]

第 4 步（组合，依赖第 2/3 步）
  CmpCoarse4b（×15 Cmp1）→ Dac2Replica（×Dac2）→ SdacSlice → SdacPool18
  判据全部来自各 spec.md 的"验收判据"，但**必须先写成 meas 语句**（见 §7-Q3）

第 5 步（壳）
  Sar1Top / Sar2Ct   ← 需 SarLogic1/2 stub 换成真行为

第 6 步（顶）
  Sar20bTop          ← 需 DigitalTop 行为模型（Verilog-A），当前 0 行
```

**顺序理由**：模型自检不过，后面全是假结论（`pdk_models.scs:19` 原话"不许为了先跑起来用理想 MOS 代替；那会把 L1 结论变成假结论"）；而"改电路"的 4 个块（BiasGen/RefBuffer/RingAmp3/CincCouple）跑通也说明不了任何指标，所以排在有判据的叶子之后。

---

## 7. 未决问题（需要 team-lead / 架构拍板，我不自作主张）

| # | 问题 | 选项 | 影响面 | 我的一票 |
|:--|:---|:---|:---|:---|
| Q1 | 数字侧仍按 **63 cmp / `TH[62:0]`** 设计（`plan/phase2_digital.md:152,169`），模拟侧只有 15 cmp（C1） | 改数字 / 改模拟 | 若数字不改，`COARSE[14:0]` 到 `D1[9:5]` 的译码不存在 → 一级不收敛 | **改数字**（模拟侧无 63 实例、无面积、无 ΦC0 余量） |
| Q2 | `SwSample5v` 挂空（C7） | (a) 插进 `SdacSlice` / (b) 划进 legacy | (a) 切片端口 +2~3、18 份实例；(b) 采样靠切片内 `tg5`，Ron 20 Ω 不可达 | **(a)** |
| Q3 | 各 spec 的"验收判据"全是文字，**没有一条 meas/角点/样本数** | 由验证组统一定义 / 每块自带 | 直接决定"跑完了算不算通过" | 应归 `verification-expert`（T05），我只给指标清单 |
| Q4 | `Cmp1`/`Cmp2` 的 `READY`、`CmpCoarse4b` 的 `COARSE_READY`（C9） | 加到端口 / 数字侧超时兜底 | A3 说"没有降级方案" | **加到端口**（3 个块各 +1~2 端口） |
| Q5 | `Dac2_11b` 桥容 28 fF 是否成立（**已升级为冲突**：`sar-adc-architect` D-11 与 `layout-design-expert` T04 **都判 55.7 f**；我复算判 27.43 f，见 §3.1-T02a / §3.2.3） | 保留 28 f / 改 27.43 f / 按 D-11 的 55.7 f | 保留 28 f → DAC2 +2.1% 增益（桥接系数吸收），11 bit 成立；改 27.43 → 精确 11.00 bit；**按 55.7 → 只有 10 bit、LSB2 = 610 µV、位账 19.5** | **保留 28 f 或改 27.43 f**。判别式：`(32C_u)·C_b/(64C_u+C_b)` 右边必须是 **0.5 C_u**（子阵 MSB = 半个主 LSB），写成 `1·C_u` 就得到 2×。→ **请 team-lead 裁决**，这是全项目唯一"两方对、一方不同"的数值分歧 |
| Q6 | `D1<10:0>` 是 10 次还是 11 次判决 | `ARCH_V2.md:16,222,252` 说 5b fine / 6 次；同文件 `:39` D-03 说删掉第 11 次、4 次 fine | 影响 `Sar1Top` 的 `COARSE<SAMN<D1` 位宽与 ΦC1 拍数 | 以 D-03 为准（有物理推导：池内无 13.5 fF 元件）→ **但 ARCH 自身未统一，必须先改 ARCH** |
| Q7 | `G` 的定义：`ARCH_V2.md:18` 写 G=32，布局按"池总容/C_INC"算成 27.68（§3.1-T02b） | 拆成 `A_RA`(32) + `k_INC`(0.529) / 或承认无源共享架构 | 决定 RA 摆幅（1.25 V vs 1.08 V）、DAC2 侧 LSB、噪声分配 | **拆符号**：`A_RA=32` 是有源增益（`RingAmp3` 验收指标），`k_INC` 单列；网表里没有任何元件实现 27.68 |
| Q8 | `C_INC` 到底取 864 f / 999 f / 1000 f | **已按 D-11 定：864 f（32 单位）**（`ARCH_V2.md:20,298`） | 级间分压由 0.5287 → 0.4848~0.4923，DAC2 节点 606–615 mV（**不是 625**） | ✅ 接受 864 f；但 D-11 的"严格 ÷2 / 625 mV"要改成 **0.485–0.492 / 606–615 mV**（桥的串联项没算进去） |
| Q9 | **D-11 要求 RA 闭环（C_FB = 864 fF）**，但网表里 RA 是开环三级、无虚拟地、无保持相（§3.2.1） | 新拓扑 / 维持开环 | 闭环后 `VTOP` 在 ΦRA 是虚拟地，而 `Cmp1`、`CmpCoarse4b` 都直读顶板 → 必须写死"ΦRA 期间 CMP 时钟不动作" | **新拓扑**，但需同时新增：虚拟地开关、C_FB×2、slice 保持相；并补一条时序契约 |
| Q10 | U1/U2/U3（Cmp2 判决时间、Cmp1 噪声口径、τ_RA）**全部卡在 PDK**（§3.2.4） | 先填 P0 / 先用文献值 | 数字侧排 19 拍、噪声预算、ρ=0.449 都悬空 | **先填 P0 的 4 条映射**（`PDK_FILL.md` §2）；在之前不要把 2.36 ns / 366 µV / τ=2.5 ns 写进任何冻结表 |

---

## 8. 证据指针（file:line）

- 块数/在用数：`spec/ARCH_V2.md:172`；`analog/MANIFEST.md:18`
- 15 cmp：`analog/blocks/CmpCoarse4b/netlist/CmpCoarse4b.scs:12,30-44`；`spec/ARCH_V2.md:44,332`；`plan/coarse_quant_decision.md:3,44`
- legacy 三名：`spec/ARCH_V2.md:169,172`；`Sar20bTop.scs:24,28,33`
- 端口权威：`analog/MANIFEST.md:3`（原规则）vs 本文 C6
- `SwSample5v` 应该在切片内：`spec/ARCH_V2.md:69,143`
- `READY` 握手必需：`spec/ARCH_V2.md:343`（A3）、`:44`（D-08）
- 位宽：`spec/ARCH_V2.md:19,274-278`（`DOUT<21:0>`/`COARSE<14:0>`/`D1<10:0>`/`D2<10:0>`）
- 数字 stub 空壳：`analog/netlist/digital_stubs.scs:4-16`
- 台架 include 断链（实测 MISS）：`analog/netlist/tb/tb_Cmp1.scs:3-4`、`tb_SdacSlice.scs:3-4`、`tb_SwSample5v.scs:3-4`
- `check_hier` 只数 token：`analog/netlist/check_hier.py:68`
- 桥容 28 fF：`analog/blocks/Dac2_11b/netlist/Dac2_11b.scs:3,35`；子阵 64 单位 `:36-54`；主阵 32 单位 `:19-34`
- D-11 三条裁决原文：`spec/ARCH_V2.md:20`（G/C_FB/C_INC）、`:68-69`（增益锚点/CT 分压）、`:292-306`（增益链表 + 桥接阻塞项）、`:363`（C_FB 功耗）、`:394`（MANIFEST unitcap 规则处置）
- RA 开环证据（无 C_FB / 无虚拟地 / 无 CMFB）：`analog/blocks/RingAmp3/netlist/RingAmp3.scs:7-25`
- 顶板直连比较器：`Sar1Top.scs:6`（`Cmp1` ← `VTOPP/VTOPN`）、`Sar20bTop.scs:33`（`CmpCoarse4b` ← `VSUM_P/VSUM_N`）
- `Cmp1` 噪声 366 µV 是占位注释：`analog/blocks/Cmp1/netlist/Cmp1.scs:9`
- `Cmp2` 判决时间三个互斥值：`Cmp2/spec.md:32`（<1 ns）/ `MANIFEST.md:41`（2.36 ns/bit）/ `ARCH_V2.md:45`（≤0.6 ns 未仿）
- 参考 buffer 现状：`DynRefBuf.scs:8-9`（300 p/60 p lumped）、`:12`（PREB 无驱动）、`:15`（单颗 20 Ω）
- 桥容对手方：`analog/LAYOUT_PLAN.md:187-200`（要求 55.7 f / 33 finger）；`MANIFEST.md:89`；`netlist/README.md:40`
- C_INC 1.0 pF：`analog/blocks/CincCouple/netlist/CincCouple.scs:9-10,18-19`；spec 864 f `CincCouple/spec.md:22`；布局 999 f `LAYOUT_PLAN.md:205-206`；`ARCH_V2.md:17`
- G=32 / DAC2 节点 ÷2：`spec/ARCH_V2.md:18,58,266`
- `unitcap` 全片唯一规则：`analog/MANIFEST.md:12`、`netlist/README.md:22`（4 个块违反：`SdacSlice:20-27`、`Dac2_11b:19-54`、`Dac2Replica`（全继承）、`CincCouple:9-10,18-19`）
