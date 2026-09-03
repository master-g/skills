#!/usr/bin/env bash
# farm preflight: 探测 multiplexer、worker CLI、可用 pairs,输出 JSON。
# 用户配置 ~/.config/farm/pairs 优先于技能自带默认;也可用 FARM_PAIRS 指定。
set -u

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
pairs_file="${FARM_PAIRS:-$HOME/.config/farm/pairs}"
[ -f "$pairs_file" ] || pairs_file="$skill_dir/pairs"

# mux
if [ "${HERDR_ENV:-}" = "1" ] && command -v herdr >/dev/null 2>&1; then
  mux="herdr"
elif [ -n "${TMUX:-}" ] && command -v tmux >/dev/null 2>&1; then
  mux="tmux"
else
  mux="none"
fi

# worker CLIs
clis=""
for c in pi claude codex; do
  command -v "$c" >/dev/null 2>&1 && clis="$clis\"$c\","
done
clis="[${clis%,}]"

# pairs(行格式: host:model = cli:model,# 开头为注释)
pairs=""
if [ -f "$pairs_file" ]; then
  while IFS='=' read -r k v; do
    k="$(printf '%s' "$k" | tr -d '[:space:]')"
    v="$(printf '%s' "$v" | tr -d '[:space:]')"
    case "$k" in '' | \#*) continue ;; esac
    pairs="$pairs{\"orchestrator\":\"$k\",\"worker\":\"$v\"},"
  done <"$pairs_file"
fi
pairs="[${pairs%,}]"

# warnings
warnings=""
if [ "$mux" = "herdr" ]; then
  outdated="$(herdr integration status 2>/dev/null | grep -E '^(pi|claude|codex): outdated' | cut -d: -f1 | paste -sd' ' -)"
  [ -n "$outdated" ] && warnings="$warnings\"herdr integration outdated: $outdated(跑 herdr integration install 更新,否则 agent 状态判定可能失真)\","
fi
[ "$clis" = "[]" ] && warnings="$warnings\"未发现任何 worker CLI(pi/claude/codex)\","
[ "$pairs" = "[]" ] && warnings="$warnings\"pairs 为空:检查 $pairs_file\","
warnings="[${warnings%,}]"

printf '{"mux":"%s","clis":%s,"pairs":%s,"pairsFile":"%s","warnings":%s}\n' \
  "$mux" "$clis" "$pairs" "$pairs_file" "$warnings"
