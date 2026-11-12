# SSOT —— 全项目唯一口径

> **本文件是唯一权威。** 任何文档、网表、RTL、模型写到的数，只能引用本表，不得自行复制一套。
> 基准：`spec/ARCH_DECISION_BLv3.md`（20.00 bit / 10-12-2 / 10-15-20-45）+ `behavioral/src/sar20b/config.py::NumericalContract`。
> 生效：2026-11-11　维护：任何改动先改本表 + `spec/params.yaml`，再改下游。
> 冲突处理：**本表 > 代码 > 网表 > 其他文档**。`plan/`、`review/`、`HANDOVER`、`STATE` 属历史记录，不作口径。

---

## 0. 三个 profile（先认领你在说哪一层）

| profile | 含义 | N1 有效 | N2 | 位账 | 谁在用 |
|:---|:---|:---:|:---:|:---:|:---|
| **`target`** | BL-v3 冻结目标 | 10 | 12 | 20.00 | 规格、接口、数字 RTL、版图预算 |
| **`as-wired`** | 当前网表真实接法（2026-11-08） | **7** | **11** | 18.00 | 网表、`native_as_wired` 行为复现 |
| **`candidate_u3b7`** | 最小网表修复候选 | 10 | 11 | 19.00 | 网表改动评审（未授权实施） |

**规则**：每份文档开头必须写 `Profile: target`（或 `as-wired`/`candidate_u3b7`）。不写 = 违规。
`target` 是设计目标；`as-wired` 只用于"当前网表能跑出什么"的复现；两者不许混算。

---

## 1. 电压与位账（FROZEN）

| # | 量 | 值 | 状态 | 来源 |
|:--|:---|:---|:---:|:---|
| 1 | 差分满量程 FS | **10 Vpp**（单侧 5 V，VREF 5/0，VCM 2.5） | FROZEN | BL-v3 §2.1 |
| 2 | 一级判决 N1 | **10** | FROZEN | BL-v3 A2 |
| 3 | 一级 LSB1 | **9.765625 mV** = FS/2^10 | DERIVED | — |
| 4 | 冗余 R | **2 bit**，DAC2 窗口 = 4·LSB1 = **39.0625 mVpp** | FROZEN | BL-v3 §2.1 |
| 5 | 二级判决 N2 | **12** | FROZEN | BL-v3 A1 |
| 6 | 二级 LSB2（折输入） | **9.536743164 µV** = 39.0625 mV/2^12 = FS/2^20 | DERIVED | 自洽 |
| 7 | 总码宽 N_total | **20.00 bit** = 10 + 12 − 2 | FROZEN | BL-v3 |
| 8 | 输出码 | **22 bit 无符号偏移二进制**，中心 2^21 | FROZEN | RTL |
| 9 | 传输 LSB | **2.384186 µV** = FS/2^22 = 0.25 LSB_total | DERIVED | — |

**自洽闸门**：`LSB2 == FS/2^20`，相对误差 <1e-12。`behavioral` 的 `NumericalContract.check()` 已锁死；本表与它必须逐字一致。

---

## 2. 模拟链（FROZEN）

| # | 量 | 值 | 状态 | 说明 |
|:--|:---|:---|:---:|:---|
| 10 | 采样率 | **10 MS/s**（2 相部分交织，单通道 5 MS/s 帧） | FROZEN | — |
| 11 | 帧长 | **100 ns**（20 tick × 5 ns） | FROZEN | — |
| 12 | 相位 | **ΦC0 10 / ΦC1 15 / ΦRA 20 / ΦC2 45 / guard 10 ns** | FROZEN | BL-v3 §4.1 |
| 13 | 主时钟 | **200 MHz 差分**，无 PLL | FROZEN | — |
| 14 | 切片池 | **18 片 = 8 转换 + 8 采样 + 2 备**，角色每 100 ns 交换 | FROZEN | — |
| 15 | 一级电容 | **1024 单位/侧 × 27 fF = 27.648 pF/侧**（8 片 × 128） | FROZEN | — |
| 16 | 一级分段 | **3 bit unary（片间）+ 7 bit binary（片内）**；`D1[9:7]`=unary 数 k，`D1[6:0]`=片内码 b | FROZEN | 映射见 §4 |
| 17 | 一级切换电平 | 目标 **三电平（VREFP/VCM/VGND）**；当前网表 **两电平（VREFP/VREFN）** | **OPEN-1** | 见 §7 |
| 18 | RA 增益 | **G = 32**（由 C_FB = 864 fF = 32 单位设定，8×128/32 = 32 严格整数） | FROZEN | ARCH_V2 D-11 |
| 19 | RA 输出 | **1.25 Vpp**（4 LSB1 × 32） | DERIVED | — |
| 20 | C_INC | **864 fF**（32 × 27 fF；1 pF 作废） | FROZEN | ARCH_V2 D-11 |
| 21 | CT 分压 k_INC | `C_INC/(C_INC+C_DAC2,eff)`；C_DAC2,eff ≈ 892 fF → **k ≈ 0.492** | DERIVED | ARCH_V2 §315 |
| 22 | DAC2 节点摆幅 | **615 mVpp**（1.25 V × k）；LSB@节点 = **150 µV**（12 bit） | DERIVED | — |
| 23 | DAC2 分段 | **5+7 / 6+6 未定**（C_top ≤1.8 pF，1 LSB2_DAC ≤0.5 LSB2） | **OPEN-2** | T-B01 |
| 24 | DAC2 当前网表 | **11 bit，5+6，桥 28 fF，C_top 0.89 pF** | AS-WIRED | `Dac2_11b.scs` |
| 25 | 参考 | VREF 5 V 单套 + DynRefBuf；VREF2 由 RA 输出摆幅定（1.8 V 域） | FROZEN | — |
| 26 | 功耗/面积 | core 3.73–4.03 mW / core 0.93 mm² / die 1.41 mm² | ESTIMATE | 面积模型，MIM 密度待 PDK |

---

## 3. 数字接口（FROZEN，除注明）

| # | 信号 | 宽度 | 定义 | 状态 |
|:--|:---|:---:|:---|:---:|
| 27 | `D1[9:0]` | 10 | 偏移二进制：`D1 = 128·k + b`，k=D1[9:7]，b=D1[6:0] | FROZEN |
| 28 | `D1_MASK[125:0]` | 126 | 18 片 × 7 bit 物理掩码；`bit[7i+6:7i]` = 物理片 i。数字把 8 个 lane 码散射到本次转换组，未选中片写 0 | FROZEN |
| 29 | `D2[11:0]` | 12 | 偏移二进制，MSB 取反；`D2=2048` 对应零余差 | FROZEN |
| 30 | `DT[7:0]` | 8 | 8× 重复码（零均值 0..7，SINC2 累加） | FROZEN |
| 31 | `DITHER[5:0]` | 6 | PRBS31，每样本推进 6 次；幅度/注入点见 OPEN-3 | OPEN-3 |
| 32 | `CMP1/2_CLK` | 2 | 比较器时钟，判决 ≤1.2 ns / 2 ns 一拍 | FROZEN |
| 33 | `CMP1/2_READY` | 2 | 4 相握手（START↑→READY↑→START↓→READY↓） | **OPEN-4** |
| 34 | `ELIGIBLE[17:0]` | 18 | 片内复位完成、可参与下一次采样 | FROZEN |
| 35 | `SLICE_ID[7:0][4:0]` | 40 | 8 个有序物理编号，一笔内冻结 | FROZEN |
| 36 | `FAULT[3:0]` | 4 | RA 越限 / ADC2 超窗 / 参考跌落 / 保留 | FROZEN |

**重建公式（target）**：
```
DOUT = 2^21 + ((D1 - 512) << 12) + ((D2 - 2048) << 2)   // 22 bit，1 LSB_total = 4 LSB_xfer
```
**重建公式（as-wired，禁止对外）**：
```
DOUT = 2^21 + ((D1 - 512) << 12) + ((D2 - 1024) << 3)   // 11 bit D2，仅供网表复现
```

---

## 4. D1 → D1_MASK 映射（FROZEN）

```
k = D1[9:7]            // 0..7 个 unary 片
b = D1[6:0]            // 片内 7 bit 二进制

lane 码（8 个）:
    if lane == bin_lane:  M[lane] = b          // 二进制片
    elif lane < k:        M[lane] = 7'h7F      // 满量程片（128 单位全接高轨）
    else:                 M[lane] = 7'h00      // 零片

散射：lane j -> 本次转换组第 j 片（按 SLICE_ID 有序）；其余 10 片 M=0。
```
- `bin_lane` 由 DEM 状态决定（0..7，每样本旋转一位），**名义和恒为 128k+b**。
- 要求：每片的第 128 个单位（termination，1C）在转换相必须接 **VREFN**，不能固定接 VCM；否则每片满量程只有 127/128，k 与 b 的权重都要重标定。
- **当前网表不满足**：`SdacSlice.scs` 的 `Cdum` 固定接 VCM，且 8 片共用 `D<6:0>`。属 AS-WIRED。

---

## 5. 时序（FROZEN）

| 相位 | 起止 tick（5 ns） | 时长 | 内容 |
|:---|:---|:---:|:---|
| ΦC0 | 0–1 | 10 ns | 4 bit flash（15 cmp）+ 2 bit SAR（共 6 次判决） |
| ΦC1 | 2–4 | 15 ns | 剩余 4 bit fine SAR（共 4 次判决） |
| ΦRA | 5–8 | 20 ns | RA 放大 + AZ 尾段 |
| ΦC2 | 9–17 | 45 ns | 12 bit SAR + 8× 重复（20 拍 × 2.25 ns） |
| guard | 18–19 | 10 ns | 复位 / 换相 |

**注意**：判决调度是 **4+2+4=10**，电容分段是 **3 unary+7 binary**。两者不是一回事：
flash 的 4 bit 落在「3 个 unary + 片内 64C 位」，SAR 的 6 次落在 32C..1C。

---

## 6. 状态与证据

| 层 | 状态 | 证据 |
|:---|:---|:---|
| 位账自洽 | ✅ | `NumericalContract.check()` |
| 码域（理想） | ✅ | `behavioral` smoke：INL 0.000 LSB20 |
| 失配→INL | ✅ | 0.2% → 16.4 ppm（旧模型）/ 45.3 LSB（behavioral） |
| 校准 | ⚠️ CONDITIONAL | INL 17.8±4.4 → 0.54±0.04 ppm；DNL 0.0235 → 0.00073 LSB1；out-of-sample 1.87 ppm，未达 ±1.5 |
| 模拟网表 | ⚠️ 仅结构 | `check_hier.py` 220 实例；零仿真、零 PDK |
| 数字 RTL | ⚠️ 仅结构 | 本机无 iverilog；`DigitalTop` 是骨架 |
| 版图/后仿/硅测 | ❌ | 无 |
| 技术有效性 | ✅ 已交叉验证 | K=10 seeds、95% CI；见 `model/results/crossval/` 与 `review/20261112_crossval.md` |

---

## 7. 未决项（唯一清单，其他文档不许另立）

| # | 项 | 影响 | 谁定 | 判据/截止 |
|:--|:---|:---|:---|:---|
| OPEN-1 | DAC1 三电平实现（VREFP/VCM/VGND）与 termination 1C 可切换 | 功耗、共模、INL | 模拟 | 网表 L1 前 |
| OPEN-2 | DAC2 12 bit 分段（5+7 vs 6+6）与桥容 | C_top / α / kickback | 架构 | T-B01 |
| OPEN-3 | dither 注入点与幅度（采样态 / 双端口 / Fig.19 位分裂） | 余量、INL | 双方 | 接口 v1.0 前 |
| OPEN-4 | `CMP1/2_READY` 握手 | ΦC2 能否实现 | 模拟+数字 | 接口 v1.0 前 |
| OPEN-5 | DEM 粒度（片级 8 态旋转 vs 单位级） | DNL/杂散 | 数字 | D1_MASK 前 |

---

## 8. 引用规则

1. 文档里写数，必须带 `[SSOT #n]`；不带的视为过期。
2. 网表/RTL 注释写数，必须带 `SSOT #n` 或 `AS-WIRED`。
3. 历史文档（`plan/`、`review/`、`spec/ARCH_V2.md`、`spec/bit_allocation.md`）只能作为证据引用，**不得作为设计输入**。
4. `tools/check_ssot.py` 每次提交前跑；失败即阻断。
5. **任何"效果"数字必须来自 `model/results/crossval/summary.csv`**（K=10、95% CI）；单 seed 点估计只能当示例，不能当结论。

---

## 更新记录

| 日期 | 变更 | 作者 |
|:---|:---|:---|
| 2026-11-11 | 首版：合并 BL-v3、behavioral 合同、README、接口文档，定义三个 profile 与 5 个 OPEN | — |
