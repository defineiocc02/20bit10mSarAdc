# SwSample5v

- 层级：L2　父：`Sar1Top`　子：（叶子）
- 功能：5V 自举采样开关

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VIN` | in | analog | 5V |  |  |
| `VOUT` | out | analog | 5V |  |  |
| `PHI_S` | in | digital | 5V |  |  |
| `CKS` | in | digital | 5V | 自举时钟 |  |
| `VDD5` | pwr | power | 5V | 5.0 |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

C_boot≈1.7pF（参考库），RON<50Ω

## 依赖

（无子模块）

## 待定 / TODO

5V 厚栅器件；自举电容与耐压

## 验收判据

RON 线性度支撑 20 bit；电荷注入 <0.1 LSB1

## 文件位置（预留）

```
blocks/SwSample5v/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
