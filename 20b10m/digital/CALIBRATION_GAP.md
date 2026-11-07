# 校准链路缺口报告（CALIBRATION_GAP）

> 审查对象：`20b10m/digital/` 下的 RTL（实际路径是 `digital/*.sv`，**不存在 `digital/rtl/`**；
> `check_ports.py` 也不在 `digital/`，实际在 `analog/netlist/check_ports.py`）。
> 审查方式：只读 RTL + 文档 + 数值自洽性核算。**未修改任何 `.sv` 文件。**
> 审查人：数字 IC（SAR 位循环 / 校准链路）
> 机内工具状态：`iverilog` / `verilator` 均未安装（`which` 返回空），因此本文不给出任何"仿真已通过"的结论；
> 所有数值均来自代码静态核算与 Python 复算，复算命令见 §5。

---

## 一句话结论

**片上不存在任何可写入的校准系数通路，也不存在任何校准采集（原始码 + slice id）通路——两条腿都断；
`ReconWeights` 只有 2 个写死的移位常数（需求 144 项），`DigitalTop` 26 个端口里没有任何 SPI/CAL_EN/TEST_MODE/CAL_DONE，
因此"片外 LMS"目前既拿不到训练数据、也灌不进训练结果，整条校准链路在 RTL 层是空闭环。**

附带的最关键前提问题：**三份文档对 DAC1 的物理结构给出三种互不相容的假设**（详见 §2.2），
所以"要多少个系数"这件事在项目内部本身没有收敛 —— 这也是 126+18 与实际实现差 72 倍的根因。

---

## §1 现状表

| 模块 | 已实现 | 缺什么 | 证据 |
|:---|:---|:---|:---|
| `ReconWeights.sv` | 2 个**写死**的移位常数：D1 权重 `2^12`、D2 权重 `2^3`；1 个 22 bit 输出寄存器；名义中心 `0x200000` | 系数寄存器、写入口、slice id 输入、按片选择、1/√2 增益抽头、D1 位宽（11→10）、溢出钳位 | `ReconWeights.sv:14-15`（d1/d2 端口）、`:21-22`（常数）、`:24-27`（唯一触发器，无写端口） |
| `SliceSched.sv` | round-robin 轮换：`base ← (base+8) mod 18`；`conv=mask8(base)`、`acq=mask8(base+8)`；`sel/selb/en` | **有序 slice id 输出**（只有 18 bit 掩码，没有 8×5 bit 顺序）、`stall`、`ELIGIBLE`、LFSR/DEM 洗牌、`m_act` 实数统计 | `SliceSched.sv:25-32`（mask8）、`:34-37`（base）、`:39-46`（全是组合派生，`m_act=4'd8` 写死）、`:6` 自述"没有 stall/ID 冻结" |
| `DigitalTop.sv` | 20 tick 帧计数与 8 个相位、3 处子模块例化（Sched/Sinc2/Recon/FramePack） | SPI slave、系数寄存器、`CAL_EN/CAL_TRIG/CAL_DONE`、`TEST_MODE`、原始码导出、slice id 上报、`SerLvds` 例化 | `DigitalTop.sv:15-47`（26 端口，无上述任一）、`:70-96`（例化表）、`:98-100`（输出） |
| `Sinc2.sv` | 8 拍一阶累加 + 二阶差分，26 bit `acc` | **`acc` 接出去后被丢掉了**，没有进入重构 | `Sinc2.sv:31-40` 产出；`DigitalTop.sv:76-82` 声明后仅 `acc_valid` 被使用，`:85-88` 重构用的是原始 `D1/D2` |
| `FramePack.sv` | 24 bit `{valid_in,fault,din}` + 16 深 FIFO | `FAULT` 语义（全被 `1'b0` 短接）、溢出置 FAULT、`count` 双赋值 bug | `FramePack.sv:24`（拼帧 ✓）、`:30-39`（count 在同拍被 +1 −1 双写）、`DigitalTop.sv:94`（`fault(1'b0)`） |
| `SerLvds.sv` | 24 bit 帧 + DDR 行为模型骨架 | **顶层从未例化**；`DRDY` 宽 5 ns（文档要求 10 ns） | `SerLvds.sv:11` 是独立模块；`grep SerLvds DigitalTop.sv` → 无匹配；`SerLvds.sv:74` vs `interface/OUTPUT_IF_10M.md:62` |
| `Sar1Ctrl.sv` | 4b 温度计→二进制、2b SAR、5b 细搜 | **两个 `always_ff` 抢同一个 `idx`**；`d1` 11 位且 LSB 恒 0 | `Sar1Ctrl.sv:36-44` 与 `:49-61` 都驱动 `idx`；`:64` `... , 1'b0}`；`:65` |
| `Sar2Ctrl.sv` | 11b SAR + 8× 重复的**计数器骨架** | **每帧只有 8 个 ΦC2 tick，但该 FSM 需要 18 个 tick → `done2` 永不置起** | `Sar2Ctrl.sv:25-44`（10+8=18 拍）；`DigitalTop.sv:64`（`PHI_C2 = cnt∈[10,17]`，8 拍） |
| `digital_stubs.scs` | 与 RTL 26 端口逐字一致 | 同样没有任何校准/SPI/LVDS 端口 | `digital_stubs.scs:11-16`；`python3 analog/netlist/check_ports.py` 输出 `stub ports=26 sv ports=26 / OK` |

---

## §2 逐条回答

### 2.1 `ReconWeights.sv` 现在实现了什么

| 项 | 现状 | 证据 |
|:---|:---|:---|
| 系数个数 | **2 个**，且是**常量**（不是寄存器，不是参数） | `ReconWeights.sv:21-22`：`<<< 12`、`<<< 3` 字面量 |
| 位宽 | 中间量 `acc` 为 26 bit **signed**；输出 `dout` 22 bit 无符号 | `:21`（`wire signed [25:0]`）、`:17`（`[21:0]`） |
| 存储形式 | **无存储**。常数烧在组合逻辑里，综合后只是连线（零 FF、零门） | `:21-22` 全组合；`:24-27` 只有 `dout` 一个 FF |
| 写入口 | **没有**。模块端口只有 `clk/rstn/d1/d2/valid/dout` 六个 | `:11-18` |
| 名义公式 | `DOUT = 0x200000 + (d1<<12) + ((d2-1024)<<3)` | `:21-22`、`:26` |

**三条必须点名的后果（都是可静态判定的硬错，不是风格问题）：**

1. **溢出**：`dout <= 22'h200000 + acc[21:0]`（`:26`）只取了 `acc` 的低 22 位，而 `d1<<12` 在 `d1=2047` 时是
   `8 384 512 = 0x7FF000`，需要 24 位。中心 `2^21` 之上只剩 `2^21` 的余量 ⇒ **`d1 ≥ 512` 就开始回绕**。
   复算（§5 命令 3）：`d1=511 → 0x3FF000`，`d1=512 → 0x000000`，`d1=1023 → 0x1FF000`。
   **输出在 `d1=512` 处从满量程直接掉到 0，非单调。**
2. **冒烟测试恰好踩在断点上**：`tb_DigitalTop.sv:7` 把 `D1` 固定为 `512` ⇒ 按上式 `DOUT` 恒为 `0x000000`。
   也就是说这个 tb 即使跑起来也**不可能证明数据通路是通的**（它只是不会报错）。
3. **量纲与规格不符**：`spec/bit_allocation.md:52-53` 要求 `DOUT = D1·2^9.5 + (D2−2^11) ≈ D1·724 + (D2−2048)`；
   `plan/phase2_digital.md:469-472` 要求 `ACC = D1·4096 + (D2−1024)·8 + (CNT−4)`，再乘 **`0.7071`（1/√2）** 才是 DOUT。
   实现里 `D1:D2` 权重比 = `4096:8 = 512`，规格要求 `724`（比值差 `√2`），并且**整条链少了 `1/√2` 增益抽头**。
   净结果是 D1 侧被放大 `2√2 ≈ 2.83×`（`plan/phase2_digital.md:53、204` 还明确要求 D1 是 **10 位**，RTL 用的是 **11 位**）。

### 2.2 需求 126 + 18 = 144 项，与现状差多少

先把需求拆开（这是你给我的口径，与 `plan/arch_10m.md:45-49` 的物理描述一致）：

```
DAC1 = 18 片，每片 128 × 27 fF = 3.456 pF，片内 7 bit 二进制，1 个 dummy
     ⇒ 每片 7 个位权（2^0…2^6）      = 18 × 7 = 126
     ⇒ 每片 1 个段/片增益            = 18     =  18
                                        合计 = 144 项
```

| 口径 | 数字 | 证据 |
|:---|:---:|:---|
| 物理需求（你的口径） | **144** | 上面；`plan/arch_10m.md:45-46`（128×27 fF、片内 7 bit）、`:47`（8 片并联成 28 pF） |
| `plan/arch_10m.md` 预留 | **40 槽**（"约 34–38，寄存器按 40 槽预留"） | `plan/arch_10m.md:49` |
| `interface/OUTPUT_IF_10M.md` 预留 | **40 槽 × 24 bit**（`0x10–0x37`） | `OUTPUT_IF_10M.md:91` |
| `plan/phase2_digital.md` 预留 | 34 槽 × 24 bit = 816 bit；P2 前瞻写 **64 槽 × 22 bit** | `plan/phase2_digital.md:475-476`、`:702` |
| **RTL 实际** | **0 个可配置系数**（2 个常量） | `ReconWeights.sv:21-22` |

**差距**：需求 144 vs 实现 0 ⇒ **缺 144 项（100%）**；vs 文档预留 40 槽 ⇒ **仍缺 104 项（差 3.6×）**；
vs phase2 前瞻的 64 槽 ⇒ **仍缺 80 项**。

**但这里有个比数字更严重的根因，必须写在报告最前面：三份文档对 DAC1 的物理结构假设互不相容。**

| 文档 | 假设的 DAC1 结构 | 推出的系数个数 |
|:---|:---|:---:|
| `spec/bit_allocation.md:10、52` | 单一 11 bit DAC1，权重 `2^p`，无片概念 | 2（D1/D2 各一） |
| `plan/phase2_digital.md:509-520` | 单一 10 bit DAC1 = 1023 + 16 trim，MSB 拆 A/B 半组 | 27–34 |
| `plan/arch_10m.md:45-49` | **18 片 × 128 单位、高 3 bit 跨片 unary** | "34–38"，但你口径下是 **144** |
| RTL | 11 bit 的 `D1` × 常数 `2^12` | 0（不可配） |

⇒ **在结构假设统一之前，"缺多少个系数"这个问题本身没有唯一答案。** 若最终采用 `arch_10m` 的 18 片池
（你的背景约束明确说"18 个 DAC1 slice 成池"，我按这个走），则 144 是对的，且现有 40/64 槽预留都要重做。
若采用 phase2 的单一 1023+16 DAC1，则 18 片轮换根本不该存在 —— 两者不能同时为真。**这是 L0 级待裁项。**

### 2.3 轮换调度与重建如何对齐

**结论：完全没有对齐。重建侧不知道这一拍用了哪 8 片，也拿不到顺序；现在是"因为没接线所以不会错配"，
一旦接上就必然错配 1 帧。**

| 环节 | 现状 | 证据 |
|:---|:---|:---|
| 调度侧知道什么 | `base`（5 bit）、`conv/acq` 18 bit 掩码、`sel/selb` | `SliceSched.sv:16-22` |
| 重建侧能看到什么 | 只有 `d1`、`d2`、`valid`。**没有 base，没有 conv 掩码，没有 slice id** | `ReconWeights.sv:11-18`；`DigitalTop.sv:85-88` 例化只连了 `.d1(D1) .d2(D2) .valid(acc_valid) .dout(recon)` |
| 顶层有没有旁路 | `MON = {m_act, base[3:0]}`，即 **base 只剩低 4 位**；而 18 片需要 5 位 ⇒ **base=16/17 与 base=0/1 无法区分** | `DigitalTop.sv:100` |
| `MON` 去哪了 | 只到端口，**没进 24 bit 帧、没进 LVDS、没进任何寄存器**，片外看不到 | `DigitalTop.sv:43`（端口）、`:92-96`（FramePack 只吃 `recon`） |
| 掩码够不够 | **不够**。18 bit 掩码只说明"哪 8 片在转换"，不说明"哪片占哪个 unary 位置"。而 unary 位置是有权重的（`arch_10m.md:46`：高 3 bit 用 8 片温度计选择），换序就是换权重 | `SliceSched.sv:39-46`（`sel` 与 `conv` 完全相同，没有位置信息） |

**跨帧错配风险（接上以后立刻暴露）**：`base` 在 `cnt==19` 更新（`DigitalTop.sv:59`、`SliceSched.sv:34-37`），
而本帧的 `DONE2` 落在 ΦC2 内（`cnt 10..17`，`DigitalTop.sv:64`），`Sinc2` 攒 8 拍、`FramePack` 再过一级 FIFO
⇒ **出帧时刻的 `base` 已经前进 1~2 帧**。若重建侧用"当前 base"查表，就会用第 n+1 帧的片组去解第 n 帧的码。
`OUTPUT_IF_10M.md:98` 已经写对了原则（"所有配置在采样沿冻结，随样本描述符走"），但 RTL 里
**没有采样沿锁存 `base` 的寄存器，也没有样本描述符（sideband）通路**。这是必须补的结构，不是可选优化。

### 2.4 片上有没有「校准采集模式」

**没有。一处都没有。**

| 需要的东西 | 现状 | 证据 |
|:---|:---|:---|
| `TEST_MODE`（含"原始码"011 模式） | **端口不存在** | `DigitalTop.sv:15-47` 全部 26 个端口；`OUTPUT_IF_10M.md:107` 定义了模式 011 要输出 `D1+D2` |
| 原始码导出（`D1/D2/DT/CNT`） | 不存在。`DOUT` 只有**已经用固定权重重构过**的 22 bit，无法反解出各片码 | `DigitalTop.sv:98`；`plan/phase2_digital.md:546` 要求"每样本导出 `{D1[9:0],D2[10:0],CNT[3:0]}` = 25 位" |
| slice id 上报 | 不存在（只有 4 bit 的 `MON`，且不在帧里，见 2.3） | `DigitalTop.sv:100` |
| SPI（系数灌入 + 观测回读） | **端口不存在**；`0x00–0x50` 寄存器映射一个都没实现 | `DigitalTop.sv:15-47`；`OUTPUT_IF_10M.md:86-98`；`plan/phase2_digital.md:111`（`SpiSlave` 是模块表第 14 项，RTL 里没有） |
| `D1_SNAP/D2_SNAP/DT_SNAP` 快照 | 不存在 | `plan/phase2_digital.md:781` 定义了 `0x0C`，RTL 无 |
| `CAL_EN/CAL_TRIG/CAL_DONE` | **都不存在**；`DOUT_RDY` 也没有被 `CAL_DONE` 门控 | `DigitalTop.sv:42`（`DOUT_RDY` 只由 `frame_valid` 驱动）；`OUTPUT_IF_10M.md:82` 要求"RSTN 后 DRDY 保持低，直到 `CAL_DONE=1`" |
| `FAULT` 语义 | 顶层把 `fault` **短接到 `1'b0`** ⇒ FAULT 位恒 0，坏样本永远不标记 | `DigitalTop.sv:94` |

**"片外 LMS 拿什么数据算"的答案：什么都拿不到。**

- 拿 `DOUT` 不行：它是 `w_名义 × 码` 的结果，18 片共用一套 `2^12/2^3`，反解 144 个未知量是欠定方程（1 个方程 144 个未知）；
- 拿 `MON` 不行：只有 4 bit `base`，且不出片；
- 拿仿真波形不行：校准要在硅上跑（PVT 边界、封装寄生、温漂都只在硅上成立），后仿只能验证算法，不能产生系数。

**唯一的现实路径**是 `plan/phase2_digital.md:546-549` 已经写好的方案：每样本导出 `{D1, D2, CNT}` 走 SPI
（25 bit/样本 × 1.4×10⁴ 点 ≈ 250 kbit，@10 MHz ≈ 25 ms）。**这条路径在 RTL 里 0 行实现。**

### 2.5 18 片轮换算不算天然 DEM

**结论：现在这个 round-robin 轮换不算 DEM，它是"确定性周期误差发生器"，
在 20 bit 目标下会变成带内确定性杂散（不是抬噪底）。**

先把数学部分钉死：

- `base ← (base+8) mod 18`，`gcd(8,18)=2` ⇒ 序列周期 = `18/2 = 9` 个样本（复算见 §5 命令 4）。
  ⇒ 误差序列是 9 周期的 ⇒ **谱线落在 `k·fs/9 = k×1.111 MHz`**（k=1..4 全在 5 MHz Nyquist 带内）。
- 使用频次我复算过：9 相 × 18 片，每片 **conv 4 次 + acq 4 次 + idle 1 次**，18/18 片完全均匀
  （`sum(conv_hist)=72`、`sum(acq_hist)=72`）。**均匀性这一条是成立的**，`SliceSched.sv:4` 的
  "每片周期 200 ns"写错了，实际是 `900/4 = 225 ns`；这不影响功能，但说明该注释未复核。
- 每相 `conv` 与 `acq` 交集为 0（复算已验证），无角色冲突 ✓。

**为什么它仍然不是 DEM。** 误差的性质决定了谱形：

设片增益失配 `δ_i`（`model/params.py:26`：`gain_sigma = 1e-3`，即 0.1%）。8 片并联组成一个 DAC1，
其合成权重 `W = Σ_{i∈CONV} w_i`。用统一名义权重重构时，误差 `e[n] = Σ_{i∈CONV(n)} δ_i·w_i`。
`CONV(n)` 以 9 为周期 ⇒ `e[n]` 是**确定性 9 周期序列**，不是随机序列。

| 项 | 值 | 依据 |
|:---|:---|:---|
| 8 片平均后的失配波动 | `σ_g/√8 = 3.5×10⁻⁴`（≈ −69 dB） | 【估算】`params.py:26` + 8 片并联 |
| 确定周期 9 ⇒ 主导谱线位置 | `1.111 / 2.222 / 3.333 / 4.444 MHz`（**带内**） | 【算术】上面 gcd 推导 |
| 单条谱线幅度（随机分配下的期望） | `≈0.67·σ_g/√8 ≈ 2.4×10⁻⁴ ≈ −72 dBc` | 【估算】9 点 DFT：`|X[k]|≈√9·s`，单边归一化 |
| 折算 ENOB | **≈12 bit**（−72 dBc） | 【算术】`(SNDR−1.76)/6.02` |

也就是说：**按 `params.py` 的失配量级，光靠轮换，SFDR 只有 ~72 dBc，比 20 bit 要求的 ~110 dB 差 38 dB，
正好卡在 12 ENOB。** 这解释了为什么"轮换"在 20 bit 系统里从来不能替代校准。

**"会成杂散还是抬噪底"的判据，以及成立条件：**

| 情形 | 谱形 | 成立条件 |
|:---|:---|:---|
| 当前 round-robin（周期 9） | **确定性杂散** @ k·fs/9 | 无条件成立（选择是确定的） |
| 换成 LFSR/随机洗牌 | 摊成**宽带噪声**，底抬 ≈ `σ_g/√8 = −69 dBFS`；16384 点 FFT 后 ≈ −108 dBFS/bin | 需 ①选择非周期（周期 ≫ 2²⁰ 样本）②使用频次均匀 ③选择与输入信号不相关 |
| 真正的"DEM 替代校准" | 需要 `σ_res/√8 < 1×10⁻⁵` 才够 −110 dBc | **不成立**：要求失配先被压到 1e-5 量级（比 `params.py` 的 1e-3 小 100×），而这正是校准要做的事 |

**⇒ 轮换能做的只有"把确定性杂散摊成噪声"，而且摊完仍是 −69 dBFS，对 20 bit 毫无意义。
必须先按片校准（把 `σ_g` 从 1e-3 压到 ≤4×10⁻⁵，约 25×），轮换才轮到它出场（把残余摊平）。**

**另有一处结构性冲突必须裁**：`plan/phase2_digital.md:522-523` 要求"MSB 两个半组角色永久冻结，
`DemDither` 严禁触碰 MSB"（否则 LMS 协方差非平稳、不收敛）；而 `plan/arch_10m.md:46-47` 的
"高 3 bit 用 8 片温度计选择 + `SliceShuffler` 随机分配片到 unary 位置"**正是让 MSB 角色每 100 ns 变一次**。
两条要求在同一颗芯片上不能同时满足。若走 18 片池，则 MSB 的可校性必须靠"按片权重"而不是"半组常数"来实现。

### 2.6 FramePack 帧格式 vs 文档；DigitalTop 端口 vs stub

**(a) 帧格式：位定义一致，语义不一致。**

| 项 | 文档 | RTL | 判定 |
|:---|:---|:---|:---|
| 帧长 / 位序 | 24 bit，MSB first，`{VALID, FAULT, DATA[21:0]}` | `{valid_in, fault, din}` = 24 bit，MSB first | ✅ **一致**（`FramePack.sv:24` vs `OUTPUT_IF_10M.md:25-27`） |
| DATA 编码 | 22 bit 无符号偏移二进制，中心 `0x200000` | `dout` 22 bit，复位 `0x200000` | ✅ 一致（`ReconWeights.sv:25-26`）——但见 2.1 的溢出/量纲错，**格式对、数值错** |
| `VALID` 语义 | "1=数据有效；0=**坏样本**（TO2/超时/校准未完成）" | 直接用 `valid_in`（= `acc_valid`，即"有数据"） | ❌ **语义错**：没有任何 TO2 / 超时 / `CAL_DONE` 门控 |
| `FAULT` | "1=该样本期间有故障（参考跌落 / RA 越限 / M≠8）" | 顶层 `fault(1'b0)` **恒 0** | ❌ **功能缺失**（`DigitalTop.sv:94`） |
| FIFO 溢出 | 溢出置 `FAULT[FIFO_OVF]`，该帧 `VALID=0` | `if (valid_in && count<16)` 静默丢帧，`full` 置起但无人使用 | ❌ **静默丢数据**（`FramePack.sv:30`） |
| SYNC 帧 | 每 256 帧一帧 `0xFFFFFF`，SPI 使能 | `SerLvds.sv:42` 有 `frame_cnt==8'hFF` 分支，但 `SYNC_EN` 无 SPI 来源，且 `SerLvds` 未被例化 | ⚠️ **孤立代码** |
| DRDY 宽度 | 10 ns（`OUTPUT_IF_10M.md:62`、`:39`） | `(cnt==5'd0)` ⇒ **5 ns**；`DigitalTop` 的 `DOUT_RDY` 更是"只要有数据就为 1" | ❌ 不一致（`SerLvds.sv:74`） |

**(b) 端口：RTL 与 stub 完全一致，但两者都不满足输出接口规格。**

- `python3 analog/netlist/check_ports.py` → `stub ports=26  sv ports=26 / OK: DigitalTop 模拟黑盒与 SV 端口逐字一致`。
  手工核对方向与顺序也一致（`DigitalTop.sv:16-46` vs `digital_stubs.scs:11-15`）。✅
- **但 `OUTPUT_IF_10M.md:56-63` 要求的 6 个 LVDS 引脚（`DOUTP/N`、`CLKOUTP/N`、`DRDYP/N`）在两处都不存在**，
  `SerLvds` 从未被例化。⇒ **芯片级交付形态（并行 22 bit + `MON[7:0]`）与接口文档（单 lane DDR LVDS）不一致**，
  且 stub 里也没有 SPI 4 线 + `CAL_TRIG`（`plan/arch_10m.md:91` 要求 6 个配置脚）。
- stub 把 `D1/D2/DT/DONE1/DONE2/COARSE` 都定义成 `DigitalTop_stub` 的**输入**
  （`digital_stubs.scs:12`），即真实芯片里 `D1/D2` 由模拟壳内的 `SarLogic1/2` 产生 ⇒
  **数字顶层根本看不到 `Sar1Ctrl/Sar2Ctrl` 内部状态，自然也无法导出"原始码 + slice id"的组合**。

---

## §3 缺口清单

> 规模口径：**S** ≤ 200 行 RTL / ≤3 人日；**M** ≤ 800 行 / ≤2 周；**L** > 2000 行或需改顶层端口与模拟 stub / >1 月。

### 3.1 必须补（不做则校准链路不可能工作）

| # | 缺口 | 规模 | 验收方法 |
|:--:|:---|:---:|:---|
| N1 | **统一 DAC1 结构口径**：18 片池（144 系数）vs 单一 1023+16（34 系数）。冻结系数表（每项：名字/物理含义/位宽/Q 格式/名义值/训练上界） | S（文档，0 行 RTL）| 系数表评审通过；`grep` 三份 plan 文档不再出现两种结构；`ReconWeights` 的端口数由该表唯一确定 |
| N2 | **`CoefReg`：144 槽 × 24 bit 系数寄存器 + 复位为名义值** | M | 复位后 `DOUT` 对斜坡单调、无跳变（`d1` 扫 0..1023 逐码检查 `ΔDOUT>0`）；`COEF_CRC` 读回 = 写入 |
| N3 | **SPI slave（4 线，≤10 MHz，16b 地址 + 24b 数据）** | M | 回环测试：写 144 槽 + 读回全等；`CAL_EN=0` 时写被拒（断言 A12） |
| N4 | **按片权重映射层**：`ReconWeights` 增加 `slice_id[7:0][4:0]` 输入，按 8 片查表求和 → 合成位权 | M | 同一 `d1` 码在 9 个不同 `base` 下，`DOUT` 与"按片权重 C 模型"逐码相等（误差 0 LSB，纯整数） |
| N5 | **`SliceSched` 输出有序 `SLICE_ID[7:0][4:0]`（40 bit）**，替换/补充 18 bit 掩码 | S | `SLICE_ID` 与 `CONV` 掩码互为一致（`CONV[i] == OR_k(SLICE_ID[k]==i)`）；`plan/phase2_digital.md:112` 的接口表签收 |
| N6 | **`base` 在采样沿锁存 + 样本描述符随数据走完全程**（`base`/`SLICE_ID` 与 `D1/D2` 同拍进重构、同拍进 FIFO） | S | 断言：`DONE2` 后 3 拍内 `SLICE_ID_S` 变化 ⇒ 报错；FIFO 每帧携带的 `base` 与当帧 `CONV` 一致 |
| N7 | **校准采集模式（`TEST_MODE=011`）**：每样本导出 `{D1, D2, DT, CNT, SLICE_ID}` 走 SPI | M | 注入已知斜坡，主机侧重构码与 `DOUT` 逐码相等；导出 1.4×10⁴ 点耗时 ≤ 30 ms |
| N8 | **`CAL_EN/CAL_TRIG/CAL_DONE` + `DOUT_RDY` 门控**（校准期 `VALID=0`、DRDY 保持低） | S | 断言：`!CAL_DONE \|-> !DOUT_RDY`；`OUTPUT_IF_10M.md:82` 判据 |
| N9 | **`FAULT` 真实化**：接 `FIFO_OVF` / `TO2` / `M≠8` / `OVF`；溢出帧 `VALID=0` 且计数 | S | 强制 `count=16` 注入溢出 → `FAULT=1`、`VALID=0`、`OVF_CNT++`；当前 `FramePack.sv:35-39` 的 `count` 双写 bug 必须同修 |
| N10 | **`ReconWeights` 名义路径修正**：`d1` 改 10 bit、补 `1/√2` 增益抽头、`DOUT` 钳位到 `[0,2²²−1]` 并置 `OVF` | S | `d1` 全范围扫描无回绕：`d1: 511→512` 处 `DOUT` 必须连续（当前 `0x3FF000 → 0x000000`）；FS 处 `DOUT` = `2²¹.5 ± 1` |
| N11 | **`Sar2Ctrl` 拍数修复**：ΦC2 只有 8 tick 而 FSM 需 18 tick ⇒ `done2` 永不置起，整条数据通路在 RTL 层是死的 | M | 断言 A3/A4（`plan/phase2_digital.md:791-792`）：ΦC2 内 `REP_CLK` 上升沿计数 == 8；`DONE2` 每帧恰好 1 次 |
| N12 | **`Sar1Ctrl` 双驱动 `idx` 修复**（`Sar1Ctrl.sv:36-44` 与 `:49-61` 同抢 `idx`） | S | lint 无 multi-driver 告警；`d1` 在 ΦC0/ΦC1 两段各自更新而不互相清零 |

### 3.2 建议补（影响可测性/可诊断性，不补会让"校准对不对"无法定位）

| # | 缺口 | 规模 | 验收方法 |
|:--:|:---|:---:|:---|
| N13 | **`ObsReg` 观测窗口**：`M_ACT`/`TO2_CNT`/`REP_MISS`/`BUBBLE_CNT`/`META_CNT`/`OVF_CNT`/`ST_SNAP` | S | `plan/phase2_digital.md:765-783` 的每一条"合格条件"可读回；上电全清零 |
| N14 | **`SerLvds` 例化 + `DRDY` 宽度改 10 ns + `SYNC_EN` 接 SPI** | S | 400 Mbit/s 波形：24 UI + 40 ns 空闲；DRDY 宽 10 ns；SYNC 帧每 256 帧 1 次 |
| N15 | **洗牌改成 LFSR（周期 ≥ 2²⁰ 样本）+ `SEED` 可配**，替换 `base+8` | S | 使用频次均匀性 χ² 检验（18 片，10⁶ 样本，p>0.01）；DC 输入下 `1.111 MHz` 及谐波处无谱线 |
| N16 | **`Sinc2.acc` 真正接入重构**（现在算完就丢，8× 平均的 3 dB/oct 收益完全没有兑现） | S | `acc` 的 fanout ≠ 0；注入 `M=1` 与 `M=8` 对比，噪底改善 ≈ 9 dB |
| N17 | **`ReconWeights` 名义值与 `spec/bit_allocation.md:52` 的 C 模型逐位对齐**（含舍入 tie-break） | S | RTL 与 Python C 模型的 `DOUT` 逐码 bit-exact（10⁶ 随机点） |
| N18 | **`m_act` 实数统计**（现在写死 `4'd8`） | S | 强制 `REP_MISS` 注入后 `m_act<8`，`FAULT[M_MISMATCH]` 置起 |

### 3.3 可延后

| # | 缺口 | 规模 | 验收方法 |
|:--:|:---|:---:|:---|
| N19 | 片上 LMS 引擎 | L | **不建议做**：`plan/phase2_digital.md:549` 已论证 +1800 门/400 FF/52 µW 且降低可定位性 |
| N20 | 系数掉电保持（NVM / eFuse） | L | 上电自动重灌时序；当前策略"主机上电灌一次"（`phase2_digital.md:476`）足够 |
| N21 | 双 bank（A/B 相位交织）系数各一套 | M | `phase2_digital.md:702` 的"2 bank 增益"；P1 单 bank 可先绑死 |
| N22 | `M64_CAL`（M=64 校 F3 斜率） | S | `phase2_digital.md:845` 已定义为"留口子不实现" |

---

## §4 建议改动方案（**只是方案，未改任何文件**）

### 4.1 系数表（N1 的产物，先把这张表冻结）

```text
group           count  width  Q       nominal        训练上界      物理含义
SLICE_W[17:0][6:0]  126  16b   Q8    {2^6..2^0}·27fF  ±2%          每片每位的 128 单位权重
SLICE_G[17:0]        18  16b   Q14   1.0             ±2%          每片段增益（含 128 单位的整体缩放）
D2_W[10:0]           11  16b   Q8    2^(k+3) u       ±32 u         DAC2 位权（全局，单片）
D2_BRIDGE             1  16b   Q8    0               ±8 u          DAC2 6+5 桥接
REP_GAIN              1  16b   Q8    0               ±32 u         (CNT−M/2) 步长
GAIN_1OSQRT2          1  24b   Q16   46341           ±1%           √2 归一 + RA 增益
OFFSET                1  16b   Q8    0               ±64 u         RA/Cmp 失调 + (CNT−4) 常数项
------------------------------------------------------------------------------
合计                144 + 16 = 160 槽   （建议按 160 槽 × 24 bit = 3840 bit 预留）
```

> 与现有预留的关系：`OUTPUT_IF_10M.md:91` 的 40 槽 → 需 ×4；`phase2_digital.md:702` 的 64 槽 → 需 ×2.5。
> 3840 bit 听起来多，但它只在 SPI 加载时翻转（`phase2_digital.md:702` 已算过 ~15 µW），
> 面积约 `3840×6 µm² ≈ 0.023 mm²`（【估算】180 nm 6T SRAM-bit 等效）。**这是必须付的钱。**

### 4.2 `ReconWeights` 重构（N4/N10 的核心）

```systemverilog
// ===== 方案示意，不要直接落地；先冻结 §4.1 的系数表 =====
module ReconWeights #(
    parameter int NW = 7            // 每片位宽
)(
    input  logic          clk,
    input  logic          rstn,

    // 数据与描述符必须在同一拍到达（N6）
    input  logic [9:0]    d1,          // ← 10 bit，不是 11 bit（phase2_digital.md:53）
    input  logic [10:0]   d2,
    input  logic [3:0]    cnt,         // 8× 重复的实际拍数（N16：用 Sinc2 的 acc 更好）
    input  logic [39:0]   slice_id,    // 8 × 5 bit，有序（N5）
    input  logic          valid,

    // 系数（由 CoefReg 静态给出，SPI 加载后冻结）
    input  logic [15:0]   w_slice [18][7],   // SLICE_W  Q8
    input  logic [15:0]   g_slice [18],      // SLICE_G  Q14
    input  logic [15:0]   w_d2    [11],
    input  logic [23:0]   w_gain,            // GAIN_1OSQRT2  Q16
    input  logic signed [15:0] w_off,

    output logic [21:0]   dout,
    output logic          ovf
);
    // ① 名义移位（0 门）：按 §4.1 的名义值，d1 权重 = 2^(k+12)·(1/√2)
    // ② 按片修正：ΔW1 = Σ_{k=0..7} Σ_{b=0..6} (w_slice[id_k][b] - nominal[b]) · d1[b] · g_slice[id_k]
    //    —— 144 项里同时用到「片」和「位」，这是 126+18 能同时成立的原因
    // ③ 合并 + 增益抽头（16 拍时序乘 26×17）+ 钳位
    // always_ff: dout <= clamp_22( 22'h200000 + round((nom + delta) * w_gain >> 16) );
    //            ovf  <= (sum > 22'h3FFFFF) || (sum < 22'h000000);
    // 复位值全部取名义值 ⇒ 未校准也能出正确码、只是 DNL 回到 10–30 LSB（phase2_digital.md:476）
endmodule
```

### 4.3 `SliceSched` 输出有序 id（N5）

```systemverilog
// 现: output logic [17:0] conv;              // 只有掩码，丢了 unary 位置
// 改: 增加有序 id，key = unary 位置（0..7，pos0 权重最小）
always_comb begin
    conv = '0;
    for (int k = 0; k < 8; k++) begin
        slice_id[k] = 5'((base + k) % 18);   // 位置 k ↔ 片 id，顺序由这里唯一确定
        conv[slice_id[k]] = 1'b1;
    end
end
// 关键：base 的"本次转换所属"版本必须随样本走，不能就地读当前 base
always_ff @(posedge clk or negedge rstn)
    if (!rstn) slice_id_s <= '0;
    else if (done2_pulse) slice_id_s <= slice_id;   // 采样沿锁存（N6）
```

### 4.4 采样沿锁存 + 描述符随帧走（N6，最容易漏的一条）

```systemverilog
// 错的做法（接上就错 1 帧）：
//   ReconWeights.u_recon.slice_id = slice_id;            // 出帧时 base 已前进 1~2
// 对的做法：
always_ff @(posedge CLK200 or negedge RSTN)
    if (!RSTN) desc_base <= '0;
    else if (DONE2) desc_base <= base;      // 与 D1/D2 同沿捕获
// FramePack 的 24 bit 不够放描述符 ⇒ 校准模式下走独立观测通道（N7），
// 正常模式下 base 只用于选权重，不出片
```

### 4.5 校准采集模式（N7）

```systemverilog
// TEST_MODE == 3'b011：绕过重构，把原始码与 id 直接送观测寄存器
// 每样本 10+11+8+4+5*8 = 73 bit；SPI 一次事务 24 bit ⇒ 4 次读完成一帧
// 采样率 10 MS/s、只采 1.4e4 点 ⇒ 观测通道只需 ~140 µs 的带宽，用 1 MHz 慢时钟足够
always_ff @(posedge CLK200)
    if (DONE2_SYNC && (test_mode == 3'b011) && obs_rdy)
        obs_shift <= {slice_id_s, cnt_s, dt_s, d2_s, d1_s};   // 锁存快照，SPI 慢慢读
```

**说明：`ReconWeights` 一定要用「按片查表」而不是「乘一个全局 gain」。**
若只做全局增益（`plan/phase2_digital.md:516` 的 `GAIN_1OSQRT2`），失配仍然是逐片的，
轮换仍会产生 2.5 节算出的 −72 dBc 带内杂散 —— 校准必须按片落到 126 项上，这不是"多留几个系数"的问题。

---

## §5 复核命令

```bash
# 0) 说明：本机没有 iverilog/verilator，下面的 lint/sim 只作模板，装好后再跑
which iverilog verilator || echo "no simulator"

# 1) 端口一致性（RTL ↔ 模拟 stub）—— 当前应输出 26/26 OK
cd /Users/zhaoyi/WorkBuddy/pipelinedsar工作站/20b10m
python3 analog/netlist/check_ports.py

# 2) 确认片上没有任何校准入口（预期：只在注释里命中，端口里 0 命中）
cd digital
grep -nE "spi|SPI|CAL_EN|CAL_TRIG|CAL_DONE|TEST_MODE|slice_id|SLICE_ID|CoefReg|w_slice" *.sv \
  | grep -v "^ReconWeights.sv:[47]:" || echo "NO CAL PORT — 缺口成立"

# 3) ReconWeights 名义路径回绕复算（预期 d1=511→0x3FF000, d1=512→0x000000）
python3 - <<'EOF'
for d1 in (255,256,511,512,1023,2047):
    acc=(d1<<12); dout=(0x200000 + (acc & 0x3FFFFF)) & 0x3FFFFF
    print(f"d1={d1:5d} acc={acc:9d} DOUT=0x{dout:06X}")
print("允许的 d1 上限 =", (2**21-1)//4096, "（当前签名 d1 宽 11 bit，可达 2047）")
EOF

# 4) 轮换周期与使用均匀性（预期：周期 9；每片 conv=4/acq=4/idle=1）
python3 - <<'EOF'
base=0; conv=[0]*18; acq=[0]*18; idle=[0]*18
for p in range(9):
    c=set((base+k)%18 for k in range(8)); a=set((base+8+k)%18 for k in range(8))
    for i in c: conv[i]+=1
    for i in a: acq[i]+=1
    for i in range(18):
        if i not in c and i not in a: idle[i]+=1
    assert not (c & a), f"phase {p}: conv/acq 重叠"
    base=(base+8)%18
print("周期(base 回到 0) = 9 ;  conv_hist =", conv)
print("acq_hist =", acq, "\nidle =", idle)
import math; print("gcd(8,18)=", math.gcd(8,18), "=> 杂散基频 fs/9 =", 10e6/9/1e6, "MHz")
EOF

# 5) Sar2Ctrl 拍数核算（ΦC2 只有 8 tick，FSM 需 10+8=18）
python3 -c "
print('ΦC2 tick 数 =', 17-10+1)
print('Sar2Ctrl 需要 =', 10, '(SAR 10 位) +', 8, '(重复) = 18')
print('=> done2 永不为 1，Sinc2/FramePack 链在 RTL 层无输出' )"

# 6) 帧格式位级对照（预期 24 bit、{valid,fault,data[21:0]} 一致）
grep -n "frame = {" digital/FramePack.sv digital/SerLvds.sv
sed -n '21,32p' interface/OUTPUT_IF_10M.md

# 7) 装好 iverilog 后的正式复核（当前不可跑）
cd digital && make lint     # 预期报出：Sar1Ctrl 的 idx 多驱动、DigitalTop.acc 未使用
make sim                    # 预期：DOUT 恒 0x000000（tb 的 D1=512 正好踩在回绕点）
```

---

## 附：需要模拟侧 / 架构侧确认的假设（我无法自证，标"待确认"）

| # | 假设 | 为什么必须问 | 若不成立的后果 |
|:--:|:---|:---|:---|
| Q1 | DAC1 是"18 片 × 128 单位 + 高 3 bit 跨片 unary"，还是"单一 1023+16" | 直接决定系数是 144 还是 34（§2.2） | 选错则 `CoefReg` 面积与映射层全部重做 |
| Q2 | 8 片并联时，低 7 bit 的二进制码是"每片各自一份"还是"8 片共享一份" | 决定 126 项是否可以合并成 7 项（若共享，合成权重 = Σ 片权，仍逐片） | 影响 N4 映射深度（144 项查表 vs 7 项求和） |
| Q3 | 片增益失配的真实 σ（`params.py:26` 的 1e-3 是估计值） | §2.5 的 −72 dBc 结论对 σ 线性 | σ 若为 1e-4，杂散降到 −92 dBc，DEM 的紧迫性下降但校准仍必需 |
| Q4 | MSB unary 位置是否需要保持时不变（vs `phase2_digital.md:522` 的"半组角色永久冻结"） | 两条要求在 18 片池下冲突 | 冲突不裁，LMS 协方差非平稳、不收敛 |
| Q5 | 200 pF 级 DAC1 顶板的建立时间（决定"按片权重"是否需要含动态项） | 若 ΦC0 内未收敛，静态系数只能吃平均值 | 校准残差压不到 2 LSB_total，需回退到模拟方案 |
