# CoarseAdc6b

- 层级：L2　父：`Sar1Top`　子：（叶子）
- 功能：6b 粗量化：预解析 D1[10:5]

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINP` | in | analog | 5V |  |  |
| `VINN` | in | analog | 5V |  |  |
| `VREFP` | in | analog | 5V |  |  |
| `VREFN` | in | analog | 5V |  |  |
| `VCM` | in | analog | 5V |  |  |
| `PHI_C0` | in | digital | 5V |  |  |
| `D1_MSB<10:5>` | out | digital | 1.8V | 6 bit |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

结构待定：flash（63 比较器）或 6 拍 SAR

## 依赖

（无子模块）

## 待定 / TODO

论文未说明结构；先按 6 拍 SAR 做，面积不够再改 flash

## 验收判据

PHI_C0 内出 6 bit，DNL<0.5 LSB

## 文件位置（预留）

```
blocks/CoarseAdc6b/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
