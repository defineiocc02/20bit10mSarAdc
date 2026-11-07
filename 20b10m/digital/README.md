# 数字 RTL 说明（10 MS/s 部分交织）

## 1. 模块

| 文件 | 模块 | 功能 | 端口对齐 |
|:---|:---|:---|:---|
| `DigitalTop.sv` | `DigitalTop` | 顶层：帧计数、相位、调度、后处理、帧打包 | `analog/netlist/digital_stubs.scs` 的 `DigitalTop_stub`（26 端口，逐字一致） |
| `SliceSched.sv` | `SliceSched` | 18 片池：8 转换 + 8 采样 + 2 备；每 100 ns 换相；base+8 mod 18 | 驱动池 `ACQ/CONV/EN` 与 `SliceMux` 的 `SEL/SELB` |
| `Sar1Ctrl.sv` | `Sar1Ctrl` | 4b flash + 2b SAR + 5b 细搜 → D1[10:0] | 放在 `Sar1Top` 的数字壳内（`SarLogic1_stub` 的实体） |
| `Sar2Ctrl.sv` | `Sar2Ctrl` | 11b SAR + 8× 重复 → D2/DT | 放在 `Sar2Ct` 的 `SarLogic2_stub` 内 |
| `Sinc2.sv` | `Sinc2` | 8× 二阶 CoI 累加，26 bit | — |
| `ReconWeights.sv` | `ReconWeights` | 位重组 + **冻结系数** → 22 bit 偏移二进制；LMS 训练在片外 | — |
| `FramePack.sv` | `FramePack` | {VALID,FAULT,DATA} 24 bit 帧 + 16 深 FIFO | — |
| `SerLvds.sv` | `SerLvds` | 24 bit 帧 → 400 Mbit/s DDR 串行 | 输出 pad |
| `tb_DigitalTop.sv` | — | 烟测：200 MHz、复位、固定码 | — |

## 2. 时序（200 MHz，5 ns/tick）

```
cnt 0..19：100 ns 一帧
ΦC0 0–1（10 ns，近似 7.5）
ΦC1 2–4（15 ns）
ΦRA 5–9（25 ns）
ΦC2 10–17（40 ns，近似 37.5）
cnt 19：swap（切片角色交换）
```

- `SliceSched` 的 `base` 每次 +8 mod 18；9 次换相覆盖全部 18 片。
- `SEL` = 转换组（8 片）→ `SliceMux`；`ACQ` = 采样组（8 片）；`EN` = 16 片，2 片备用。
- `DONE2` 触发 `Sinc2`；`acc_valid` 触发 `ReconWeights`；`FramePack` 出帧。

## 3. 仿真

```bash
cd 20b10m/digital
make lint     # 需要 iverilog 或 verilator
make sim      # 跑 tb_DigitalTop
```

本机当前没有 iverilog/verilator；`make` 只作命令模板，安装后即可跑。

## 4. 待接

- `Sar1Ctrl` / `Sar2Ctrl` 目前是独立模块，需替换 `SarLogic1_stub` / `SarLogic2_stub` 的空壳。
- `SliceSched` 的洗牌目前是 round-robin（base+8）；LFSR/DEM 洗牌在 `SliceShuffler` 里扩展。
- `ReconWeights` 只做“系数 × 码”的冻结重构；**48 个系数由片外 LMS 训练后经 SPI 灌入**，片上没有自适应环路。
- `SerLvds` 的 DDR 双沿是行为级，综合时换 ODDR。
