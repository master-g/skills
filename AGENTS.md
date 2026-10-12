# skills

- 直接提交到 `main`，提交信息用 conventional commits 格式，scope 写技能名，如 `fix(farm): ...`。
- 技能文档之间按标题名引用章节（「门禁」），不按编号；`make check` 会检查这一条和失效的相对链接，pre-commit 也会跑。
- 弃用技能用 `make deprecate SKILL=<name>`，再按它打印的提示补完 ARCHIVE.md 和 README.md。
- 新增或改名技能时同步 README.md 的技能列表。

## 技术栈

<!-- 使用的语言、框架、工具链、版本约束。例: Python 3.12 / FastAPI / uv / Postgres 16 -->

- 内容仓库：Agent Skills 约定的 Markdown 技能文档，无构建产物。
- 工具链：Node（当前 v26，`scripts/check-skills.mjs` 只用标准库）+ Python 3 标准库脚本（如 `skills/bootstrap-claude/scripts/`，无第三方依赖，未装 pytest）。
- devDependencies 仅 prettier / husky / lint-staged，由 `npm install` 的 `prepare` 装好 git 钩子。

## 导航

<!-- 代码放在哪、开工前先读哪份文档、怎么搜（大仓库限定目录或用专用索引工具，而不是全仓 grep）、哪些子目录有自己的 CLAUDE.md / AGENTS.md。单包小仓库写一行即可。 -->

- 每个技能在 `skills/<name>/`，入口 `SKILL.md`，按需有 `references/`、`assets/`、`scripts/`、`evals/`；弃用的在 `skills/deprecated/<name>/ARCHIVE.md`。
- `README.md` 是技能清单；`Makefile` 收敛所有操作（`make help`）；`scripts/check-skills.mjs` 是文档门禁。
- `plans/` 是 improve 技能产出的执行计划（索引在 `plans/README.md`）；`docs/plans`、`docs/research` 是更早的计划与调研。
- `skills/bootstrap-claude/evals/files/**` 下的 CLAUDE.md / AGENTS.md 是 eval 夹具，不是本仓库的指令文件。
- 仓库小，搜索限定 `skills/` 即可；`node_modules/` 已被 `.gitignore`。

## 命令

<!-- 常用脚本、构建命令、测试命令、lint/格式化命令。让代理无需猜测即可运行。 -->

- 安装依赖: `npm install`（只装格式化与钩子）
- 构建: 无
- 测试: 无统一测试；带脚本的技能自带 `python3 skills/<name>/scripts/test_*.py`（如 bootstrap-claude 的 `test_setup_context.py`、`test_memory.py`，各打印 `…: ok`）
- Lint / 格式化: `make check`（引用与链接检查）；`npx prettier --write <file>`
- 安装到本机: `make install SKILL=<name> SOURCE=.`；列出可用技能 `make list`

## 工作流与陷阱

<!-- 每条写做法 + 原因。需用户确认才能做的操作（推送、开 PR、跑付费 CI、改生产配置）；慢命令把输出重定向到文件再选读，不用管道过滤；按改动范围选构建 / 测试变体；检出过旧先同步；踩过的坑及其原因。 -->

- 推送到 origin、`make deprecate`（移动目录并卸载本机技能）须用户明确要求：前者对外可见，后者改本机环境。
- 仓库里的改动不会自动生效：`~/.claude/skills` 里是副本，改完要 `make install SKILL=<name> SOURCE=.`，否则会话和依赖该技能的构建仍用旧版。
- pre-commit 跑 lint-staged（prettier）和 `make check`；prettier 会重排 Markdown 表格对齐，提交后的 diff 可能比手改的大，这是预期。
- 技能脚本的测试直接 `python3 test_*.py` 运行，不要用 pytest（未安装）。
- `test_memory.py` 运行中会打印一行 `ERROR: append-sections take one line per entry`，那是负例用例的被测输出，结尾 `test_memory: ok` 才是结果。

## 代码风格

<!-- 命名约定、格式规则、架构偏好。例: 函数用 snake_case、组件单文件、优先组合而非继承 -->

- Markdown 以简体中文为主，代码标识、命令、文件名保持英文；格式由 `.prettierrc` 决定（2 空格、80 列、双引号、分号、trailingComma es5）。
- `SKILL.md` frontmatter 含 `name`、`description`、`license: MIT`；只由用户触发的技能加 `disable-model-invocation: true`。
- 技能文档的写法遵循 writing-for-agents：正向措辞、按需披露、章节按标题名引用。
- Python 脚本只用标准库，报告文本中英混用、PASS/FAIL 用中文。

## 禁止文件

<!-- 绝对不能修改的文件清单: 生成物、密钥、锁文件、迁移历史、第三方 vendor 目录等 -->

- `.gitignore` 列出的生成物与本地状态：`node_modules/`、`**/__pycache__/`、`**/dist/`、`.farm/`、`.pi-glla/`、`skills/show-me-html/scenarios/rounds/`。
- `package-lock.json` 由 npm 生成，不手改。
- 第三方资产及其许可证只整体更新、不手改：`skills/*/assets/vendor/**`、`skills/mdxcn-term/LICENSE-mdxcn`、`skills/tufte-reader/assets/LICENSE-tufte-css.txt`。
- `skills/deprecated/**/ARCHIVE.md` 是历史档案，只读。

## 审查规则

<!-- PR 审查的标准和流程: 必须通过的检查、谁审、合并条件、提交信息规范 -->

- 无 PR 流程，直接提交 `main`；提交必须通过 pre-commit（prettier + `make check`）。
- 提交信息 conventional commits，scope 写技能名；跨技能的用 `chore` / `docs`。
- 新增或改名技能同步 `README.md` 列表；弃用走 `make deprecate` 并补完 ARCHIVE.md 的 description 与 README.md 那一行。
- 原创内容 MIT；引入第三方资产时把许可证文件放在资产旁边。

## 项目记忆 (回写约定)

跨会话的持久信息记录在 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md)，只写代码、Git 和文档推导不出的内容。

收尾顺序：验证 → 回写记忆 → 提交 → 推送。回写与本次改动进同一个提交；不提交的任务在结束前回写。

回写是提炼，不是记录：

- 「上次会话」「下次运行」整节改写成一块（分支、验证命令与实际结果、停在何处；接下来做什么），旧块直接删，历史由 Git 保存。
- 本次确认的决策追加到「已验证的事实」，走不通的路径及原因追加到「失败尝试」；每条一行，写结论、原因和来源或适用范围。能从 `git log`、代码或计划文档 30 秒内推出来的（commit SHA、进度状态、计划内容）不写，只留一行指向证据目录。
- 同主题已有条目就改写它，不追加；结论被推翻就删旧条。写不进两行的长期知识搬进 docs/ 后只留一行指针；反复出现或每次会话都要先知道的陷阱，晋升到本文件「工作流与陷阱」后从记忆里删掉。
- 结束前核对门槛：全文 ≤ 24 KB，单行 ≤ 300 字符，改写节各一块。装了 bootstrap-claude 技能的会话用它的 `scripts/memory.py check` 校验，`compact` 只压改写节；追加节条目由人合并或搬出，脚本不自动删。

<!-- bootstrap-claude convention v3 -->
