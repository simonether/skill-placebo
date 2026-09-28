# Harder task candidates for Opus 5.5 (2026-09-28)

Why: the target is now Claude Opus 5.5 in Claude Code, much stronger than the Sonnet-class models the
pool (`tasks/pool/manifest.json`, 30 tasks) was calibrated for. This note adds 10 harder candidates
(6 SWE-bench Verified, 4 Terminal-Bench 2.1) whose baseline could plausibly land at 30-70%.
None of them is in the current manifest.

Method: read-only `gh api`, HF and web reads, and `docker manifest inspect` (no pulls, no model
calls). The frontier panel from `2026-09-25-task-pool.md` §2.2 was reproduced exactly (below).

## TL;DR

- **SWE-bench: 6 picks, all 2/6 on the frontier panel.** Four are django, plus one sphinx and one
  sympy. Each has an Epoch arm64 image and a Harbor task dir, and none needs network in its tests.
  Two other 2/6 instances were rejected: their hidden tests check things the issue text does not
  ask for, or contradicts.
- **Terminal-Bench 2.1: 4 picks meet every stated criterion.** They are `query-optimize`,
  `write-compressor`, `headless-terminal` and `make-mips-interpreter`, each at 40-60% for CC + Opus 4.6.
- **Main risk: the TB picks, and the existing TB pool, look saturated for Opus-4.7-class agents.**
  Three TB2.0 leaderboard submissions on Opus 4.7 (WOZCODE, a Claude Code plugin, 80.2% overall;
  vix 89.9%; logos 84.1%) score **15/15** on `write-compressor`, `headless-terminal` and
  `make-mips-interpreter`. They score 13-15/15 on all 8 TB tasks already in the pool
  (`openssl-selfsigned-cert` and `largest-eigenval` 13/15, the rest 14-15/15). Only `query-optimize`
  stays in band for them (9/15).
  - For comparison, CC + Opus 4.6 scores 58.0% overall on TB2.0.
  - Published Claude Code rows on TB2.1: Opus 4.7 max 68.9%, Opus 4.8 high 78.9%, Sonnet 5 high 74.6%.
  - Expect Opus 5.5 near the ceiling on most TB tasks. Pilot the TB picks first, or use the
    Opus-4.7-in-band reserves in §B.3.

## Panel reproduction

Source: `swe-bench/experiments` at `40f164d` (2026-09-03), file
`evaluation/verified/<run>/per_instance_details.json`.

**F panel (6 runs):**
- `20251124_mini-v1.16.0_claude-opus-4-5-20251101`
- `20260217_mini-v2.0.0_claude-4-5-opus-high`
- `20260217_mini-v2.0.0_claude-4-6-opus`
- `20251211_mini-v1.17.2_gpt-5.2-2025-12-11-high`
- `20260217_mini-v2.0.0_gpt-5-2-high`
- `20260901_mini-v2.4.2_gemini-3-5-flash`

The Gemini 3.5 Flash file lists 441 instances. Its README says 59 of the 500 produced no patch, so
missing instances count as unresolved (359/500 = 71.8%).

**Distribution over the 500 instances.** Number of instances by how many of the 6 runs resolved them:

| Runs that resolved (of 6) | 0 | 1 | 2 | 3 | 4 | 5 | 6 |
|---|---|---|---|---|---|---|---|
| Instances | 60 | 34 | 13 | 20 | 33 | 76 | 264 |

This matches the 25.09 report: 264 at 6/6, 76 at 5/6, 66 at 2-4/6. S and O were recomputed for pool
rows (for example `django-10973` F 3, S 3, O 8) and match the report too.

**Other panels.** S and O are as defined in the 25.09 report:
- S = Sonnet 4, Sonnet 4.5, Sonnet 4.5-high, Haiku 4.5-high.
- O = 12 open-model runs: Qwen3-Coder-480B, GLM-4.5, GLM-4.6, GLM-5-high, Kimi-K2-instruct,
  Kimi-K2.5-high, DeepSeek-V3.2-reasoner, DeepSeek-3.2-high, MiniMax-M2, MiniMax-2.5-high,
  gpt-oss-120b, Devstral-2512.

**Instance metadata.** Taken from HF `princeton-nlp/SWE-bench_Verified` @ `c104f84`: difficulty
label, gold patch, test patch, FAIL_TO_PASS.

**Broken Harbor oracles.** The list comes from `harbor/adapters/swebench/README.md` @ `a658623`:
astropy-8872, -7606, -8707; django-10097; sklearn-14710; sphinx-8595, -9711. No pick is among them.

**arm64 images.** Checked with `docker manifest inspect -v ghcr.io/epoch-research/swe-bench.eval.arm64.<id>:latest`
on 2026-09-28; all picks are `arm64`. In zsh, quote the reference as `"...${i}:latest"`. Written as
`$i:latest`, zsh reads `:l` as a modifier and the lookup fails with "manifest unknown".

## A. SWE-bench Verified: 6 picks (F = 2/6)

Filter:
- F = 1-2/6;
- repo in django, sympy, pytest, sphinx, seaborn, pylint, requests, flask, xarray;
- gold patch touches ≤ 2 files;
- not a broken oracle;
- Epoch arm64 manifest present.

This leaves 11 instances at 2/6 and 25 at 1/6, before the ≤ 2-file filter.

Harbor path: `laude-institute/harbor-datasets` @ `86723674f04e4209ac479d0fb75d9d9f44b4377e`,
`datasets/swebench-verified/<id>`. All 6 exist, each with `environment`, `instruction.md`,
`solution`, `task.toml` and `tests`. Upstream `task.toml`: agent/verifier 3000 s, 1 CPU, 4G.

Column notes:
- **Label** is the human difficulty label.
- **Patch** is files / changed ± lines.
- **Calls** is the mean mini-SWE-agent step count on the F panel.
- **arm64** is the Epoch image: digest prefix and layer size.

| # | Instance | Issue (one line) | Label | Patch | F (who) | S | O | Calls | arm64 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | django__django-11265 | `exclude()` on an annotated `FilteredRelation` raises FieldError | 15m-1h | 1 / 11 | 2/6 (GPT-5.2-high v2, Gemini 3.5 Flash; **0/3 Claude**) | 1/4 | 3/12 | 53 | `5ec76619…`, 960 MB |
| 2 | django__django-15957 | **feature**: `Prefetch()` should accept sliced querysets | 1-4 h | 1 / 33 | 2/6 (Opus 4.5, Opus 4.6) | 1/4 | 2/12 | 58 | `2b7839f5…`, 1026 MB |
| 3 | django__django-11885 | **perf/refactor**: combine fast-delete queries per table with OR | 1-4 h | 2 / 130 | 2/6 (both GPT-5.2-high; **0/3 Claude**) | 2/4 | 0/12 | 55 | `f8891118…`, 960 MB |
| 4 | django__django-12273 | Setting pk = None on a multi-table-inheritance child overwrites the parent row instead of creating a new one | 15m-1h | 1 / 3 | 2/6 (Opus 4.6, Gemini 3.5 Flash) | 0/4 | 1/12 | 46 | `e78c0470…`, 960 MB |
| 5 | sphinx-doc__sphinx-8056 | napoleon renders `x1, x2 : array_like, optional` wrongly | 15m-1h | 1 / 13 | 2/6 (Opus 4.5-high, Gemini 3.5 Flash) | 0/4 | 4/12 | 40 | `4cb0476e…`, 825 MB |
| 6 | sympy__sympy-20916 | pprint unicode doesn't subscript digits after Greek letters (`ω0`) | <15m | 1 / 4 | 2/6 (Opus 4.5-high, Opus 4.6) | 0/4 | 1/12 | 29 | `9b4e744e…`, 899 MB |

Full digests:
- 11265: `sha256:5ec766194c8370a04d2adcf57e2f5df870a2085f5f438017acae64779d63e6c7`
- 15957: `sha256:2b7839f529cdbf38b2748987841670e17d7a449ebaaacc11567d22d5ccf1f4e3`
- 11885: `sha256:f88911185c2911801e98aa00ac1e348044a4141cd29fc738c0acf0458f037769`
- 12273: `sha256:e78c04708c57f2ffd435bf4bfe809ff3f7fac70c448dd50c6e8049f3f9fd6c66`
- 8056: `sha256:4cb0476ede6f121defbec1238a7b4fc611d6629c0e47936fc51b4ee28955d1f8`
- 20916: `sha256:9b4e744e61da530e77856634d27b5e29dd0e211034b528784083518ea16106ba`

**Network.** None of the FAIL_TO_PASS tests needs the network:
- django runs `tests/runtests.py --settings=test_sqlite`;
- sphinx runs the pure-Python `tests/test_ext_napoleon_docstring.py`;
- sympy runs `bin/test sympy/printing/tests/test_conventions.py`.

The verifier still runs `pip install -e .` and `uv run parser.py`, the same pattern as the pool
tasks that already pass the oracle. The sphinx variant runs `pip install -e .[test]`; run the oracle
before relying on it offline.

**Test fairness.** I read each issue and test patch:
- 11265, 15957, 11885: the tests exercise the behaviour the issue describes. 11265 is the issue's own
  example. 11885 is `assertNumQueries(2)` on a delete. 15957 is prefetch results with slices.
- 12273: the issue text is muddled (the reporter's own test asserts the opposite). The hidden tests
  are behavioural: pk = None, then save, gives 2 rows. Keep it, but expect noise.
- 8056: the test compares exact reST output (`**x1, x2** (:class:`array_like`)`, plus a separate
  `:param x1:`/`:param x2:` when `napoleon_use_param=True`). The issue does not specify that format.
- 20916: the hidden test also needs non-ASCII digits (`w𝟙`, `ω𝟙2^3α`), beyond the Greek letters in
  the issue. A generic Unicode regex (`[^\W\d_]+` / `\d+`) passes; an ASCII+Greek range fails.

**Rejected at 2/6:**
- `django__django-12406`: the hidden `test_choices_radio_blank` calls `ModelChoiceField(..., blank=...)`,
  a new keyword the issue never names.
- `sympy__sympy-17318`: the issue text says the expression should be "returned unchanged". The test
  asserts `sqrtdenest(...) == I`, and also asserts the private `_sqrt_match(4 + I) == []`.
- `pylint-dev__pylint-6386`: the patch touches 4 files.
- `mwaskom__seaborn-3069` and `sympy__sympy-18211`: already in the pool.

**Reserves at 1/6, with tests that match the issue.** Each has an arm64 image and a Harbor dir,
both verified:

| Instance | Issue | Label | Patch | F (who) | S | O |
|---|---|---|---|---|---|---|
| django__django-15563 | `QuerySet.update()` on a multi-parent child updates the wrong parent rows | 15m-1h | 2 / 25 | 1/6 (Opus 4.6) | 1/4 | 3/12 |
| django__django-15973 | M2M `through` model in another app: `'str' has no attribute '_meta'` in the autodetector | 15m-1h | 1 / 2 | 1/6 (Opus 4.6) | 0/4 | 1/12 |
| pylint-dev__pylint-7080 | `--recursive=y` ignores `ignore-paths` | 15m-1h | 1 / 1 | 1/6 (GPT-5.2-high) | 1/4 | 2/12 |
| django__django-11141 | allow migrations directories without `__init__.py` | 15m-1h | 1 / 10 | 1/6 (Gemini 3.5 Flash) | 0/4 | 1/12 |

The xarray 1/6 instances (6599, 6938) have **no** Epoch arm64 manifest.

## B. Terminal-Bench 2.1: 4 picks

**Sources:**
- `harbor-framework/terminal-bench-2-1` @ `7131e4375048a0e408a8fb404b5f499d726b695b` (`tasks/<name>`);
- per-trial TB2.0 rewards from HF `yoonholee/terminalbench-trajectories` @ `04e8940`
  (52,104 trials; CC + Opus 4.6 = 445 trials, 5 per task);
- HF `harborframework/terminal-bench-2-leaderboard` @ `572b261` for per-trial `result.json` of Opus 4.7
  submissions. They ran with default timeouts (`timeout_multiplier` 1.0, no overrides, checked on one
  trial).

**Changes from TB2.0 to 2.1.** I diffed the file SHAs of TB2.0 (`terminal-bench-2` @ `69671fb`) and
TB2.1. For the 4 picks, only `task.toml` changed (metadata), except `query-optimize`:
- verifier timeout 900 → 1800 s;
- one sentence added to `instruction.md`: "Do not modify the database file in any way."

Column notes:
- **Other O4.6** pools 7 other Opus 4.6 harnesses: Droid, Terminus-2, CC-enhanced, mux, judy,
  Terminus-3-3.
- **O4.7** is WOZCODE (a Claude Code plugin) / vix / logos, each out of 5.
- **Med. min** is the CC + Opus 4.6 median wall time.
- Prebuilt images are amd64. Build them from the Dockerfile as the pool does. Base images are already
  mirrored locally (`tasks/pool/BASE_IMAGES.txt`).

| # | Task | What | CC + O4.6 | CC + O4.5 | Other O4.6 | O4.7 | Agent timeout / RAM | Base | Med. min |
|---|---|---|---|---|---|---|---|---|---|
| 1 | query-optimize | Rewrite a slow SQLite query over the OEWN db: exact same output, median time ≤ 1.05 × a hidden golden query | **2/5** | 4/5 | 16/35 | 5/5, 4/5, 0/5 → 9/15 | 900 s / 2 GB | ubuntu:24.04 + sqlite3; 50.6 MB db fetched from HF at build | 13.9 |
| 2 | write-compressor | Produce `data.comp` ≤ 2500 B that a given C decompressor expands to `data.txt` (reverse-engineer the format, write an encoder) | **2/5** (the 3 failures stop at ~15.6 min, the 900 s timeout) | 1/5 | 21/34 | 15/15 | 900 s / 2 GB | ubuntu:24.04 + gcc, rustc | 15.6 |
| 3 | headless-terminal | Implement a `HeadlessTerminal(BaseTerminal)` over an interactive bash: keys, Ctrl-C, rc files, background jobs | **3/5** | 3/5 | 28/35 | 15/15 | 900 s / 2 GB | python:3.13-slim-bookworm + tmux, screen, expect | 2.2 |
| 4 | make-mips-interpreter | Write `vm.js`, a MIPS interpreter with syscalls, that boots doomgeneric and saves a frame ≥ 95% similar to the reference | **2/5** | 1/5 | 14/33 | 15/15 | **1800 s** / 2 GB | python:3.13-slim-bookworm + nodejs, clang, gcc-mips-linux-gnu | 16.9 |

**Fit notes:**
- All four are general software work in the categories software-engineering or data-science.
- None uses QEMU or downloads a model, and none needs a server that outlives the agent.
  (headless-terminal's test starts its own background HTTP server through the terminal it tests.)
- `gcc-mips-linux-gnu` is published for arm64 in Debian bookworm (packages.debian.org). The
  make-mips-interpreter build also clones `ozkl/doomgeneric` and fetches `doom1.wad` from ibiblio at
  build time.
- query-optimize's timing check compares against the golden query on the same host, so run it on
  native arm64, not under Rosetta. Its 2.0 trials were partly lost to the 900 s verifier timeout
  (logos Opus 4.7: 4 × `VerifierTimeoutError`), which 2.1 raised to 1800 s.
- The pool caps agent time at 1200 s (`tasks/pool/PATCHES.md`). That cap would cut
  make-mips-interpreter below its 1800 s; one CC + Opus 4.6 success took 21.3 min. Keep 1800 s or
  drop it.

**Checked against the report's reserves:**

| Reserve | Timeout | CC + Opus 4.6 | Fits? |
|---|---|---|---|
| headless-terminal | 900 s | 3/5 | yes (pick 3) |
| query-optimize | 900 s | 2/5 | yes (pick 1) |
| distribution-search | 3600 s | 5/5 | no |
| schemelike-metacircular-eval | 2400 s | 2/5 | no: timeout above 1800 s (O4.7 12/15) |

**Excluded although CC + Opus 4.6 is 20-60%:**

| Task | Reason |
|---|---|
| polyglot-rust-c | Polyglot trick; tests changed in 2.1; O4.7 14/15 |
| path-tracing | Image-reconstruction puzzle; CC median 30.9 min |
| raman-fitting, tune-mjcf | Domain science |
| dna-assembly, protein-assembly | Bio |
| feal-linear-cryptanalysis | Crypto |
| regex-chess, winning-avg-corewars | Puzzles |
| configure-git-webserver | Server must stay up |
| torch-tensor-parallelism, torch-pipeline-parallelism | 8 GB in 2.1 |
| video-processing, portfolio-optimization | 3600 s timeout |
| count-dataset-tokens | Downloads models and data |
| cancel-async-tasks, extract-elf, financial-document-processor, openssl-selfsigned-cert, sanitize-git-repo, sparql-university | Already in the pool |

### B.3 Reserves that stay in band for Opus 4.7 but miss one stated criterion

| Task | CC + O4.6 | O4.7 (woz/vix/logos) | Why it is only a reserve |
|---|---|---|---|
| gcode-to-text | 1/5 | 2/5, 3/5, 3/5 → 8/15 | Decode what text a Prusa G-code file prints: file operations, puzzle-like |
| raman-fitting | 2/5 | 0/5, 2/5, 3/5 → 5/15 | Fit graphene G/2D peaks: domain science |
| adaptive-rejection-sampler | 0/5 | 2/5, 5/5, 2/5 → 9/15 | Implement Gilks-Wild ARS in R with tests; CC + O4.6 is below 20%; R is installed by the agent |

All three: agent timeout 900 s, 2 GB, TB2.1 `task.toml`.

## Reproduce

- **SWE panel:**
  1. Download the 22 `per_instance_details.json` files named above via
     `gh api -H "Accept: application/vnd.github.raw" repos/swe-bench/experiments/contents/evaluation/verified/<run>/per_instance_details.json`.
  2. Download the HF parquet `princeton-nlp/SWE-bench_Verified/data/test-00000-of-00001.parquet`.
  3. Count `resolved` per instance over the F, S and O panels.
- **TB:**
  1. Read the `yoonholee/terminalbench-trajectories` parquet, columns `task_name, agent, model, reward`.
  2. Filter `agent == "claude-code" and model == "claude-opus-4-6@anthropic"`.
  3. For Opus 4.7, read `verifier_result.rewards.reward` from each trial's `result.json` under
     `submissions/terminal-bench/2.0/{WOZCODE__Claude-Opus-4-7,vix__claude-opus-4-7,logos-latest__claude-opus-4.7}/`.
