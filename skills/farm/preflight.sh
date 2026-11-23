#!/usr/bin/env bash
# farm preflight: 探测 multiplexer、worker CLI、可用 pairs,输出 JSON。
# 用户配置 ~/.config/farm/pairs 优先于技能自带默认;也可用 FARM_PAIRS 指定。
set -u

skill_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# mux
if [ "${HERDR_ENV:-}" = "1" ] && command -v herdr >/dev/null 2>&1; then
  mux="herdr"
elif [ -n "${TMUX:-}" ] && command -v tmux >/dev/null 2>&1; then
  mux="tmux"
else
  mux="none"
fi

# worker CLIs
clis=()
for c in pi claude codex grok; do
  command -v "$c" >/dev/null 2>&1 && clis+=("$c")
done
outdated=""
if [ "$mux" = "herdr" ]; then
  outdated="$(herdr integration status 2>/dev/null | grep -E '^(pi|claude|codex|grok): outdated' | cut -d: -f1 | paste -sd' ' -)"
fi
exec python3 -I - "$skill_dir" "$mux" "${clis[*]-}" "$outdated" <<'PYTHON'
import json
import sys

sys.path.insert(0, sys.argv[1])
from pair_config import load_pairs

mux, clis, stale = sys.argv[2:]
warnings = []
try:
    kind, path, pairs = load_pairs()
except (OSError, ValueError) as error:
    sys.exit(f"读取 pairs 失败：{error}")
if stale:
    warnings.append(f"herdr integration outdated: {stale}(跑 herdr integration install 更新)")
if not clis:
    warnings.append("未发现任何 worker CLI(pi/claude/codex/grok)")
if not pairs:
    warnings.append(f"pairs 为空:检查 {path}")
print(json.dumps(dict(mux=mux, clis=clis.split(), pairs=pairs, pairsFile=path,
                      pairsSource=kind, warnings=warnings), ensure_ascii=False))
PYTHON
