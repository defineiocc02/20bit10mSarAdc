# 输出接口规划（10 MS/s，22 bit）

> 先例（本机论文/报告）：
> - **Bannon VLSI 2014，18 b / 5 MS/s / 0.18 µm / 10 Vpp**：明确写 “An **LVDS interface** is used to transfer the ADC result off chip”，封装 **32-lead LFCSP + exposed pad**，总芯片面积 5.74 mm²，core 功耗 30.52 mW（不含接口）。
> - **ADI ISSCC 2024 9.8，20 b / 40 MS/s / 40 nm**：18 片 sDAC 池（8 转换 + 8 采样 + 2 备），两相交织——与本项目 10 MS/s 架构同源。
> - **AD4080（ADI 20 b / 40 MSPS）**：`Single lane, DDR, serial LVDS, 800 Mbps`；49-ball **CSP_BGA 5×5 mm / 0.65 mm pitch**；片上有 **Result FIFO**、Event Detection、SPI 系数接口。
>
> 结论：**我们走单 lane DDR LVDS，400 Mbit/s（200 MHz 双沿），24 bit 帧；不选并口。**

## 1. 为什么不是并口

| 方案 | 数据脚 | 时钟/握手 | 总 pad | 问题 |
|:---|:---:|:---:|:---:|:---|
| 22 bit 并行 @10 MHz | 22 | DRDY 1 | **23** | 1 mm 级 die 一边放不下 23 个 90 µm pitch pad；地弹大 |
| 8 bit DDR 并行 @100 MHz | 8 | DCO+DRDY 2 | 10 | 可行，但 FPGA 侧要 8 根走线等长，板级复杂 |
| **单 lane LVDS DDR 400 Mbit/s** | **2** | CLK± + DRDY± | **6** | **选定**：与 Bannon/AD4080 同路线，pad 最省 |
| 双 lane LVDS DDR 200 Mbit/s | 4 | CLK± + DRDY± | 8 | 400 Mbit/s 眼图不过时的 fallback |

400 Mbit/s 下 24 bit = 60 ns，而采样周期 100 ns → **占空比 60%，余 40 ns 空闲**，接收端有充足余量。

## 2. 帧格式（24 bit，MSB first）

| 位 | 名称 | 含义 |
|:--:|:---|:---|
| 23 | `VALID` | 1 = 本帧数据有效；0 = 坏样本（TO2/超时/校准未完成） |
| 22 | `FAULT` | 1 = 该样本期间有故障（参考跌落 / RA 越限 / M≠8） |
| 21:0 | `DATA` | 22 bit 无符号偏移二进制，中心 `0x200000`，LSB=0.5 LSB_total=3.372 µV |

- **10 MS/s × 24 bit = 240 Mbit/s 有效载荷**，400 Mbit/s 链路余量 67%。
- 帧与帧之间：数据线保持最后一比特（或 0），**DRDY 上升沿标志帧首**。
- 可选 **SYNC 帧**：每 256 帧插入一帧 `0xFFFFFF`（VALID=1、FAULT=1、DATA=全 1），接收端据此做字对齐与丢帧检测；由 SPI 使能。

## 3. 时序

```
CLKOUT (200 MHz, DDR)  ──┐_┌─┐_┌─┐_┌─ ... 24 个 UI（2.5 ns/UI）
DOUT   (400 Mbit/s)    ──< D23 >< D22 > ... < D0 >── 空闲 40 ns ──
DRDY                   ──┌───────┐___________________________┌──
                         0      10 ns                       100 ns
```

| 参数 | 值 | 说明 |
|:---|:---:|:---|
| 位时钟 | 200 MHz | 与主时钟同源，÷1 |
| 数据率 | 400 Mbit/s DDR | UI = 2.5 ns |
| 帧长 | 60 ns | 24 bit |
| 帧周期 | 100 ns | 10 MS/s |
| 采样沿→帧首 | **120 ns** | 转换 90 + 后处理 20 + 对齐 10 |
| 帧首→帧尾 | 60 ns | 共 180 ns < 200 ns |
| 输出延迟 | **1.2 个样本** | FFT 脚本按此对齐；比“整 1 样本”多 20 ns |
| 驱动摆幅 | 350 mV 差分 | 电流型 3.5 mA / 100 Ω |
| 共模 | 1.2 V | LVDS 标准 |
| 上升/下降 | ≤250 ps | 400 Mbit/s 眼高 >0.5 UI |
| 确定性抖动 | ≤0.15 UI | 随机抖动 ≤0.02 UI |

## 4. 引脚（6 个）

| 引脚 | 方向 | 说明 |
|:---|:---|:---|
| `DOUTP` / `DOUTN` | 输出 | 400 Mbit/s DDR 数据 |
| `CLKOUTP` / `CLKOUTN` | 输出 | 200 MHz 随路时钟，与数据边沿对齐 |
| `DRDYP` / `DRDYN` | 输出 | 帧首脉冲，宽度 10 ns |
| `SPARE` ×2 | — | 预留第二 lane（fallback） |

> 时钟与数据**边沿对齐**（不是中心对齐）：FPGA 用 IDELAY 逐 bit 找眼心；上电用 SYNC 帧训练。若版图能提供 90° 移相，则改中心对齐，接收端更简单——列为 L1 选项。

## 5. 数字侧实现（已在 `digital/SerLvds.sv` 给出端口与骨架）

```
DigitalTop.DOUT[21:0] + VALID/FAULT
        │
   ┌────┴────┐    ┌──────────┐    ┌───────────┐
   │ FramePack│ → │ 16×24 FIFO│ → │ DDR 串行器 │ → LVDS 驱动
   └─────────┘    └──────────┘    └───────────┘
                         │
                    DRDY 生成（帧首 10 ns）
```

- **FIFO 深度 16**：吸收后处理抖动与接收端反压；溢出置 `FAULT[FIFO_OVF]`，该帧 `VALID=0`。
- **串行器**：`CLK200` 上升沿出奇数位、下降沿出偶数位（DDR）；用 `ODDR` 原语或双沿寄存器。
- **字数**：24 bit 固定，不做 bit-stuffing；接收端靠 DRDY 对齐，不靠位同步。
- **复位**：`RSTN` 后 DRDY 保持低，直到校准完成（`CAL_DONE=1`）。

## 6. SPI 与寄存器（配置/回读）

| 地址 | 名称 | 内容 |
|:---|:---|:---|
| 0x00 | `ID` | 芯片 ID / 版本 |
| 0x01 | `CFG0` | `M_CFG[1:0]`（1/2/4/8）、`TRACK_EN`、`CAAZ_EN`、`TEST_MODE[2:0]` |
| 0x02 | `CFG1` | `PP_START[1:0]`、`FIFO_TH`、`SYNC_EN`、`DOUT_EN` |
| 0x10–0x37 | `COEF[39:0]` | 40 槽 × 24 bit LMS 系数（34 有效 + 备用） |
| 0x40 | `STAT0` | `M_ACT[3:0]`、`TO2_CNT[7:0]`、`REP_MISS[7:0]`、`FAULT[3:0]` |
| 0x41 | `STAT1` | 结温、VREF 监视、校准残差 |
| 0x50 | `TESTDATA` | 测试模式下的固定码/PRBS 种子 |

- SPI 4 线（SCLK/SDI/SDO/CS），≤20 MHz；一次事务 16 bit 地址 + 24 bit 数据。
- `CAL_TRIG` 上升沿启动前台校准；校准期间 `DOUT VALID=0`。
- 所有配置在**采样沿冻结**，随样本描述符走，避免“配置半途改变码流”。

## 7. 测试模式（硅上必须能复现）

| 模式 | `TEST_MODE` | 输出 | 用途 |
|:---|:---:|:---|:---|
| 正常 | 000 | ADC 码流 | 指标测试 |
| 斜坡 | 001 | 22 bit 计数器，10 MS/s | 验证链路/字对齐，不依赖模拟 |
| 固定码 | 010 | `0x2AAAAA` / `0x155555` 交替 | 眼图/抖动/地弹 |
| 原始码 | 011 | `D1[9:0]`+`D2[11:0]` 打包 | 分离一级/二级 |
| PRBS7 | 100 | 2^7−1 伪随机 | 误码率 |
| 关断 | 111 | 全 0，`VALID=0` | 功耗/泄漏 |

## 8. 风险与 fallback

| 风险 | 判据 | 处置 |
|:---|:---|:---|
| 400 Mbit/s 眼图不过 | 眼高 <0.5 UI 或 DJ >0.2 UI | 降 200 Mbit/s 双 lane（用 2 个 SPARE pad），帧长仍 60 ns（12 bit/lane） |
| FPGA 接收端不支持 400 Mbit/s DDR | 板级实测 | 同上；或加 1:2 解串芯片 |
| 输出地弹耦合到输入 | 固定码模式下 INL 变化 >0.5 LSB_total | 增大 LVDS 驱动串联电阻、独立 VDDIO 脚、数字区远离输入 |
| 帧对齐错位 | 斜坡模式出现每 24 bit 跳变 | 用 SYNC 帧 + DRDY 双保险；接收端加 bitslip |

## 9. 与本机先例的对照

| 项 | Bannon 2014 | AD4080 | 本项目 |
|:---|:---|:---|:---|
| 分辨率/速率 | 18 b / 5 MS/s | 20 b / 40 MS/s | 20.5 b / 10 MS/s |
| 工艺 | 0.18 µm，1.8/5 V | 40 nm | 0.18 µm BCD，1.8/5 V |
| 输入 | 10 Vpp 差分 | 6 Vpp 差分 | 10 Vpp 差分 |
| 输出 | LVDS | 单 lane DDR LVDS 800 Mbit/s | **单 lane DDR LVDS 400 Mbit/s** |
| 封装 | 32-LFCSP + EP | 49-ball CSP_BGA 5×5 | **QFN-48 6×6 或 COB** |
| 参考 | 外部 5 V | 封装内 9.4 µF + 片内 buffer | 外部 5 V + 片内 buffer + 300 pF |

> 这三条先例共同说明：**20 bit 级精密 SAR 的瓶颈不在“能不能并口”，而在“参考/输入/封装寄生”；输出一律走 LVDS 串行，SPI 管配置与回读。**
