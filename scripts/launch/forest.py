# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib==3.10.*"]
# ///
"""Forest plot: cost ratio R (skill / its placebo) with 95% CI per skill, from results JSON.

  uv run --script scripts/launch/forest.py OUT_PREFIX RESULTS.json [RESULTS.json ...] [--title T] [--pilot]
Writes OUT_PREFIX-light.svg/.png and OUT_PREFIX-dark.svg/.png (GitHub shows one or the other with
<picture> and prefers-color-scheme). One row per skill, grouped by harness; log x axis; reference line
at R = 1; the shaded band 0.90-1.10 is METHOD.md's "trivial" range. Numbers come only from the JSON.
"""
import argparse
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

THEMES = {  # reference palette (dataviz skill): surface, text, muted, series-1, band
    "light": dict(surface="#fcfcfb", text="#0b0b0b", muted="#52514e", grid="#e4e3df", mark="#2a78d6", band="#ecebe7"),
    "dark": dict(surface="#1a1a19", text="#ffffff", muted="#c3c2b7", grid="#34332f", mark="#3987e5", band="#2a2927"),
}
HARNESS_LABEL = {"claude-code": "Claude Code", "codex": "Codex"}


def rows_from(paths: list[str]) -> list[dict]:
    rows = []
    for p in paths:
        d = json.loads(Path(p).read_text())
        h = d.get("harness", "")
        comps = d["comparisons"]
        for skill, c in sorted(comps.items(), key=lambda kv: kv[1]["ratio"]):
            rows.append({"harness": HARNESS_LABEL.get(h, h), "skill": skill, "r": c["ratio"], "lo": c["ratio_ci"][0],
                         "hi": c["ratio_ci"][1], "placebo": c.get("placebo", "").replace("placebo-", ""),
                         "verdict": c.get("verdict"), "n": f"{c.get('n_treat')}/{c.get('n_control')}"})
    return rows


def draw(rows: list[dict], theme: str, title: str, subtitle: str, out: str) -> None:
    t = THEMES[theme]
    groups = []
    for r in rows:
        if not groups or groups[-1][0] != r["harness"]:
            groups.append((r["harness"], []))
        groups[-1][1].append(r)
    # y positions: a header line per group, one line per row
    ypos, labels, y = [], [], 0.0
    headers = []
    for g, rs in groups:
        if len(groups) > 1:
            headers.append((y, g))
            y += 0.9
        for r in rs:
            ypos.append(y)
            labels.append(r)
            y += 1.0
        y += 0.4
    height = 1.3 + 0.36 * y
    fig, ax = plt.subplots(figsize=(8.6, height), dpi=200)
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])
    lo = min(min(r["lo"] for r in rows), 0.6)
    hi = max(max(r["hi"] for r in rows), 1.6)
    ax.set_xscale("log")
    ax.set_xlim(lo / 1.08, hi * 1.08)
    ax.axvspan(0.90, 1.10, color=t["band"], zorder=0, lw=0)
    ax.axvline(1.0, color=t["muted"], lw=1, ls=(0, (3, 3)), zorder=1)
    for yy, r in zip(ypos, labels):
        ax.plot([r["lo"], r["hi"]], [yy, yy], color=t["mark"], lw=2, solid_capstyle="round", zorder=3)
        ax.plot([r["r"]], [yy], "o", ms=8, color=t["mark"], mec=t["surface"], mew=2, zorder=4)
    ax.set_ylim(y - 0.2, -0.9)
    ax.set_yticks(ypos)
    ax.set_yticklabels([r["skill"] for r in labels], color=t["text"], fontsize=10)
    for yy, g in headers:
        ax.text(-0.26, yy, g, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=10,
                fontweight="bold", color=t["text"])
    for yy, r in zip(ypos, labels):
        txt = f"{r['r']:.2f} [{r['lo']:.2f}, {r['hi']:.2f}]  vs {r['placebo']}"
        if r["verdict"]:
            txt += f" · {r['verdict']}"
        ax.text(1.01, yy, txt, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=9, color=t["muted"])
    ticks = [x for x in (0.5, 0.6, 0.75, 0.9, 1.0, 1.1, 1.25, 1.5, 2.0, 3.0) if lo / 1.08 <= x <= hi * 1.08]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f"{x:g}" for x in ticks], color=t["muted"], fontsize=9)
    ax.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    ax.tick_params(axis="both", length=0)
    ax.grid(axis="x", color=t["grid"], lw=0.6, zorder=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_xlabel("cost with skill / cost with same-length placebo (log scale; < 1 = skill is cheaper)",
                  color=t["muted"], fontsize=9, labelpad=8)
    fig.suptitle(title, x=0.02, ha="left", fontsize=12, fontweight="bold", color=t["text"], y=0.995)
    fig.text(0.02, 1 - 0.55 / height, subtitle, ha="left", va="top", fontsize=9, color=t["muted"])
    fig.subplots_adjust(left=0.2, right=0.62, top=1 - 1.05 / height, bottom=0.62 / height)
    for ext in ("svg", "png"):
        fig.savefig(f"{out}-{theme}.{ext}", facecolor=t["surface"], metadata={"Date": None} if ext == "svg" else None)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_prefix")
    ap.add_argument("results", nargs="+")
    ap.add_argument("--title", default="Cost of each skill relative to a same-length placebo")
    ap.add_argument("--subtitle", default="point = mean cost ratio R, line = 95% CI (cluster bootstrap over tasks); "
                                          "grey band = 0.90-1.10")
    a = ap.parse_args()
    rows = rows_from(a.results)
    Path(a.out_prefix).parent.mkdir(parents=True, exist_ok=True)
    for theme in THEMES:
        draw(rows, theme, a.title, a.subtitle, a.out_prefix)
    print(f"{len(rows)} rows -> {a.out_prefix}-{{light,dark}}.{{svg,png}}")


if __name__ == "__main__":
    main()
