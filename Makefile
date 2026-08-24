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

# SKILL: install target 要安装的技能名称
SKILL ?=

.DEFAULT_GOAL := help

.PHONY: help list install install-all

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
