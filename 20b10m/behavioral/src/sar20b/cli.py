# [CODE-INDEX] cli.py —— 命令入口（规范 §15）
#
# 命令：doctor / validate / run / figures / report
# 约定：失败返回非零；figures 只读已保存数据，不重跑模型；run 目录默认不覆盖。
"""sar20b 命令行。"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------- 工具

def _pkg_versions() -> dict:
    v = {"python": platform.python_version()}
    for m in ("numpy", "scipy", "matplotlib"):
        try:
            mod = __import__(m)
            v[m] = getattr(mod, "__version__", "?")
        except Exception as e:                       # noqa: BLE001
            v[m] = f"MISSING ({e.__class__.__name__})"
    return v


def _git(*args) -> str | None:
    try:
        r = subprocess.run(["git", *args], capture_output=True, text=True,
                           cwd=Path(__file__).resolve().parents[3], timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except Exception:                                # noqa: BLE001
        return None


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def _prepare_out(out: str) -> Path:
    p = Path(out)
    if p.exists() and any(p.iterdir()):
        raise SystemExit(f"输出目录已存在且非空：{p}（不覆盖，换一个名字）")
    p.mkdir(parents=True, exist_ok=True)
    return p


# ---------------------------------------------------------------- doctor

def cmd_doctor(args) -> int:
    from .config import PROFILES, NumericalContract
    print("=== sar20b doctor ===")
    v = _pkg_versions()
    for k, val in v.items():
        flag = "OK " if "MISSING" not in str(val) else "FAIL"
        print(f"  [{flag}] {k:12s} {val}")
    bad = [k for k, val in v.items() if "MISSING" in str(val)]

    print(f"\n  git HEAD     {_git('rev-parse', '--short', 'HEAD') or '(非 git)'}")
    dirty = _git("status", "--porcelain")
    print(f"  git dirty    {'有未提交改动' if dirty else '干净'}")

    c = NumericalContract()
    print(f"\n  数值合同     n_total={c.n_total}  LSB1={c.lsb1_v*1e3:.6f} mV  "
          f"LSB2={c.lsb2_v*1e6:.5f} µV")
    errs = c.check()
    print(f"  自洽检查     {'通过' if not errs else '；'.join(errs)}")

    print(f"\n  profile 数   {len(PROFILES)} -> {list(PROFILES)}")

    print("\n  HDL 工具：")
    for t in ("iverilog", "verilator", "yosys"):
        import shutil
        print(f"    {t:10s} {'有' if shutil.which(t) else '无（RTL 只能 NOT_RUN）'}")

    print("\n  字体：")
    import matplotlib
    from matplotlib import font_manager
    names = {f.name for f in font_manager.fontManager.ttflist}
    for f in ("PingFang SC", "Heiti SC", "Arial Unicode MS"):
        print(f"    {f:18s} {'有' if f in names else '无'}")

    if bad or errs:
        print("\n结果：有问题（见上）")
        return 1
    print("\n结果：通过")
    return 0


# ---------------------------------------------------------------- validate

def cmd_validate(args) -> int:
    from .config import make_config
    import yaml
    cfg_path = Path(args.config)
    if not cfg_path.exists():
        print(f"配置不存在：{cfg_path}")
        return 2
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    profile = raw.get("profile", "ideal")
    ni = raw.get("nonidealities", {}) or {}
    try:
        cfg = make_config(profile, **ni)
    except KeyError as e:
        print(f"配置非法：{e}")
        return 2
    errs = cfg.validate()
    print(f"profile = {cfg.profile.name}（{cfg.profile.mapping}）")
    print(f"  n1_effective = {cfg.profile.n1_effective}")
    print(f"  LSB1_eff = {cfg.profile.lsb1_effective_v*1e3:.4f} mV")
    print(f"  非理想项 = {len([v for v in ni.values() if v is not None])} 个显式指定")
    if errs:
        print("校验失败：" + "；".join(errs))
        return 1
    print("校验通过")
    return 0


# ---------------------------------------------------------------- run

def cmd_run(args) -> int:
    import yaml
    from .config import make_config
    from .core.pipeline import Pipeline
    from .analysis.spectrum import fft_metrics

    raw = yaml.safe_load(Path(args.config).read_text(encoding="utf-8")) or {}
    profile = raw.get("profile", "ideal")
    ni = raw.get("nonidealities", {}) or {}
    exp = raw.get("experiment", {}) or {}
    cfg = make_config(profile, **ni)
    cfg.seed = int(exp.get("seed", 1))

    out = _prepare_out(args.out)
    pipe = Pipeline(cfg)
    c = cfg.contract

    kind = exp.get("kind", "tone")
    n = int(exp.get("n", 4096))
    if kind == "ramp":
        v = np.linspace(-c.fs_diff_v / 2 * 0.96, c.fs_diff_v / 2 * 0.96, n, endpoint=False)
        outs = pipe.run(c.vref_p / 2 + v / 2, c.vref_p / 2 - v / 2)
        codes = pipe.codes(outs)
        ideal = (v / c.fs_diff_v + 0.5) * 2 ** c.n_total
        err = (codes >> (c.n_xfer - c.n_total)) - ideal
        A = np.stack([np.ones_like(ideal), ideal], 1)
        coef, *_ = np.linalg.lstsq(A, err, rcond=None)
        inl = err - A @ coef
        metrics = dict(kind="ramp", n=n,
                       inl_peak_lsb20=float(np.max(np.abs(inl))),
                       inl_peak_ppm=float(np.max(np.abs(inl)) / 2 ** c.n_total * 1e6))
        (out / "raw").mkdir(exist_ok=True)
        np.savez(out / "raw" / "ramp.npz", v=v, codes=codes, inl=inl)
    else:
        fs = c.fs_hz
        k = int(exp.get("bin", 41))
        fin = k * fs / n
        t = np.arange(n) / fs
        amp = float(exp.get("amp", 4.8))
        v = amp * np.sin(2 * np.pi * fin * t)
        outs = pipe.run(c.vref_p / 2 + v / 2, c.vref_p / 2 - v / 2)
        codes = pipe.codes(outs)
        x = codes.astype(float) / 2 ** c.n_xfer * c.fs_diff_v - c.fs_diff_v / 2
        m = fft_metrics(x, fs, fin)
        metrics = dict(kind="tone", n=n, fin_hz=fin, input_bin=k, amp_v=amp, **m)
        (out / "raw").mkdir(exist_ok=True)
        np.savez(out / "raw" / "tone.npz", t=t, v=v, codes=codes)

    valid = sum(1 for o in outs if o.ctx.valid)
    metrics["n_valid"] = valid
    metrics["n_overload"] = len(outs) - valid

    manifest = dict(
        cmd=" ".join(sys.argv), label=cfg.label, profile=cfg.profile.name,
        git_head=_git("rev-parse", "HEAD"), git_dirty=bool(_git("status", "--porcelain")),
        packages=_pkg_versions(), seed=cfg.seed,
        config_sha=hashlib.sha256(json.dumps(cfg.to_dict(), sort_keys=True,
                                             default=str).encode()).hexdigest()[:16],
        chip=pipe.chip.summary(),
    )
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                                       encoding="utf-8")
    (out / "config_resolved.json").write_text(
        json.dumps(cfg.to_dict(), indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False),
                                      encoding="utf-8")
    print(json.dumps(metrics, indent=2, ensure_ascii=False))
    print(f"\n写入 {out}")
    ok = metrics.get("n_overload", 0) == 0
    if not ok:
        print(f"警告：{metrics['n_overload']} 个样本越界/故障（已保留，不剔除）")
    return 0 if ok else 3


# ---------------------------------------------------------------- figures

def cmd_figures(args) -> int:
    """只读已保存数据出图；不重跑模型。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from .config import NumericalContract

    run = Path(args.run)
    mf = run / "manifest.json"
    if not mf.exists():
        print(f"不是合法 run 目录（缺 manifest.json）：{run}")
        return 2
    manifest = json.loads(mf.read_text(encoding="utf-8"))
    metrics = json.loads((run / "metrics.json").read_text(encoding="utf-8"))
    figdir = run / "figures"
    figdir.mkdir(exist_ok=True)

    plt.rcParams.update({
        "font.sans-serif": ["PingFang SC", "Heiti SC", "Arial Unicode MS", "DejaVu Sans"],
        "axes.unicode_minus": False, "axes.spines.top": False,
        "axes.spines.right": False, "axes.grid": True, "grid.alpha": .25, "font.size": 9.5})

    c = NumericalContract()
    made = []
    if metrics.get("kind") == "ramp":
        d = np.load(run / "raw" / "ramp.npz")
        fig, ax = plt.subplots(figsize=(9.0, 3.4))
        ax.plot(d["v"], d["inl"], lw=.7, color="#D85A30")
        ax.axhline(0, color="#444441", lw=.5)
        ax.set(xlabel="差分输入 (V)", ylabel="INL (LSB$_{20}$)")
        ax.set_title(f"F04 全链 INL：峰值 {metrics['inl_peak_lsb20']:.2f} LSB20"
                     f"（{metrics['inl_peak_ppm']:.1f} ppm FS）", loc="left", fontsize=10.5)
        fig.text(.5, .005, f"profile={manifest['profile']}  seed={manifest['seed']}  "
                          f"σu={manifest['chip']['sigma_u']*100:.3f}%  "
                          f"git={str(manifest['git_head'])[:7]}", ha="center", fontsize=7.5,
                 color="#5F5E5A")
        fig.tight_layout(rect=[0, .03, 1, 1])
        p = figdir / "F04_inl.png"
        fig.savefig(p, dpi=160); fig.savefig(figdir / "F04_inl.svg")
        plt.close(fig); made.append(p.name)

    (run / "figures_manifest.json").write_text(json.dumps(
        dict(figures=made, source_metrics="metrics.json", config="config_resolved.json",
             manifest="manifest.json"), indent=2), encoding="utf-8")
    print(f"出图 {len(made)} 张 -> {figdir}")
    return 0


# ---------------------------------------------------------------- report

def cmd_report(args) -> int:
    run = Path(args.run)
    mf = run / "manifest.json"
    if not mf.exists():
        print("缺 manifest.json"); return 2
    m = json.loads(mf.read_text(encoding="utf-8"))
    met = json.loads((run / "metrics.json").read_text(encoding="utf-8"))
    lines = [f"# run: {run.name}", "",
             f"- profile: `{m['profile']}`",
             f"- git: `{m['git_head']}` dirty={m['git_dirty']}",
             f"- seed: {m['seed']}", f"- chip: {m['chip']}", "",
             "## 指标", "", "```json",
             json.dumps(met, indent=2, ensure_ascii=False), "```", ""]
    (run / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"写入 {run/'report.md'}")
    return 0


# ---------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="sar20b")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("doctor", help="检查依赖/合同/工具/字体").set_defaults(fn=cmd_doctor)

    p = sub.add_parser("validate", help="校验配置与 profile 合法性")
    p.add_argument("--config", required=True); p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("run", help="跑一次实验")
    p.add_argument("--config", required=True); p.add_argument("--out", required=True)
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("figures", help="从已保存数据出图（不重跑）")
    p.add_argument("--run", required=True); p.set_defaults(fn=cmd_figures)

    p = sub.add_parser("report", help="生成 run 的 report.md")
    p.add_argument("--run", required=True); p.set_defaults(fn=cmd_report)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
