# 与 GitHub 参考实现（`20b10mtask`）的逐点对照审计

> 审计对象 A：`20b10m/model/`（charge_model / adc / sources / params / metrics / static / experiments / selftest）
> 审计对象 B：`/tmp/ref_20b10mtask/`（`src/adi_model/charge_ref.py`、`src/adi_model/metrics.py`、`task2/eight/model.py`、`task2/eight/plots.py`、`task2/eight/experiment.py`、`task1/experiments/{inl_dnl,run_effects,adctoolbox_calibration}.py`、`task1/model/scheduler.py`、`task3/tools/run_joint_noise.py`、`task3/tools/run_caaz_effect.py` 及归档 `evidence/*/summary.json`）
> 约束：本次审计**未修改任何 `.py` 文件**，所有数字均由只读调用现有模块重算得出（复现命令见 §5）。

---

## 一句话结论

**电荷公式与 FFT 口径这两层基本对齐（同口径实测差 <0.05 dB），但"量"和"机制"两层没有对齐：我们报的 INL 是单状态 10 bit DAC1 电压传输的最差拟合残差，参考报的是 512 个 DEM/dither 状态平均后、经 12 bit ADC2 在环量化、冻结 LMS 重构的 20 bit 码密度 INL——两者不可比；我们把"重复采样相关性"写在沿重复序号 m 的 AR(1) 上，而参考实现里根本没有 M 次平均这一机制（它的 8 是每笔 8 片，相关性只以"同一笔 AZ 共享 ρ≡1 + fresh 独立"的形态出现），因此 `M=1→8 只涨 +1.71 dB` 是全部结论里最不可靠的一个数。**

---

## §1 对照表

| # | 功能点 | 参考 `文件:行` | 我们 `文件:行` | 差异 | 影响（含实测） | 处置 |
|:--|:---|:---|:---|:---|:---|:---|
| 1 | 电荷→输出电压闭式 | `charge_ref.py:98-99`：`β=Cb/(Cb+Σcs+Cpar)`，`C_F v_R=Σcm(wm−bm)+βΣcs(ws−bs)` | `charge_model.py:52-55`：`v=vin+[Σc(bot−vin)+c127(bot_term−vin)]/(Σc+cp)` | 参考是**两节点（主+子，桥衰减 β）+ 虚地电荷转入 C_F**；我们是**单一顶板无源分压 + 8 片电压求和**，无桥、无子节点寄生 | 参考的 β 只把子阵列整体缩放到"恰好跨 1 个粗 LSB"（`model.py:136-139`，nominal 256 单位），对我们拓扑等价于"128 单位直接同节点"，是常数缩放 → 被每段增益特征吸收，不改 ppm 结论 | 不改电路模型，但**必须在文档里声明"等效 Cb→∞、Cpar=0"** |
| 2 | 主节点寄生 Cp | `charge_ref.py:132-134`：主节点被钉在 0，矩阵行不含主节点寄生（虚地使寄生不参与电荷转移）；`model.py:138` 连 `sub_parasitic` 都丢掉 → 实验用模型是 Cpar=0 | `charge_model.py:53`：`ctot=caps.sum()+cp`，cp 为全局、每片各自加一次 | cp 在参考里**原则上不出现**（虚地），在我们里进分母 | 实测（`§5.5`）：cp=0/1%/10% → INL 峰值 **16.395 / 16.227 / 14.855 ppm**，增益 **1.0000 / 0.9901 / 0.9091**。对 ppm 级结论 ≤1.6 ppm（≈10%），但**增益错 9%（cp=10%）**，且把"8 片求和"写成电压求和（每片独立寄生）而非电荷求和 | cp 只作增益项保留，**禁止用本模型报增益/满量程**；要报就写"cp 未标定，增益误差 ±cp/ΣC" |
| 3 | termination / dummy 单位 | `model.py:139`：权重用 `cap.sub[:, :-1]`（剔除 dummy），但 `model.py:138` 的 β 分母 `cap.sub.sum()` **含** dummy；dummy 的采样态另作特征被减掉 `model.py:104-109` | `charge_model.py:45-51,54`：`caps[127]` 只在 `full=True` 接 VREF、否则接 VGND，只进分母 + 常数项 | 两者都做到"不贡献权重但加载节点"；差别在我们**没有采样相**（dummy 无采样态、无 CDS） | 对我们的 INL 无净影响（常数/每片增益被吸收）；但"底板采样扰动"这一物理量在我们模型里**完全缺失**，见 §2-5 第 5 项 | 保留，但删除"termination 已建模采样"的任何暗示 |
| 4 | 差分归一化 / 共模参考点 | `charge_ref.py:70-99` **完全单端**（无互补码，两节点）；采样/转换底板电压全部由调用方给 `charge_ref.py:53-64`；强制码本从 −peak 起步 `inl_dnl.py:455` | `charge_model.py:63-82`：`v=(vp−vn)/8`，vn 用互补码 `1023−k`、**同一组 caps**；`VCM=2.5` 声明于 `charge_model.py:22` 但**全工程无引用**（唯一一处）；实际参考点是 0（`vin` 默认 0、`vgnd=0`） | 我们多了一层"互补差分"，参考没有；共模点我们写了没用 | 实测（`§5.2`）：单端 8 片求和曲线 INL 峰值 **23.58 ppm**，其中**偶分量 19.36、奇分量 16.41**；差分结果 **16.40 ppm = 奇分量**。即 16.4 ppm 完全依赖"同一阵列互补开关、偶阶抵消"这一拓扑假设；若两侧为独立阵列，偶分量不抵消，量级回到 23 ppm 侧（−44% 的乐观） | **必须**在结论里绑定"同一阵列互补开关"；否则 ppm 数按 1.4× 记 |
| 5 | 逐状态开关（DEM / dither） | `model.py:104-109` 特征 = 主位 + 子位减采样位；`model.py:40-62` 每笔 6 bit 扰动字 → 8 slot 底板掩码；`model.py:85-101` 扰动字偏移粗判决；`model.py:142-144` 每个状态一组 `(gain, base)`；`experiment.py:189-192` 逐笔取字 | **无**：`charge_model.py:58-82` 每个码只有一条确定性曲线，状态由码唯一决定 | 参考的动态量是"状态平均后的均值曲线 + 状态离散"；我们是"单一状态曲线" | 参考归档（`task1/evidence/inl_dnl/adc2_16bit`，σ=2%）：512 状态、`midpoint_state_spread_median_rms_v=9.36e-7 V`（≈0.09 ppm FS）、DEM 后均值曲线残差峰 `2.69e-7 V`（≈0.03 ppm）。我们没有这个维度，**无法产生也无法验证任何 DEM 收益** | 见 §4-1（必须补） |
| 6 | 校准 | `model.py:112-122` 逐**物理片**×逐位散布特征（`FEATURES_PER_SLICE=MAIN+SUB−1=21`，`model.py:24`），`experiment.py:114-122` 用真实目标做 LMS，训练 8192 笔 × 6 轮（`experiment.py:496-498`） | `charge_model.py:91-108` 把 INL 投影到 65 个段/位特征上（本征投影→数学 0）；`charge_model.py:125-148` 再用"每码平均 `n_avg` 次、单次 σ=2.8 LSB20"的高斯投影造出有限样本残差 | 参考的残差来自**训练量+ADC2 量化+特征不完备**；我们的残差来自**人为假设的测量噪声** | 同一个"校准后残差"：参考 2% 档 **0.457 LSB20 = 0.436 ppm FS**（`task2/evidence/eight_native/sigma_2pct`，`endpoint_inl_peak_lsb20`），我们 0.2% 档 **0.287 ppm**（n_avg=64，`charge_model.py:147-148`）/ **0.574 ppm**（n_avg=16，`static.py:49`）。数量级可比，**物理来源完全不同** | 见 §4-2（必须补） |
| 7 | 残余 ADC2（在环） | `adctoolbox_calibration.py:119-133`：12 bit、`adc2_half_range_v=0.1`（`experiment.py:415`）→ LSB 48.83 µV；`experiment.py:69` 残差先量化再重构；`experiment.py:125-135` 20 bit 输出取码中点 | **无**：`adc.py:11-14` 直接对输入折算值做 22 bit 量化（`bits=22`） | 我们的"ADC2"被 22 bit 输出量化器替代，比参考细 26 dB | 实测（`§5.6`）：把参考配置的 ADC2 量化并进去 → 26.88 µV ⊕ 14.10 µV = 30.35 µV，SNDR **102.03 → 100.97 dB（−1.06 dB）**；若用我们 `params.py:33` 的 `LSB2=19.07 µV` → **−0.18 dB** | 见 §4-3（必须补） |
| 8 | INL/DNL 口径 | `inl_dnl.py:202` `dnl=interior/mean_width−1`，`:203-204` `inl=[0,cumsum(dnl)]`（端点），`:205,220` 另报 `best_fit`；`experiment.py:404-408` 同为端点法，字段名带口径 `:393`；`metrics.py:595` 最佳直线且 `:593` 声明"不代表码密度" | `charge_model.py:84-88` **最佳直线**算 INL，但 DNL 用**标称 LSB1** 归一；`static.py:17-21` 端点法（`lsb=v[-1]/(len−1)`）；两条路径并存（`static.py:45-57` 用 charge_model 的 INL，`static.py:23-37` legacy 用端点） | 参考**两个口径都给、字段名区分**；我们**混用且不自洽**（我们的 DNL 均值 ≠ 0，实测 +2.23 ppm，参考的均值宽度归一使 mean(DNL)≡0） | 实测（`§5.1`）：同一曲线端点峰值 **15.81 ppm** vs 最佳直线 **16.40 ppm**，差 0.59 ppm（3.7%）。所以"口径混用"本身只值 4%，**真正不可比的是量的定义**（10 bit 电压传输 vs 20 bit 码密度） | 见 §4-4（必须补）；短期至少把两条路径合并成一条并写清"最佳直线/端点" |
| 9 | FFT 指标 | 头条数字走 `experiment.py:138-156`：**矩形窗+整数 bin+单 bin 信号（`power[tone_bin]`）+ 其余全部计入噪声（含谐波）+ Nyquist 减半**；`adctoolbox_calibration.py:412-421` 用 `win_type="rectangular", side_bin=0` 交叉验证（`experiment.py:148-150`，atol=1e-5）。另一条更严的路径 `adi_model/metrics.py:416-505`（BH4 窗 + 时域 LSQ 去谐波 + coherent/NaN 标志）只被 `task1/experiments/run_effects.py:230`、`run_sndr_sweep.py:83` 使用 | `metrics.py:11` 矩形窗；`:18` 信号取基波 **±2 bin**；`:21-25` 前 10 次谐波；`:27-31` 噪声剔除 DC/基波/谐波；`:33-34` SFDR 只挖 DC+基波；`experiments.py:19` fin 吸附整数 bin；`:23` 对 dB 求种子均值 | 定义等价、实现细节 4 处不同 | 实测（`§5.3`）：单 bin vs ±2 bin **0.00 dB**；Nyquist/去 bin 1-2 的组合 **<0.03 dB**；22 bit → 20 bit **−0.04…−0.14 dB**；dB 域种子平均 vs 功率域 **0.000 dB**（8 seeds，std 0.051）。**唯一致命项**：无相干性保护——bin 偏 0.25 时 SNDR 掉到 **13.76 dB**、偏 0.50 时 **10.44 dB**（矩形窗要求是硬前置条件，参考至少有 `coherent` 标志 `metrics.py:504` 与 `fund_bin<16` 置 NaN `metrics.py:24,475-479`） | 补相干性断言 + 可靠性标志（S） |
| 10 | 重复采样相关性 | **没有 M 次平均机制**：`scheduler.py:6-7` `SLICE_COUNT=18, GROUP_SIZE=8` 是**每笔占用的片数**；相关性只以 CAAZ 配对出现：`run_joint_noise.py:293` `az_shared=np.repeat(az_independent[::2],2)`（同一笔内 ρ≡1）、`:292` fresh 逐笔独立、`:295` 保持误差 `0.75·az+5 µV`、`:89-95` 配对 `(even−odd)//2`、`:117-119` 输出 `az_pair_pearson`；最小版同构于 `run_caaz_effect.py:59-69` | `sources.py:16-24` 每个样本 M 次读，按**重复序号 m** 递推 AR(1)；`adc.py:49` 只对 RA 噪声施加；`params.py:22` ρ=0.61（`params.py:4` 自注"反解的推断值，不是实测"） | 机理完全不同（见 §2-4） | 实测（`§5.4`）：F_AR=0.3931（+1.71 dB）；把同样的首阶 ρ=0.61 改成**常数相关**（=参考的共享机理）F=0.6587 → **+0.88 dB**；全独立 F=1/8 → **+2.76 dB**；全公共 F=1 → **0.00 dB**。即 AR(1) 相对共享机理**高估 0.83 dB**，相对全独立**低估 1.04 dB** | 见 §2-4 / §4-5 |
| 11 | 交织调度 | `scheduler.py:105-126` 18 片池、8 采 + 8 转、LFSR 决定扫描起点；`run_effects.py:62-99` 校验片所有权/相位/样本号 | `adc.py:52-66` 每笔随机或顺序选 8 片，误差在 8 片内平均；`params.py:24-29` 18/8/增益 σ/skew | 参考的选片是**确定性数字状态机**并被逐笔断言校验；我们是独立随机抽样 | 一阶增益/失调/skew 足以定量级（`AUDIT.md:99-110`）；但"SKEW 只在斜率上取一阶均值"两边都缺采样网络 | 可延后；但**洗牌与 DEM 必须同源**，否则我们无法回答"DEM 关/开"对比 |
| 12 | 验证工艺（可验收性） | 独立两节点矩阵解互校 `charge_ref.py:102-137` + `tests/test_independent_charge.py:24,171`；质量守恒 `inl_dnl.py:357-359`（atol 5e-11）；单调性检查 `inl_dnl.py:375-382`（归档里 `negative_export_code_boundary_jumps=3754` **如实报出**）；与 adctoolbox 互校 `inl_dnl.py:404-405`；源码/产物 SHA 收据 `experiment.py:489-492` | `selftest.py:26-53` 4 项（纯正弦 DR、AR(1) 方差、AZ 抵消、理想权重 INL） | 我们自检覆盖"公式对不对"，参考覆盖"结果守恒/单调/互校/可复现" | 我们没有：码密度质量守恒、缺码计数、非单调边界计数、产物指纹 | 见 §4-4、§4-8 |

---

## §2 逐条回答

### §2-1 `charge_ref.py` 到底怎么算电荷/输出电压？我们的 `_vtop` 与它是否一致？不一致会不会改变 ppm 级结论？

**参考怎么算（三层，逐层可查）**

1. 边界条件写在模块头：采样时两个顶板节点**钳位为零**，放大时**主节点为理想虚地**，子节点浮置，桥保持连接，反馈电容从复位态开始（`charge_ref.py:1-5`）。即：采样相是"顶板强制归零"，不是"顶板预充到 Vin 后浮空"。
2. 闭式（`charge_ref.py:98-99`）：
   `β = Cb/(Cb + Σcs + Cpar)`，
   `C_F·v_R = Σ cm(wm−bm) + β·Σ cs(ws−bs)`。
   注意主节点电容的**全部**电荷增量都进 C_F，主节点寄生不出现在分母里——因为虚地电位恒为 0，寄生不参与电荷转移。
3. 独立矩阵解（`charge_ref.py:130-137`）：未知量 = 子节点电压 + 输出；`M[0,0]=Cb+Σcs+Cpar`、`M[0,1]=0`（主节点为 0 的显式实现）、`M[1,0]=Cb`、`M[1,1]=C_F`；`rhs=[Σcs(bs−ws), Σcm(wm−bm)]`；返回 `C_F·v`（C_F 是纯缩放，数值不影响 v_R）。闭式与矩阵解自洽（把 `v_sub` 代回即得 β 项）。
4. 实验里真正用的 `ChargePool.from_caps`（`model.py:131-140`）是闭式的推广：`nominal_c = GROUP_SIZE·ΣMAIN_WEIGHTS·unit_cap`（`:136`）、`span_over_c = 2·peak/nominal_c`（`:137`）、`β=Cb/(Cb+Σcs)`（`:138`，**丢掉 Cpar**）、`weight=[cm, cs[:,:-1]·β]·span_over_c`（`:139`）、`gain=Σcm/nominal_c`（`:140`）。残差写成仿射 `r=g·(x−Vlow)−b`（`model.py:142-144`）。

**我们的 `_vtop`**

`charge_model.py:52-55`：`num=(c·(bot−vin)).sum()+c127·(bot_term−vin)`，`return vin + num/(Σc+cp)`。
代数展开：`Vtop = [Σ c_i·bot_i + cp·vin]/(Σc+cp)`，即"顶板从 vin 起浮空、寄生接地、底板切轨"的**无源分压**；这是一个**没有虚地、没有子节点、没有桥**的单一顶板。8 片各自解一次再 `(ΣP−ΣN)/8`（`charge_model.py:63-82`）——这是**电压域求和**。

**四项逐项结论**

| 项 | 是否一致 | 依据 | 是否改变 ppm 结论 |
|:---|:---|:---|:---|
| termination 单位 | **结构一致、机理不同**：两边都"不贡献权重但加载节点"；参考另把 dummy 的**采样态**做成了特征（`model.py:104-109`），我们没有任何采样相 | `model.py:138-139` vs `charge_model.py:45-51,54` | 不改变（常数/每片增益被吸收）；但**堵死了采样扰动相关的任何结论** |
| Cp 处理 | **不一致**：参考主节点为虚地→cp 不出现（`charge_ref.py:132-134`）；我们 cp 进分母（`charge_model.py:53`） | 实测：cp 0→10%：INL 16.395→14.855 ppm，增益 1.0000→0.9091 | **不改 ppm 结论（≤1.6 ppm）**，但**增益错 9%**，且我们的"8 片电压求和 + 每片独立 cp"如果真实是共享顶板/虚地，就是把 cp 重复算了 8 次 |
| 差分归一化 | **不一致（我们多一层）**：参考完全单端（`charge_ref.py:70-99`），我们互补差分（`charge_model.py:74-82`）且 P/N 共用同一组 caps | 实测：单端 8 片求和 INL 峰 23.58 ppm（偶 19.36 / 奇 16.41），差分 = 16.40 ppm | **会**：16.4 ppm 是"偶阶被互补开关抵消后"的数；换独立双阵列 → 回到 ~23 ppm 量级（+44%） |
| 共模参考点 | **不一致**：参考的采样/转换电压全由调用方给（`charge_ref.py:53-64`）、码本强制从 −peak 起（`inl_dnl.py:455`）；我们 `VCM=2.5` 只有定义（`charge_model.py:22`），实际参考点是 0 | `VCM` 全工程唯一出现处即 `charge_model.py:22` | 不改 ppm；但任何涉及 VCM 的结论（开关 Vgs、比较器共模、底板扰动幅度）都不能从本模型出 |

**一句话**：`_vtop` 与 `charge_ref` 在"单位电容 → 权重 × 底板电压"这一层等价（同一电荷守恒、同一 1/ΣC 归一），差异在**边界条件（虚地 vs 无源分压）**与**汇总方式（电荷 vs 电压）**。前者只影响增益与 cp 的符号位置，**不改变 ppm 级 INL**；后者（单端 vs 互补差分）**会**把 INL 从 16.4 ppm 改到 23 ppm 量级。

### §2-2 参考的 INL/DNL 是端点还是最佳直线？我们混用会不会让两份数字不可比？

**参考：两个都给，且字段名写死口径。**
- `inl_dnl.py:202`：`dnl = interior/mean_width − 1`（**均值宽度归一**，因此 `mean(DNL) ≡ 0`）。
- `inl_dnl.py:203-204`：`inl = [0, cumsum(dnl)]`（**端点法**，起点强制 0）。
- `inl_dnl.py:205,220`：另算 `fit = inl − polyfit(直线)` 并报 `best_fit_inl_peak_lsb`，与 `endpoint_inl_peak_lsb`（`:219`）**并列**。
- task2 路径同样：`experiment.py:404-408` 的 `linearity()` 明确"INL 扣除端点直线"，字段叫 `endpoint_inl_peak_lsb20`（`:393`）。
- `adi_model/metrics.py:595` 的 `inl_from_mean_error` 用最佳直线，但 `:593` 明写"该名称不代表已完成逐码转换边界或码密度测试"。

**我们：混用，且其中一处内部不自洽。**
- `charge_model.py:84-88`：INL 用**最佳直线**（`np.linalg.lstsq([1, codes])`），但同一函数的 DNL 用**标称 LSB1**（`:88` `diff(v)/LSB1 − 1`）→ 实测 `mean(dnl_raw)=+2.23 ppm ≠ 0`，与"最佳直线 INL"不配对（参考用均值宽度归一，两者恒自洽）。
- `static.py:17-21`：**端点法**（`lsb=v[-1]/(len−1)`）。
- `static.run` 的 `inl_raw_ppm` 取自 `charge_model`（最佳直线，`static.py:56,74`），legacy 路径取自 `curves_binary`（端点，`static.py:46`）——两条路径的 ppm 会差 4%，`static.py:4` 已经用注释警告"不要混用"。

**量化后果（同一 pool、seed=7、σu=0.2%）**
- 端点（端点 LSB 归一，等价于参考的 `[0,cumsum]` 再扣端点直线）：峰值 **15.81 ppm**
- 最佳直线：峰值 **16.40 ppm**
- 差 **0.59 ppm = 3.7%**；DNL 两种口径完全相同（−14.13/+12.75 vs −14.13/+12.75 ppm）。

**结论**：混用只值 4%，**不足以让 16.4 与参考的 0.436 ppm 不可比**；真正不可比的是**量**——参考的 0.457 LSB20 是"20 bit 导出码密度 + 12 bit ADC2 + 冻结 LMS + 512 状态 DEM 平均"的结果（`task2/evidence/eight_native/sigma_2pct/summary.json`），我们的 0.287 ppm 是"10 bit 电压传输 + 线性投影 + 假设测量噪声 σ=2.8 LSB20、n_avg=64"的结果（`charge_model.py:125-148`）。**把这两行并排放进同一张表就是错的口径混用**，与端点/最佳直线无关。

### §2-3 SNR/SNDR/SFDR 逐项对比，可能带来多少 dB 偏差

参考实际存在**两条**指标路径，引用时必须说明是哪一条：

- **路径 B（头条数字用这条）**：`experiment.py:138-156`——矩形窗、`tone_bin` **单 bin** 作信号、`power[0]=power[tone_bin]=0`、`power[-1]*=0.5`、`SNDR=10log10(Psig/Σ其余)`、`SFDR=10log10(Psig/max(其余))`（**含谐波**）；并用 `_spectrum`（`adctoolbox_calibration.py:412-421`，`win_type="rectangular", side_bin=0`）互校到 1e-5（`experiment.py:148-150`）。绘图注释也写了"矩形窗"（`plots.py:133`）。
- **路径 A（更严，只用于 effect 实验）**：`adi_model/metrics.py:416-505`——可选窗（`:38-47`，默认 BH4）、时域 LSQ 去谐波得 `SNR`（`:455-466`）、`ENOB=(SNDR−1.76)/6.02`（`:491`）、`NSD=noise_rms/√(fs/2)`（`:492`）、`coherent` 标志（`:504`）、基波 bin<16 置 NaN（`:24,475-479`）、异常/越界**不自动剔除**（`:437-442`）。**归档 SNDR 不是这条路径算的。**

| 项 | 参考 | 我们 | 实测偏差 |
|:---|:---|:---|:---|
| 窗 | 矩形（`experiment.py:140`；`plots.py:133`） | 矩形 `metrics.py:11` | 0 |
| 相干条件 | `tone_bin` 整数（`run_effects.py:33-36,44-48`），A 路径有 `coherent` 标志 | `experiments.py:19` 吸附整数 bin，**无断言** | bin 偏 0.25 → SNDR **13.76 dB**；偏 0.50 → **10.44 dB**（`§5.3`）。这是唯一的"几十 dB 级"风险 |
| 信号带宽 | 单 bin（`:142`） | 基波 **±2 bin**（`metrics.py:18`） | **0.00 dB**（相干时 ±1/±2 bin 恰为 0） |
| DC | 去 `power[0]`（`:143`） | 去 bin 0,1,2（`metrics.py:28`） | **<0.03 dB**（丢掉 2/8192 噪声 bin） |
| Nyquist | `power[-1]*=0.5`（`:144`） | 不修正 | **<0.005 dB** |
| 谐波 | SNDR **含**谐波（无独立 SNR 字段）；SFDR 搜峰含谐波 | SNDR 拆成 `pnoise+pharm`（`metrics.py:25,31,38`）；SFDR 只挖 DC+基波（`:33-34`）→ 也含谐波 | 定义等价；差异仅在"Harm 与基波/DC 重叠"的边界情形，本配置（fin=164 bin，N=16384）不发生 → **0.00 dB** |
| 输出量化 | 20 bit 码中点重构（`experiment.py:125-135`） | 22 bit（`adc.py:11`） | **−0.04…−0.14 dB** |
| 残余 ADC2 | 12 bit/±0.1 V，**在环**（`adctoolbox_calibration.py:119-127`） | **完全没有** | 加上参考配置：**−1.06 dB**；用我们 `LSB2=19.07 µV`：**−0.18 dB** |
| 多 seed 平均 | 单次实现（`experiment.py:159-265`） | dB 域 4 seed 均值（`experiments.py:23`） | 8 seed 实测：dB 域 vs 功率域 **0.000 dB**，seed std 0.051 dB → 4 seed 标准误 0.025 dB |

**结论**：**定义层面两边只差 0.05 dB 量级**（窗相同、都含谐波、都只扣 DC+基波）；**真正会吃掉 1 dB 的是"我们根本没有在环 ADC2"**，而"会吃掉 90 dB 的是矩形窗的非相干误用"。任何对外引用必须连同"矩形窗 + 整数 bin + 含谐波 SNDR + 无 ADC2"一起写。

### §2-4 参考怎么处理重复采样（tracking/8×）的相关性？我们的 AR(1) 沿 m 递推在物理上对应什么？增益算高还是算低？

**参考根本没有"M 次重复平均"这个机制。**
- `scheduler.py:6-7`：`SLICE_COUNT=18`、`GROUP_SIZE=8`——8 是**每笔同时占用的物理片数**（8 片并行采样 + 8 片并行转换，`scheduler.py:105-126`）。
- 因此参考里没有"同一余差的 M 次读"，也就不需要 M 次之间的 ρ。它的"8×"收益走的是另一条路：**用 dither/DEM 随机化"哪个片/哪个位"**（`model.py:40-62,104-121`），把固定失配的静态误差变成跨状态的平均（归档 `effective_states=512`）。
- 参考**唯一**显式建模的相关性是 CAAZ 配对（M=2 的一类平均）：`run_joint_noise.py:293` `az_shared = np.repeat(az_independent[::2], 2)` —— 同一样本的两笔注入**同一个** AZ 值，即 ρ≡1；`:292` 的 fresh 噪声逐笔独立，即 ρ≡0；`:295` 另给一个"保持误差"档（`0.75·AZ + 5 µV`）；`:117-119` 直接把 `az_pair_pearson`、`az_pair_residual_ac_uv` 打出来作为可检验量。`run_caaz_effect.py:59-69` 是同一分解的最小实现（`caaz_ideal` 用 `az_e` 两次、`az_independent_odd` 用 `az_o`）。

**我们的 AR(1) 沿 m 递推在物理上对应什么。**
`x[:,m]=ρ·x[:,m−1]+√(1−ρ²)w_m`（`sources.py:21-23`）意味着：同一余差的 8 次读之间相关性按 `ρ^{|Δm|}` **指数衰减**，即一个一阶低通/一阶马尔可夫漂移。要让它成为可检验的物理命题，必须给出**重复间隔 T_r** 与**相关时间 τ**（ρ=e^{−T_r/τ}）；我们既没写 T_r（`params.py:21-22` 只有 M 和 ρ），ρ 又是"由 M_eff 反解"（`params.py:4` 自注）——**这是用一个被解释量去定义解释变量的循环**，无法被任何电路量检验。

对照参考的机理，物理上更可能的形态是**两项之和**：一次采样的公共失调（对 8 次读 ρ≡1，对应参考的 `az_shared`）+ 每次独立的新噪声（ρ≡0，对应 `fresh`）。这两者的方差占比才是有电路含义的参数（σ_common²/σ_total²）。

**算高还是算低：高。** 依据（`§5.4` 实测，同一噪声预算 kT/C 17.3 / RA 24.0 / AZ 9.7 / cmp 9.7 / ref 2.9 µV）：

| 机理 | F | M=1→8 的 ΔDR |
|:---|---:|---:|
| 全公共（ρ≡1，参考的 `az_shared`） | 1.000 | **+0.00 dB** |
| 首阶 ρ=0.61 但**常数相关**（常数相关项） | 0.659 | **+0.88 dB** |
| **我们的 AR(1) ρ=0.61** | **0.393** | **+1.71 dB** |
| 全独立（ρ≡0，参考的 `fresh`） | 0.125 | **+2.76 dB** |

即：同样是"首阶相邻相关 0.61"，把相关性从"AR(1) 衰减"改成"8 次全共享"（这才是共享失调/AZ 的形态），增益从 +1.71 dB 掉到 **+0.88 dB**——**我们高估 0.83 dB**。反过来若真实是逐次独立，则我们**低估 1.04 dB**。所以这个数的**不确定区间由 0 到 +2.76 dB，宽度与效应本身同量级**；+1.71 dB 只是"ρ=0.61 反解后的自洽值"，不是物理结论。

### §2-5 参考有、我们完全没有的效应（按影响排序）

| # | 效应 | 参考证据 | 我们的状态 | 对结论的影响 | 判级 |
|:--|:---|:---|:---|:---|:---|
| 1 | **逐状态开关：dither 字 + DEM + 每状态仿射残差** | `model.py:40-62`（6 bit 字→8 slot 底板掩码）、`:85-101`（扰动偏移粗判决）、`:104-121`（每状态特征）、`:142-144`（每状态 gain/base）；`experiment.py:189-192` | `charge_model.py:58-82` 一码一条固定曲线，无状态维度 | 直接决定"DEM 收益/状态离散"这一整类结论；参考归档 512 状态、状态离散中位 0.936 µV（≈0.09 ppm FS） | **必须补（L）** |
| 2 | **校准的真实来源：可观测量 LMS + 有限训练量** | `model.py:112-122`（逐片×逐位 21 列/片）、`experiment.py:114-122`（LMS）、`:496-498`（8192 笔×6 轮） | `charge_model.py:125-148` 假设 σ_meas=2.8 LSB20、n_avg | 我们的"0.287 ppm"是假设值；参考的 0.436 ppm@2% 是训练量决定的值。两者不能互相印证 | **必须补（M）** |
| 3 | **残余 ADC2 在环量化（12 bit/±0.1 V）** | `adctoolbox_calibration.py:119-133`、`experiment.py:69`、`:415` | 22 bit 输出量化（`adc.py:11`） | **−1.06 dB**（参考配置）或 −0.18 dB（我们的 LSB2）；也是参考 104 dB 天花板的主因（14.1 µV vs 104 dB 需要的 14.9 µV） | **必须补（S）** |
| 4 | **码密度 INL/DNL：质量守恒 + 缺码计数 + 非单调边界** | `inl_dnl.py:197-222, 357-359, 375-382`；`experiment.py:394`（`zero_width_codes`）；归档 `negative_export_code_boundary_jumps=3754` 如实报出 | 只有 `diff(v)/LSB1`（`charge_model.py:88`）；无守恒、无缺码、无非单调计数 | 20 bit 级 INL/缺码声称的**唯一合法路径**；我们的 DNL 连 mean=0 都不满足 | **必须补（M）** |
| 5 | **采样相（底板采样态、CDS 特征 `sub − sampled`）** | `model.py:104-109`；`decode` 的 8 slot 采样底板掩码 `model.py:49-62` | `_vtop` 只有转换相；`vin` 只作为统一的电荷参考（`charge_model.py:54`） | 底板扰动（dither 的作用量）在我们模型里不存在，因此"dither 有效/无效"无法回答 | **必须补（M）** |
| 6 | **前级增益估计/校准（两参考点 + flags 拟合 + 强制码）** | `experiment.py:73-111`（`_calibrate_gain`、`forced_gain_code`、`gain_reference_span`） | 增益硬编码 1.0（`adc.py:64` 交织里 `g=1+ε`；`charge_model` 里被拟合吸收） | 影响 interstage gain error 类结论（增益 50 ppm → DR 96.78 dB，`AUDIT.md:110`），但量级可先按解析估 | 可延后（S） |
| 7 | **交织调度的物理约束（片所有权/相位/每笔断言）** | `scheduler.py:105-126`；`run_effects.py:62-99` 逐笔断言 ownership/phase/sample_id | `adc.py:59-63` 随机/顺序取 8 片，无所有权、无相位 | 我们的一阶 gain/offset/skew 足够定量级；但无法声称"与 RTL 一致" | 可延后（M） |
| 8 | **验证工艺：独立矩阵解互校、质量守恒、SHA 收据、第三方库互校** | `charge_ref.py:102-137`+`tests/test_independent_charge.py:171`；`inl_dnl.py:357-359,404-405`；`experiment.py:489-492` | `selftest.py` 4 项公式自检 | 决定"这个数能不能被验收"；不影响数值本身 | 可延后，但 #1 落地前应先建互校（S） |

---

## §3 能声称 / 不能声称

**能声称（每条都必须连同前提一起写）**

1. **在"同一 10 bit DAC1 阵列 + 互补差分开关 + 单位电容相对失配 σu=0.2% + 无 DEM/dither + 单一开关状态"前提下**，DAC1 静态 INL 峰值为 **16.4 ppm FS（最佳直线口径）/ 15.8 ppm FS（端点口径）**，DNL 为 **−14.1/+12.7 ppm FS**。
   *依据*：`charge_model.py:58-88`；重算见 §5.1；单端 23.58 ppm 的偶/奇分解见 §5.2。
2. **在"校准只由 8 段增益 + 56 个段内位权特征张成、且权重估计残差等效为 σ=2.8 LSB20/√n_avg"的假设下**，校准后 DAC1 残差为 **0.287 ppm（n_avg=64）/ 0.574 ppm（n_avg=16）**。这是**假设下的数值**，不是 LMS 仿真结果。
   *依据*：`charge_model.py:125-148`；`static.py:43,49` 与 `charge_model.py:156-163` 的 n_avg 默认值分别是 16 与 64，两者不一致（见 §4-6）。
3. **在给定 5 项热噪声预算（17.3/24.0/9.7/9.7/2.9 µV，`params.py:15-19`）且 RA 相关因子 F=0.393 时**，M=8 的 DR = **102.0 dB**（相对 M=1 的 +1.71 dB 依赖 ρ=0.61 的 AR(1) 假设）。
4. **指标口径**：我们的 `metrics.py` 与参考头条口径（矩形窗、整数 bin、单/±2 bin 信号、SNDR 含谐波、SFDR 含谐波）**在同一数据上实测差 <0.05 dB**，因此两边采用同一口径的数字可以直接对比。
   *依据*：§5.3 实测。

**不能声称**

1. **不能声称"校准后 SNDR 102.0 dB 就是噪声底"**。缺三项：在环 ADC2 量化（−0.18…−1.06 dB）、DAC1 后校准残差的真实谱（我们现在注入的是**随机符号白包络** `charge_model.py:161-163`，不是 LMS 残差）、DEM 状态平均（参考 512 状态、状态离散 0.09 ppm 量级）。
2. **不能声称"8× 只涨 +1.71 dB"是物理结论**。它是 ρ 的反解结果；同首阶 ρ 的共享机理给 +0.88 dB，全独立给 +2.76 dB（§5.4）。
3. **不能声称"与参考实现的 INL 一致/可比"**。0.436 ppm@σ=2%（20 bit 码密度 + 12 bit ADC2 + 冻结 LMS + 512 状态 DEM，`task2/evidence/eight_native/sigma_2pct`）与 0.287 ppm@σ=0.2%（10 bit 电压传输 + 线性投影 + 假设测量噪声）**不是同一个量**，并排放就是错的口径混用。
4. **不能声称"未校准 SNDR 94.6 dB 是电路的未校准失真"**。它是把 DAC1 的**一阶粗量化码**索引到的静态 INL 曲线作为加性误差注入（`adc.py:33-41`），等价于：单状态、无 DEM、无 dither、二阶以后不复现、无 DAC2/冗余。参考同一失配档下"关 DEM、未校准"的 SNDR 是 **51.9–55.1 dB**（`task2/evidence/eight_native/sigma_2pct`），差这么大不是模型好坏，而是**量的定义不同**。
5. **不能声称任何共模/VCM 相关结论**：`VCM=2.5` 只在 `charge_model.py:22` 定义、全文未使用。
6. **不能声称"仿真通过 = 设计通过"**：settling / 参考纹波 / jitter / 亚稳态 / DAC2 / 冗余 我们都缺（`AUDIT.md:112-126`），参考实现也缺（`inl_dnl.py:712` 的 scope 明确写 "no thermal noise, no timing skew"）。两边的行为级都不能替代后仿与硅实测。

**我们现在最可能错的一个数字：`M=1→8 只涨 +1.71 dB`。**
理由三条：(a) ρ=0.61 是反解值，`params.py:4` 自己标注"不是实测"；(b) 相关方向写在 `m` 轴上（`sources.py:21-23`），而参考实现给出的物理形态是"ρ≡1 的共享项 + ρ≡0 的独立项"（`run_joint_noise.py:292-295`），两者在 M=8 上不等价：同首阶 ρ=0.61 时 AR(1) 给 +1.71 dB、共享形态给 **+0.88 dB**；(c) 该数字的全部可能取值跨 **0…+2.76 dB**，误差与效应同量级，并且它同时抬着所有绝对值（DR 100.31…103.07 dB）。**紧随其后的是 102.0 dB 这个绝对值**——它还额外漏了 ADC2 量化的 −1.06 dB。

---

## §4 待补清单（优先级 + 规模）

| 优先级 | 待补项 | 交付判据（可验收） | 规模 |
|:--|:---|:---|:--|
| P0 | **ADC2 在环量化**：在 `adc.py` 的输出路径上加 12 bit/±0.1 V 残差量化 + 中点重构，保留"无 ADC2"作为对照 | 同一输入下 102.03 → 100.97 dB（参考配置）；误差谱中 48.83 µV 台阶可见；提供 `adc2_rejected` 计数 | **S** |
| P0 | **相干性断言 + 可靠性标志**：`fft_metrics` 里断言 `fin·N/fs` 距整数 <1e-8，否则报错；基波 bin<16 时谐波类指标置 NaN（对齐 `metrics.py:24,475-479,504`） | 故意传 0.25 bin 偏移必须抛错而不是返回 13.76 dB | **S** |
| P0 | **口径统一**：删掉 `static.py:17-21` 与 `charge_model.py:84-88` 的并行口径，单一函数同时返回 `endpoint_*` 与 `best_fit_*` 字段；DNL 改均值宽度归一使 `mean(DNL)≡0` | 同一 pool 下 `mean(dnl)<1e-12`；两类 INL 字段名显式带口径 | **S** |
| P1 | **逐状态开关（dither + DEM）**：给 DAC1 加 6 bit 字 → 8 slot 底板掩码 + 每状态仿射残差，输出均值曲线与状态离散 | 报出 `state_count`、`midpoint_state_spread_median_rms_v`；DEM 开/关的 INL 与 SNDR 对比各一组 | **L** |
| P1 | **校准改真 LMS**：用可观测量（逐片×逐位）做最小二乘/LMS，训练笔数扫描，残差随训练量下降 | 复现"残差 ∝ 1/√n"并给出 8192 笔×6 轮的收敛曲线；能回答"0.29 ppm 需要多少训练笔数" | **M** |
| P1 | **码密度 INL/DNL**：均匀斜坡/区间积分、质量守恒到 1e-11、缺码计数、非单调边界计数 | 报 `mass_balance_error_v`、`zero_width_codes`、`negative_boundary_jumps`；20 bit 导出 | **M** |
| P2 | **采样相 + CDS 特征**（`sub − sampled`），打通"dither 到底改了什么" | 关闭/开启采样相扰动的对照实验；能给出底板扰动到输入折算的传递系数 | **M** |
| P2 | **相关性模型替换**：把 `tracking_noise` 的 AR(1) 换成"共享项（ρ≡1）+ 独立项（ρ≡0）"两参数模型，并给出重复间隔 T_r 与 τ 的对应表；保留 AR(1) 作为敏感性对照 | 输出 F 的三点区间（共享/AR1/独立）与对应 DR 区间，而不是单点 | **S** |
| P3 | **增益估计/校准 + 交织调度物理约束** | 与参考 `_calibrate_gain` 同构的两参考点估计；片所有权逐笔断言 | **M** |
| P3 | **验收工艺**：独立矩阵解互校、与外部库互校、产物 SHA 收据 | 一次运行的收据里含源码/产物指纹与互校断言结果 | **S** |

---

## §5 复核命令

全部为只读调用，不写任何 `.py`，不修改现有文件。工作目录：`/Users/zhaoyi/WorkBuddy/pipelinedsar工作站/20b10m`。

**§5.1 静态数字 + 端点/最佳直线差**
```bash
cd /Users/zhaoyi/WorkBuddy/pipelinedsar工作站/20b10m && python3 -c "
import numpy as np, sys; sys.dont_write_bytecode=True
from model.charge_model import dac1_curves, LSB1
c=dac1_curves(sigma=0.002,seed=7); v=c['v']; codes=c['code']
print('INL best-fit ppm', abs(c['inl_raw']).max()*1e6/1024)
print('DNL min/max ppm', c['dnl_raw'].min()*1e6/1024, c['dnl_raw'].max()*1e6/1024)
print('mean(DNL) ppm', c['dnl_raw'].mean()*1e6/1024)
lsb=(v[-1]-v[0])/(len(v)-1); ep=(v-v[0])/lsb-np.arange(len(v))
print('INL endpoint ppm', abs(ep).max()*1e6/1024)"
```
期望：`16.395 / −14.128, +12.749 / +2.229e-6 / 15.808`

**§5.2 单端偶/奇分解（说明 16.4 ppm 依赖互补假设）**
见 §5.1 之后的 `_vtop` 累加脚本（本次审计实际执行版）：单端 8 片求和 INL 峰 **23.58 ppm**，偶 **19.36**、奇 **16.41**，差分 **16.40**。

**§5.3 指标口径一致性 + 非相干敏感性**
```bash
python3 -c "
import numpy as np, sys; sys.dont_write_bytecode=True
from model.adc import simulate; from model.metrics import fft_metrics
from model.params import P
fs,n=P.fs,P.n
for off in (0.0,0.25,0.5):
    fin=(164+off)*fs/n; x,_=simulate(fin,fs=fs,n=n,seed=301)
    m=fft_metrics(x,fs,fin); print(off, round(m['SNDR_dB'],2), round(m['SFDR_dBc'],2))"
```
期望：`0.0 → 102.07/132.26`；`0.25 → 13.76/21.56`；`0.50 → 10.44/17.59`
（口径对比：同数据"参考单 bin 口径"重算得 102.07/102.07，20 bit 中点重构后 **101.93**）

**§5.4 F 与 ADC2 量化影响**
```bash
python3 -c "
import numpy as np
M,rho=8,0.61
F_ar=1/M+2/M**2*sum((M-k)*rho**k for k in range(1,M)); F_c=rho+(1-rho)/M
ktc,cmp_,az_,rf,ra=17.3,9.7,9.7,2.9,24.0
t=lambda F: np.sqrt(ktc**2+cmp_**2+az_**2+rf**2+ra**2*F)
for F,n in ((F_ar,'AR1'),(F_c,'const'),(1/8,'indep'),(1.0,'shared')):
    print(n,round(F,4),'%+.2f dB'%(20*np.log10(t(1)/t(F))))"
```
期望：`AR1 0.3931 +1.71` / `const 0.6587 +0.88` / `indep 0.125 +2.76` / `shared 1.0 +0.00`

**§5.5 cp 灵敏度**
```bash
python3 -c "
import numpy as np, sys; sys.dont_write_bytecode=True
from model.charge_model import Pool, dac1_curves, C_UNIT, UNITS, LSB1
for f in (0.0,0.01,0.10):
    p=Pool.make(sigma=0.002,seed=7); p.cp=f*C_UNIT*UNITS
    c=dac1_curves(pool=p)
    print(f, round(abs(c['inl_raw']).max()*1e6/1024,3), round(np.polyfit(c['code'],c['v'],1)[0]/LSB1,4))"
```
期望：`0.0 → 16.395 / 1.0000`；`0.01 → 16.227 / 0.9901`；`0.10 → 14.855 / 0.9091`

**§5.6 读参考归档（不复制代码，只核对字段）**
```bash
python3 -c "
import json
d=json.load(open('/tmp/ref_20b10mtask/task2/evidence/eight_native/sigma_2pct/summary.json'))
g=d['groups']['fig21_dem']
print({k:(g['linearity']['on']['lms'][k]) for k in ('endpoint_inl_peak_lsb20','dnl_min_lsb20','dnl_max_lsb20','zero_width_codes')})
print({k:(g['tone']['on']['lms'][k]) for k in ('sndr_db','sfdr_dbc')})
print('LSB20',d['output_lsb20_v'],'adc2',d['calibration']['adc2_bits'],d['calibration']['adc2_half_range_v'])"
```
期望：`endpoint_inl_peak_lsb20=0.4903`、`zero_width_codes=0`、`sndr=103.974`、`sfdr=128.554`、`LSB20=9.5367e-06`、`adc2=12 / 0.1`
（0.4903 LSB20 ÷ 2^20 × 1e6 = **0.468 ppm FS**，与我们的 0.287 ppm 不是同一个量）

**§5.7 复现全部自检**
```bash
python3 -m model.selftest          # 4 项：纯正弦 DR / AR(1) 方差 / AZ 抵消 / 理想权重 INL
```

---

### 附：本次审计未覆盖 / 证据不足项

| 项 | 缺什么 |
|:---|:---|
| 参考的 `MAIN_WEIGHTS=(2,)*15+(1,1)`（和 32 单位当量）、`SUB_WEIGHTS=(8,4,2,1,1)`（和 16，含 1 个 dummy）、`GROUP_SIZE=8`（`run_effects.py:31-32`、`scheduler.py:7`）是否与我们 8×128 单位拓扑"等价" | 只能判定"结构同构（unary 片 + 片内二进制 + 1 个 dummy 终止单位）"，单位数不同：参考每片 32+16=48 单位当量（8 片 384），我们每片 128（8 片 1024），且参考有桥衰减 β≈1/17（`model.py:138`）。**拓扑等价性现有证据不足**，需要主理人给架构预算表才能判定能否互校 |
| 参考 104 dB 天花板的逐项归因 | 本报告只做了量级核对（12 bit ADC2 量化 14.1 µV vs 104 dB 需要 14.9 µV），**未做逐项功率分解**；要确认需单独跑参考的 `_metrics` 分量 |
| 我们 `LSB2=19.07 µV`（`params.py:33`）的电路来源 | `params.py` 未标来源，与参考 ±0.1 V/12 bit（48.83 µV）差 2.6×，需主理人确认 ADC2 档位 |
| 交织 skew/增益在真实采样网络下的高阶效应 | 两边都只有一阶模型（参考 `ExperimentConfig.skew_s=5e-12` 亦未在 task2 的 tone 里使用），**无法互校** |
