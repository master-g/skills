# exportkit — 项目上下文

> 项目指令与常用命令，供 AI 编码代理按任务需要查阅；Claude Code 经 CLAUDE.md 的 `@AGENTS.md` 导入读到同一份内容。
> 跨会话记忆见 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md)。

## 技术栈

<!-- 使用的语言、框架、工具链、版本约束。例: Python 3.12 / FastAPI / uv / Postgres 16 -->

- Python 3.12 / FastAPI / SQLAlchemy 2 / psycopg 3 / Postgres 16，依赖和虚拟环境用 uv 管理。
- 迁移用 alembic；测试用 pytest，lint 与格式化用 ruff（行宽 100）。

## 导航

<!-- 代码放在哪、开工前先读哪份文档、怎么搜（大仓库限定目录或用专用索引工具，而不是全仓 grep）、哪些子目录有自己的 CLAUDE.md / AGENTS.md。单包小仓库写一行即可。 -->

- 代码在 `src/exportkit/`：`api.py` 是 HTTP 入口，`csv_writer.py` 负责把行写成 CSV（BOM、公式转义）。
- 测试在 `tests/`，标了 `integration` 的用例要连本地 Postgres，默认 `make test` 不跑它们。
- 单包小仓库，直接在 `src/` 和 `tests/` 里搜即可。

## 命令

<!-- 常用脚本、构建命令、测试命令、lint/格式化命令。让代理无需猜测即可运行。 -->

- 安装依赖: `make install`（即 `uv sync`）
- 本地启动: `make run`，监听 8040 端口
- 构建: 无，服务直接以源码运行
- 测试: `make test`（单元测试）；`make test-integration`（需要本地 Postgres，连接串取 `DATABASE_URL`）
- 重建本地库: `make db-reset`（清空 public schema 后 `alembic upgrade head`）
- Lint / 格式化: `make lint` 检查，`make fmt` 改写

## 工作流与陷阱

<!-- 每条写做法 + 原因。需用户确认才能做的操作（推送、开 PR、跑付费 CI、改生产配置）；慢命令把输出重定向到文件再选读，不用管道过滤；按改动范围选构建 / 测试变体；检出过旧先同步；踩过的坑及其原因。 -->

- 推送到 origin 和打 tag 先问用户：main 有推送即部署到预发环境，对外可见。
- 改了 `csv_writer.py` 要跑 `make test`：输出格式被下游财务脚本按列位置解析，列顺序或换行符变了会静默读错。
- 慢的命令把输出重定向到文件再选读，不要用管道截断，失败信息常在末尾。

## 代码风格

<!-- 命名约定、格式规则、架构偏好。例: 函数用 snake_case、组件单文件、优先组合而非继承 -->

- 函数和变量用 snake_case，类型标注必填；ruff 的默认规则集加 `I`（import 排序）。
- 导出逻辑保持流式：按行产出，不把整张表读进内存。
- 注释和文档用中文，标识符用英文。

## 禁止文件

<!-- 绝对不能修改的文件清单: 生成物、密钥、锁文件、迁移历史、第三方 vendor 目录等 -->

- `uv.lock` 由 `uv` 生成，不手改。
- `alembic/versions/` 下已合并的迁移文件不改，要变更就新增一个迁移。
- `.env` 含本地数据库口令，不提交。

## 审查规则

<!-- PR 审查的标准和流程: 必须通过的检查、谁审、合并条件、提交信息规范 -->

- 合并前 `make lint` 和 `make test` 必须通过；改了迁移的再跑一遍 `make test-integration`。
- 提交信息用 conventional commits，如 `fix(export): ...`。
- 至少一位同事审过再合并到 main。

## 项目记忆 (回写约定)

跨会话的持久信息记录在 [PROJECT_MEMORY.md](./PROJECT_MEMORY.md)，只写代码、Git 和文档推导不出的内容。

收尾顺序：验证 → 回写记忆 → 提交 → 推送。回写与本次改动进同一个提交；不提交的任务在结束前回写。

回写是提炼，不是记录：

- 「上次会话」「下次运行」整节改写成一块（分支、验证命令与实际结果、停在何处；接下来做什么），旧块直接删，历史由 Git 保存。
- 本次确认的决策追加到「已验证的事实」，走不通的路径及原因追加到「失败尝试」；每条一行，写结论、原因和来源或适用范围。能从 `git log`、代码或计划文档 30 秒内推出来的（commit SHA、进度状态、计划内容）不写，只留一行指向证据目录。
- 同主题已有条目就改写它，不追加；结论被推翻就删旧条。写不进两行的长期知识搬进 docs/ 后只留一行指针；反复出现或每次会话都要先知道的陷阱，晋升到本文件「工作流与陷阱」后从记忆里删掉。
- 结束前核对门槛：全文 ≤ 24 KB，单行 ≤ 300 字符，改写节各一块。装了 bootstrap-claude 技能的会话用它的 `scripts/memory.py check` 校验，`compact` 只压改写节；追加节条目由人合并或搬出，脚本不自动删。

<!-- bootstrap-claude convention v3 -->
