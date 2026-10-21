#!/usr/bin/env bash
# 「用真实配置把 v1 的三个 CLI 各无头跑通一次」的冒烟清单（见 ../issues/12-cli-smoke-run.md）。
# 由用户亲手执行，推进地图的代理不代跑。选手用本机真实配置：不传档位旗标、不关扩展与技能。
#
# 用法：bash smoke.sh <步骤> [对象]
#   setup              建输出目录、记版本与配置指纹、生成评委看图用的 shot.png
#   quota <标签>       记一次额度快照（Claude 读 ~/.claude.json 的缓存，Kimi / 智谱调用量接口）
#   edit <选手>        最小改文件任务
#   skill <选手>       显式调用 show-me-html，只答 SKILL.md 的第一个二级标题，不构建
#   build [选手]       显式调用 show-me-html 真做一页并构建（默认 astra，验证沙箱里能否起无头 Chrome）
#   judge <评委>       评委看图：fable / astra / kimi
#   after              列出运行期间日常状态里新增或改动的文件，汇总各步结果
#   all                按顺序跑完以上全部
# 选手：opus fable sonnet astra glm kimi
# 输出目录：$BENCH_SMOKE_OUT，默认 ~/.cache/bench-smoke

set -uo pipefail

OUT="${BENCH_SMOKE_OUT:-$HOME/.cache/bench-smoke}"
SKILLS="$HOME/.agents/skills"
CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
LIMIT="${BENCH_SMOKE_LIMIT:-1200}" # 单次调用超时（秒），build 步加倍

PROMPT_EDIT='把 notes.txt 里的 TODO 改成 DONE。只改这一处，不要创建或修改别的文件，改完直接结束。'
PROMPT_SKILL='不要生成页面，不要运行任何脚本或构建，也不要打开浏览器。只回答一件事：这个技能的说明文件里，第一个二级标题（## 开头）的原文是什么。'
PROMPT_BUILD='用下面的材料做一页状态小结，页面文件写到当前目录的 page.html。构建时不要打开浏览器（不要加 --open）。材料：bench 冒烟测试，2026-10-21。已完成：评分方式全部定下（7 个场景）。进行中：三个 CLI 的无头实跑。待办：隔离与联网、任务定义样张。'
PROMPT_JUDGE='看 shot.png 这张图片，回答两项：图里写的数字是多少；图里的圆是什么颜色。只回答这两项，不要做别的。'

die() { echo "smoke: $*" >&2; exit 2; }

model_of() {
  case "$1" in
    opus) echo claude-opus-5-5 ;;
    fable) echo claude-fable-5-1 ;;
    sonnet) echo claude-sonnet-5-5 ;;
    astra) echo gpt-6-astra ;;
    glm) echo zai-coding-cn/glm-5.3 ;;
    kimi) echo kimi-coding/k3 ;;
    *) die "未知选手：$1（可选 opus fable sonnet astra glm kimi）" ;;
  esac
}

cli_of() {
  case "$1" in
    opus | fable | sonnet) echo claude ;;
    astra) echo codex ;;
    glm | kimi) echo pi ;;
  esac
}

# 显式调用技能的写法按「各 CLI 加载技能的方式」
skill_prefix() {
  case "$(cli_of "$1")" in
    claude) echo '/show-me-html ' ;;
    codex) echo '$show-me-html ' ;;
    pi) echo '/skill:show-me-html ' ;;
  esac
}

new_task() { # <目录> ：建一个干净的 git 仓库作任务目录
  local d="$1"
  [ -f "$OUT/runs.tsv" ] || die "先跑 setup"
  [ -e "$d" ] && die "$d 已存在；要重跑先删掉它"
  mkdir -p "$d" && git -C "$d" init -q && git -C "$d" config user.email smoke@bench.local && git -C "$d" config user.name smoke
}

# 跑一次选手 / 评委调用：<步骤> <对象> <任务目录> <超时> <提示词> [沙箱] [图片]
invoke() {
  local step="$1" who="$2" dir="$3" limit="$4" prompt="$5" sandbox="${6:-}" image="${7:-}"
  local model cli start rc r="$OUT/runs/$step-$who"
  model="$(model_of "$who")"
  cli="$(cli_of "$who")"
  mkdir -p "$r"
  start=$(date +%s)
  echo "== $step ${who}（$cli · ${model}）开始 $(date '+%H:%M:%S')"
  case "$cli" in
    claude)
      local extra=(--permission-mode bypassPermissions)
      [ -n "$image" ] && extra=(--allowedTools Read)
      (cd "$dir" && timeout "$limit" claude -p "$prompt" --model "$model" "${extra[@]}" \
        --output-format stream-json --verbose </dev/null >"$r/out.jsonl" 2>"$r/err.txt")
      ;;
    codex)
      local extra=()
      [ -n "$sandbox" ] && extra+=(-s "$sandbox")
      [ -n "$image" ] && extra+=(-i "$dir/$image")
      timeout "$limit" codex exec -C "$dir" -m "$model" ${extra[@]+"${extra[@]}"} --json \
        -o "$r/last.txt" -- "$prompt" </dev/null >"$r/out.jsonl" 2>"$r/err.txt"
      ;;
    pi)
      local files=()
      [ -n "$image" ] && files=("@$image")
      (cd "$dir" && timeout "$limit" pi --mode json --model "$model" ${files[@]+"${files[@]}"} "$prompt" \
        </dev/null >"$r/out.jsonl" 2>"$r/err.txt")
      ;;
  esac
  rc=$?
  printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$step" "$who" "$cli" "$model" "$rc" "$(($(date +%s) - start))" >>"$OUT/runs.tsv"
  echo "== $step $who 结束：退出码 ${rc}，$(($(date +%s) - start)) 秒（124 = 超时）"
}

answer() { # <运行目录> <cli> ：尽力取出最终回答，取不到就看 out.jsonl
  case "$2" in
    claude) jq -r 'select(.type == "result") | .result' "$1/out.jsonl" 2>/dev/null ;;
    codex) cat "$1/last.txt" 2>/dev/null ;;
    pi) jq -r 'select(.type == "message_end") | .message | select(.role == "assistant") | .content[]? | select(.type == "text") | .text' "$1/out.jsonl" 2>/dev/null | tail -5 ;;
  esac
}

step_setup() {
  mkdir -p "$OUT/tasks" "$OUT/runs" "$OUT/quota" || die "建不了 $OUT"
  touch "$OUT/marker"
  printf 'step\twho\tcli\tmodel\texit\tseconds\n' >"$OUT/runs.tsv"
  {
    date '+%F %T %z'
    claude --version
    codex --version
    (cd "$OUT" && pi --version)
    shasum -a 256 ~/.claude/settings.json ~/.codex/config.toml ~/.pi/agent/settings.json 2>&1
    find "$SKILLS/show-me-html" -type f -not -path '*/__pycache__/*' -print0 | sort -z | xargs -0 shasum -a 256 | shasum -a 256 | sed 's/-$/show-me-html 技能目录/'
  } >"$OUT/versions.txt" 2>&1
  cat >"$OUT/shot.html" <<'EOF'
<!doctype html><meta charset="utf-8">
<body style="margin:0;height:100vh;background:#1e3a8a;display:flex;align-items:center;justify-content:center;gap:48px">
<div style="width:160px;height:160px;border-radius:50%;background:#dc2626"></div>
<p style="margin:0;color:#fff;font:bold 96px sans-serif">7429</p>
</body>
EOF
  "$CHROME" --headless=new --disable-gpu --hide-scrollbars --window-size=640,360 \
    --screenshot="$OUT/shot.png" "file://$OUT/shot.html" >/dev/null 2>&1
  [ -s "$OUT/shot.png" ] || die "shot.png 没生成，检查 Chrome 路径"
  echo "setup 完成：$OUT"
  cat "$OUT/versions.txt"
}

step_quota() {
  local label="${1:?quota 要一个标签，如 pre / post}" key
  local q="$OUT/quota/$label"
  date -u '+%FT%TZ' >"$q-time.txt"
  jq '.cachedUsageUtilization' ~/.claude.json >"$q-claude.json" 2>&1
  key=$(jq -r '."kimi-coding".key' ~/.pi/agent/auth.json)
  printf 'Authorization: Bearer %s\n' "$key" |
    curl -s --max-time 20 -H @- -H 'Accept: application/json' https://api.kimi.com/coding/v1/usages >"$q-kimi.json"
  key=$(jq -r '."zai-coding-cn".key' ~/.pi/agent/auth.json)
  printf 'Authorization: %s\n' "$key" |
    curl -s --max-time 20 -H @- https://bigmodel.cn/api/monitor/usage/quota/limit >"$q-zhipu.json"
  unset key
  echo "quota ${label}：Claude 缓存 as_of $(jq -r '.utilization.seven_day_breakdown.as_of // "?"' "$q-claude.json")，周 $(jq -r '.utilization.seven_day.utilization // "?"' "$q-claude.json")%"
  echo "  Kimi 周：$(jq -r '.usage | "\(.used)/\(.limit)"' "$q-kimi.json" 2>/dev/null)；智谱：$(jq -c '[.data.limits[]? | {unit, percentage}]' "$q-zhipu.json" 2>/dev/null)"
  echo "  Codex 的额度不在这里取：从各次运行的 ~/.codex/sessions rollout 里读 rate_limits"
}

step_edit() {
  local who="${1:?edit 要一个选手}" d="$OUT/tasks/$1-edit"
  new_task "$d" || return
  printf 'status: TODO\n' >"$d/notes.txt"
  git -C "$d" add notes.txt && git -C "$d" commit -qm init
  invoke edit "$who" "$d" "$LIMIT" "$PROMPT_EDIT"
  { echo "notes.txt: $(cat "$d/notes.txt")"; git -C "$d" status --short --untracked-files=all; } >"$OUT/runs/edit-$who/check.txt"
  cat "$OUT/runs/edit-$who/check.txt"
}

step_skill() {
  local who="${1:?skill 要一个选手}" d="$OUT/tasks/$1-skill"
  new_task "$d" || return
  invoke skill "$who" "$d" "$LIMIT" "$(skill_prefix "$who")$PROMPT_SKILL"
  echo "回答：$(answer "$OUT/runs/skill-$who" "$(cli_of "$who")")"
  echo "期望：## 意图与材料"
}

step_build() {
  local who="${1:-astra}" d="$OUT/tasks/${1:-astra}-build"
  new_task "$d" || return
  invoke build "$who" "$d" "$((LIMIT * 2))" "$(skill_prefix "$who")$PROMPT_BUILD"
  local c="$OUT/runs/build-$who/check.txt"
  if [ -f "$d/page.html" ]; then
    python3 "$SKILLS/show-me-html/scripts/build.py" "$d/page.html" --check-only >"$c" 2>&1
    echo "check-only 退出码 $?" >>"$c"
  else
    echo "没有 page.html" >"$c"
  fi
  cat "$c"
}

step_judge() {
  local who="${1:?judge 要一个评委}" d="$OUT/tasks/$1-judge" sandbox=""
  case "$who" in fable | astra | kimi) ;; *) die "评委只有 fable / astra / kimi" ;; esac
  new_task "$d" || return
  cp "$OUT/shot.png" "$d/shot.png"
  [ "$who" = astra ] && sandbox=read-only
  invoke judge "$who" "$d" "$LIMIT" "$PROMPT_JUDGE" "$sandbox" shot.png
  echo "回答：$(answer "$OUT/runs/judge-$who" "$(cli_of "$who")")"
  echo "期望：7429，红色"
}

step_after() {
  find ~/.claude ~/.codex ~/.pi ~/.agents ~/.claude.json -newer "$OUT/marker" -type f 2>/dev/null |
    grep -v "^$OUT" | sort >"$OUT/state-changed.txt"
  echo "日常状态里新增或改动 $(wc -l <"$OUT/state-changed.txt" | tr -d ' ') 个文件，清单在 $OUT/state-changed.txt"
  find "$OUT/tasks" -path '*/.git' -prune -o -type f -print | sort >"$OUT/task-files.txt"
  column -t -s $'\t' "$OUT/runs.tsv"
}

step_all() {
  step_setup
  step_quota pre
  for c in glm kimi astra sonnet opus fable; do
    step_edit "$c"
    step_skill "$c"
  done
  step_build astra
  for j in kimi astra fable; do step_judge "$j"; done
  step_quota post
  step_after
}

cmd="${1:-}"
shift || true
case "$cmd" in
  setup) step_setup ;;
  quota) step_quota "$@" ;;
  edit) step_edit "$@" ;;
  skill) step_skill "$@" ;;
  build) step_build "$@" ;;
  judge) step_judge "$@" ;;
  after) step_after ;;
  all) step_all ;;
  *) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 2 ;;
esac
