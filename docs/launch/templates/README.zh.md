{{scope_banner}}
<p align="center">
{{chart}}
</p>

# skill-placebo

[English](README.md) · 中文

**给最热门的 coding agent skill 做安慰剂对照：一个 skill 是否比同样长度的中性文字更好？**

> 药物试验会给对照组吃糖丸。我们也给 coding agent 准备了一颗：与每个 skill 长度相同、安装方式相同的中性说明文字。

**{{cc.n_skills}} 个 skill 中 {{cc.n_beats}} 个优于安慰剂，{{cc.n_worse}} 个更差，{{cc.n_nobetter}} 个没有差别。** 对照组：同样长度、同样安装方式的中性安慰剂。<br>
<sub>测量日期 {{date}}：{{cc.n_tasks}} 个公开任务（SWE-bench Verified、Terminal-Bench 2.1、OpenThoughts-TBLite），Claude Code + {{cc.model}}，每组 {{cc.n_per_arm}} 次试验，共 {{cc.n_trials}} 次。方法在第一次运行前登记：[METHOD.md](METHOD.md)。原始轨迹：[`results/`](results/)。复现一行：`uvx skill-placebo run <owner/repo>`。</sub>

## 结果：Claude Code（{{cc.model}}）

{{cc.results_table}}

R 是 skill 的平均成本除以对应安慰剂的平均成本，小于 1 表示 skill 更省。D 是通过率差（百分点）。判定规则见
[METHOD.md 9.1](METHOD.md#91-verdict-per-skill-and-harness)，对 {{cc.n_skills}} 个 skill 做 Holm 校正。

## Codex（{{codex.model}}，次要结果）

{{codex.results_table}}

## 局限

- 两个模型，均为默认推理强度；任务是公开的，可能出现在训练数据中。
- 多数任务对 {{cc.model}} 来说已接近满分，因此通过率信息有限，结论以成本为主。
- 成本按 token 数乘以公开价格估算（运行使用的是订阅）。
