# [CODE-INDEX] sources.py —— 噪声/失配源
# 关键：tracking_noise 的相关方向是“重复序号 m”，不是时间；这是 8× 的核心。
# ar1/ dac_weights/ slice_errors 均为显式参数，不含隐式拟合。
"""噪声源与失配源。所有函数只接收显式参数，返回输入折算值。"""
import numpy as np

def ar1(n, rho, sigma, rng):
    """AR(1) 噪声，稳态标准差 sigma。"""
    w = rng.normal(0, sigma*np.sqrt(max(1-rho*rho, 1e-12)), n)
    x = np.empty(n)
    x[0] = rng.normal(0, sigma)
    for i in range(1, n):
        x[i] = rho*x[i-1] + w[i]
    return x

def tracking_noise(size, M, rho, sigma, rng):
    """每个样本做 M 次重复读；同一样本的 M 次读之间是 AR(1) 相关。
    注意：相关是“重复序号 m”方向，不是时间方向——这是 8× tracking 的核心。"""
    x = np.empty((size, M))
    x[:, 0] = rng.normal(0, sigma, size)
    for m in range(1, M):
        w = rng.normal(0, sigma*np.sqrt(max(1-rho*rho, 1e-12)), size)
        x[:, m] = rho*x[:, m-1] + w
    return x.mean(axis=1)

def dac_weights(bits, unit_sigma, rng):
    """单位电容失配 → 每位权重误差；大位由多个单位平均，误差按 1/sqrt(2^i) 缩小。"""
    w = np.empty(bits)
    for i in range(bits):
        units = 2**i
        rel = unit_sigma / np.sqrt(units)
        w[i] = units * (1.0 + rng.normal(0, rel))
    return w

def slice_errors(n_slices, gain_sigma, offset_sigma, skew_sigma, rng):
    g = 1.0 + rng.normal(0, gain_sigma, n_slices)
    o = rng.normal(0, offset_sigma, n_slices)
    t = rng.normal(0, skew_sigma, n_slices)
    return g, o, t
