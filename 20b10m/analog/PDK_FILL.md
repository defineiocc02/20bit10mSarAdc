# PDK 模型填充清单（PDK_FILL）

> 基线：**BL-v1-draft** ｜ 作者：analog-circuit-designer-2（任务 T02）
> 对象：`20b10m/analog/netlist/pdk_models.scs`（当前 **21 行、全是注释、include 被注释掉**，`:22` 只有 `simulator lang=spectre`、`:23` 是注释掉的 include）
> 原则：**本文件不给出任何模型名、器件参数、section 值**。凡是仓库里没有的，一律写 `TODO(PDK)`。理由见 `pdk_models.scs:19` 原文：
> > "不许为了'先跑起来'用理想 MOS 代替；那会把 L1 结论变成假结论。"
> 本文件的作用是：**把"填什么"变成一张可勾选的表**，并把"从 PDK 的哪个文件取"变成可执行步骤。

---

## 1. 现状：为什么 28 个 .scs 一个都跑不了

| 事实 | 证据 |
|:---|:---|
| `pdk_models.scs` 里没有任何模型定义，`include` 是注释 | `netlist/pdk_models.scs:22-23` |
| `build.scs` 里 `include "pdk_models.scs"` 也是注释 | `netlist/build.scs:8` |
| 所有块网表直接写 `M0 (d g s b) nch5 w=.. l=..` 这类**未定义的模型名** | 见 §2 用量表，共 105 条 |
| 因此 `spectre -f build.scs` 会在第一条 M 语句报 unknown model | 推断（未实跑，缺 PDK） |
| `check_hier.py` 不解析模型，所以"通过" | `check_hier.py:44-77` |

**结论**：模拟侧唯一的口径是 `nch5 / pch5 / nch18 / pch18` 四个别名（`MANIFEST.md:11`、`netlist/README.md:23`、`pdk_models.scs:3-5`）。只要这四个别名解析成功，23 个块网表**全部**具备进入仿真的条件（剩下的缺的是激励/判据/连接缺陷，见 `BLOCK_CONTRACTS.md` §6）。

---

## 2. P0：必须填的 4 条 MOS 映射（不填 = 0 个仿真可跑）

### 2.1 用量表（按别名×文件，`grep -c` 可复现）

| 别名 | 次数 | 语义（网表注释口径） | 用在哪些文件 |
|:---|:---:|:---|:---|
| `nch5` | **26** | 5 V 厚栅 NMOS | `Cmp1.scs`(2) `CmpQ2.scs`(2) `RefBuffer.scs`(3) `SdacSlice.scs`(3) `SwSample5v.scs`(5) `TriLevelDrv.scs`(8) `common_cells.scs`(3) |
| `pch5` | **21** | 5 V 厚栅 PMOS | `Cmp1.scs`(2) `CmpQ2.scs`(2) `RefBuffer.scs`(4) `SdacSlice.scs`(3) `SwSample5v.scs`(4) `TriLevelDrv.scs`(8) `common_cells.scs`(2) |
| `nch18` | **33** | 1.8 V 薄栅 NMOS | `AmpA2.scs`(3) `BiasGen.scs`(4) `Cmp1.scs`(3) `Cmp2.scs`(5) `CmpQ2.scs`(3) `FiaA1.scs`(4) `FiaA3.scs`(2) `RaMux.scs`(4) `common_cells.scs`(3) `clk_rx.scs`(2) |
| `pch18` | **25** | 1.8 V 薄栅 PMOS | `AmpA2.scs`(2) `BiasGen.scs`(2) `Cmp1.scs`(2) `Cmp2.scs`(2) `CmpQ2.scs`(2) `FiaA1.scs`(4) `FiaA3.scs`(2) `RaMux.scs`(4) `RingAmp3.scs`(1) `common_cells.scs`(2) `clk_rx.scs`(2) |
| **合计** | **105** | 与源文件 M 语句数一致 | 15 个文件 |

> 展开到层次后（`SdacSlice` ×18、`Cmp1` ×15 在 `CmpCoarse4b` 内）晶体管数量是另一个量级，但 **PDK 只需要 4 条映射**，与实例数无关。

### 2.2 四条映射的填写卡（**每条都要填满，留空即未完成**）

| 项 | `nch5` | `pch5` | `nch18` | `pch18` |
|:---|:---|:---|:---|:---|
| ① PDK 中真实的模型/subckt 名 | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` |
| ② 所在文件（绝对路径，**不复制进仓库**） | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` |
| ③ 所在 section（tt/ss/ff 之外的工艺角名以 PDK 为准） | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` |
| ④ 器件类型（core / IO / DNW / 高压） | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` |
| ⑤ 支持的最小/最大 W、L（网表用到 L=0.5u 与 L=0.18u） | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` |
| ⑥ 是否 4 端（d g s b）可实例化 | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` |
| ⑦ 是否要求 `ad/as/pd/ps/nf` 等必需参数（**网表只给 w/l**） | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` |
| ⑧ 模型版本 / PDK 版本号 | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` | `TODO(PDK)` |

**⑦ 是本轮最容易踩的坑**：105 条 M 语句**只带 `w=` 和 `l=`**（例如 `common_cells.scs:15` `w=2u l=0.18u`）。若 PDK 模型把 `ad/as/pd/ps` 或 `nf` 声明为必需，会在**每一条**上失败。三种处置（按优先级）：
1. 选一个**不要求**这些参数的模型/角点（很多 PDK 的 `models` 视图给默认值）；
2. 在 `pdk_models.scs` 的别名包装层里用 `params:` 给默认（见 §4 选项 B）；
3. 改 105 条网表 —— **最差**，且违反"不改网表"的约束。

### 2.3 怎么从 PDK 找到这四条（**可执行步骤，不猜名字**）

```bash
# 0) 先问 PDK 管理员要三样：模型根目录、器件清单（Device List / 工艺说明）、
#    以及"5 V 与 1.8 V 器件分别叫什么"的一句话答复。下面只是自助路径。

PDK_ROOT=/path/to/pdk            # TODO(PDK)：替换为真实路径

# 1) 找模型入口文件（Spectre 侧）
ls -R "$PDK_ROOT" | grep -iE 'models?|spectre|\.scs$|\.lib$' | head -50

# 2) 看是"library/section"式还是"每角一文件"式
grep -rn -E '^\s*(library|section|endlibrary)\b' "$PDK_ROOT" --include=*.scs --include=*.lib | head -40

# 3) 列出所有可实例化的器件（model 或 inline subckt 定义）
grep -rn -E '^\s*(model|inline\s+subckt|subckt)\s+\S+' "$PDK_ROOT" \
     --include=*.scs --include=*.lib | grep -viE 'parasitic|dummy' | head -80

# 4) 把候选按"5 V / 1.8 V"分组：看模型定义附近的注释、或 PDK 器件清单里的 VDS 额定
grep -rn -iE '5v|5\.0|1p8|1\.8v|vds|vgs' "$PDK_ROOT"/models* 2>/dev/null | head -40
```

**判定规则（写死在这里，避免后人误判）**：
- 5 V 器件的判据：PDK 器件清单里 **VDS 额定 ≥ 5.5 V**、栅氧厚度/`tox` 明显大于 1.8 V 器件。**不要**凭名字里的 `_5`、`hv`、`io` 猜——同名不一定同额定。
- 1.8 V 器件的判据：**VDS 额定 ≥ 1.98 V**，且允许 `L=0.18u`。
- 必须能 4 端实例化（`d g s b`）；若 PDK 只给 3 端，需要在别名层补 bulk 节点。
- 每个角点（tt/ss/ff，以及 PDK 有的话 fs/sf）都要能取到，否则后续 PVT 全断。

---

## 3. P1：电容 / 电阻（**不阻塞首个 tb，但阻塞所有"精度类"结论**）

### 3.1 现状：全部是 Spectre 内建理想元件

| 元件 | 语句形式 | 次数 | 例子 |
|:---|:---|:---:|:---|
| 电容 | `C0 (a b) capacitor c=27f` | 33 | `common_cells.scs:10`（`c=CUNIT`）、`SdacSlice.scs:20-27`（27f…1728f）、`Dac2_11b.scs:19-54`、`CincCouple.scs:9-10`（1.0p）、`DynRefBuf.scs:8-9`（300p/60p）、`SwSample5v.scs:11`（1.7p）、`RefBuffer.scs:18`（2p） |
| 电阻 | `R0 (a b) resistor r=1k` | 33 | `CmpCoarse4b.scs:13-29`（16×1k 梯）、`BiasGen.scs:17-18`、`RefBuffer.scs:9-22`、`RingAmp3.scs:14-15`（1G）、`clk_rx.scs:8-9` |

`capacitor` / `resistor` 是 Spectre **内建原语**，**不需要 PDK 模型**，所以：
- ✅ **首个 DC/瞬态 tb 可以跑**（P0 填完即可）
- ❌ 但它们是**理想、无失配、无温度系数、无电压系数、无寄生**的 → 以下结论**全是假的**：
  - DAC1/DAC2 的 INL/DNL（依赖单位电容失配 σ_u，`ARCH_V2.md:41` 用 σ_u=0.1%）
  - 27 fF 单位电容的**物理可实现性**（MIM 密度 1–2 fF/µm² 区间，`ARCH_V2.md:319`：27 fF → 13.5–27 µm²/单位，×1039 单位是面积预算的关键）
  - `CmpCoarse4b` 的 1 kΩ 梯**绝对值/匹配**（16 个电阻决定 15 个比较器阈值，失配直接决定粗量化误差）
  - `RingAmp3` 的 1 GΩ 弱定义共模、`RefBuffer` 的 R_out ≈20 Ω（`RefBuffer.scs:21-22` 用 100 kΩ/100 kΩ 分压、`:9-10` 反馈 100 kΩ/100 kΩ，R_out 由 `Mpass` 的 gm 与环路增益决定，与"20 Ω"没有任何关系）
  - `DynRefBuf` 的 300 pF 去耦（`ARCH_V2.md:182` 把"300 pF"当结论，但它现在是理想电容）

### 3.2 需要补的映射（P1，**同样不许编名字**）

| 项 | 需要什么 | 从 PDK 哪里取 | 何时必须 |
|:---|:---|:---|:---|
| `CUNIT` = 27 fF 的物理实现 | MIM（或 MOM）单位电容模型 + 密度/失配参数 | PDK 的 `cap`/`mim`/`mom` 模型段；密度看 PDK 工艺说明的 "MIM capacitance per area" | 出 INL/DNL、面积复核前 |
| 16×1 kΩ 梯 | 高阻/低阻 poly 或 well 电阻模型（按匹配需求选） | PDK 的 `res` 段（通常有 `rpo`/`rppoly`/`rnwell` 多档） | 粗量化修调/失配分析前 |
| `R_buf` 20–50 Ω、`Rd=20` | 同上（可能要指状并联 + 金属电阻） | 同上 | 参考建立/纹波仿真前 |
| 去耦 300 p/60 p | MOS 电容或 MOM（`DynRefBuf.scs:7` 注释"L1 定"） | PDK 的 MOS-cap / MOM 模型 | 参考 droop 仿真前 |
| 自举电容 1.7 pF | MIM 或 MOM | 同上 | `SwSample5v` 的 Ron 线性度前（可先用理想电容过渡，但要标注） |

> **过渡策略（建议，但必须打标签）**：P1 未就绪时，允许用理想 R/C 跑**功能/时序**台架，但报告里必须写 `CUNIT=ideal 27f, 无失配`，且**不得**据此宣称 INL/DNL/面积/噪声达标。这与 `pdk_models.scs:19` 的禁令不冲突——禁的是"用理想 MOS 顶替"，R/C 的过渡要显式标注。

---

## 4. 模板骨架（**保留 TODO，不填任何数字/名字**）

> 直接替换 `netlist/pdk_models.scs` 的内容即可（本文件**不**替你写，因为写错一个字符就是假结论）。两种结构二选一，**选 B 更稳**（别名与 PDK 解耦）。

### 选项 A：PDK 模型名恰好就叫 `nch5/pch5/nch18/pch18`

```spectre
// pdk_models.scs —— PDK 模型映射
// 状态：TODO(PDK) 未填。填完把下面三行的 TODO 全部消掉，并勾掉 §6 的自检清单。
simulator lang=spectre

// ---- PDK 入口（三选一，按 PDK 打包方式）----
// A1) library/section 式：
// include "TODO(PDK)/models.scs" section=TODO(PDK_corner)
// A2) 每角一文件：
// include "TODO(PDK)/models_TODO(PDK_corner).scs"
// A3) 已 include 过更高层 models.lib：
// include "TODO(PDK)/models.lib"

// ---- 别名核对（若 PDK 名不叫 nch5 等，请改用选项 B）----
// 断言式自检：下面四条必须能解析到 model 或 inline subckt
//   期望：nch5  = 5 V NMOS, VDS 额定 TODO(PDK)
//   期望：pch5  = 5 V PMOS, VDS 额定 TODO(PDK)
//   期望：nch18 = 1.8 V NMOS, L_min 0.18u
//   期望：pch18 = 1.8 V PMOS, L_min 0.18u

// ---- 全局选项（按项目口径，一般不需改）----
// simulator lang=spectre
// parameters tnom=TODO(PDK)   // 标称温度，PDK 默认即可，勿自造
```

### 选项 B：PDK 名不同 → 用 subckt 别名包装（**推荐**）

```spectre
// pdk_models.scs —— PDK 模型映射（别名包装版）
// 状态：TODO(PDK) 未填。下面 4 个 subckt 的器件名、参数全部是 TODO。
simulator lang=spectre

// ---- 1) 先引入 PDK ----
// include "TODO(PDK)/models.scs" section=TODO(PDK_corner)"   // 或 A2/A3 形式

// ---- 2) 再定义四个别名 ----
// 注意：网表只给 w / l；若 PDK 要求 ad/as/pd/ps/nf，就在这里给默认值或加参数
//       TODO(PDK)：确认是否需要下面 params: 里的可选参数
subckt nch5 d g s b params: w=1u l=1u
//    M0 (d g s b) TODO(PDK_5V_NMOS) w=w l=l
//    TODO(PDK)：若必需，补 nf/ad/as/pd/ps
ends nch5

subckt pch5 d g s b params: w=1u l=1u
//    M0 (d g s b) TODO(PDK_5V_PMOS) w=w l=l
ends pch5

subckt nch18 d g s b params: w=1u l=1u
//    M0 (d g s b) TODO(PDK_1V8_NMOS) w=w l=l
ends nch18

subckt pch18 d g s b params: w=1u l=1u
//    M0 (d g s b) TODO(PDK_1V8_PMOS) w=w l=l
ends pch18

// ---- 3) 可选：P1 的 R/C 别名（现在网表直接用内建原语，可暂不建）----
// subckt rpoly a b params: r=1k w=1u l=1u
//    R0 (a b) TODO(PDK_RES) r=r w=w l=l
// ends rpoly
// subckt cmim a b params: c=27f w=1u l=1u
//    C0 (a b) TODO(PDK_MIM) c=c w=w l=l
// ends cmim
// ---- 4) P2（当前完全不用，禁止提前填）----
// bandgap 用的 BJT/齐纳：TODO（BiasGen 的 bandgap 定性为"需自建/外供"，见 MANIFEST.md:23）
```

**为什么推荐 B**：①PDK 换版本时只改这一处；②能把 `ad/as/pd/ps` 默认值集中处理；③`nch5` 之类的名字如果撞上 PDK 内部名，包装层能规避冲突。

---

## 5. 分级与"不阻塞/阻塞"边界

| 级别 | 内容 | 填完能做什么 | 不填会怎样 |
|:---|:---|:---|:---|
| **P0** | `nch5 pch5 nch18 pch18` + 一个可用角点 | 全部 23 个块可进 tran/DC；`BLOCK_CONTRACTS.md` §6 第 1–2 步全部可开工 | **0 个仿真可跑**（当前状态） |
| **P1** | MIM/MOM 电容、poly/well 电阻 | 可信的 INL/DNL、匹配、面积、参考建立 | 功能能跑，但 `ARCH_V2.md` §1.1 的第 1/2/3/5 条数值全部无法验证 |
| **P2** | BJT / 齐纳 / bandgap 器件、ESD、pad | `BiasGen` 的 bandgap、`Sar20bTop` 的 pad 环 | 只影响 `BiasGen` 与顶层 LAY，**不阻塞 L1 单元** |
| **禁止** | 理想 MOS、行为 MOS、从别的工艺借模型、手写 `vth=0.5` 之类 | — | 违反 `pdk_models.scs:19`；结论不可用 |

---

## 6. 填完之后的自检清单（**必须逐条过，贴 log**）

```bash
# ① 语法层：能读进 Spectre（不做仿真，先过 parse）
cd 20b10m/analog/netlist && spectre -f build.scs -o /tmp/pdk_parse +escchars 2>&1 | head -40
#   期望：无 "unknown model" / "cannot find" / "undefined"
#   TODO：本仓库尚未实跑过这条命令（缺 PDK），第一条真实 log 必须存档到 analog/netlist/sim/pdk_check/

# ② 别名层：4 条最小 DC 台架，逐个确认"是 MOS 不是二极管/电容"
#    每个台架：VDD 到漏、栅给 0 与 VDD 两点、源/体接地，看 Id 单调且量级合理
#    TODO：4 个 .scs 放在 netlist/tb/pdk_<alias>_dc.scs（本轮未建，属验证组台架规范）

# ③ 参数层：确认 w/l 是"实例参数"不是"模型参数"
#    若 ② 里改 w 不改变 Id → 说明 w/l 被模型吞掉了，映射方式错了（常见于把 subckt 名当 model 用）

# ④ 电压层：5 V 器件的栅/漏在 5.5 V 下不报 oxide/breakdown 警告（若 PDK 有该检查）
#    TODO(PDK)：确认 PDK 是否带 reliability check

# ⑤ 角点层：把 section 换成 ss / ff 各跑一次 ②，三条 Id 必须有差异
#    无差异 = section 没生效（最常见的"填了等于没填"）
```

**自检记录（空缺，填的人签字）**

| 项 | 结果 | log 路径 | 人 | 日期 |
|:---|:---|:---|:---|:---|
| ① parse 通过 | `TODO` | `TODO` | `TODO` | `TODO` |
| ② 4 个别名 DC | `TODO` | `TODO` | `TODO` | `TODO` |
| ③ w/l 生效 | `TODO` | `TODO` | `TODO` | `TODO` |
| ④ 5 V 耐压 | `TODO` | `TODO` | `TODO` | `TODO` |
| ⑤ 角点可切 | `TODO` | `TODO` | `TODO` | `TODO` |

---

## 7. 填之前必须先想清楚的 5 个坑（都与"填错"有关，不是"没填"）

| # | 坑 | 现象 | 后果 | 处置 |
|:--|:---|:---|:---|:---|
| K1 | **bulk 接法**：全项目 M 语句的 b 端都接 `GND` 或对应电源轨，**不是各自源极** | 例：`Cmp1.scs:10` `M1 (d1 VINP tail GND) nch5` → 源极是 `tail`（会浮动）、体接 `GND` → VSB 随输入变化 | 体效应 → Vth 随信号变；若 PDK 的 5 V NMOS 需要 **DNW/隔离环**才能这样接，版图侧要提前知道 | 填模型时**同时确认**该器件允许"体接固定轨"（即是否 DNW 型）。不允许就得改网表拓扑 → 提前暴露 |
| K2 | `SwSample5v.scs:18` `M3 (VIN PHI_S sbot GND) nch5`：源极 `sbot` 会被抬到 ≈VIN（最高 5 V），体接 `GND` | VBS ≈ **−5 V** | 超出部分 PDK 的 VBS 额定（一般 −4~−6 V） | 填模型时查 **VBS 额定**；不够则这块拓扑要改 |
| K3 | 4 端 + 只给 `w/l`，PDK 若要求 `ad/as/pd/ps/nf` | 105 条同时失败 | 无法开工 | 见 §2.2-⑦，优先在别名层补默认 |
| K4 | `l=0.5u` 用在 5 V 器件、`l=0.18u` 用在 1.8 V 器件 | 若 PDK 的 5 V 器件 L_min > 0.5u，或 1.8 V 器件最小 L 不是 0.18u | 部分器件非法 | 填 §2.2-⑤ 时逐条核对，不要假设 |
| K5 | `VDDIO` 端口在顶层存在（`Sar20bTop.scs:15`）但**全项目没有一条器件用它** | `VDDIO` 是空轨 | 顶层台架给了 1.8 V 也无电流；LAY 侧 pad 却要供电 | 要么补 I/O 器件（数字侧），要么在 `PINOUT_QFN48.md` 里说明 VDDIO 只喂数字 → **本轮不改，登记** |

---

## 8. 依赖关系（填完之后谁先动）

```
P0 填完 ──┬─→ BLOCK_CONTRACTS §6 第 0 步（4 别名 DC 自检）
          ├─→ 第 1 步 标准单元（inv/tg/sw）
          ├─→ 第 2 步 Cmp1 / Cmp2 / SliceMux / SwSample5v / ClkRx
          └─→ 第 3 步 Dac2_11b / BiasGen / RefBuffer / RingAmp3 / TriLevelDrv
P1 填完 ──┬─→ DAC1/DAC2 的 INL/DNL（唯一能验 20.5 bit 的地方）
          ├─→ 面积复核（27 fF 的真实单位面积 × 1039）
          └─→ RefBuffer 的 R_out/噪声、DynRefBuf 的 droop
P2 填完 ──→ BiasGen bandgap、Sar20bTop pad/ESD（LAY 阶段）
```

**给 team-lead 的一句话**：P0 是**单点阻塞**——4 条映射，谁有 PDK 谁填，半天可完成；在这之前，模拟侧 105 个晶体管、23 个块、220 个实例的"完成度"都只是结构完成度，**不是可仿真完成度**。
