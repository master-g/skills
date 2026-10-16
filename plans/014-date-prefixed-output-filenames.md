# Plan 014: show-me-html 与 tufte-reader 的默认输出文件名带日期前缀 `YYYY-MM-DD-<标题>.html`

> **Executor instructions**: 按步骤执行，每一步跑完验证命令并确认预期结果后再进下一步。遇到「STOP conditions」里的任何情况就停下汇报，不要自行发挥。完成后更新 `plans/README.md` 里本计划的状态行（除非派发你的审阅者说明由他维护索引）。
>
> **Drift check (run first)**: `git diff --stat 84632f4..HEAD -- skills/show-me-html/SKILL.md skills/tufte-reader/SKILL.md`
> 预期无输出。有输出就把下面「Current state」的两段摘录与现行文件对照；对不上即为 STOP 条件。

## Status

- **Priority**: P2
- **Effort**: S（两个文件各改一段文字）
- **Risk**: LOW（只改技能文档里的命名规则，不动脚本）
- **Depends on**: none
- **Category**: dx
- **Planned at**: commit `84632f4`, 2026-10-16

## Why this matters

本仓库是 Agent Skills 约定的 Markdown 技能文档仓库：每个技能是 `skills/<name>/SKILL.md`，由 agent 读取后照做，没有构建产物。`show-me-html`（把素材做成单文件 HTML 页面）和 `tufte-reader`（把论文做成 Tufte 版式的 HTML 读本）都会在用户的工作目录里留下一个 `.html` 文件，文件名目前只取标题的 kebab-case，例如 `reelshort-tech-notes.html`。同一目录里积累多份页面后，看不出哪份是哪天做的，按名字排序也不是按时间排序。

维护者要求：用户没指定文件名时，默认文件名改成 `YYYY-MM-DD-<标题>.html`，例如 `2026-10-16-reelshort-tech-notes.html`。日期格式沿用仓库里已有的写法：show-me-html 的场景轮次目录就叫 `scenarios/rounds/2026-09-23-bb65054/`（ISO 日期、连字符）。

改完后，两个技能产出的页面在目录里按日期排好；tufte-reader 的工作区 `<页面名>.work/` 和 show-me-html `--snap` / `--shot` 的截图名都从页面名派生，自动带上同一前缀，不需要另外改。

## Current state

只有两处文字决定默认文件名，脚本里没有取文件名的逻辑。

- `skills/show-me-html/SKILL.md:68`（「交付与反馈」一节第一行，当前全文）：

```markdown
文件名用可辨认的 kebab-case，存到用户指定位置或工作目录。报告文件路径、先看哪里及材料缺口。
```

- `skills/tufte-reader/SKILL.md:16`（「1. 取材，列结构清单」一节第一段，当前全文）：

```markdown
输出路径是用户指定的位置，否则当前目录；页面文件名取原文标题的 kebab-case，原创撰写取书名。页面旁建**工作区** `<页面名>.work/`：取到的原文、结构清单 `outline.md`、术语表 `glossary.md` 都放在这里，不进页面。
```

从页面名派生、会自动继承前缀的地方（**都不用改**，列出来是为了让你别去改）：

- `skills/tufte-reader/SKILL.md:16` 后半句的 `<页面名>.work/`，以及 `skills/tufte-reader/references/dispatch.md:22` 的 `<页面名>.NN.check.html`。
- `skills/show-me-html/scripts/build.py:938`：截图名是 `f"{page.stem}{suffix}…png"`；`build.py:1163`：临时目录前缀是 `show-me-snap-{args.page.stem}-`。

这次需要定下、而原请求没写明的四件事（维护者 2026-10-16 已确认，照写即可）：

1. **「默认」的边界**：用户给了完整文件名就照用，不加前缀；只给了目录，或什么都没给，才按默认格式命名。
2. **日期从哪来**：取本机当天日期，文档里写明运行 `date +%F`（输出形如 `2026-10-16`）。两个技能都带 `agents/openai.yaml`，会在不注入当天日期的宿主上运行，模型凭记忆写日期会出错。
3. **修改已有页面时沿用原文件名**：否则 show-me-html 每轮反馈换一个名字，tufte-reader 每天多出一个新的 `.work/` 工作区。
4. **标题部分**：仍用英文 kebab-case；中文标题先意译成简短英文再转 kebab-case（如「注意力机制」→ `attention-mechanism`），不用拼音，也不保留中文。这一条由维护者 2026-10-16 选定。

仓库的写作约定（`AGENTS.md`「代码风格」）：技能文档以简体中文为主，代码标识、命令、文件名保持英文；遵循 writing-for-agents，用正向措辞写默认做法，少写「不要」。两个 SKILL.md 都是一段一行的长行，prettier 不折行（`.prettierrc` 没设 `proseWrap`，默认 preserve），保持一段一行。

## Commands you will need

| Purpose  | Command                                                                          | Expected on success                          |
| -------- | -------------------------------------------------------------------------------- | -------------------------------------------- |
| 文档门禁 | `make check`                                                                     | exit 0                                       |
| 格式检查 | `npx prettier --check skills/show-me-html/SKILL.md skills/tufte-reader/SKILL.md` | `All matched files use Prettier code style!` |
| 改动范围 | `git status --short`                                                             | 只列出 Scope 里的文件                        |

`make check` 跑 `node scripts/check-skills.mjs`，检查失效的相对链接和「按编号引用章节」；pre-commit 也会跑它和 prettier。

## Scope

**In scope**（只改这些文件）：

- `skills/show-me-html/SKILL.md`（只改第 68 行那一段）
- `skills/tufte-reader/SKILL.md`（只改第 16 行那一段）
- `plans/README.md`（只改本计划的状态行）

**Out of scope**（看着相关，但不要碰）：

- `skills/show-me-html/scripts/`、`skills/tufte-reader/scripts/`：脚本只读写传入的路径，不决定文件名；截图名已从页面名派生。
- `skills/show-me-html/scenarios/`、`scripts/probe_round.mjs`：冻结场景页必须叫 `<场景名>.html`（`probe_round.mjs:377` 按 `${name}.html` 找文件），日期已经在轮次目录名里。场景流程在 `scenarios/README.md` 里写明了文件路径，属于「指定了文件名」，不受默认规则影响。
- `skills/show-me-html/scripts/gallery.py` 生成的 `all-charts.html`、`skills/tufte-reader/assets/specimen.html`：维护用的固定名字。
- `skills/show-me-html/references/compose-and-check.md:64` 的 `输出文件.html`、`skills/tufte-reader/SKILL.md:55` 的 `页面.html`：命令示例里的占位符，不是命名规则。
- `skills/tufte-reader/references/dispatch.md`、两个技能的 `agents/openai.yaml`、`README.md`。
- `PROJECT_MEMORY.md`：合并时由维护者回写；这条规则改完后从 SKILL.md 就能读到，不需要进记忆。

## Git workflow

- 分支：`advisor/014-date-prefixed-filenames`。
- 提交信息用 conventional commits，scope 写技能名（仓库已有的例子：`feat(show-me-html): TOC collapses h3 by section and sizes to the page, narrow diagram variants`）。按技能分两个提交：
  - `feat(show-me-html): default output filename gets a YYYY-MM-DD- date prefix`
  - `feat(tufte-reader): default output filename gets a YYYY-MM-DD- date prefix`
- pre-commit 会跑 prettier 和 `make check`。
- 不推送，不改 `PROJECT_MEMORY.md`，不跑 `make install`（合并后由维护者装到本机）。

## Steps

### Step 1: 改 show-me-html 的命名规则

把 `skills/show-me-html/SKILL.md` 第 68 行整行替换为下面这一行（一段一行，不折行）：

```markdown
文件名默认是 `YYYY-MM-DD-<标题>.html`：日期取生成当天的本机日期（运行 `date +%F`），标题部分用可辨认的英文 kebab-case，中文标题先意译成简短英文，例如 `2026-10-16-reelshort-tech-notes.html`、「注意力机制」→ `2026-10-16-attention-mechanism.html`。用户给了完整文件名时照用；只给了目录时存到该目录，什么都没给时存到工作目录，两种情况都用默认文件名。修改已有页面时沿用原文件名。报告文件路径、先看哪里及材料缺口。
```

**Verify**:

- `grep -c 'date +%F' skills/show-me-html/SKILL.md` → `1`
- `grep -c '文件名用可辨认的 kebab-case' skills/show-me-html/SKILL.md` → `0`
- `grep -c '中文标题先意译成简短英文' skills/show-me-html/SKILL.md` → `1`
- `sed -n 67,69p skills/show-me-html/SKILL.md`：67 行是 `## 交付与反馈` 后的空行，68 行是上面的新段落，69 行以 `最后一次构建直接带` 开头。

### Step 2: 改 tufte-reader 的命名规则

把 `skills/tufte-reader/SKILL.md` 第 16 行整行替换为下面这一行（一段一行，不折行）：

```markdown
输出路径是用户指定的位置，否则当前目录。页面文件名默认是 `YYYY-MM-DD-<标题>.html`：日期取动笔当天的本机日期（运行 `date +%F`），标题部分取原文标题（原创撰写取书名）的英文 kebab-case，中文标题先意译成简短英文，例如 `2026-10-16-attention-is-all-you-need.html`。用户给了完整文件名时照用；续写或修订已有读本时沿用原文件名。页面旁建**工作区** `<页面名>.work/`：取到的原文、结构清单 `outline.md`、术语表 `glossary.md` 都放在这里，不进页面。
```

**Verify**:

- `grep -c 'date +%F' skills/tufte-reader/SKILL.md` → `1`
- `grep -c '页面文件名取原文标题的 kebab-case' skills/tufte-reader/SKILL.md` → `0`
- `grep -c '中文标题先意译成简短英文' skills/tufte-reader/SKILL.md` → `1`
- `grep -c '<页面名>.work/' skills/tufte-reader/SKILL.md` → `1`（工作区那半句保留）

### Step 3: 跑门禁并提交

1. `npx prettier --check skills/show-me-html/SKILL.md skills/tufte-reader/SKILL.md` → `All matched files use Prettier code style!`。若报格式问题，运行 `npx prettier --write` 这两个文件，再确认 diff 只涉及第 68 / 16 行。
2. `make check` → exit 0。
3. `git diff --numstat` → 恰好两行：`1	1	skills/show-me-html/SKILL.md` 和 `1	1	skills/tufte-reader/SKILL.md`（列之间是制表符）。
4. 按「Git workflow」分两个提交。

**Verify**: `git log --oneline -2` 显示上面两条提交信息；`git status --short` 无输出（`plans/README.md` 的状态行在 Done criteria 前最后改，单独处理）。

## Test plan

本仓库没有针对技能文档行为的自动测试，这次改动也不新增测试：规则由 agent 读文档执行，现有检查只能覆盖链接与格式（`make check`、prettier）。行为验证由维护者在合并并 `make install` 之后做一次手动冒烟，见「Maintenance notes」。

## Done criteria

- [ ] `make check` exit 0
- [ ] `npx prettier --check skills/show-me-html/SKILL.md skills/tufte-reader/SKILL.md` 通过
- [ ] `grep -c 'date +%F' skills/show-me-html/SKILL.md skills/tufte-reader/SKILL.md` → 两个文件各 `1`
- [ ] `grep -c '中文标题先意译成简短英文' skills/show-me-html/SKILL.md skills/tufte-reader/SKILL.md` → 两个文件各 `1`
- [ ] `grep -rn '文件名用可辨认的 kebab-case\|页面文件名取原文标题的 kebab-case' skills/` 无输出
- [ ] `git diff --stat 84632f4..HEAD` 只列出 `skills/show-me-html/SKILL.md`、`skills/tufte-reader/SKILL.md`（和更新状态行后的 `plans/README.md`）
- [ ] `plans/README.md` 本计划状态行已更新

## STOP conditions

- Drift check 有输出，且第 68 行 / 第 16 行与「Current state」的摘录对不上（例如那段文字已被改写或移动）。
- `grep -rn 'kebab-case' skills/show-me-html skills/tufte-reader --include=*.md` 除这两行之外还找到别的**输出文件命名规则**：汇报位置，不要顺手改。规划时这条命令另有两处已知命中，都是章 `id` 的规则、与文件名无关，不算：`skills/tufte-reader/references/style.md:87` 和 `skills/tufte-reader/references/markup.md:68`。
- `make check` 失败且报错指向本次未改动的文件：说明基线本来就坏了，汇报，不要修。

## Maintenance notes

- **合并后要装到本机才生效**：`~/.claude/skills` 里是副本，维护者需运行 `make install SKILL=show-me-html SOURCE=.` 和 `make install SKILL=tufte-reader SOURCE=.`，再 `grep -c 'date +%F' ~/.claude/skills/show-me-html/SKILL.md ~/.claude/skills/tufte-reader/SKILL.md` 确认各为 `1`。
- **手动冒烟**：装好后在一个空目录里各调用一次技能、不指定文件名，确认产出 `<今天日期>-<标题>.html`（tufte-reader 还应有同名前缀的 `.work/`）；再指定一次完整文件名，确认照用。
- 中文标题按维护者 2026-10-16 的选择意译成英文；意译不稳定（同一主题两次得到不同名字）时，修订沿用原文件名这条规则会兜住，不必再加约束。
- 以后若新增类似的单文件输出技能，命名规则可照这两段写，保持同一格式。
