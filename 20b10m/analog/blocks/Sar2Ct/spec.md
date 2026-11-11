# Sar2Ct

- 层级：L1　父：`Sar20bTop`　子：`CincCouple`、`Dac2_11b`（as-wired）、`Dac2Replica`、`Cmp2`、`SarLogic2`（stub）
- 功能：二级 CT SAR：C_INC 交流耦合 + DAC2 + replica + 8× LSB 重复。
- Profile: target（DAC2 12 bit；as-wired 11 bit）。

## 端口（与网表 `Sar2Ct.scs` 一致）

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VRESP` / `VRESN` | in | analog | 1.8V | 来自 RA | 1.25 Vpp |
| `VREFP2` / `VREFN2` | in | analog | 1.8V | DAC2 参考 |  |
| `VCM` | in | analog | 1.8V |  |  |
| `PHI_RA` | in | digital | 1.8V | 20 ns |  |
| `PHI_C2` | in | digital | 1.8V | 45 ns | 20 拍 × 2.25 ns |
| `D2<11:0>` | out | digital | 1.8V | 12 bit | as-wired 为 11 bit |
| `DT<7:0>` | out | digital | 1.8V | 8× 重复码 | 零均值 0..7 |
| `DONE2` | out | digital | 1.8V |  |  |
| `VDD18` / `GND` | pwr | power | 1.8V / — |  |  |

## 关键参数

| 项 | 值 | 来源 |
|:---|:---|:---|
| C_INC | 864 fF（32 × 27 fF） | SSOT #20 |
| CT 分压 k_INC | 0.492 | SSOT #21 |
| DAC2 节点摆幅 | 615 mVpp | SSOT #22 |
| DAC2 LSB@节点 | 150 µV（12 bit） | SSOT #22 |
| 重复 | 8 次，20 拍内 | SSOT #30 |
| 二级窗口 | ±2 LSB1 = 39.0625 mVpp（输入折算） | SSOT #4 |

## 待定 / TODO

- DAC2 12 bit 分段（OPEN-2）。
- replica 的参考与反相注入（当前网表把 `VREFP/VREFN` 接 VCM，D4 未修）。
- `RST` 与 `PHI_RA` 下降沿的关系。

## 验收判据

kickback 残差 <1 LSB2；20 拍在 45 ns 内完成；C_INC 失配 <0.1%。

## 文件位置

```
blocks/Sar2Ct/
├── spec.md          本文件
├── netlist/         Sar2Ct.scs
├── sim/
├── reports/
└── layout/
```
