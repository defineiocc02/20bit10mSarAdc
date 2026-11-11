# Dac1_11b（LEGACY）

- 层级：L2　父：`Sar1Top`　子：（叶子）
- **状态：不再使用。** V1 单路基线，已被 `SdacPool18`（18 片池）+ `SdacSlice` 取代；目录保留只为历史引用，**无网表**（`netlist/` 为空）。
- Profile：target 拓扑见 `SdacPool18` / `SdacSlice`；本块不代表当前设计。

## 目标拓扑（由 SdacSlice 实现）

| 项 | 值 | 来源 |
|:---|:---|:---|
| 每片单位数 | 128（127 个二进制 + 1 个 termination） | SSOT #15 |
| 单位电容 | 27 fF | SSOT #15 |
| 每片容量 | 3.456 pF | 128 × 27 fF |
| 活跃片数 | 8（共 18 片池） | SSOT #14 |
| 每侧总容 | 27.648 pF | SSOT #15 |
| 分段 | 3 bit unary（片间）+ 7 bit binary（片内） | SSOT #16 |
| 切换电平 | 目标三电平；当前网表两电平 | SSOT #17 / OPEN-1 |

## 端口

本块无网表，端口以 `SdacSlice` 为准（14 个：VINP/VINN/VREFP/VREFN/VCM/VGND/D<6:0>/PHI_ACQ/PHI_CONV/EN/VTOPP/VTOPN/VDD5/GND）。

## 待定 / TODO

- 三电平落点与 termination 1C 可切换（OPEN-1）。
- 底板寄生预算（每片 ≤0.5%）。

## 验收判据

总容 27.648 pF/侧；权重误差 <0.5 LSB1（前仿）；建立 20 ns 内到 0.25 LSB1。

## 文件位置

```
blocks/Dac1_11b/
├── spec.md          本文件（历史）
├── netlist/         空；历史 V1 网表未保留
├── sim/
├── reports/
└── layout/
```
