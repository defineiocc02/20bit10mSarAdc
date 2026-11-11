# 数字 RTL 说明（10 MS/s 部分交织）

> 基线：**`spec/SSOT.md`**（2026-11-11 统一口径）｜ 历史：T03（包络 + 自定时重写）
> **本目录的 RTL 未经编译、未经仿真**（本机 `iverilog`/`verilator`/`yosys` 均未安装）。
> 当前的验证状态只有静态检查，见 `LINT_REPORT.md`。

---

## 1. 模块

| 文件 | 模块 | 功能 | 端口对齐 | 状态 |
|:---|:---|:---|:---|:---|
| `DigitalTop.sv` | `DigitalTop` | 顶层：帧计数、相位包络、调度、**D1→D1_MASK mapper + 8 态 DEM**、后处理、帧打包 | `analog/netlist/digital_stubs.scs` 的 `DigitalTop_stub`（**27 端口，逐字一致**） | 骨架（2026-11-11 加 mapper） |
| `SliceSched.sv` | `SliceSched` | 18 片池：8 转换 + 8 采样 + 2 备；`base+8 mod 18` | 驱动池 `ACQ/CONV/EN` 与 `SliceMux` 的 `SEL/SELB` | 骨架（round-robin，无 stall） |
| `Sar1Ctrl.sv` | `Sar1Ctrl` | 4b flash + 2b SAR + 4b 细搜 → `D1[9:0]`；**包络 + 自定时**（6 轮） | `Sar1Top` 数字壳内（`SarLogic1_stub` 是黑盒） | **已按 SSOT 改 10 bit** |
| `Sar2Ctrl.sv` | `Sar2Ctrl` | 12b SAR + 8× 重复 → `D2[11:0]`/`DT[7:0]`；**自定时（20 轮）** | `Sar2Ct` 的 `SarLogic2_stub` 内 | **已按 SSOT 改 12 bit** |
| `Sinc2.sv` | `Sinc2` | 8 拍二阶 CoI 累加，26 bit | — | 骨架；`dt` 未使用（R-03/R-07） |
| `ReconWeights.sv` | `ReconWeights` | 位重组 + **冻结系数** → 22 bit 偏移二进制（含 −512/−2048 偏置） | — | 骨架；R-01 回绕已修 |
| `FramePack.sv` | `FramePack` | {VALID,FAULT,DATA} 24 bit 帧 + 16 深 FIFO | — | **已修 count 双写（T03）** |
| `SerLvds.sv` | `SerLvds` | 24 bit 帧 → 400 Mbit/s DDR 串行 | 输出 pad | 骨架；未例化；`tx_bit` 双驱动（R-08） |
| `tb_DigitalTop.sv` | — | 顶层自检：8× DONE2/帧、D1/D2 斜坡、CHK + KNOWN 分开计数 | — | **已重写（T03），未跑** |
| `tb_SarCtrls.sv` | — | 两个控制器的自定时/超时直测（含 2.36 ns 慢比较器注入） | — | **新增（T03），未跑** |
| `lint_static.py` | — | 5 类结构启发式静态检查（多驱动/无驱动/非主时钟/`case`/复位覆盖） | — | 可跑 |
| `check_bitmap.py` | — | 位映射与轮次账复算（纯 Python，替代仿真器的一部分职能） | — | 可跑 |

---

## 2. 时序（200 MHz，5 ns/tick；相位是**包络**，不是判决时钟）

```
cnt 0..19：100 ns 一帧
ΦC0 0–1（10 ns）   ΦC1 2–4（15 ns）   ΦRA 5–8（20 ns）
ΦC2 9–17（45 ns）   cnt 18–19：HOLD / 换相 / 后处理
cnt 19：swap（切片角色交换，DEM 状态 +1）
```

**判决不吃 tick**（ARCH_V2 D-09）：`Sar1Ctrl`/`Sar2Ctrl` 的位循环由比较器的
`cmp_ready` 事件推进（≈2.1 ns/轮），200 MHz 只负责：

| 谁 | 用 clk 做什么 |
|:---|:---|
| `Sar1Ctrl` / `Sar2Ctrl` | 包络判定、超时看门狗（≈包络落 + 2 clk）、2FF 同步、`done`/`fault`/码值锁存 |
| `DigitalTop` | 帧计数、相位包络、调度、后处理 |

> 看门狗是**时间型**的（"包络落了还没完成"），不是"数 `cmp_ready` 的沿"——
> 后者用 5 ns 采样 2.1 ns 的窄脉冲会自己误报，理由写在 `LINT_REPORT.md §2.4'`。

轮次账：

| 相位 | 轮数 | 包络 | 每轮预算 | 备注 |
|:---|:---:|:---:|:---:|:---|
| ΦC0 | 6（4 flash + 2 SAR） | 10 ns | 1.67 ns | 4 拍是 CmpCoarse4b 温度计；2 拍经 Cmp1 握手（A-IF1） |
| ΦC1 | 4（fine） | 15 ns | 3.75 ns | `d1={c4,sar2,fine[3:0]}` |
| ΦC2 | 12 + 8 = **20** | 45 ns | **2.25 ns** | Cmp2 指标 ≤2.0 ns/拍，余 0.25 ns |

数据流：`D1/D2/DT → Sinc2 → ReconWeights → FramePack → DOUT/DRDY`

---

## 3. 两个控制器的接口（T03 新增端口）

```systemverilog
Sar1Ctrl (clk, rstn, coarse[14:0], cmp, cmp_ready, phi_c0, phi_c1,
          d1[9:0], samn[9:0], cmp_start, done1, fault, obs_rnd[2:0]);
Sar2Ctrl (clk, rstn, cmp2, cmp_ready, phi_c2,
          d2[11:0], dt[7:0], cmp_start, done2, fault, obs_rnd[4:0]);
```

| 信号 | 语义（**改了，务必看这条**） |
|:---|:---|
| `cmp_ready` | 输入。比较器就绪，**脉冲式**，是位循环的事件时钟（A-IF2） |
| `cmp_start` | 输出。4 相握手请求：`START↑→READY↑→START↓→READY↓`（A-IF3） |
| `done1`/`done2` | 输出。**1 拍脉冲**（5 ns），不是电平。原实现是电平，会让下游累加器连计多拍 |
| `fault` | 输出。超时/卡死，**粘到下一帧包络上升沿**。置起时 `d1/d2` 的值无意义 |
| `obs_rnd` | 输出。当前轮次，纯观测，可悬空 |

`Sar1Ctrl`/`Sar2Ctrl` 在模拟壳内部，所以端口变化**不外泄**到 `DigitalTop` 的 27 端口。

---

## 4. 仿真与检查

```bash
cd 20b10m/digital

make check            # Python 位映射复算（本机可跑）
python3 lint_static.py    # 结构启发式检查（本机可跑）

make tools            # 确认工具链在不在
make lint             # iverilog -g2012 -Wall
make vlint            # verilator --lint-only
make sim              # tb_DigitalTop
make sim_ctrl         # tb_SarCtrls
```

**本机当前没有 iverilog/verilator/yosys，上面后 5 条只是命令模板。**

`make sim` 的预期输出（**不是已跑结果**）：`CHK-0..4` 全 PASS，`KNOWN-1` 命中若干次
—— 后者是 `ReconWeights` 22 bit 溢出（R-01）的已知问题，不是本次改动的回归。
`make sim_ctrl` 的预期输出：快相位 PASS，慢相位（2.36 ns）**应该**报 `fault`，
这是故意把 A-T1 的算术变成测试项。

---

## 5. 待接（按优先级）

1. **A-T1：ΦC2 只有 40 ns，装不下 19 轮 × 2.36 ns = 44.8 ns。** 需要架构拍板
   （ΦC2 拉长 / 重复数降 / 帧周期加长），RTL 改不出来。见 `LINT_REPORT.md §4.1`。
2. **R-07：8× 平均的语义前后不一致。** `Sar2Ctrl` 每帧给 1 个 `done2`，而 `Sinc2` 要 8 个
   `valid`；且 `Sinc2` 从不使用 `dt[7:0]`。三种自洽解见 `LINT_REPORT.md §6`，要选一个。
3. **R-01：`ReconWeights` 的 22 bit 溢出**（`d1≥512` 回绕、非单调）。要同时定 `W2` 权重
   与 `DOUT` 位宽（22/24），属 A4/E16。
4. **A-IF1..A-IF5**：5 条模拟侧接口假设待确认（`LINT_REPORT.md §5`），
   其中 A-IF2（`cmp_ready` 必须是脉冲）是自定时环正确性的前提。
5. `Sar1Ctrl` / `Sar2Ctrl` 还要替换 `SarLogic1_stub` / `SarLogic2_stub` 的空壳；
   `fault` 现在没有引脚，需要在壳层决定接到哪（或只进观测寄存器）。
6. `SliceSched` 的洗牌目前是 round-robin（`base+8`）；LFSR/DEM 洗牌在 `SliceShuffler` 里扩展。
7. `ReconWeights` 只做"系数 × 码"的冻结重构；**48 个系数由片外 LMS 训练后经 SPI 灌入**，
   片上没有自适应环路（`CALIBRATION_GAP.md §1` 的"空闭环"问题仍在）。
8. `SerLvds` 未例化；DDR 双沿是行为级，综合时换 `ODDR`；另注意 `tx_bit` 双驱动（R-08）。

---

## 6. 文档索引

| 文件 | 内容 |
|:---|:---|
| `LINT_REPORT.md` | **T03 的静态检查报告**：逐模块检查项、无法确认的风险、接口假设、未修项 |
| `CALIBRATION_GAP.md` | 校准链路缺口（校准系数通路、原始码采集通路两条腿都断） |
| `../interface/DIGITAL_ARCH.md` | L2 模块接口 + §3.1 包络+自定时决策 |
| `../spec/ARCH_V2.md` | 位账、相位表、模块树（唯一权威） |
