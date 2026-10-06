{{scope_banner}}
<p align="center">
{{chart}}
</p>

# skill-placebo

[English](README.md) · 中文

**给最热门的 coding agent skill 做安慰剂对照：一个 skill 是否比同样长度的中性文字更好？**

> 药物试验会给对照组吃糖丸。我们也给 coding agent 准备了一颗：与每个 skill 长度相同、安装方式相同的中性说明文字。

**{{cc.headline_zh}}。** 对照组：同样长度、同样安装方式的中性安慰剂。<br>
{{cc.secondary_line_zh}}<br>
<sub>测量日期 {{date}}：{{cc.n_tasks}} 个公开任务（SWE-bench Verified、Terminal-Bench 2.1、OpenThoughts-TBLite），Claude Code + {{cc.model}}，每组 {{cc.n_per_arm}} 次试验，共 {{cc.n_trials}} 次。方法在第一次运行前登记：[METHOD.md](METHOD.md)。逐次试验记录：[`results/`](results/)；智能体完整日志：[release v0.1.0](https://github.com/simonether/skill-placebo/releases/tag/v0.1.0)（sha256 见 `results/*/*/AGENT_LOGS.json`）。复现一行：`{{run_cmd}}`。</sub>

## 结果：Claude Code（{{cc.model}}）

{{cc.results_table}}

{{cc.ci_note_zh}}<br>
{{cc.approval_note_zh}}<br>
2026-10-06 更正（[METHOD.md 修订 19](METHOD.md#16-amendments)）：两次代理超时、但之后测试通过的试验，按第 5、7 节改记为失败；planning-with-files 由“没有差别”改为“比安慰剂差”。成本不变。

R 是 skill 的平均成本除以对应安慰剂的平均成本，小于 1 表示 skill 更省。D 是通过率差（百分点）。判定规则见
[METHOD.md 9.1](METHOD.md#91-verdict-per-skill-and-harness)，对 {{cc.n_skills}} 个 skill 做 Holm 校正。

## Codex（{{codex.model}}，仅试点，次要结果）

{{codex.results_table}}

这是 Codex 试点阶段的 kill 测试：{{codex.n_skills}} 个 skill、{{codex.n_tasks}} 个任务、每组 {{codex.n_per_arm}} 次试验。v1 没有进行 Codex 主实验。

## 致 skill 作者

如果你的 skill 安装方式不对，或者对应的安慰剂对它不公平，请[提交 issue](https://github.com/simonether/skill-placebo/issues/new?template=skill-install-dispute.yml)：写明 skill、commit、问题所在以及如何验证。
所有试验记录都是公开的，可以直接指向具体的运行。确认的安装错误会让该 skill 的各组全部重跑、更新结果，在 METHOD.md 中以修订记录，
并在此处链接该 issue（[METHOD.md 第 14 节](METHOD.md#14-fairness-to-skill-authors)）。

## 局限

- 主实验只有一个模型：Claude Code 中的 {{cc.model}}，medium 推理强度（默认值）；Codex 只做了小规模试点；任务是公开的，可能出现在训练数据中。
- 多数任务对 {{cc.model}} 来说已接近满分，因此通过率信息有限，结论以成本为主。
- 成本按 token 数乘以公开价格估算。

---
<sub>作者 Simon（@simonether）· 我在 Keelfast 把用 AI 搭建的应用从演示带到生产环境。</sub>
