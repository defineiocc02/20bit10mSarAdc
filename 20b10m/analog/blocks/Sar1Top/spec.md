# Sar1Top

- 层级：L1　父：`Sar20bTop`　子：`Cmp1`、`SarLogic1`（stub）、`TriLevelDrv`（target，当前未接）
- 功能：一级壳：比较器 + 三电平驱动 + SAR1 逻辑。**不含采样开关、不含 DAC1 阵列**（都在 `SdacPool18`）。
- Profile: target（10 bit，3 unary + 7 binary）。

## 端口（与网表 `Sar1Top.scs` 一致）

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VTOPP` | in | analog | 5V | DAC1 顶板 P | 来自 SliceMux |
| `VTOPN` | in | analog | 5V | DAC1 顶板 N |  |
| `VREF` | in | analog | 5V | 5.0 V | 三电平高轨 |
| `VCM` | in | analog | 5V | 2.5 V | 三电平中轨 |
| `VGND` | in | analog | 5V | 0 V | 三电平低轨 |
| `COARSE<14:0>` | in | digital | 1.8V | 15 比较器温度计 | 4 bit flash |
| `PHI_C0` | in | digital | 5V | 10 ns | 6 次判决 |
| `PHI_C1` | in | digital | 5V | 15 ns | 4 次判决 |
| `D1M<55:0>` | in | digital | 1.8V | 8 片 × 7 bit | 逐片底板码 |
| `CMPP` / `CMPN` | out | digital | 1.8V | 高有效 | 判决 |
| `DONE1` | out | digital | 1.8V |  | 一级完成 |
| `VDD5` / `VDD18` / `GND` | pwr | power | 5V / 1.8V / — |  |  |

## 关键参数

| 项 | 值 | 来源 |
|:---|:---|:---|
| 一级判决 | 10（4 flash + 2 SAR + 4 fine） | SSOT #2 |
| 电容分段 | 3 unary + 7 binary | SSOT #16 |
| 每侧总容 | 27.648 pF | SSOT #15 |
| 转换窗 | ΦC0 10 + ΦC1 15 ns | SSOT #12 |
| 切换 | 目标三电平；as-wired 两电平 | SSOT #17 |

## 待定 / TODO

- 三电平在 MSB 的分配（OPEN-1）。
- `TriLevelDrv` 当前输出 `SEG` 悬空；target 应下沉到 `SdacSlice` 的每位底板。

## 验收判据

余差在 ΦRA 结束前建立到 0.5 LSB2；INL <2 LSB（前仿）。

## 文件位置

```
blocks/Sar1Top/
├── spec.md          本文件
├── netlist/         Sar1Top.scs
├── sim/
├── reports/
└── layout/
```
