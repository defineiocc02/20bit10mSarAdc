# 层次结构

> 模拟 25 块 + 数字 11 块（10 MS/s 部分交织）。带子模块的是结构性封装，叶子是可独立设计的模块。

```
Sar20bTop
├── BiasGen
├── DigitalTop   [digital]
│   ├── BitRecombine   [digital]
│   ├── GainScale   [digital]
│   ├── LmsCal   [digital]
│   ├── LsbRepeat8   [digital]
│   ├── Sinc2Dec   [digital]
│   └── SliceShuffler   [digital]
├── DynRefBuf
├── SdacPool18（18 片，A/B 共享）
│   └── SdacSlice
│       └── SwSample5v（每片一个，3.5 pF）
├── CmpCoarse4b（15 cmp，单套）
├── SliceMux（18:1 选 8 片）
├── RefBuffer
├── RingAmp3
│   ├── AmpA2
│   ├── FiaA1
│   └── FiaA3
├── Sar1Top（单相）
│   ├── AcqTrackCtl   [digital]
│   ├── Cmp1
│   ├── CmpQ2
│   ├── CoarseAdc6b   [digital]
│   ├── SarLogic1   [digital]
│   └── TriLevelDrv
└── Sar2Ct ×2（A/B 各一套）
    ├── CincCouple
    ├── Cmp2
    ├── Dac2Replica
    ├── Dac2_11b
    └── SarLogic2   [digital]
```

## 统计

- 模块总数：**34**（模拟 23 + 数字 11）
- 叶子模块：**28**
- 端口总数：以 `interfaces.csv` 为准（10M 版待重导）

## 模块职责

| 层 | 域 | 模块 | 职责 |
|:---:|:---:|:---|:---|
| L0 | analog | `Sar20bTop` | 顶层 ADC：20.5 bit / **10 MS/s（2×5 MS/s 交织）** / 10 Vpp 差分输入 |
| L1 | analog | `BiasGen` | 偏置与共模产生 |
| L1 | digital | `DigitalTop` | 数字后端：重复码、SINC2、1/G、位重组、LMS |
| L1 | analog | `DynRefBuf` | 动态参考缓冲：粗预充 + 进 RA 前切精确参考 |
| L1 | analog | `RaMux` | 两相位共享 RA 的输入开关网络 |
| L1 | analog | `RefBuffer` | 参考缓冲（5V 与 1.8V 两套） |
| L1 | analog | `RingAmp3` | 三级 ring amp（A1 FIA / A2 / A3 FIA） |
| L1 | analog | `Sar1Top` | 一级单相：比较器 + 三电平驱动 + SAR1 逻辑（采样在 slice 内） |
| L1 | analog | `Sar2Ct` | 二级：CT SAR（C_INC 直连 DAC2，**11b**，8× LSB 重复）；**每相一套** |
| L2 | digital | `AcqTrackCtl` | 采样边沿/回采样边沿/hold-low/tracking 预置控制 |
| L2 | analog | `AmpA2` | 第二级：diode-connected 负载，提高次极点 |
| L2 | digital | `BitRecombine` | 位重组：D1(11b) + D2(12b) → 20.5b |
| L2 | analog | `CincCouple` | C_INC 耦合 + replica 抵消 kickback |
| L2 | analog | `Cmp1` | 一级低噪声动态比较器 |
| L2 | analog | `Cmp2` | 二级比较器 |
| L2 | analog | `CmpQ2` | 第二量化器：避免转换结束时扰动输入 |
| L2 | digital | `CoarseAdc6b` | 6b 粗量化：预解析 D1[10:5] |
| L2 | analog | `Dac1_11b` | 一级 CDAC：1039×27fF，二进制+冗余，三电平切换 |
| L2 | analog | `Dac2Replica` | DAC2 复刻：只用于 kickback 抵消，不参与量化 |
| L2 | analog | `Dac2_11b` | 二级 CDAC：11 bit（5+6 分段，桥接） |
| L2 | analog | `FiaA1` | 第一级浮栅反相放大器（FIA） |
| L2 | analog | `FiaA3` | 输出级偏置 FIA：无需全局 CMFB，大摆幅 |
| L2 | digital | `GainScale` | 1/G 定点缩放 |
| L2 | digital | `LmsCal` | 一次性 LMS 失配校准 |
| L2 | digital | `LsbRepeat8` | 8× LSB 重复码生成（驱动 DAC2 低位） |
| L2 | digital | `SarLogic1` | 一级 SAR 逻辑：11 位逐次逼近 + 握手 |
| L2 | digital | `SarLogic2` | 二级 SAR 逻辑 + 8× LSB 重复状态机 |
| L1 | analog | `SdacPool18` | 18 片池：A 相 9（8 用 1 备）+ B 相 9（8 用 1 备） |
| L2 | digital | `Sinc2Dec` | 二阶 CoI（SINC2）+ M 倍抽取 |
| L2 | digital | `SliceShuffler` | 3b round-robin + 二维 unary 洗牌 + dither |
| L2 | analog | `SwSample5v` | 5V 自举采样开关 |
| L2 | analog | `TriLevelDrv` | 每位三电平开关驱动（VREF/VCM/VGND） |
| L3 | analog | `SdacSlice` | DAC1 的一个 slice（1/8 阵列，3.5 pF），V2 交织用 |
