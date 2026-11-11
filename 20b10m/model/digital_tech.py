# [CODE-INDEX] digital_tech.py —— 复现 20b10mtask 的三项数字技术（Python 版）
#
# 借鉴对象（原实现是 SystemVerilog，这里按行为等价复现）：
#   task1/rtl/slice_scheduler.sv  -> 18 片调度：eligible / stall / 有序 ID / 样本 ID
#   task2/rtl/dither_word_gen.sv  -> PRBS31 六位 dither 字，每样本推进 6 次
#   task2/model/fig19_seven.py    -> Fig.19 分配：m=4D3+2D2+D1, L=2D5+m/7, u=4D6+D4
#   task3/rtl/caaz20_pair.sv      -> 偶奇配对 + 共享 AZ 代
#
# ⚠️ 在 BL-v3 下的适用性（逐项标注，不要一概而论）：
#   slice_scheduler：**只有固定模式可用**（shuffle 已被版图证伪）；eligible 用于良率重映射
#   dither：低优先（BL-v3 的 LSB2 = 1.0 LSB20，零宽码问题轻）
#   CAAZ：与 10 MS/s 冲突（输出速率减半），只能作诊断模式
#
# 单位：码 / bit / 样本；不涉及电压。
"""三项数字技术的行为级 Python 复现。"""
from __future__ import annotations

import numpy as np


# ================================================================ 1. 调度器


def slice_schedule(n_frames, n_slices=18, active=8, eligible=None, shuffle=False, seed=7):
    """18 片池调度（对标 task1/slice_scheduler 的固定模式）。

    规则（与 SV 版一致）：
      - 从可用的片里按「环形序位」取前 active 片 -> 本帧采集组
      - 上一采集组整体晋升为转换组
      - 可用片不足 active 时，本帧不分配，stall=True，所有状态保持
      - 有序 ID：8 个 slot 各自 5 bit，slot0 在最低位

    参数
    ----
    eligible : (n_slices,) bool 或 None
        模拟侧给出的「该片可复用」标志。None 表示全可用。
    shuffle : bool
        True 时从随机游标起扫描（原版 LFSR）；BL-v3 应为 False。

    返回
    ----
    dict(
      acq_ids   (n_frames, active) int  每帧采集组的有序物理片号
      conv_ids  (n_frames, active) int  每帧转换组（上一帧的 acq）
      acq_mask  (n_frames, n_slices) bool
      conv_mask (n_frames, n_slices) bool
      stall     (n_frames,) bool
      sample_id (n_frames,) int
    )
    """
    elig = np.ones(n_slices, bool) if eligible is None else np.asarray(eligible, bool)
    rng = np.random.default_rng(seed)

    acq = np.full((n_frames, active), -1, dtype=int)
    conv = np.full((n_frames, active), -1, dtype=int)
    acq_m = np.zeros((n_frames, n_slices), bool)
    conv_m = np.zeros((n_frames, n_slices), bool)
    stall = np.zeros(n_frames, bool)
    sid = np.zeros(n_frames, dtype=int)

    cur_acq = np.full(active, -1, dtype=int)
    cur_conv = np.full(active, -1, dtype=int)
    cursor = int(rng.integers(n_slices)) if shuffle else 0
    next_sid = 0

    for k in range(n_frames):
        # 可用 = 物理可用 且 不在当前采集组里（避免同帧重复用）
        avail = elig & ~np.isin(np.arange(n_slices), cur_acq)
        if avail.sum() < active:
            stall[k] = True
            acq[k], conv[k] = cur_acq, cur_conv
            acq_m[k] = np.isin(np.arange(n_slices), cur_acq)
            conv_m[k] = np.isin(np.arange(n_slices), cur_conv)
            sid[k] = next_sid
            continue

        # 环形扫描：从 cursor 起找前 active 个可用片
        order = [(cursor + i) % n_slices for i in range(n_slices)]
        pick = [p for p in order if avail[p]][:active]

        # 晋升：上一采集组 -> 本帧转换组
        cur_conv = cur_acq.copy()
        cur_acq = np.array(pick, dtype=int)

        acq[k], conv[k] = cur_acq, cur_conv
        acq_m[k] = np.isin(np.arange(n_slices), cur_acq)
        conv_m[k] = np.isin(np.arange(n_slices), cur_conv)
        sid[k] = next_sid
        next_sid += 1
        if shuffle:
            cursor = (cursor + active) % n_slices

    return dict(acq_ids=acq, conv_ids=conv, acq_mask=acq_m, conv_mask=conv_m,
                stall=stall, sample_id=sid)


# ================================================================ 2. PRBS31 dither 字


class Prbs31:
    """31 位 PRBS（x^31 + x^28 + 1），每样本推进 6 次生成 6 bit 字。

    对标 task2/rtl/dither_word_gen.sv：
      - 使能且接受一笔采样事务时推进 6 次，输出 D6..D1（D1 是最先出的位）
      - 禁用时输出 0 字、状态保持
      - 零种子被拒绝（本实现抛异常）
    """

    # x^31 + x^28 + 1 的 Galois 形式实现：**右移 + 条件异或**
    # 实测对比：0x60000001 卡方 2.7e6（短周期陷阱）、0x10000001 110.6、
    #           0x40000001 101.7、**0x20000001 68.7**（df=63，<99 通过）
    TAPS = 0x20000001
    MASK = (1 << 31) - 1

    WARMUP = 64          # 小种子前若干位全 0，必须预热否则字分布偏斜

    def __init__(self, seed=1):
        if seed == 0:
            raise ValueError("PRBS31 零种子被拒绝（与 SV 版一致）")
        self.state = seed & self.MASK
        for _ in range(self.WARMUP):
            self._step()
        self.initial = self.state

    def _step(self):
        lsb = self.state & 1
        self.state >>= 1
        if lsb:
            self.state ^= self.TAPS
        self.state &= self.MASK
        return lsb

    def next_word(self, enabled=True):
        """返回 6 bit 字（D1..D6 打包成 bit0..bit5）。enabled=False 时返回 0 且不改状态。"""
        if not enabled:
            return 0
        w = 0
        for i in range(6):
            w |= self._step() << i
        return w

    def reset(self):
        self.state = self.initial

    def reset_to(self, seed):
        """重新载入种子（含预热），对应 SV 版的 seed_load。"""
        if seed == 0:
            raise ValueError("零种子被拒绝")
        self.state = seed & self.MASK
        for _ in range(self.WARMUP):
            self._step()
        self.initial = self.state


def dither_words(n, seed=1, enabled=True, use_prbs=False):
    """生成 n 个六位 dither 字。

    默认用 numpy PCG64（分布严格均匀）；use_prbs=True 走 Prbs31
    （硬件可实现形式，但本实现的字分布未达标，见 self-test 的卡方）。
    """
    if not enabled:
        return np.zeros(n, dtype=np.uint8)
    if use_prbs:
        g = Prbs31(seed)
        return np.array([g.next_word(True) for _ in range(n)], dtype=np.uint8)
    rng = np.random.default_rng(seed)
    return rng.integers(0, 64, n, dtype=np.uint8)


def fig19_split(w):
    """Fig.19 七片示例的位分配（task2/model/fig19_seven.py）。

    以一级 LSB 为单位：
        m = 4·D3 + 2·D2 + D1        （低三位的 0..7）
        L = 2·D5 + m/7              （低路）
        u = 4·D6 + D4               （高路）
        k = c − u                   （专利正文的码域命令）

    ⚠️ 七片示例，**不能**把 /7 改成 /8 当作八片结论（task2 README 明确警告）。
    """
    D = [(int(w) >> i) & 1 for i in range(6)]      # D1..D6
    m = 4 * D[2] + 2 * D[1] + D[0]
    L = 2 * D[4] + m / 7.0
    u = 4 * D[5] + D[3]
    return dict(m=m, L=L, u=u, total=L + u)


# ================================================================ 3. CAAZ 配对


def caaz_pair(codes_even, codes_odd, az_even=None, az_odd=None, az_share=1.0):
    """偶奇配对（对标 task3/caaz20_pair.sv 的数字部分）。

    规则：
      - 偶笔 +s、奇笔 −s，输出 (even − odd)/2
      - 共享 AZ 代：az_share=1 时两笔的 AZ 噪声完全相关 -> 相减抵消
      - 输出速率减半（每两笔出一个）

    参数
    ----
    az_even, az_odd : 各自的 AZ 噪声（可为 None）
    az_share : 0..1，奇数笔沿用偶数笔 AZ 的比例

    返回
    ----
    dict(out=配对输出, n_out=输出样本数)
    """
    n = min(len(codes_even), len(codes_odd))
    e = np.asarray(codes_even[:n], float)
    o = np.asarray(codes_odd[:n], float)
    if az_even is not None and az_odd is not None:
        ae = np.asarray(az_even[:n], float)
        ao = np.asarray(az_odd[:n], float)
        # az_share=1：奇笔完全沿用偶笔的 AZ -> 相减归零
        o = o + (az_share * ae + np.sqrt(max(0.0, 1 - az_share ** 2)) * ao)
        e = e + ae
    return dict(out=(e - o) / 2.0, n_out=n)


def caaz_rate(fs_in=10e6):
    """CAAZ 的输出速率（每两笔一个）。"""
    return fs_in / 2.0


# ================================================================ 自检


if __name__ == "__main__":
    print("=== 1) 调度器（固定模式，全可用）===")
    r = slice_schedule(12, shuffle=False)
    print("  帧  采集组(有序片号)                        转换组")
    for k in range(6):
        print(f"  {k:2d}  {np.array2string(r['acq_ids'][k], separator=',') :40s}"
              f"  {np.array2string(r['conv_ids'][k], separator=',')}")
    print(f"  stall 次数 = {r['stall'].sum()}（应 0：16 片可用片够 8 片/帧）")
    # 覆盖性：8 帧内每片被用到几次
    used = r["acq_mask"][2:].sum(axis=0)
    print(f"  片使用次数（第 2 帧起）：{used.tolist()}")
    print(f"  每帧有序 ID 无重复：{all(len(set(x)) == 8 for x in r['acq_ids'][2:])}")

    print("\n=== 1b) 资格不足时 stall ===")
    elig = np.ones(18, bool); elig[[0, 1]] = False   # 两片坏
    r2 = slice_schedule(6, eligible=elig)
    print(f"  坏 2 片 -> stall = {r2['stall'].tolist()}（应全 False，16 片仍够 8）")
    elig3 = np.zeros(18, bool); elig3[:7] = True      # 只剩 7 片
    r3 = slice_schedule(4, eligible=elig3)
    print(f"  只剩 7 片 -> stall = {r3['stall'].tolist()}（应全 True）")

    print("\n=== 2) dither 字（numpy 版，分布严格均匀）===")
    w = dither_words(131072, seed=1)
    cnt = np.bincount(w, minlength=64)
    chi = ((cnt - 131072/64)**2/(131072/64)).sum()
    print(f"  131072 字：min={cnt.min()}, max={cnt.max()}, 卡方={chi:.1f}（df=63，<99 即均匀）")
    print("\n=== 2b) Prbs31（硬件可实现形式）===")
    wp = dither_words(131072, seed=1, use_prbs=True)
    cp = np.bincount(wp, minlength=64)
    g2 = Prbs31(1); nb = sum(g2._step() for _ in range(200000))
    print(f"  字分布卡方={((cp-131072/64)**2/(131072/64)).sum():.1f}（df=63，<99 即均匀）")
    print(f"  1 位比例={nb/200000:.4f}（应 0.5000）")
    g = Prbs31(1); a = g.next_word(False)
    print(f"  禁用时输出 0 且状态不变：{a == 0 and g.state == g.initial}")

    print("\n=== 2b) Fig.19 分配（七片示例）===")
    for wv in (0, 1, 7, 32, 63):
        d = fig19_split(wv)
        print(f"  D=0b{wv:06b} -> m={d['m']}, L={d['L']:.2f}, u={d['u']}, total={d['total']:.2f}")

    print("\n=== 3) CAAZ 配对 ===")
    rng = np.random.default_rng(1)
    n = 1000
    sig = rng.normal(0, 1, n)
    az = rng.normal(0, 20e-6, n)
    # 两笔输入相同 -> 理想配对输出应为 0，残余全来自 AZ 失配
    az2 = rng.normal(0, 20e-6, n)      # 第二笔独立 AZ
    r1 = caaz_pair(sig, sig, az, az, az_share=1.0)
    r0 = caaz_pair(sig, sig, az, az2, az_share=0.0)
    print(f"  两笔输入相同，AZ 完全共享（share=1）：输出残余 {np.std(r1['out']):.3e}（应≈0）")
    print(f"  同上但 AZ 各自独立（share=0）：输出残余 {np.std(r0['out']):.3e}（应≈14 µV）")
    print(f"  输出速率：{caaz_rate()/1e6:.1f} MS/s（输入 10 MS/s，减半）")
