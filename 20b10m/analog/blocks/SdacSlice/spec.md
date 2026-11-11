# SdacSlice

- 层级：L2　父：`SdacPool18`　子：（叶子）
- 功能：DAC1 的单片：128 × 27 fF = 3.456 pF，片内 7 bit 二进制；差分（P/N 两个 `sdac_half`）。
- Profile: target（结构）；切换电平 as-wired 两电平，target 三电平。

## 端口（与网表 `SdacSlice.scs` 一致）

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` / `VINN` | in | analog | 5V | 采样期底板接 VIN |  |
| `VREFP` / `VREFN` | in | analog | 5V | 转换期高/低轨 |  |
| `VCM` | in | analog | 5V | 2.5 V | `EN=0` 时整片底板接 VCM |
| `VGND` | in | analog | 5V | 0 V | target 三电平低轨 |
| `D<6:0>` | in | digital | 1.8V | 片内 7 bit | 来自 pool 的 `D<55:0>` |
| `PHI_ACQ` | in | digital | 5V | 采样相 |  |
| `PHI_CONV` | in | digital | 5V | 转换相 |  |
| `EN` | in | digital | 1.8V | 片使能 | 0 = 备用 |
| `VTOPP` / `VTOPN` | io | analog | 5V | 顶板 |  |
| `VDD5` / `GND` | pwr | power | 5V / — |  |  |

## 关键参数

| 项 | 值 | 说明 |
|:---|:---|:---|
| 单位电容 | 27 fF | 1C..64C + 1C termination |
| 二进制电容 | 27, 54, 108, 216, 432, 864, 1728 fF | 1C..64C |
| termination | 27 fF | **当前固定接 VCM**；target 应可切换（OPEN-1） |
| 合计 | 3456 fF | 128 × 27 fF |
| 采样 | 底板采样，顶板高阻 |  |
| 转换 | as-wired：每位 VREFP/VREFN 两电平 | target：VREFP/VCM/VGND 三电平 |

## 待定 / TODO

- termination 1C 的开关（OPEN-1）。
- 底板寄生 ≤0.5%；共质心布局。
- 三电平驱动放到片内还是片外（当前 `TriLevelDrv` 在 `Sar1Top`，输出悬空）。

## 验收判据

权重误差 <0.5 LSB1；采样带宽 >10× Nyquist；片间增益失配 <1e-4。

## 文件位置

```
blocks/SdacSlice/
├── spec.md          本文件
├── netlist/         SdacSlice.scs
├── sim/
├── reports/
└── layout/
```
