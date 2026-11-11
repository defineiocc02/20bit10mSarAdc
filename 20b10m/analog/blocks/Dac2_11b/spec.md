# Dac2_11b（as-wired）

- 层级：L2　父：`Sar2Ct`　子：（叶子）
- **Profile: as-wired**（11 bit，5+6 分段）。target 是 12 bit，分段未定（SSOT OPEN-2 / T-B01）。
- 功能：二级 CDAC，5 bit 主阵 + 串联桥 + 6 bit 子阵；顶板经 C_INC 接 RA，无采样开关（CT）。

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `DIN<10:0>` | in | digital | 1.8V | 11 bit（as-wired） | target 12 bit 时为 DIN<11:0> |
| `RST` | in | digital | 1.8V | 复位（高有效） | 12 个 tg18 的栅极 |
| `VREFP` | in | analog | 1.8V |  |  |
| `VREFN` | in | analog | 1.8V |  |  |
| `VCM` | in | analog | 1.8V |  |  |
| `VTOP` | io | analog | 1.8V | 顶板 | 接 Cmp2 / C_INC |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数（as-wired）

| 项 | 值 | 说明 |
|:---|:---|:---|
| 单位电容 | 27 fF | 与 DAC1 同单位 |
| 主阵 | 32 单位 = 864 fF | 5 bit（1C..16C + dummy） |
| 子阵 | 64 单位 = 1728 fF | 6 bit（1C..32C + dummy） |
| 桥 | 28 fF | β = 28/(28+1728) = 1/62.7，比 1/64 偏 +2.1%（安全侧） |
| 顶板等效 | 0.89 pF | 864 + (28 ∥ 1728) |
| LSB@节点 | 305 µV | 615 mVpp / 2^11 |
| 位宽 | 11 bit | target 12 bit 见 SSOT #23 |

> **target 12 bit 的分段（5+7 或 6+6）尚未裁定**。裁定前本块只能用于 as-wired 复现，不得用于 20 bit 预算。
> 桥容 28 fF 只在 11 bit/6+5 下成立；12 bit 的桥容随分段重算。

## 待定 / TODO

- 12 bit 分段与桥容（OPEN-2）。
- 子阵 dummy 的接法（VCM 还是 VREFN）。
- 复位时序：RST 与 PHI_RA 下降沿的关系。

## 验收判据

权重误差 <0.5 LSB2；桥接比例误差 <0.1%；复位后顶板残差 <0.5 LSB2。

## 文件位置

```
blocks/Dac2_11b/
├── spec.md          本文件
├── netlist/         Dac2_11b.scs（as-wired）
├── sim/
├── reports/
└── layout/
```
