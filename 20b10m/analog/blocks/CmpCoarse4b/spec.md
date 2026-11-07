# CmpCoarse4b

- 层级：L1　父：`Sar20bTop`　子：`Cmp1` ×15
- 功能：4 bit 粗量化（16 段梯 + 15 比较器），再经 2 步 SAR 细化到 6 bit

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 |
|:---|:---|:---|:---|:---|
| `VINP/VINN` | in | analog | 5V | 转换总线（8 片求和顶板） |
| `VREFP/VREFN` | in | analog | 5V | 5 V / 0 V |
| `PHI_C0` | in | digital | 1.8V | 粗量化窗口 |
| `D<14:0>` | out | digital | 1.8V | 15 位温度计 |
| `VDD18/GND` | pwr | power | 1.8V | — |

## 关键参数

15 cmp；2.0 ns；±0.5 LSB4 = ±8 LSB1；每 cmp 5 bit 失调修调。

## 验收判据

- 16 个边界码不越细窗（±16 LSB1）；
- 极码（0111…/1000…）不出现气泡；
- 比较器失调修调后 ≤0.25 粗 LSB。
