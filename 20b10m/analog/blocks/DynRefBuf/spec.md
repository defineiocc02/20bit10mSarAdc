# DynRefBuf

- 层级：L1　父：`Sar20bTop`　子：（叶子）
- 功能：动态参考缓冲：粗预充 + 进 RA 前切精确参考

> **V2（交织）新增模块**，V1 基线不含此模块。

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 | 备注 |
|:---|:---|:---|:---|:---|:---|
| `REF_IN` | in | analog | 5V | 精确参考 |  |
| `VREFP_PRE` | in | analog | 5V | 粗预充 |  |
| `SEL` | in | digital | 1.8V |  |  |
| `EN` | in | digital | 1.8V |  |  |
| `VREFP_OUT` | out | analog | 5V |  |  |
| `VREFN_OUT` | out | analog | 5V |  |  |
| `VDD5` | pwr | power | 5V | 5.0 |  |
| `GND` | pwr | power | - | 0 |  |

## 关键参数

预充期承担 RDAC 电荷；切换在 RA 前

## 依赖

（叶子）

## 待定 / TODO

切换时刻与 RA 相位的关系；残余建立 65% RA 时间

## 验收判据

参考端纹波 <2µV；20b 建立不拖累 RA

## 文件位置（预留）

```
blocks/DynRefBuf/
├── spec.md          本文件
├── netlist/
├── sim/
├── reports/
└── layout/
```
