# BitRecombine

- 层级：L2　父：`DigitalTop`　子：（叶子）
- 功能：位重组：D1(10b) + D2(12b) → 20.00b（10 + 12 − 2）
- Profile: target（SSOT #27–#29）

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `D1<9:0>` | in | digital | 1.8V | D1=128k+b |  |
| `D2<11:0>` | in | digital | 1.8V | D2=2048 为零余差 |  |
| `W2<15:0>` | in | digital | 1.8V | 权重（α 相关） |  |
| `DOUT<21:0>` | out | digital | 1.8V | 22 bit 偏移二进制 |  |
| `VDD18` / `GND` | pwr | power | 1.8V / — |  |  |

## 关键参数

α = 4 LSB1（±2 LSB1 冗余）；1 LSB_total = 4 传输 LSB；名义 `DOUT = 2^21 + ((D1−512)<<12) + ((D2−2048)<<2)`。

## 依赖

（无子模块）

## 待定 / TODO

冗余位合并（D2 超出 ±2 LSB1 时的饱和/回退）。

## 验收判据

无失码，INL 无台阶；D1 段边界（k 与 b 交界）连续。

## 文件位置

```
blocks/BitRecombine/
├── spec.md          本文件
├── netlist/         导出的 CDL/网表（G2 起）
├── sim/             测试台与运行记录（run_id 子目录）
├── reports/         单元/集成报告
└── layout/          GDS、DRC/LVS（G4 起）
```
