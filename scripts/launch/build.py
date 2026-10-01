#!/usr/bin/env python3
"""Launch package builder: fills the templates in docs/launch/templates/ with numbers from results JSON.
No number is typed by hand anywhere in the package; every one comes from here.

  uv run python scripts/launch/build.py --scope pilot   # check on pilot data -> docs/launch/pilot/ (PILOT banner)
  uv run python scripts/launch/build.py --scope main    # final -> README.md + docs/launch/final/

Inputs per scope (the same schema; see docs/launch/RESULTS_SCHEMA.md):
  pilot: results/pilot/kill-claude-code.json, results/pilot/kill-codex.json
  main:  results/main/claude-code.json, results/main/codex.json (Codex top-up)
  both:  results/claims.json
Templates use {{key}}; a key the data cannot fill is left as [[MISSING key]] and listed at the end, so
nothing unfilled can pass unnoticed. Charts: scripts/launch/forest.py (run separately; needs matplotlib).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from skill_placebo.analysis import Comparison, verdicts  # noqa: E402

TEMPLATES = ROOT / "docs" / "launch" / "templates"
SCOPES = {
    "pilot": {"cc": ROOT / "results/pilot/kill-claude-code.json", "codex": ROOT / "results/pilot/kill-codex.json",
              "out": ROOT / "docs/launch/pilot", "readme": ROOT / "docs/launch/pilot/README.md",
              "chart": "forest", "date": "2026-09-30"},
    "main": {"cc": ROOT / "results/main/claude-code.json", "codex": ROOT / "results/main/codex.json",
             "out": ROOT / "docs/launch/final", "readme": ROOT / "README.md", "chart": "forest", "date": None},
}
# The one-command run works through PyPI only once the package is published. Until then
# the texts use the clone-and-run form. Flip PYPI to True when the package is on PyPI.
PYPI = False
REPO_URL = "https://github.com/simonether/skill-placebo"
RUN = ({"run_cmd": "uvx skill-placebo run <owner/repo>", "run_cmd_example": "uvx skill-placebo run DietrichGebert/ponytail"}
       if PYPI else
       {"run_cmd": f"git clone {REPO_URL} && cd skill-placebo && uv run skill-placebo run <owner/repo>",
        "run_cmd_example": f"git clone {REPO_URL} && cd skill-placebo && uv run skill-placebo run DietrichGebert/ponytail"})
# Trajectories are exported per arm (see docs/launch/README.md): results/main/<harness>/trials/<arm>/
TRAJ_URL = REPO_URL + "/tree/main/results/{scope}/{harness}/trials/skill-{skill}"
CODEX_SCOPE = "pilot"  # amendment 17: no Codex main run in v1; the Codex numbers are the pilot's kill test
PRIORITY = ["superpowers", "mattpocock", "karpathy", "ponytail", "caveman", "agent-skills", "i-have-adhd",
            "planning-with-files", "compound-engineering"]
HARNESS = {"cc": "Claude Code", "codex": "Codex"}
PILOT_BANNER = """> [!WARNING]
> **PILOT DATA - NOT THE RESULT.** Every number on this page comes from the pilot's kill test
> (3 skills per harness, 5 tasks x 2 trials per arm). It only checks that the pipeline fills the page.
> Verdicts are illustrative (Holm over 3 skills). The study's results replace this page before the launch.
"""


def pct(r: float) -> str:
    """Ratio -> signed percent change, e.g. 0.75 -> '-25%'."""
    v = (r - 1) * 100
    return f"{v:+.0f}%".replace("-", "−")


def fmt_ci(ci) -> str:
    return f"[{ci[0]:.2f}, {ci[1]:.2f}]"


def fmt_pp_ci(ci) -> str:
    return f"[{ci[0]:+.0f}, {ci[1]:+.0f}]".replace("-", "−")


def load(path: Path) -> dict | None:
    return json.loads(path.read_text()) if path.exists() else None


def with_verdicts(d: dict) -> dict:
    """Adds METHOD 9.1 verdicts when the file does not carry them (pilot files)."""
    comps = d["comparisons"]
    if all("verdict" in c for c in comps.values()):
        return d
    fields = Comparison.__dataclass_fields__
    objs = {k: Comparison(**{f: c[f] for f in fields}) for k, c in comps.items()}
    for k, v in verdicts(objs).items():
        comps[k]["verdict"] = v["verdict"]
        comps[k]["ratio_p_adj"], comps[k]["diff_p_adj"] = v["ratio_p_adj"], v["diff_p_adj"]
    return d


def harness_context(key: str, d: dict | None) -> dict:
    ctx: dict[str, str] = {}
    if d is None:
        return ctx
    d = with_verdicts(d)
    comps = d["comparisons"]
    meta = d.get("meta") or {}
    n_treat = sorted({c["n_treat"] for c in comps.values()})
    ctx[f"{key}.name"] = HARNESS[key]
    ctx[f"{key}.n_skills"] = str(len(comps))
    ctx[f"{key}.n_tasks"] = str(meta.get("n_tasks") or max(c["n_tasks"] for c in comps.values()))
    ctx[f"{key}.n_per_arm"] = str(meta.get("n_per_arm") or (n_treat[0] if len(n_treat) == 1 else f"{n_treat[0]}-{n_treat[-1]}"))
    # Without a meta block (pilot files): trials = every skill arm + every placebo arm once; model = the pin.
    n_trials = meta.get("n_trials") or (sum(c["n_treat"] for c in comps.values())
                                        + sum({c.get("placebo"): c["n_control"] for c in comps.values()}.values()))
    ctx[f"{key}.n_trials"] = f"{n_trials:,}"
    from skill_placebo.harnesses import HARNESSES
    ctx[f"{key}.model"] = meta.get("model") or HARNESSES[{"cc": "claude-code", "codex": "codex"}[key]].model.split("/")[-1]
    counts = {"beats placebo": 0, "no better than placebo": 0, "worse than placebo": 0, "trade-off": 0}
    for skill, c in comps.items():
        p = f"{key}.{skill}"
        ctx[f"{p}.R"] = f"{c['ratio']:.2f}"
        ctx[f"{p}.R_ci"] = fmt_ci(c["ratio_ci"])
        ctx[f"{p}.pct"] = pct(c["ratio"])
        ctx[f"{p}.pct_ci"] = f"[{pct(c['ratio_ci'][0])}, {pct(c['ratio_ci'][1])}]"
        ctx[f"{p}.D"] = f"{c['diff_pp']:+.0f} pp".replace("-", "−")
        ctx[f"{p}.D_ci"] = fmt_pp_ci(c["diff_ci_pp"])
        ctx[f"{p}.pass_skill"] = f"{c['pass_treat']:.0%}"
        ctx[f"{p}.pass_placebo"] = f"{c['pass_control']:.0%}"
        ctx[f"{p}.placebo"] = c.get("placebo", "").replace("placebo-", "")
        ctx[f"{p}.verdict"] = c["verdict"]
        ctx[f"{p}.n"] = f"{c['n_treat']}/{c['n_control']}"
        base = ((d.get("vs_baseline") or {}).get(skill) or {}).get("cost_vs_baseline")
        if base:
            ctx[f"{p}.R_base"] = f"{base['ratio']:.2f}"
            ctx[f"{p}.R_base_ci"] = fmt_ci(base["ratio_ci"])
        if c.get("mean_output_tokens_skill") and c.get("mean_output_tokens_placebo"):
            ctx[f"{p}.output_pct"] = pct(c["mean_output_tokens_skill"] / c["mean_output_tokens_placebo"])
        counts[c["verdict"]] = counts.get(c["verdict"], 0) + 1
    ctx[f"{key}.n_beats"] = str(counts["beats placebo"])
    ctx[f"{key}.n_worse"] = str(counts["worse than placebo"])
    ctx[f"{key}.n_nobetter"] = str(counts["no better than placebo"])
    ctx[f"{key}.n_tradeoff"] = str(counts["trade-off"])
    lo = min(comps, key=lambda k: comps[k]["ratio"])
    hi = max(comps, key=lambda k: comps[k]["ratio"])
    for tag, k in (("cheapest", lo), ("dearest", hi)):
        ctx[f"{key}.{tag}.skill"] = k
        ctx[f"{key}.{tag}.pct"] = pct(comps[k]["ratio"])
        ctx[f"{key}.{tag}.R"] = f"{comps[k]['ratio']:.2f}"
        ctx[f"{key}.{tag}.R_ci"] = fmt_ci(comps[k]["ratio_ci"])
    ctx[f"{key}.results_table"] = results_table(comps)
    # Unadjusted CIs vs Holm-adjusted verdicts: name every case where they seem to disagree.
    odd, odd_zh = [], []
    for s_, c_ in comps.items():
        if (c_["ratio_ci"][1] < 1 or c_["ratio_ci"][0] > 1) and c_.get("ratio_p_adj", 0) >= 0.05:
            odd.append(f"{s_}: cost CI excludes 1, Holm-adjusted p = {c_['ratio_p_adj']:.3f}")
            odd_zh.append(f"{s_}：成本的未校正置信区间不含 1，Holm 校正后 p = {c_['ratio_p_adj']:.3f}")
        if (c_["diff_ci_pp"][1] < 0 or c_["diff_ci_pp"][0] > 0) and c_.get("diff_p_adj", 0) >= 0.05:
            odd.append(f"{s_}: pass-rate CI excludes 0, Holm-adjusted p = {c_['diff_p_adj']:.3f}")
            odd_zh.append(f"{s_}：通过率的未校正置信区间不含 0，Holm 校正后 p = {c_['diff_p_adj']:.3f}")
    ctx[f"{key}.ci_note"] = (f"CIs are unadjusted; verdicts use Holm-adjusted p across {len(comps)} skills"
                             + (f" ({'; '.join(odd)})" if odd else "") + ".")
    ctx[f"{key}.ci_note_zh"] = (f"置信区间未经校正；判定使用 {len(comps)} 个 skill 的 Holm 校正 p 值"
                                + (f"（{'；'.join(odd_zh)}）" if odd_zh else "") + "。")
    pvb = d.get("placebo_vs_baseline") or {}
    if pvb:  # every placebo vs no skill: what extra text alone does to cost
        rs = sorted(m["cost_vs_baseline"]["ratio"] for m in pvb.values())
        ctx[f"{key}.placebo_vs_base_range"] = f"{pct(rs[0])} to {pct(rs[-1])}"
    vb = d.get("vs_baseline") or {}
    if vb:
        k = min(vb, key=lambda s: vb[s]["cost_vs_baseline"]["ratio"])
        m = vb[k]["cost_vs_baseline"]
        ctx[f"{key}.base_cheapest.skill"], ctx[f"{key}.base_cheapest.pct"] = k, pct(m["ratio"])
        ctx[f"{key}.base_cheapest.R"] = f"{m['ratio']:.2f}"
        ctx[f"{key}.base_cheapest.R_ci"] = fmt_ci(m["ratio_ci"])
        ctx[f"{key}.n_dearer_than_base"] = str(sum(1 for x in vb.values() if x["cost_vs_baseline"]["ratio_ci"][0] > 1))
        n_cheaper = sum(1 for x in vb.values() if x["cost_vs_baseline"]["ratio_ci"][1] < 1)
        ctx[f"{key}.n_cheaper_than_base"] = str(n_cheaper)
        ctx[f"{key}.n_cheaper_than_base_text"] = (f"none of the {len(vb)} skills" if n_cheaper == 0
                                                  else f"{n_cheaper} of the {len(vb)} skills")
        ctx[f"{key}.secondary_line"] = (
            f"Secondary, against no skill: {ctx[f'{key}.n_cheaper_than_base_text']} "
            f"{'was' if n_cheaper in (0, 1) else 'were'} measurably cheaper than running without a skill; "
            f"a same-length placebo alone changed cost by {ctx.get(f'{key}.placebo_vs_base_range', '')}.")
        ctx[f"{key}.secondary_line_zh"] = (
            f"次要结果（与不装 skill 相比）：{'没有一个' if n_cheaper == 0 else str(n_cheaper) + ' 个'} skill 的成本明显低于不装 skill；"
            f"同样长度的安慰剂本身使成本变化 {ctx.get(f'{key}.placebo_vs_base_range', '')}。")
    halves = sorted((c["diff_ci_pp"][1] - c["diff_ci_pp"][0]) / 2 for c in comps.values())
    hw = halves[len(halves) // 2]  # median half-width of D's 95% CI over skills
    ctx[f"{key}.d_ci_halfwidth"] = f"{hw:.0f}"
    ctx[f"{key}.d_sentence"] = (f"with this many trials its 95% CI is about ±{hw:.0f} points, too wide to rank skills by"
                                if hw >= 5 else
                                f"most tasks sit at the ceiling, so pass rates barely differ between arms "
                                f"(median 95% CI ±{hw:.0f} points) and carry little information")
    rest = [f"{counts['worse than placebo']} worse", f"{counts['no better than placebo']} no better"]
    if counts["trade-off"]:
        rest.append(f"{counts['trade-off']} trade-off")
    beat_p = sorted({f"{c['ratio_p_adj']:.3f}".rstrip("0") for c in comps.values() if c["verdict"] == "beats placebo"})
    p_txt = (f", at Holm-adjusted p = {' and '.join(beat_p)}" if len(beat_p) > 1 else
             f", at Holm-adjusted p = {beat_p[0]}" if beat_p else "")
    if counts["beats placebo"] == 2 and len(beat_p) == 1:
        p_txt = f", both at Holm-adjusted p = {beat_p[0]}"
    ctx[f"{key}.headline"] = (f"{counts['beats placebo']} of {len(comps)} skills beat a same-length placebo{p_txt} "
                              f"({', '.join(rest)})")
    ctx[f"{key}.beat_p_zh"] = (f"（Holm 校正后 p = {'、'.join(beat_p)}）" if beat_p else "")
    ctx[f"{key}.headline_zh"] = (f"{len(comps)} 个 skill 中 {counts['beats placebo']} 个优于安慰剂{ctx[f'{key}.beat_p_zh']}，"
                                 f"{counts['worse than placebo']} 个更差，{counts['no better than placebo']} 个没有差别"
                                 + (f"，{counts['trade-off']} 个有取舍" if counts["trade-off"] else ""))
    return ctx


def results_table(comps: dict) -> str:
    rows = ["| Skill | Cost vs placebo R [95% CI] | Change | Pass skill / placebo | D, pp [95% CI] | Verdict | n |",
            "|---|---|---:|---|---|---|---|"]
    for skill in sorted(comps, key=lambda k: (PRIORITY.index(k) if k in PRIORITY else 99)):
        c = comps[skill]
        d = f"{c['diff_pp']:+.0f}".replace("-", "−")
        rows.append(f"| {skill} | {c['ratio']:.2f} {fmt_ci(c['ratio_ci'])} | {pct(c['ratio'])} | "
                    f"{c['pass_treat']:.0%} / {c['pass_control']:.0%} | {d} {fmt_pp_ci(c['diff_ci_pp'])} | {c['verdict']} | "
                    f"{c['n_treat']}/{c['n_control']} |")
    return "\n".join(rows)


def claims_table(claims: dict, cc: dict | None) -> str:
    """'Claimed' comes from results/claims.json; 'measured' from the Claude Code results when the
    quantity exists there (vs_baseline for the main run), otherwise it says why not."""
    comps = (cc or {}).get("comparisons", {})
    vb = (cc or {}).get("vs_baseline", {})
    rows = ["| Skill | Claimed (quote, source) | Their setup | Our closest measure | Measured |", "|---|---|---|---|---|"]
    for s in claims["skills"]:
        if not s["claims"]:
            rows.append(f"| {s['skill']} | no numeric claim in README at [`{s['sha'][:7]}`](https://github.com/{s['repo']}/tree/{s['sha']}) | | | verdict only |")
            continue
        for cl in s["claims"]:
            src = f"[{cl['file']}{':' + str(cl['line']) if cl['line'] else ''}]({cl['url']})"
            for part in cl["parts"]:
                got = measured(part.get("our_key"), s["skill"], comps, vb)
                rows.append(f"| {s['skill']} | {part['claim']} ({src}) | {cl['their_setup']} | {part['our_measure']} | {got} |")
    return "\n".join(rows)


def measured(key: str | None, skill: str, comps: dict, vb: dict) -> str:
    if key is None:
        return "not measured by this design"
    b = vb.get(skill) or {}
    c = comps.get(skill) or {}
    if key == "pass_vs_baseline" and key in b:
        m = b[key]
        return f"{m['pass_arm']:.0%} vs {m['pass_baseline']:.0%} without the skill, D {m['diff_pp']:+.0f} {fmt_pp_ci(m['diff_ci_pp'])} pp".replace("D -", "D −")
    if key in b:
        m = b[key]
        n = f"; n = {m['n_treat']} / {m['n_control']} trials on {m['n_tasks']} tasks" if "n_treat" in m else ""
        small = " (few trials: read with care)" if m.get("n_treat", 99) < 20 else ""
        return f"{pct(m['ratio'])}, 95% CI [{pct(m['ratio_ci'][0])}, {pct(m['ratio_ci'][1])}]{n}{small}"
    if key in c and isinstance(c[key], dict):
        m = c[key]
        return f"{pct(m['ratio'])}, 95% CI [{pct(m['ratio_ci'][0])}, {pct(m['ratio_ci'][1])}]"
    if key == "output_tokens_vs_placebo" and c.get("mean_output_tokens_skill"):
        return f"{pct(c['mean_output_tokens_skill'] / c['mean_output_tokens_placebo'])} (means, no CI in this file)"
    if not comps:
        return "pending"
    return "not in this data (pilot kill test has no baseline arm)" if skill in comps else "not in this run"


def chart_block(prefix: str, rel: str) -> str:
    return (f'<picture>\n  <source media="(prefers-color-scheme: dark)" srcset="{rel}/{prefix}-dark.svg">\n'
            f'  <img src="{rel}/{prefix}-light.svg" width="820" alt="Forest plot: cost ratio of each skill vs its '
            f'same-length placebo with 95% confidence intervals">\n</picture>')


def badge_svg(label: str, message: str, color: str) -> str:
    """Flat static badge (shields-style geometry; width from a 6.5 px/char estimate)."""
    lw, mw = 10 + int(6.5 * len(label)), 10 + int(6.5 * len(message))
    w = lw + mw
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{label}: {message}">'
            f'<title>{label}: {message}</title><clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>'
            f'<g clip-path="url(#r)"><rect width="{lw}" height="20" fill="#555"/><rect x="{lw}" width="{mw}" height="20" fill="{color}"/></g>'
            f'<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">'
            f'<text x="{lw / 2}" y="14">{label}</text><text x="{lw + mw / 2}" y="14">{message}</text></g></svg>')


BADGE_COLOR = {"beats placebo": "#2a78d6", "no better than placebo": "#6e6d69", "worse than placebo": "#6e6d69",
               "trade-off": "#6e6d69"}


def unwrap(text: str) -> str:
    """One line per paragraph (Gmail and X DMs show hard wraps as ragged lines); a block where every line is
    "Label: value" stays one line per item."""
    out = []
    for para in text.strip("\n").split("\n\n"):
        lines = para.split("\n")
        keep = len(lines) > 1 and all(re.match(r"^[A-Z][^:]{1,45}: ", ln) for ln in lines)
        out.append(para if keep else " ".join(ln.strip() for ln in lines))
    return "\n\n".join(out) + "\n"


def fill(text: str, ctx: dict, missing: set) -> str:
    def sub(m):
        k = m.group(1).strip()
        if k in ctx:
            return ctx[k]
        missing.add(k)
        return f"[[MISSING {k}]]"
    return re.sub(r"\{\{\s*([^{}]+?)\s*\}\}", sub, text)


def build_context(scope: str, cc_path: str | None = None, codex_path: str | None = None, out: str | None = None):
    """Every {{key}} the templates can use, from the results files of a scope; returns (ctx, sc, cc, cx)."""
    sc = dict(SCOPES[scope])
    if cc_path:
        sc["cc"] = Path(cc_path)
    if codex_path:
        sc["codex"] = Path(codex_path)
    if out:
        sc["out"], sc["readme"] = Path(out), Path(out) / "README.md"
    cc, cx = load(sc["cc"]), load(sc["codex"])
    claims = json.loads((ROOT / "results" / "claims.json").read_text())
    ctx = {**RUN, "scope_banner": PILOT_BANNER if scope == "pilot" else "",
           "date": sc["date"] or ((cc or {}).get("meta") or {}).get("date", ""),
           "claims_table": claims_table(claims, cc)}
    ctx.update(harness_context("cc", cc))
    ctx.update(harness_context("codex", cx))
    manual = ROOT / "docs" / "launch" / f"manual-{scope}.json"
    if manual.exists():  # e.g. {"surprise": "..."}: sentences chosen on final data, may hold placeholders
        for k, v in json.loads(manual.read_text()).items():
            ctx[k] = fill(v, ctx, set())
    for s_ in claims["skills"]:  # claim.<skill>.<our_key>: the measured side of one claims-table line
        for cl in s_["claims"]:
            for part in cl["parts"]:
                if part.get("our_key"):
                    ctx[f"claim.{s_['skill']}.{part['our_key']}"] = measured(
                        part["our_key"], s_["skill"], (cc or {}).get("comparisons", {}), (cc or {}).get("vs_baseline", {}))
                    m_ = ((cc or {}).get("vs_baseline", {}).get(s_["skill"]) or {}).get(part["our_key"])
                    if m_ and "ratio" in m_:  # short form for posts: "-2% [-9%, +6%]"
                        ctx[f"claim_short.{s_['skill']}.{part['our_key']}"] = (
                            f"{pct(m_['ratio'])} [{pct(m_['ratio_ci'][0])}, {pct(m_['ratio_ci'][1])}]")
    for k_, path_ in (("cc", ROOT / "results/main/claude-code/AGENT_LOGS.json"), ("codex", ROOT / "results/pilot/codex/AGENT_LOGS.json")):
        if path_.exists():  # the release assets (amendment 18)
            m_ = json.loads(path_.read_text())
            ctx[f"logs.{k_}.archive"], ctx[f"logs.{k_}.sha256"] = m_["archive"], m_["sha256"]
    rel_chart = "." if scope == "pilot" else "docs/img"
    ctx["chart"] = chart_block(sc["chart"], rel_chart)
    return ctx, sc, cc, cx


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scope", choices=list(SCOPES), default="pilot")
    ap.add_argument("--cc", help="override the Claude Code results file (dry runs)")
    ap.add_argument("--codex", help="override the Codex results file (dry runs)")
    ap.add_argument("--out", help="override the output directory; the README goes there too (dry runs)")
    a = ap.parse_args()
    ctx, sc, cc, cx = build_context(a.scope, a.cc, a.codex, a.out)
    out = sc["out"]
    out.mkdir(parents=True, exist_ok=True)
    missing: set[str] = set()
    written = []
    for tpl in sorted(TEMPLATES.rglob("*.md")):
        rel = tpl.relative_to(TEMPLATES)
        # README*.md go next to the README (repo root for the final build); the rest into the package.
        dest = sc["readme"].parent / rel.name if rel.name.startswith("README") else out / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        body = fill(tpl.read_text(), ctx, missing)
        if rel.name == "zh.md":  # HelloGitHub form limits: title <= 50 characters, description 32-256
            limits = {"项目标题": (1, 50), "Project Title": (1, 50), "项目描述": (32, 256), "Project Description": (32, 256)}
            body = re.sub(r"^\*\*(项目标题|项目描述|Project Title|Project Description)\*\*: (.*)$",
                          lambda m: (f"**{m.group(1)}**: {m.group(2)}  `{len(m.group(2))} chars"
                                     + ("" if limits[m.group(1)][0] <= len(m.group(2)) <= limits[m.group(1)][1]
                                        else f" - OUT OF {limits[m.group(1)][0]}-{limits[m.group(1)][1]}") + "`"),
                          body, flags=re.M)
        if rel.name == "x-thread.md":  # each post's length after filling (X: 280 without Premium)
            body = re.sub(r"(?ms)^(\d+/ .*?)(?=^\d+/ |\Z)",
                          lambda m: m.group(1).rstrip("\n") + f"  `{len(' '.join(m.group(1).split()))} chars"
                          + (" - over 280" if len(' '.join(m.group(1).split())) > 280 else "") + "`\n\n", body)
        if rel.name == "hn.md":  # annotate title lengths after filling (HN cuts at 80)
            body = re.sub(r"^(\d+\. )(Show HN: .*)$",
                          lambda m: f"{m.group(1)}{m.group(2)}  `{len(m.group(2))} chars{' - TOO LONG' if len(m.group(2)) > 80 else ''}`",
                          body, flags=re.M)
        if a.scope == "pilot" and not rel.name.startswith("README"):
            body = PILOT_BANNER + "\n" + body
        dest.write_text(body)
        written.append(dest)
    # Badges
    for h, d in (("cc", cc), ("codex", cx)):
        for skill, c in ((d or {}).get("comparisons") or {}).items():
            v = with_verdicts(d)["comparisons"][skill]["verdict"]
            msg = f"{v} ({pct(c['ratio'])} cost)" if v == "beats placebo" else v
            label = "placebo-tested" + (" (pilot)" if a.scope == "pilot" else "")
            dest = (out if a.scope == "pilot" else ROOT / "docs") / "badges" / f"{skill}-{h}.svg"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(badge_svg(label, msg, BADGE_COLOR.get(v, "#6e6d69")))
            written.append(dest)
    print(f"scope={a.scope}: {len(written)} files -> {out}, README -> {sc['readme']}")
    if missing:
        print(f"MISSING ({len(missing)}): " + ", ".join(sorted(missing)))


if __name__ == "__main__":
    main()
