#!/bin/sh
# farm 无头 worker:启动与分段等待。永远用 `sh` 执行,外层 shell(fish/zsh/bash)只需解析纯单词。
# 在项目根目录运行,标记文件都在 .farm/ 下。
#   sh headless.sh run  <task> <model> [-c]  跑 pi,写 .farm/<task>.pid(已启动)/.pgid(pi 的进程组)/.log/.exit(退出码)
#   sh headless.sh wait <task> [seconds]     等一段(默认 100s),打印状态,退出码:
#     0 done <worker 退出码> | 2 running | 3 not-started(15s 内无 pid) | 4 dead(进程消失且无 .exit)
#   sh headless.sh stop <task>               结束 pi 的整个进程组:先 TERM,10s 后仍在就 KILL,退出码:
#     0 stopped | 0 killed | 1 not-running(已结束或从未启动)
set -u
d=.farm

# 结束进程组 $1:先 TERM,10s 后仍有进程就 KILL。返回 0 已结束 | 1 组不存在 | 2 用了 KILL
end_group() {
  kill -TERM -"$1" 2>/dev/null || return 1
  t=0
  while kill -0 -"$1" 2>/dev/null; do
    if [ "$t" -ge 10 ]; then
      kill -KILL -"$1" 2>/dev/null
      return 2
    fi
    sleep 1
    t=$((t + 1))
  done
  return 0
}

mode="${1:-}"
task="${2:-}"
[ -n "$task" ] || { echo "usage: sh headless.sh run <task> <model> [-c] | wait <task> [seconds] | stop <task>" >&2; exit 64; }

case "$mode" in
run)
  model="${3:?model required}"
  cont="${4:-}"
  mkdir -p "$d"
  echo $$ >"$d/$task.pid"
  # set -m:pi 作为后台作业自成进程组(组 id = pi 的 pid),stop 能连同它派生的进程一起结束
  set -m
  g=
  # 外层 sh 被关窗(HUP)或被 kill(INT/TERM)时先结束 pi 的进程组,再照常写退出码
  trap '[ -n "$g" ] && end_group "$g"' HUP INT TERM
  # shellcheck disable=SC2086 # $cont 为空时应展开为无参数
  pi -p $cont --model "$model" "读 $(pwd)/$d/$task-brief.md 并执行,报告按其中要求落盘" \
    <"/dev/null" >"$d/$task.log" 2>&1 &
  g=$!
  echo "$g" >"$d/$task.pgid"
  wait "$g"
  echo $? >"$d/$task.exit"
  ;;
stop)
  # 已写退出码说明 run 已收尾;不再按旧组 id 发信号,组 id 可能已被别的进程重用
  if [ -f "$d/$task.exit" ] || [ ! -f "$d/$task.pgid" ]; then
    echo not-running
    exit 1
  fi
  end_group "$(cat "$d/$task.pgid")"
  case $? in
  0) echo stopped ;;
  2) echo killed ;;
  *)
    echo not-running
    exit 1
    ;;
  esac
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
