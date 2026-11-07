# SarLogic1

- 层级：L2　父：`Sar1Top`　子：（叶子）
- 功能：一级 SAR 逻辑：11 位逐次逼近 + 握手

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `CMPP` | in | digital | 1.8V |  |  |
| `CMPN` | in | digital | 1.8V |  |  |
| `VALID` | in | digital | 1.8V | 启动 |  |
| `DONE` | out | digital | 1.8V | 完成 |  |
| `Q<10:0>` | out | digital | 1.8V |  |  |
| `P<10:0>` | out | digital | 1.8V | 开关驱动 |  |
| `N<10:0>` | out | digital | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

半同步：全局 90ns 窗口 + 局部自定时

## 依赖

（无子模块）

## 待定 / TODO

异步 or 半同步的最终选择（倾向半同步）

## 验收判据

11 拍在 PHI_C1 窗内完成；无死锁

## 文件位置（预留）

```
blocks/SarLogic1/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
