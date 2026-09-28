import json

from skill_placebo.arms import PRIORITY, claude_arms, mounts


def test_claude_arms_cover_all_skills_and_buckets():
    arms = claude_arms(PRIORITY)
    assert "baseline" in arms and arms["baseline"].harbor_args == ()
    assert sum(a.startswith("skill-") for a in arms) == 9
    assert sum(a.startswith("placebo-") for a in arms) == 5
    assert "SP_CLAUDE_MD=/opt/plugins/karpathy/CLAUDE.md" in arms["skill-karpathy"].harbor_args
    assert "CLAUDE_CODE_PLUGIN_DIRS=/opt/plugins/ponytail" in arms["skill-ponytail"].harbor_args


def test_every_plugin_mounted_read_only_in_every_arm():
    m = json.loads(mounts())
    targets = {x["target"] for x in m}
    assert {"/opt/plugins/ponytail", "/opt/plugins/placebo-cc-4", "/opt/plugins/placebo-cx-4"} <= targets
    assert all(x["read_only"] for x in m)


def test_codex_arms():
    from skill_placebo.arms import codex_arms
    arms = codex_arms(PRIORITY)
    skills = sorted(a for a in arms if a.startswith("skill-"))
    assert skills == ["skill-agent-skills", "skill-compound-engineering", "skill-mattpocock", "skill-planning-with-files",
                      "skill-ponytail", "skill-superpowers"]
    assert "SP_CODEX_PLUGINS=ponytail@ponytail-pinned" in arms["skill-ponytail"].harbor_args
    assert arms["skill-mattpocock"].harbor_args.count("--skill") == 25
    assert sum(a.startswith("placebo-") for a in arms) == 4
