---
name: makemake
license: MIT
description: 把当前项目散落的命令收敛成一个自文档 Makefile。
---

把当前项目散落在 README、scripts/、CI 配置里的命令收敛成一个 Makefile。成品的标准是:新人 clone 后只需 `make help`,不必再翻文档找命令。

## 1. 清点

读项目文件,列出候选 target。每条候选带**出处** —— 项目文件里真实存在的那行命令,连同它所在的文件。

按优先级找出处:

- **已有 Makefile / justfile / Taskfile** —— 存在则本次是增量合并:保留原 target 名与语义,只补不改。
- **构建清单** —— `Cargo.toml`、`package.json` 的 `scripts`、`pyproject.toml`、`go.mod`、`Gemfile`、`CMakeLists.txt`、`build.gradle`。
- **脚本目录** —— `scripts/`、`bin/`、根目录的 `*.sh`。逐个读开头的注释与用法行。
- **CI 配置** —— `.github/workflows/*.yml`、`.gitlab-ci.yml`。只收本地跑得起来的命令:一条 `run:` 依赖 runner 才有的东西(secrets、模拟器、矩阵变量、artifact 上传)时,它属于 CI,不属于 Makefile。长 job 先扫它的 `run:` 有没有裸命令,有才细读 —— 一个三百行的模拟器矩阵 job 常常一条都不产出。
- **文档** —— `README`、`CONTRIBUTING`、`CLAUDE.md` 里的命令块。
- **容器** —— `Dockerfile`、`docker-compose.yml` 的 build/up 命令。

顺带确认技术栈与包管理器:`package-lock.json` / `pnpm-lock.yaml` / `bun.lockb` 决定用 npm 还是 pnpm 还是 bun;`uv.lock` / `poetry.lock` 同理。用错包管理器的 target 等于没有。

**完成条件**:清单上每条候选都写明了出处文件。目录不是 repo 也不是工程目录(没有任何构建清单)时,在这里停下并说明。

## 2. 问答

只询问会改变 target 语义且不能从项目或已有答复确定的缺口。清单已有依据时直接实施，不要求用户重复确认。

`build`、`test`、`clean`、`lint` 是候选类别，项目没有对应工作流时省略；不为凑齐它们新增工具或测试设施。

仍有实质缺口时，按项目形态从以下候选中选择问题，不全套照搬:

- **运行形态** —— `run` / `serve` / `dev`(热重载) / `watch`
- **环境准备** —— `bootstrap`:装依赖、拉数据、生成证书、跑数据库迁移
- **发布** —— `release` / `publish` / `docker-build`
- **需要变量化的档位** —— `PROFILE=release|debug`、`PORT`、并发数

每个选项给出推荐答案和它对应的命令,让用户能直接确认而不是从头描述。

**选项标签直接写 target 名** —— 写 `android-lib + android-install-dep`,不写「Android 构建」。用户确认功能的同时就确认了命名,省掉之后再问一轮。名字取自项目已有词汇:crate 名、`CONTEXT.md` 的术语、脚本名;同族共用前缀(`android-*`、`bench-*`)。

**完成条件**:最终 target 清单里每条都能追到项目文件或用户答复；真正阻塞的缺口已解决。

## 3. 写

Makefile 落在项目根目录。house style:

```makefile
# <项目名> Makefile —— 统一功能入口
#
# 用法: make <target> [PROFILE=debug]
#
# 前置条件:
#   - <需要先装的东西, 没有则删掉本段>

CARGO ?= cargo
# PROFILE: release | debug; 切换所有编译目标的档位
PROFILE ?= release

ifeq ($(PROFILE),release)
CARGO_PROFILE_FLAG := --release
else
CARGO_PROFILE_FLAG :=
endif

.DEFAULT_GOAL := help

.PHONY: help build test clean

help: ## 显示本帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

build: ## 编译 workspace
	$(CARGO) build $(CARGO_PROFILE_FLAG)
```

规则:

- **每条 target 带 `## 说明`** —— help 靠它自动生成,漏一条就等于这条命令不存在。
- **可覆盖的值用 `?=` 提到文件顶部**,并在上一行写注释说明取值范围。工具名(`CARGO`、`NPM`、`PYTHON`)也提上去,方便替换成 `cargo +nightly` 之类。
- **档位用变量,不用位置参数** —— `make build PROFILE=debug`。Make 会把 `make build debug` 里的 `debug` 当成第二个 target。
- **全部 target 进 `.PHONY`**,除非它真的产出同名文件。
- **`.DEFAULT_GOAL := help`** —— 裸 `make` 打印帮助。
- **说明用中文**,与项目现有文档语言一致。

`clean` 保守处理:分开 `clean`(全清)与 `clean-debug`(只清 debug 产物)这类粒度,比一条 `rm -rf` 安全。

## 4. 验证

1. `make help` —— 输出必须列出清单上的每一条 target。
2. 对每条 target 跑 `make -n <target>` —— 全部退出 0,展开出的命令行与出处一致。
3. `make -n` 只验证命令展开，不证明命令执行成功；递归 make 或 `$(shell ...)` 仍可能执行，预览前检查相关 target。运行验证按本次需求选择，未实际执行的命令明确标为未验证。

**完成条件**:每条 target 的验证结果都有记录 —— 通过、或标为未验证并写明原因。
