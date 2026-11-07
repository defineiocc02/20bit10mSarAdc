# SliceMux

- 层级：L1　父：`Sar20bTop`　子：（叶子）
- 功能：18:1 顶板选通，把 8 个转换 slice 的顶板汇到 RA 输入

## 端口

| 端口 | 方向 | 类型 | 域 | 范围/说明 |
|:---|:---|:---|:---|:---|
| `VTOPP<17:0>` | in | analog | 5V | 18 片 P 侧顶板 |
| `VTOPN<17:0>` | in | analog | 5V | 18 片 N 侧顶板 |
| `SEL<17:0>` | in | digital | 5V | 8 个高有效 |
| `SELB<17:0>` | in | digital | 5V | SEL 反相 |
| `VOUTP/VOUTN` | out | analog | 5V | 到 RA 输入 |
| `VDD5/GND` | pwr | power | 5V | — |

## 关键参数

Ron ≤20 Ω/片；8 片失配 ≤5%；总线寄生 ≤0.5 pF；片间偏斜 ≤50 ps；电荷注入 <0.1 LSB1。

## 待定

8 片同时导通时的总线电容分配；dummy TG 位置。

## 验收判据

- 8 片同时导通，片间电流差 ≤5%；
- 换相注入引起的顶板跳变 ≤0.1 LSB1；
- 换相沿 <200 ps，先断后合。
