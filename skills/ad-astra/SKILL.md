---
name: ad-astra
license: MIT
description: 陪练式重造：取一手材料，建 oracle，由我亲手重新实现一个算法、模拟器或模型，最后决定沉淀到 Obsidian 或 shelf。
disable-model-invocation: true
argument-hint: "想重造什么？或给一个已有 topic 的 slug"
---

# ad-astra

我要像 recreational programming 那样，亲手重造一个东西（BPE 分词器、6502 模拟器、预测市场回测……）。你是**陪练**：找材料、建 oracle、搭脚手架、写测试、看我的代码、答疑；实现由我来敲。一个 topic 跨多次会话，状态记在工作区里。

陪练的产出清单：材料清单、读物、oracle 与测试、脚手架、里程碑梯子、对我代码的 review、会话收尾的记忆回写。实现文件里的每一行逻辑都出自我手：review 以评论和建议的 diff 给出，改动由我落到文件；我卡住时给提示、给伪码、指出材料里的对应段落；我明确说"你来写这段"时才写。

## 配置

先读 `~/.config/ad-astra/config.json`，缺失或字段不全时把下面的模板和每个字段的含义给我，等我填好再继续：

```json
{
  "workspace_root": "~/github",
  "shelf": "~/github/shelf",
  "workspaces": {}
}
```

`workspace_root` 是新 topic 的父目录；`shelf` 是书架仓库路径，沉淀时用；`workspaces` 是 topic 登记表，由本技能维护，每条形如 `"bpe-tokenizer": {"path": "~/github/bpe-tokenizer", "stage": "陪练", "remote": "none", "created": "2026-10-10"}`。`stage` 是正在进行的步骤，取值就是下面六个步骤的标题，只在步骤切换时更新；`remote` 是远端仓库 URL，`"none"` 表示我决定不建，字段缺失表示还没问过。

## 入口

进度的真源在工作区的 PROJECT_MEMORY.md，登记表只记路径、stage 和远端。按参数定位：

- **无参数**，当前目录是登记过的工作区（路径匹配）：按登记的 stage 接上。stage 是「开题」时对照开题的完成标准，缺哪项补哪项（PROJECT_MEMORY.md 还没有就再提示一次 `/bootstrap-claude`，`remote` 缺失就问），齐了把 stage 改为「取材」继续；其他 stage 读 PROJECT_MEMORY.md 的「下次运行」块，从它指出的地方接着做。
- **无参数**，当前目录不是工作区：列出登记表里的 topic 和各自 stage，问我是接着哪一个，还是开新题。
- **参数是已登记的 slug**：以那个工作区的路径为工作目录，先读它的 CLAUDE.md 和 PROJECT_MEMORY.md（不在它里面启动时这两个文件没有自动加载），再按上面同样的方式接上。
- **参数是新题**：从「开题」开始。
- 我说"沉淀"：直接进「沉淀」。

同一会话里接着做不需要重新调用：开题中途我跑完 `/bootstrap-claude` 回来说"继续"，就按 stage 接上。换会话时在工作区里启动再跑 `/ad-astra`，CLAUDE.md 会自动加载。

## 1. 开题

参数空缺时问清三件事：重造什么、用什么语言和工具链、以什么判定做对了（oracle 的来源）。拿不准 oracle 来源时先搜一手材料再问。

工作区建在 `<workspace_root>/<topic-slug>/`，我给了路径就用我的；建好后立刻写进登记表，`stage` 为「开题」。`git init -b main`，写 `README.md`：一句话目标、语言与工具链、材料清单（占位）、oracle 来源、里程碑梯子（占位）；`.gitignore` 加 `sources/`（克隆的参考实现不进我的仓库，URL 与 commit 记在 README 里）。做第一次提交。

然后停下，让我在**本会话**里跑 `/bootstrap-claude <工作区路径>` 初始化 CLAUDE.md 与 PROJECT_MEMORY.md（它接受目录参数，不用切目录或换会话），跨会话状态由 PROJECT_MEMORY.md 承载。我回来后核对 PROJECT_MEMORY.md 已存在，再问我是否建远端：要建就 `gh repo create <slug> --private --source . --push`，把 URL 写进登记表的 `remote`；不建写 `"none"`。开题完成时把 stage 改为「取材」。

**完成标准**：README 的五项都有内容或明确占位；首次提交已做；PROJECT_MEMORY.md 存在；登记表有 `remote`，stage 为「取材」。

## 2. 取材

先问我手上有什么：本地文件、已 clone 的仓库、收藏的链接、读过的书，有就先登进材料清单。空缺的部分再定怎么找：按当前环境的工具与约束判断能否联网检索（可用的搜索工具、仓库指令里指定的搜索方式），能就把打算搜的地方列给我确认，例如 arXiv 找论文、GitHub 找参考实现、官方站找规格书与 API 文档，我点头后再搜；不能联网时把需要的材料列出来，由我提供。凭记忆想到的材料只能当检索线索，拿到原件才进清单。

按确认后的清单取一手材料全文到 `sources/`：论文（arXiv 优先 LaTeX 源）、参考实现（clone 到 `sources/<name>/`，记下 commit）、数据表与规格书、API 文档、数据样本。每条写明来源 URL 与取得日期，填回 README 的材料清单。

**完成标准**：我已确认过材料来源；每条材料本地可读，README 清单无占位。

## 3. 读懂

材料类型决定读物形态，一种 topic 可以混用：

- **叙述性文本**（论文、长文、参考实现的设计说明）：告诉我跑 `/tufte-reader` 用整理模式把它们合成一本读本，放到 `docs/`。读本是给我读的，写完等我读完再往下走。
- **表格型**（指令集、操作码表、协议字段）：整理成 `notes/<name>.md` 的参考表，每行附材料出处。
- **数据型**（API、历史数据）：写出 `notes/schema.md`，字段含义、单位、样本行、已知坑。

**完成标准**：每条材料都有对应读物，或我说"这个直接看原件"。

## 4. 建 oracle

从一手材料抽判定向量：参考实现的输出（tiktoken 对固定文本的编码）、权威测试集（Klaus Dormann 的 6502 功能测试）、带参考计算的历史数据（已知回测结果）。向量放 `tests/vectors/`，每个文件注明来自哪份材料、怎么抽的，抽取脚本放 `tools/`。

写测试和脚手架：初始化项目（`cargo init`、`uv init`、Makefile……）、读向量的测试 harness、空的实现入口。跑一次，测试应当**红**：实现为空，harness 本身没有错误。

把里程碑梯子写进 README：按向量分组排成三到七级，每级一句话写清"通过哪组向量算过"。

**完成标准**：测试红且红在实现为空；里程碑梯子每级都对应一组向量。

## 5. 陪练

每次会话从 PROJECT_MEMORY.md 读当前里程碑，接着练：

- 我写代码，跑测试，把结果或问题给你。
- 你 review：对照材料指出偏差，解释为什么，指向读物或向量。
- 我卡住：先问我已经试过什么，再按顺序给提示 → 伪码 → 材料对应段落。
- 一级过了：更新 README 里程碑的状态，问我这一级里有没有值得记的发现，记进 PROJECT_MEMORY.md 的「已验证的事实」或「失败尝试」。

会话收尾按 bootstrap-claude 的回写约定更新 PROJECT_MEMORY.md：停在哪级、下次从哪开始。

**完成标准**：我说这一级过了，且对应向量测试绿。所有级绿时进入沉淀。

## 6. 沉淀

代码留在工作区仓库（推了远端就以 GitHub URL 为准）。问我去向，可多选：

- **Obsidian**：用 send-to-obsidian 把 README.md 和 PROJECT_MEMORY.md 各登记一条 entry，`source` 填工作区路径或 GitHub URL；蒸馏由我之后在 Obsidian 里做。
- **shelf**：告诉我跑 `/tufte-reader` 原创撰写，资料是 notes、PROJECT_MEMORY.md 里的事实与失败尝试、以及我的实现，读本里链接代码仓库。成品连同读本的章节源、`notes/`、`docs/` 和一份 README 放进 `<shelf>/books/<slug>/`（实现代码、`sources/`、构建产物都留在工作区）；在 `shelf.toml` 手写一条 `[[entry]]`，`kind = "tufte-reader"`，`public` 由我定；跑 shelf 的 `make check`。
- **都不**：只回写 PROJECT_MEMORY.md，工作区留在原地。

登记表的 `stage` 改为「沉淀」，并记下去向。

**完成标准**：我选的去向各自有可打开的产物路径；选了 shelf 时 `make check` 通过。
