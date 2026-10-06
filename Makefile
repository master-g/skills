# skills Makefile —— 统一技能操作入口
#
# 用法: make <target> [SOURCE=master-g/skills] [SKILL=<name>]
#
# 前置条件:
#   - Node.js
#   - npx

NPX ?= npx

# SOURCE: Agent Skills 仓库地址或本地目录
SOURCE ?= master-g/skills

# SKILL: install / deprecate 操作的技能名称
SKILL ?=

.DEFAULT_GOAL := help

.PHONY: help list install install-all check deprecate

help: ## 显示本帮助
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

list: ## 列出可用技能
	$(NPX) skills add $(SOURCE) --list

install: ## 全局安装指定技能（需要 SKILL=<name>）
	@test -n "$(SKILL)" || { echo "错误: 请指定 SKILL=<name>" >&2; exit 2; }
	$(NPX) skills add $(SOURCE) --skill "$(SKILL)" -g

install-all: ## 全局安装全部技能
	$(NPX) skills add $(SOURCE) --skill '*' -g

check: ## 检查技能文档的交叉引用（失效链接、按编号引用章节）
	node scripts/check-skills.mjs

deprecate: ## 归档并卸载指定技能（需要 SKILL=<name>）
	@test -n "$(SKILL)" || { echo "错误: 请指定 SKILL=<name>" >&2; exit 2; }
	@test -f "skills/$(SKILL)/SKILL.md" || { echo "错误: skills/$(SKILL)/SKILL.md 不存在" >&2; exit 2; }
	@test ! -e "skills/deprecated/$(SKILL)" || { echo "错误: skills/deprecated/$(SKILL) 已存在" >&2; exit 2; }
	mkdir -p skills/deprecated
	mv "skills/$(SKILL)" "skills/deprecated/$(SKILL)"
	mv "skills/deprecated/$(SKILL)/SKILL.md" "skills/deprecated/$(SKILL)/ARCHIVE.md"
	perl -pi -e 'print "deprecated: true\n" if /^description:/ && !$$seen++' "skills/deprecated/$(SKILL)/ARCHIVE.md"
	-$(NPX) skills remove "$(SKILL)" -g -y
	@echo "还需手工完成: ARCHIVE.md 的 description 改为以 DEPRECATED 开头并写明原因和替代技能；正文顶部加历史档案说明；更新 README.md 里 $(SKILL) 那一行。"
