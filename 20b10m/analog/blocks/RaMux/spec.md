# RaMux

- 层级：L1　父：`Sar20bTop`　子：（叶子）
- 功能：两相位共享 RA 的输入开关网络

> **V2（交织）新增模块**，V1 基线不含此模块。

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `VINA_P` | in | analog | 1.8V | A 相顶板 |  |
| `VINA_N` | in | analog | 1.8V |  |  |
| `VINB_P` | in | analog | 1.8V | B 相顶板 |  |
| `VINB_N` | in | analog | 1.8V |  |  |
| `PHI_SEL` | in | digital | 1.8V |  |  |
| `VOUTP` | out | analog | 1.8V | 去 RA |  |
| `VOUTN` | out | analog | 1.8V |  |  |
| `VDD18` | pwr | power | 1.8V | 1.8 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

导通电阻 <50Ω；寄生 <5fF

## 依赖

（叶子）

## 待定 / TODO

开关电荷注入对余差的影响

## 验收判据

切换残差 <0.25 LSB2

## 文件位置（预留）

```
blocks/RaMux/
├── spec.md          本文件
├── netlist/
├── sim/
├── reports/
└── layout/
```
