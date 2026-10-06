
<p align="center">
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/simonether/skill-placebo/main/docs/img/forest-dark.svg">
  <img src="https://raw.githubusercontent.com/simonether/skill-placebo/main/docs/img/forest-light.svg" width="820" alt="Forest plot: cost ratio of each skill vs its same-length placebo with 95% confidence intervals">
</picture>
</p>

# skill-placebo

[English](https://github.com/simonether/skill-placebo/blob/main/README.md) · 中文

**给最热门的 coding agent skill 做安慰剂对照：一个 skill 是否比同样长度的中性文字更好？**

> 药物试验会给对照组吃糖丸。我们也给 coding agent 准备了一颗：与每个 skill 长度相同、安装方式相同的中性说明文字。

**9 个 skill 中 2 个优于安慰剂（Holm 校正后 p = 0.049），1 个更差，6 个没有差别。** 对照组：同样长度、同样安装方式的中性安慰剂。<br>
次要结果（与不装 skill 相比）：没有一个 skill 的成本明显低于不装 skill；同样长度的安慰剂本身使成本变化 +2% to +16%。<br>
<sub>测量日期 2026-09-30：15 个公开任务（SWE-bench Verified、Terminal-Bench 2.1、OpenThoughts-TBLite），Claude Code + claude-opus-5-5，每组 30 次试验，共 450 次。方法在第一次运行前登记：[METHOD.md](https://github.com/simonether/skill-placebo/blob/main/METHOD.md)。逐次试验记录：[`results/`](https://github.com/simonether/skill-placebo/tree/main/results/)；智能体完整日志：[release v0.1.0](https://github.com/simonether/skill-placebo/releases/tag/v0.1.0)（sha256 见 `results/*/*/AGENT_LOGS.json`）。复现一行：`uvx skill-placebo run <owner/repo>`。</sub>

## 结果：Claude Code（claude-opus-5-5）

| Skill | Cost vs placebo R [95% CI] | Change | Pass skill / placebo | D, pp [95% CI] | Verdict | n |
|---|---|---:|---|---|---|---|
| superpowers † | 0.98 [0.91, 1.06] | −2% | 83% / 87% | −3 [−10, +0] | no better than placebo | 30/30 |
| mattpocock | 1.05 [0.99, 1.12] | +5% | 83% / 87% | −3 [−10, +0] | no better than placebo | 30/30 |
| karpathy | 1.09 [0.93, 1.23] | +9% | 83% / 87% | −3 [−13, +7] | no better than placebo | 30/30 |
| ponytail † | 0.88 [0.76, 0.97] | −12% | 90% / 87% | +3 [−7, +13] | beats placebo | 30/30 |
| caveman | 0.99 [0.91, 1.06] | −1% | 90% / 83% | +7 [+0, +17] | no better than placebo | 30/30 |
| agent-skills | 0.95 [0.90, 0.99] | −5% | 83% / 83% | +0 [−10, +10] | beats placebo | 30/30 |
| i-have-adhd † | 0.92 [0.86, 0.98] | −8% | 87% / 87% | +0 [−10, +10] | no better than placebo | 30/30 |
| planning-with-files | 1.05 [0.91, 1.19] | +5% | 80% / 100% | −20 [−37, −7] | worse than placebo | 30/30 |
| compound-engineering | 1.04 [0.91, 1.23] | +4% | 87% / 87% | +0 [−10, +10] | no better than placebo | 30/30 |

置信区间未经校正；判定使用 9 个 skill 的 Holm 校正 p 值（i-have-adhd：成本的未校正置信区间不含 1，Holm 校正后 p = 0.095）。<br>
† 脚本化批准，不是作者文档中的模式（[METHOD.md 5.1](https://github.com/simonether/skill-placebo/blob/main/METHOD.md#51-scripted-approval-turn)）：在 448 次有记录的试验中触发 4 次（ponytail 1、i-have-adhd 2、安慰剂 cc-3 1），superpowers 从未触发。<br>
2026-10-06 更正（[METHOD.md 修订 19](https://github.com/simonether/skill-placebo/blob/main/METHOD.md#16-amendments)）：两次代理超时、但之后测试通过的试验，按第 5、7 节改记为失败；planning-with-files 由“没有差别”改为“比安慰剂差”。成本不变。

R 是 skill 的平均成本除以对应安慰剂的平均成本，小于 1 表示 skill 更省。D 是通过率差（百分点）。判定规则见
[METHOD.md 9.1](https://github.com/simonether/skill-placebo/blob/main/METHOD.md#91-verdict-per-skill-and-harness)，对 9 个 skill 做 Holm 校正。

## Codex（gpt-6-sol，仅试点，次要结果）

| Skill | Cost vs placebo R [95% CI] | Change | Pass skill / placebo | D, pp [95% CI] | Verdict | n |
|---|---|---:|---|---|---|---|
| ponytail | 1.09 [0.90, 1.23] | +9% | 90% / 100% | −10 [−30, +0] | no better than placebo | 10/10 |
| agent-skills | 1.24 [1.10, 1.42] | +24% | 100% / 80% | +20 [+0, +60] | worse than placebo | 10/10 |
| compound-engineering | 1.42 [1.23, 1.64] | +42% | 100% / 100% | +0 [+0, +0] | worse than placebo | 10/10 |

这是 Codex 试点阶段的 kill 测试：3 个 skill、5 个任务、每组 10 次试验。v1 没有进行 Codex 主实验。

## 致 skill 作者

如果你的 skill 安装方式不对，或者对应的安慰剂对它不公平，请[提交 issue](https://github.com/simonether/skill-placebo/issues/new?template=skill-install-dispute.yml)：写明 skill、commit、问题所在以及如何验证。
所有试验记录都是公开的，可以直接指向具体的运行。确认的安装错误会让该 skill 的各组全部重跑、更新结果，在 METHOD.md 中以修订记录，
并在此处链接该 issue（[METHOD.md 第 14 节](https://github.com/simonether/skill-placebo/blob/main/METHOD.md#14-fairness-to-skill-authors)）。

## 局限

- 主实验只有一个模型：Claude Code 中的 claude-opus-5-5，medium 推理强度（默认值）；Codex 只做了小规模试点；任务是公开的，可能出现在训练数据中。
- 多数任务对 claude-opus-5-5 来说已接近满分，因此通过率信息有限，结论以成本为主。
- 成本按 token 数乘以公开价格估算。

---
<sub>作者 Simon（@simonether）· 我在 Keelfast 把用 AI 搭建的应用从演示带到生产环境。</sub>
