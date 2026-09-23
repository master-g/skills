#!/bin/sh
# farm 无头 worker:启动与分段等待。永远用 `sh` 执行,外层 shell(fish/zsh/bash)只需解析纯单词。
# 在项目根目录运行,标记文件都在 .farm/ 下。
#   sh headless.sh run  <task> <model> [-c]  跑 pi,写 .farm/<task>.pid(已启动)/.log/.exit(退出码)
#   sh headless.sh wait <task> [seconds]     等一段(默认 100s),打印状态,退出码:
#     0 done <worker 退出码> | 2 running | 3 not-started(15s 内无 pid) | 4 dead(进程消失且无 .exit)
set -u
d=.farm
mode="${1:-}"
task="${2:-}"
[ -n "$task" ] || { echo "usage: sh headless.sh run <task> <model> [-c] | wait <task> [seconds]" >&2; exit 64; }

case "$mode" in
run)
  model="${3:?model required}"
  cont="${4:-}"
  mkdir -p "$d"
  echo $$ >"$d/$task.pid"
  # shellcheck disable=SC2086 # $cont 为空时应展开为无参数
  pi -p $cont --model "$model" "读 $(pwd)/$d/$task-brief.md 并执行,报告按其中要求落盘" \
    <"/dev/null" >"$d/$task.log" 2>&1
  echo $? >"$d/$task.exit"
  ;;
wait)
  limit="${3:-100}"
  t=0
  while :; do
    if [ -f "$d/$task.exit" ]; then
      echo "done $(cat "$d/$task.exit")"
      exit 0
    fi
    if [ -f "$d/$task.pid" ]; then
      if ! kill -0 "$(cat "$d/$task.pid")" 2>/dev/null; then
        [ -f "$d/$task.exit" ] && continue
        echo dead
        exit 4
      fi
    elif [ "$t" -ge 15 ]; then
      echo not-started
      exit 3
    fi
    if [ "$t" -ge "$limit" ]; then
      echo running
      exit 2
    fi
    sleep 5
    t=$((t + 5))
  done
  ;;
*)
  echo "unknown mode: $mode" >&2
  exit 64
  ;;
esac
