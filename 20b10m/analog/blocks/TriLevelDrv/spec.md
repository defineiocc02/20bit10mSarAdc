# TriLevelDrv

- 层级：L2　父：`Sar1Top`　子：（叶子）
- 功能：每位三电平开关驱动（VREF/VCM/VGND）

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VREF` | in | analog | 5V |  |  |
| `VCM` | in | analog | 5V |  |  |
| `VGND` | in | analog | 5V |  |  |
| `VIN` | in | analog | 5V | 采样期 |  |
| `SAM-` | in | digital | 5V | 低有效 |  |
| `PI` | in | digital | 1.8V |  |  |
| `NI` | in | digital | 1.8V |  |  |
| `OUT` | out | analog | 5V | 接电容底板 |  |
| `VDD5` | pwr | power | 5V | 5.0 |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

每位一份；驱动能力按该位电容定

## 依赖

（无子模块）

## 待定 / TODO

按位尺寸阶梯（MSB 大、LSB 小）

## 验收判据

开关导通电阻引起的建立误差 <0.1 LSB

## 文件位置（预留）

```
blocks/TriLevelDrv/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
