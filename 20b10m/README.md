# SAR20-10M —— 20.0 bit / 10 MS/s 两级 SAR（180 nm BCD）

> **架构**：10 bit DT（3 unary + 7 binary）→ **G=32 三级 RA** → **12 bit CT**（C_INC + DAC2 + replica）→ 同笔 8× 重复 → 数字重构。
> **交织**：DAC1 拆 18 片池（8 转换 + 8 采样 + 2 备），量化器 / RA / CT2 / 参考 / 数字全部单套共享。
> **状态**：码域已用 Python 闭合（理想 INL **0.000 LSB20**、SNDR **122.06 dB**、ENOB **19.98**）；**零晶体管仿真、零 RTL 编译、零版图**。

![架构](docs/arch_diagram.svg)

---

## 1. 架构为什么这样选

| 约束 | 结论 |
|:---|:---|
| 20 bit 不能单级（需 2^20 单位） | 必须两级 |
| 10 MS/s 且驱动不能难做 | 2 相部分交织：采样窗占满 100 ns，驱动带宽 **22.3 MHz**（不交织要 89 MHz） |
| 余差要能被二级吃下 | 冗余 2 bit，窗口 ±2 LSB1 = **39.06 mVpp** |
| RA 摆幅 ≤1.7 V | G=32 → 输出 1.25 Vpp（占 73%） |

**位账自洽**：`LSB2 = 39.0625 mV / 2^12 = 9.5367 µV = FS/2^20` —— 二级最低位恰好等于系统最低位，没有「平均折算位」。
`behavioral` 包里有断言锁死这条，改任何位账参数立刻报错。

## 2. 关键数字

| 项 | 值 | 来源 |
|:---|:---|:---|
| 分辨率 / 速率 | **20.0 bit** / 10 MS/s | 位账推导 |
| 输入 / 采样电容 | 差分 10 Vpp；27.6 pF/侧（8×3.456 pF） | 8 片活跃 |
| LSB1 / LSB2 / LSB_total | 9.7656 mV / **9.5367 µV** / 9.5367 µV | 自洽 |
| 帧 / 相位 | 100 ns；**10 / 15 / 20 / 45 ns** + guard 10 | 5 ns 整 tick |
| RA | G=32；A0 ≥50 dB；τ ≤2.04 ns | 前仿待做 |
| 参考 buffer | **Zout ≤0.67 Ω**；平均 2.76 mA | droop 恒等式 |
| 面积 | core 0.93 / die 1.41 mm² | 面积模型（MIM 密度待 PDK） |
| 功耗 | 3.73–4.03 mW | 估算 |

## 3. 技术有效性：交叉验证后的结论

> 协议：**K=10 seeds（1000–1009）**，配对差值 + 95% CI；图另用 2000–2009 独立复现。
> 原始数据：`model/results/crossval/{results.json,summary.csv}`；报告：`review/20261112_crossval.md`。

| 技术 | 结论 | 判定 |
|:---|:---|:---:|
| 位账 | LSB2 = FS/2^20，相对差 <1e-12 | **PASS** |
| 8× LSB 重复 | **+1.69 dB [1.66,1.72]** @100k；+1.70 @1M；解析预测 1.714 | **VALIDATED** |
| CAAZ | **+3.65 dB** @100k；@1M +3.54；@2M +3.21；其中 AZ 只 **+0.60** | **VALIDATED** |
| 片级 shuffle | SFDR **+22.3 dBc** @100k、+21.7 @2M；**DR 方向不稳**（+0.9 / −1.7 两段相反） | SFDR **VALIDATED**；DR **NOT VALIDATED** |
| 静态校准 | INL **18.6 → 0.56 LSB20**（33×）；DNL **24.0 → 0.75 LSB20**（32×），失码 0→0；out-of-sample **2.0 LSB20** | **CONDITIONAL**（OOS 超 1 LSB20） |
| 交织 skew | 0.5→2 ps：**−1.44 dB [−1.73,−1.14]**，10/10 负 | **VALIDATED（退化）** |
| 交织增益 | 10→50 ppm：**−5.58 dB [−6.11,−5.06]**，10/10 负 | **VALIDATED（退化）** |
| DEM（片级 8 态，模型） | INL **22.9→6.3 LSB20（3.6×）**；DNL 24.0→8.5 LSB20（2.8×）；网表/RTL 未实现 | 模型 VALIDATED / 实现 OPEN-5 |
| dither（码域 D=2，模型） | DNL **24.0→5.2 LSB20（4.6×）**；INL 22.9→21.1（1.08×，几乎无效）；采样态注入未实现 | 模型 VALIDATED（DNL）/ 实现 OPEN-3 |
| DEM+dither | INL **5.2 LSB20（4.4×）**；DNL **1.7 LSB20（13.8×）** | 互补 |
| 跨实现 INL | `model` 16.4 ppm vs `behavioral` 43.3 ppm（**2.64×**） | **DISCREPANT** |

**不能声称**：8× 在硅上值 1.7 dB；shuffle 用 DR 换 SFDR；校准后 0.3 ppm 达 20 bit；INL=16.4 ppm 是绝对值；DEM/dither 有效。
> 换算：1 LSB20 = 0.954 ppm FS；1 LSB1 = 1024 LSB20。

### 效果图（每张带来源脚注）

| 图 | 回答的问题 | 数据来源 | 等级 | 判定 |
|:---|:---|:---|:---:|:---|
| `docs/figures/f0_architecture.svg` | 结构 + 口径（target vs as-wired） | 网表逐行 + SSOT | L0 | 结构事实 |
| `f1_spectrum` | 100 kHz 的 SNDR/DR/SFDR | `model.adc.simulate` + FFT | L1 | 单点示例 |
| `f2_averaging` | 8× 重复值多少 dB | `model.adc.simulate`，10 seeds | L1 | VALIDATED |
| `f3_shuffle` | 片级随机选片换到什么 | `model.adc.simulate`，10 seeds | L1 | SFDR VALIDATED / DR 不稳 |
| `f4_inl_dnl` | 0.2% 失配的 INL/DNL 与校准残差 | `charge_model` + 有限样本拟合，seed 7 + 10 chips | L1 | INL 33× / DNL 32×；OOS CONDITIONAL |
| `f5_skew_gain` | 交织 skew/增益失配的代价 | `model.adc.simulate`，10 seeds | L1 | VALIDATED（退化） |
| `f6_crossval` | 哪些效果统计显著 | `model.crossval`，K=10 | L1 | 森林图 + INL 三口径 |
| `f7_dem_dither` | DEM 与 dither 各自贡献 | `model.tech_effects`，K=10 | L1 | DEM 管 INL / dither 管 DNL |

> 规则：图上每个效果数字带 `[模型]` / `[论文]` / `[估算]`；脚注写脚本、N、seeds、SSOT 口径、等级、日期。
> 生成：`python3 -m model.crossval && python3 -m model.figures_ssot`；清单：`docs/figures/manifest.json`。

### 其他层

| 层 | 状态 | 证据 |
|:---|:---|:---|
| 码域闭合 | ✅ | `behavioral` `runs/smoke_ramp`：σu=0 → INL 0.000 LSB20 |
| 理想动态（无噪声） | ✅ | `runs/smoke_tone`：SNDR 122.06 dB（无噪声，非 20 bit 系统指标） |
| 网表层次 | ⚠️ 仅静态 | `check_hier.py`：28 文件 / **222 实例** / 端口一致 |
| 模拟电路 | ❌ **零仿真** | PDK 空；DAC1 termination 接 VCM、三电平未接、replica 单套 |
| 数字 RTL | ❌ **零编译** | 本机无 iverilog/verilator |
| 版图 | ❌ **零** | 只有面积模型 |

## 4. 首要阻塞（按严重度）

| # | 问题 | 影响 |
|:--|:---|:---|
| 1 | **ΦC2 在 SS 角差 0.15 ns**（需 2.40，只有 2.25） | SS 下二级永远超时 → Cmp2 收紧到 ≤1.05 ns |
| 2 | **DAC1 仍产不出真 10 bit**：pool 已改 126-bit mask，但 termination 1C 固定 VCM、三电平未接 | 逐码扫描会少 8/1024 码 |
| 3 | **DAC2 12 bit 分段未定** | C_top / α / kickback 全部参数悬空 |
| 4 | **参考 buffer Zout 需 ≤0.67 Ω**（当前网表拓扑错） | droop 19.97 LSB1，SNDR 崩 |

## 5. 最短复现

```bash
cd 20b10m/behavioral
python -m pip install -e .
python -m sar20b.cli doctor                          # 依赖 / 合同 / 工具 / 字体
python -m pytest -q                                  # 不变量测试
python -m sar20b.cli run --config configs/experiments/ideal_tone.yaml --out runs/tone
python -m sar20b.cli run --config configs/experiments/mismatch_ramp.yaml --out runs/ramp
python -m sar20b.cli figures --run runs/ramp
python -m sar20b.cli report  --run runs/ramp
```

一致性检查（跨文档/跨域，含正反例）：

```bash
python3 tools/check_consistency.py
```

## 6. 下一批任务（可直接分配）

| ID | 任务 | 责任 | 验收 |
|:---|:---|:---|:---|
| T-A01 | 参考 buffer：Zout ≤0.67 Ω @1 k–10 MHz，平均 2.76 mA | 模拟 | Zout 曲线 + 69 pC/0.3 ns 阶跃恢复 <1 ns |
| T-A02 | Cmp2：SS ≤1.05 ns（tail 12→18 µA） | 模拟 | TT 0.9 / SS 1.05 |
| T-B01 | DAC2 12 bit 分段选型（6+6 vs 7+5） | 架构→模拟 | C_top ≤1.8 pF |
| T-B03 | DAC1 网表修到 10 bit（pool 接口已改 126 bit；slice 的 termination 1C 仍固定 VCM） | 模拟 | 1024 码逐码扫，LSB 台阶 = 1 单位 |
| T-C01…C06 | 数字六项（相位 / NB_D2 / Sinc2 / ReconWeights / SliceSched / SerLvds） | 数字 | 出帧率 = fs，逐码 bit-exact |

完整任务表见 `TASKS.md`。

## 7. 文档地图

| 文件 | 作用 |
|:---|:---|
| **`spec/SSOT.md`** | **唯一口径**（分辨率/位账/FS/G/电容/时序/接口/未决项）；所有数从这里引 |
| `spec/params.yaml` | SSOT 的机器可读副本（脚本/RTL/网表生成器读它） |
| `tools/check_ssot.py` | 口径闸门：派生量、代码合同、旧值扫描、必需标记；失败即阻断 |
| `spec/LEGACY_INDEX.md` | 历史文件清单：哪些不能作为设计输入 |
| `STATE.md` | 状态总表（架构 / 模拟 / 数字 / 模型 / 安排） |
| `TASKS.md` | 任务与验收追踪（唯一任务入口） |
| `spec/ADR-001_ARCH_DECISION.md` | 架构决策 + 三候选比较（历史依据） |
| `spec/ARCH_REVIEW.md` | 现存架构的五项余量检查 |
| `spec/DROOP_OPTIONS.md` | droop 的唯一要求（Zout ≤0.67 Ω）与三次修正记录 |
| `spec/MODULES.md` | 模块卡（模拟 7 + 数字 6）+ 接口 |
| `spec/REUSE.md` | 参考库复用表（到文件/符号） |
| `interface/PINOUT.md` | 引脚（最少 17 脚 + 完整 48 脚） |
| `behavioral/` | Python 主引擎（可安装包 `sar20b`） |
| `docs/arch_diagram.svg` | 架构图（可编辑源） |
| `spec/TASKS_ARCH_V2_legacy.md` · `spec/README_ARCH_V2_legacy.md` | 旧口径（20.5 bit / 10+11+1.5−2），仅作历史  SSOT-ALLOW |

## 8. 不宣称的事

- 不宣称 SNDR 99.4 dB 可达（droop / settling 未闭合）；
- 不宣称模拟网表可用（DAC1 仅 7 bit、三电平悬空、replica 开断）；
- 不宣称版图完成（无 PDK 器件、无 DRC/LVS）；
- 不宣称架构已冻结（`spec/ADR-001` 是候选，用户已确认「不大改」，但未逐条签字）。
