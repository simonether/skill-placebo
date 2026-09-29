# Harder task candidates, round 2 (2026-09-29)

Why: in the pilot, Claude Code + Opus 5.5 (medium) solved 10/10 baseline trials, including
`django__django-15957` (frontier panel 2/6) and `pylint-dev__pylint-7080` (1/6). This note looks for
harder candidates: SWE-bench Verified instances at 0-1/6 on the frontier panel, and Terminal-Bench 2.1
tasks where Opus 4.7 agents pass at most 60%. None of the picks is in `tasks/pool/manifest.json`.

Method: read-only `gh api`, anonymous HF/S3/GitHub reads, `docker manifest inspect` (no pulls), no
model calls. The frontier panel and filters are the ones in `2026-09-28-harder-tasks.md`; the panel
distribution reproduces exactly (0/6: 60, 1/6: 34, ..., 6/6: 264; `django-10973` F 3, S 3, O 8).

## TL;DR

- **SWE-bench: 7 picks and 2 borderline reserves, not 10.** 48 instances pass the mechanical filters
  (F ≤ 1/6, allowed repo, ≤ 3 files, solved by some run, not broken, not in pool). Two of them have
  no arm64 image, and only 9 of the remaining 46 survive the fairness check. The eval logs of the
  six panel runs show why. In most 0-1/6 instances, frontier models fail because the hidden tests
  pin something the issue does not ask for. Examples:
  - an exact output string or doctree node type;
  - a particular fix location;
  - an extra case, or a behaviour change.

  In 2 instances the panel failures come from a flaky test, not from difficulty.
- **The panel signal needs the logs, not just the counts.** `pylint-7277` is solved by 104 runs in total but
  only 1/6 on the panel. Opus 4.5 and Opus 4.6 submitted byte-identical patches (same blob
  `2ddc613d`): one resolved, the other failed on the P2P test `test_jobs_score`.
- **Terminal-Bench 2.1: only 1 clean pick and 1 conditional pick, not 5.** Pooled Opus 4.7
  (WOZCODE, vix, logos) is at or below 60% on 15 tasks. Two of these, `query-optimize` and
  `adaptive-rejection-sampler`, are already in the pool. The rest are almost all excluded:
  - chess, crypto or maths puzzles;
  - QEMU;
  - model or video tasks;
  - 8 GB of RAM;
  - agent timeouts of 1800-7200 s.

  The pick is `make-doom-for-mips` (3/15); the conditional pick is `video-processing` (8/15).

## A. SWE-bench Verified (F = 0-1/6)

### Sources

- Per-run resolved sets: `swe-bench/experiments` @ `40f164d5b8` (2026-09-03). The 175 runs with
  `results/results.json` or `per_instance_details.json` count; 7 runs have neither.
- Why the panel failed: `report.json` and `patch.diff` from the public bucket
  `s3://swe-bench-submissions/bash-only/<run>/logs/<id>/` (anonymous HTTPS; path from each run's
  `metadata.yaml`) for 5 panel runs. For Gemini 3.5 Flash they come from
  `github.com/john-b-yang/20260901_mini-v2.4.2_gemini-3-5-flash` @ `2f6637a`.
- Instance data: HF `princeton-nlp/SWE-bench_Verified` @ `c104f840`.
- Git-peek flags: `evaluation/verified/*/git_peek_suspicious_commits.md` (21 runs). Flagged
  (run, instance) pairs are not counted as solves. No pick is affected.
- Harbor dirs: `laude-institute/harbor-datasets` @ `86723674`, `datasets/swebench-verified/<id>`. All picks
  have `environment, instruction.md, solution, task.toml, tests`. `instruction.md` is the issue text
  only, without hints.
- arm64 images: `docker manifest inspect -v ghcr.io/epoch-research/swe-bench.eval.arm64.<id>:latest`,
  run 2026-09-29.

### Funnel

| Step | Left |
|---|---|
| F ≤ 1/6 over 500 instances | 94 |
| repo in django, sympy, pytest, sphinx, pylint, requests, flask, seaborn, xarray | 75 |
| solved by ≥ 1 run of any model (git-peek excluded) | 52 |
| gold patch ≤ 3 files | 51 |
| not a broken Harbor oracle, not in pool | 48 |
| Epoch arm64 manifest exists (both xarray instances fail this) | 46 |
| fairness check (issue text vs hidden tests, panel failure modes) | **7 picks + 2 reserves** |

### A.1 Picks

**Column notes:**
- **Total** is the number of runs of all 175 that solve the instance.
- **S** and **O** are the 4-run Sonnet-class and 12-run open-model panels.
- **Patch** is files and added/removed lines.
- **arm64** is the Epoch image: digest prefix and layer size.

| # | Instance | Issue (one line) | Label | Patch | F (who) | S | O | Total | arm64 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | django__django-13512 | Admin shows non-ASCII in JSONField as `\uXXXX` | <15m | 2 / +3-2 | 0/6 | 2/4 | 6/12 | 53 | `6a272aaf…`, 961 MB |
| 2 | django__django-14140 | `Q(Exists(...)).deconstruct()` crashes: single-child special case | 15m-1h | 1 / +4-8 | 1/6 (GPT-5.2-high v1) | 1/4 | 4/12 | 46 | `1578851f…`, 987 MB |
| 3 | django__django-11141 | allow migrations dirs without `__init__.py` (namespace packages) | 15m-1h | 1 / +4-6 | 1/6 (Gemini 3.5 Flash) | 0/4 | 1/12 | 23 | `0986d26e…`, 960 MB |
| 4 | sphinx-doc__sphinx-10435 | LaTeX inline code highlighting adds a space at start and end | <15m | 1 / +3-3 | 1/6 (GPT-5.2-high v2) | 0/4 | 2/12 | 7 | `c402b674…`, 824 MB |
| 5 | django__django-16256 | `acreate`/`aget_or_create`/`aupdate_or_create` on related managers call the QuerySet versions | 15m-1h | 2 / +55 | 1/6 (Gemini 3.5 Flash) | 0/4 | 0/12 | 6 | `4015ab52…`, 1026 MB |
| 6 | sympy__sympy-17630 | `block_collapse(b*b*b)` with ZeroMatrix blocks: `'Zero' object has no attribute 'cols'` | 1-4h | 1 / +2 | 1/6 (Gemini 3.5 Flash) | 0/4 | 1/12 | 4 | `8a73a348…`, 898 MB |
| 7 | django__django-11734 | `OuterRef` in `exclude()` / `~Q()` uses the wrong model | 15m-1h | 3 / +4-6 | 0/6 | 0/4 | 0/12 | 4 | `6acc328f…`, 960 MB |

**Full digests:**
- 13512: `sha256:6a272aafc118cce5a8cf69a799a68a4466e6621d583ae160a00929fc332aed30`
- 14140: `sha256:1578851fcc2acd92b9f942c13f70d54ee696b64335fa4a82ab8c7cfd56fe6315`
- 11141: `sha256:0986d26e380dedb0c9b7515b9a3d734dc1754604d4d744886cd0e9ddfc0a53d5`
- 10435: `sha256:c402b674b9ad20fe157b63be3ba86b4ddb98850ec044e75fbcedca9ee252a87c`
- 16256: `sha256:4015ab52b068f071ec268f4914bdb3301edc6c170485263a107afbe4d07bb88b`
- 17630: `sha256:8a73a34820b271dea84bccdc0874709b180b08d040fed7be938c32db92cfb650`
- 11734: `sha256:6acc328f952f95c2bfcb0dcc3dedd024923e8e4c343851c3b1d686f5f1753aee`

**Why the panel fails, and why the test is still fair** (taken from the panel `report.json` files and
the issue and test patch):

1. **13512.** All 6 runs fix the form widget (`forms.JSONField.prepare_value`) but not the admin
   read-only display (`admin.utils.display_for_field`). The issue title is "Admin doesn't display
   properly unicode chars", so the display is in scope.
   - `test_label_for_field` is also listed in FAIL_TO_PASS although it is unrelated. It flips together
     with `test_json_display_for_field` in every panel run, so in practice there is one requirement.
2. **14140.** Five runs pick the "backward-compatible" variant: keep the kwargs special case and
   check for a 2-tuple. The hidden tests need the variant the issue attributes to PR 14126: a
   single child deconstructs into args. The issue adds that "it's unlikely that anyone is relying on
   this undocumented behavior".
   - **Borderline:** the issue names both options. It leans toward the PR, and the hidden tests
     update existing visible `test_deconstruct*` expectations.
3. **11141.** The F2P test is exactly the issue. The 5 failing runs all break the existing, visible P2P
   test `test_load_empty_dir`, because an empty directory must stay "unmigrated". Running the
   migrations test module catches it. This is a verification failure, which is the behaviour workflow
   skills aim at.
4. **10435.** The test checks an exact string, but the issue spells out that exact markup
   (`\sphinxupquote{%` … `%` newline `}}`). All three Claude runs instead strip the newlines. That also
   removes the visible space, but it does not match what the issue asks for. GPT-5.2-high v2
   follows the issue and passes.
5. **16256.** The F2P tests cover the managers in `related_descriptors.py` (6 tests) and the
   GenericRelation manager in `contrib/contenttypes/fields.py` (3 tests). The issue says "related
   managers" in general; its example diff shows only the first file. Opus 4.6 passes the first 6 and
   misses the generic manager. This is a thoroughness failure.
6. **17630.** Every failing run passes `test_issue_17624` (the issue's example) and fails
   `test_zero_matrix_add`: `Add(ZeroMatrix, ZeroMatrix) == ZeroMatrix`. The issue itself identifies
   `Zero` instead of `ZeroMatrix` as the cause and asks why it happens. The test checks the root
   cause, not the symptom.
   - **Borderline:** a local fix inside `blockmatrix.py` resolves the example but fails.
7. **11734.** The F2P test is the issue's pattern: `Exists(...exclude(m2m=OuterRef(...)))`. It is
   behavioural (`qs.exists()` before and after a delete). The case is hard: ORM internals across 3
   files, 0/22 on the F, S and O panels, and solved by only 4 runs, all from 2025 (zencoder, trae,
   two Gemini 3 Pro runs). **Risk: 0% baseline.**

**Network:** every F2P test runs locally. Django uses `runtests.py --settings=test_sqlite`, sympy
uses `bin/test`, and sphinx `test_build_latex.py` writes `.tex` without compiling it. **Caveat:** the
sphinx verifier script runs `python -m pip install -e .[test]` and `tox --current-env`
(`tests/test.sh:16,50`). Run the oracle twice, as the pool rule requires, before relying on
it offline.

### A.2 Borderline reserves

| Instance | F | Total | Epoch arm64 | Why only a reserve |
|---|---|---|---|---|
| sympy__sympy-13974 (`TensorProduct` powers don't evaluate) | 1/6 (Gemini 3.5 Flash) | 26 | `f193a40d…`, 897 MB | The test needs `tensor_product_simp(TP(A,B)**x) == TP(A**x,B**x)` with a **symbolic** exponent. The issue shows only squares. GPT-5.2-high restricts to non-negative integers (mathematically careful) and fails. |
| django__django-13195 (`delete_cookie()` should preserve SameSite) | 0/6 | 3 | `0bae2c3e…`, 961 MB | Needs several things the issue only implies: a `samesite` kwarg, automatic `Secure` for `samesite='none'`, and sessions and messages passing their settings. Most runs fail `test_delete_cookie_secure_samesite_none`. 3 files. |

Still unused from 28.09: the 2/6 picks `django__django-12273`, `sphinx-doc__sphinx-8056` and
`sympy__sympy-20916` (see that note for their caveats).

### A.3 Rejected (37 on fairness, 2 without an arm64 image)

The panel failure mode comes from `report.json`.

| Reason | Instances (F, total runs) |
|---|---|
| **Panel failures are a flaky or environment P2P test, not difficulty** | pylint-7277 (1, 104): 4/5 runs fail only `test_jobs_score`, and an identical patch passes in Opus 4.6. pylint-6528 (1, 56): F2P passes and every failing run breaks the same multiprocessing P2P set, including `test_jobs_score`. |
| **Hidden test forbids a correct answer, or contradicts the issue** | sympy-15875 (0, 77): `is_zero is None`, where `True` is correct and the issue allows it. django-15695 (1, 14): backwards stays a no-op, against the issue's "should restore the old name". django-14170 (0, 3): the tests keep the BETWEEN optimisation for `iso_year`, while the issue's fix removes it (all 6 fail the same 9 P2P tests). sympy-13798 (0, 8): expected spacing differs from the issue's own example. |
| **Hidden test needs behaviour the issue does not state** | sympy-23950 (1, 99): a second free symbol in `Contains(x, FiniteSet(y))`. django-15022 (0, 90): changes search semantics over multi-valued relations; the issue is only about JOINs. sympy-18763 (0, 56): parentheses around a plain Mul. pylint-4970 (1, 28): standalone `symilar` output. django-12308 (0, 27): fallback repr for non-JSON keys. django-12325 (0, 19): drops implicit parent-link inference. seaborn-3187 (1, 9): the issue suggests putting the offset in the title or labels, but the test needs plain full values. django-13344 (1, 7): deprecation warnings for 19 middlewares. django-13794 (0, 7): `lazy int + lazy int`. django-11477 (0, 5): the issue points at a test in an unshown patch. pytest-10356 (0, 3): new `consider_mro` kwarg. sphinx-9461 (1, 2): new `:classmethod:` option. django-15098 (0, 2): extra BCP-47 forms (`i-mingo`, `nan-hani-tw`). sphinx-10614 (0, 2): intersphinx external links. django-11820 (0, 1): extra E015 case. django-15252 (0, 1): `TEST['MIGRATE']=False` path. sympy-13852 (0, 1): extra polylog values. sympy-18199 (0, 1): composite moduli. sympy-21596 (0, 1): extra imageset cases. |
| **Hidden test pins an exact string, node type or fix location** | pylint-8898 (1, 12): exact regex error message. sympy-14248 (1, 12): pretty string `-A*B -B*C + A*B*C`. sphinx-9602 (1, 8) and sphinx-7462 (1, 1): doctree node types. sympy-22080 (0, 2): codegen strings. django-14792 (0, 2): fix must be in `_get_timezone_name`, but all 6 runs fix the backends. django-14315 (0, 3): `runshell` must pass `env=None`. django-11400 (0, 1): fix must be in `Field.get_choices`. sphinx-9229 (0, 1): alias output. sphinx-7590 (0, 1): C++ id encodings, over 4 h. pytest-5840 (0, 2): a Windows-only bug, and the test pins internal dict keys. django-14140 is kept as pick 2 despite a similar concern (see A.1). |
| **Network in F2P** | sphinx-7985 (1, 7): the linkcheck tests reach google.com and sphinx-doc.org. |
| **No Epoch arm64 image** | pydata__xarray-6599, pydata__xarray-6938. |

**Context on the pool picks.** In the pool picks from 28.09, the panel fails for real reasons, not
flakes: 7080 fails F2P `test_ignore_path_re` in 4/5 runs, and 15957, 15563, 15973 and 11265 all
fail F2P. Opus 5.5 in Claude Code still solved 7080 and 15957. So 0/6 on the mini-SWE-agent panel
does not mean out of reach for it.

## B. Terminal-Bench 2.1

### Sources

- Tasks: `harbor-framework/terminal-bench-2-1` @ `7131e4375048a0e408a8fb404b5f499d726b695b`
  (`tasks/<name>/task.toml`, `instruction.md`, `environment/Dockerfile`, `tests/`).
- Opus 4.7 per trial: HF `harborframework/terminal-bench-2-leaderboard` @ `572b2614`. The job-level
  `result.json` (`stats.evals.*.reward_stats`, `exception_stats`) comes from:
  - `WOZCODE__Claude-Opus-4-7/2026-04-19__20-07-00`;
  - `vix__claude-opus-4-7/2026-04-30__17-57-22`;
  - `logos-latest__claude-opus-4.7/2026-04-21`.

  Each has 445 trial dirs, 5 per task. A trial without a reward counts as a fail.
  - These runs are **TB2.0**. For the tasks below, 2.1 changed only `task.toml` (metadata), README
    and `.gitignore`, except `make-doom-for-mips`, where `solution/solve.sh` also changed (tree
    diff: `terminal-bench-2` @ `69671fb` vs 2.1).
- CC + Opus 4.6 (5 trials per task, TB2.0): HF `yoonholee/terminalbench-trajectories` @ `04e8940`.
- Not usable: TB2.1 per-task results for CC + Opus 4.7 max (job `10e2e56b…`, PR #44). The Harbor hub page
  returns 404 anonymously (2026-09-29); the leaderboard JSON lists only trial UUIDs.

### Tasks with pooled Opus 4.7 ≤ 60% (TB2.0)

| Task | O4.7 (woz / vix / logos) | CC + O4.6 | Agent timeout / RAM (2.1) | Verdict |
|---|---|---|---|---|
| **make-doom-for-mips** | 0/5, 3/5, 0/5 → **3/15** | 0/5 (median 16.1 min) | 900 s / 2 GB | **Pick** |
| **video-processing** | 1/5, 4/5, 3/5 → **8/15** | 1/5 (median 8.2 min) | **3600 s** / 2 GB | **Conditional pick** |
| gcode-to-text | 2/5, 3/5, 3/5 → 8/15 | 1/5 | 900 s / 2 GB | reserve: a CTF puzzle; the test compares against one exact `flag{...}` string |
| raman-fitting | 0/5, 2/5, 3/5 → 5/15 | 2/5 | 900 s / 2 GB | reserve: domain science (spectral peak fitting) |
| train-fasttext | 0/5, 2/5, 5/5 → 7/15 | 0/5 (median **61 min**) | 3600 s / 4 GB | no: 1200 s is not plausible (CC + O4.6 runs about 61 min; 7 O4.7 trials hit the 3600 s AgentTimeout, plus 2 cancelled); model training |
| gpt2-codegolf | 7/15 | 0/5 | 900 s / **8 GB** | no: 8 GB, code golf |
| model-extraction-relu-logits | 6/15 | 0/5 | 900 s / 2 GB | no: maths / cryptanalysis puzzle |
| sam-cell-seg | 6/15 | 0/5 | 7200 s / 4 GB | no: SAM model, 7200 s |
| caffe-cifar-10 | 3/15 | 0/5 | 3600 s / 8 GB | no: 8 GB, ML training |
| extract-moves-from-video | 1/15 | 0/5 | 1800 s / 2 GB | no: OCR of a video; the video file changed in 2.1 |
| regex-chess, chess-best-move | 6/15, 9/15 | 3/5, 0/5 | 3600 / 900 s | no: chess |
| install-windows-3.11 | 0/10 | 0/5 | 3600 s / 4 GB | no: QEMU |
| query-optimize, adaptive-rejection-sampler | 9/15, 9/15 | 2/5, 0/5 | 900 s | already in the manifest (ARS left the pool on the oracle rule) |

The next band up (61-73%) does not help. Every task in it misses a hard criterion:
- `filter-js-from-html` 10/15: 8 GB, security.
- `mteb-leaderboard` 10/15: 8 GB, 3600 s.
- `dna-insert` 11/15: bio.
- `mailman` 11/15: the server must stay up.
- `rstan-to-pystan` 11/15: 8 GB.
- `pytorch-model-cli` 11/15: CC + O4.6 already 4/5.

### Pick notes

- **make-doom-for-mips.** Build `doomgeneric` into a MIPS ELF that the provided `vm.js` runs.
  - The tests check behaviour: they run `node vm.js`, expect the `I_InitGraphics` line on stdout, and
    compare `/tmp/frame.bmp` to a reference (L2 similarity).
  - The work is cross-compilation and build engineering. The reference solution writes its own
    Makefile, a minimal libc and a clang → llc → `mips-linux-gnu-as/ld` pipeline. The expert
    estimate is 480 min (`task.toml`).
  - No QEMU and no model. The image build clones `ozkl/doomgeneric` and fetches `doom1.wad` from
    ibiblio. The agent must `apt install` clang, llvm and `binutils-mips-linux-gnu` itself, so it
    needs network in the agent phase. All three exist for bookworm arm64 (packages.debian.org).
  - Base image `python:3.13-slim-bookworm` is already mirrored.
  - **Timeouts dominate:** 8 of 12 O4.7 failures are `AgentTimeoutError` at 900 s (woz 1, vix 2,
    logos 5). The pool rule min(upstream, 1200) keeps 900 s. The risk is a baseline near 0% at
    900 s. `logos-ts` Opus 4.7 scores 0/5 as well.
- **video-processing (conditional).** Write `jump_analyzer.py` (cv2, numpy, toml) that finds the
  take-off and landing frames in hurdle videos. It is graded against a hidden `test_video.mp4`.
  - Upstream agent timeout is 3600 s, above our 1200 s cap. 1200 s is plausibly enough:
    - the CC + O4.6 median is 8.2 min, and its one success took 8.6 min;
    - only 1 of 7 O4.7 failures is a timeout (vix); the rest are wrong answers.
  - It is general scripting against unseen data, but it is heuristic computer vision.
  - `pip install opencv-contrib-python` at build; aarch64 wheels exist.

**Bottom line for TB.** The criteria leave 1-2 tasks, not 5. For more, relax one criterion:
- allow domain or puzzle tasks: add `raman-fitting`, `gcode-to-text`;
- or use SWE-bench / TBLite for the hard end instead.

## Reproduce

1. **SWE panel**
   1. Download every `evaluation/verified/*/results/results.json` and `per_instance_details.json`
      at `40f164d5b8` with
      `gh api -H "Accept: application/vnd.github.raw" repos/swe-bench/experiments/contents/<path>?ref=40f164d5b8`.
   2. Count `resolved` per instance over the F panel and over all runs.
   3. Drop (run, instance) pairs listed in the "All iids" block of `git_peek_suspicious_commits.md`.
2. **Panel failure modes**
   - `curl https://swe-bench-submissions.s3.amazonaws.com/bash-only/<run>/logs/<id>/report.json`
     (and `patch.diff`). This works for the Opus 4.5 v1.16, Opus 4.5-high, Opus 4.6, GPT-5.2-high
     v1.17.2 and GPT-5.2-high v2 runs.
   - Gemini 3.5 Flash: `gh api repos/john-b-yang/20260901_mini-v2.4.2_gemini-3-5-flash/contents/logs/<id>/report.json?ref=2f6637a`.
   - Read `tests_status.FAIL_TO_PASS/PASS_TO_PASS.failure`.
3. **TB**
   - Opus 4.7: read `stats.evals.*.reward_stats.reward["1.0"]` and `exception_stats` from the three job-level
     `result.json` files above, and count trial dirs per task from the HF tree API.
   - CC + Opus 4.6: filter the parquet on `agent == "claude-code"` and `model == "claude-opus-4-6@anthropic"`.
