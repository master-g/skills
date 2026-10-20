#!/bin/sh
# farm headless.sh 进程组收尾的冒烟测试。用法: sh smoke.sh <headless.sh 的绝对路径>
set -u
H="$1"
T=$(mktemp -d)
mkdir -p "$T/bin" "$T/bin-stubborn" "$T/bin-exit3" "$T/proj"
# 假 pi 派生一个孙进程。孙进程是参数里带 $T 路径的 perl,好让 pgrep -f "$T/" 连它一起找到
printf '#!/bin/sh\nperl -e "sleep 300" "%s/gc" &\nperl -e "sleep 300" "%s/gc"\n' "$T" "$T" >"$T/bin/pi"
printf '#!/bin/sh\ntrap "" TERM\nperl -e "sleep 300" "%s/gc" &\nwhile :; do sleep 1; done\n' "$T" >"$T/bin-stubborn/pi"
printf '#!/bin/sh\necho "args: $*"\nexit 3\n' >"$T/bin-exit3/pi"
chmod +x "$T"/bin*/pi
cd "$T/proj" || exit 1
fail=0
check() { if [ "$2" = "$3" ]; then echo "PASS $1"; else echo "FAIL $1: 期望 [$3] 实际 [$2]"; fail=1; fi; }
left() { pgrep -f "$T/" >/dev/null && echo yes || echo no; }

PATH="$T/bin-exit3:$PATH" sh "$H" run a m -c
check "退出码透传" "$(sh "$H" wait a 3)" "done 3"
check "-c 透传" "$(grep -c -- '-p -c --model m' .farm/a.log)" "1"
check "已结束的任务 stop" "$(sh "$H" stop a; echo $?)" "not-running
1"

PATH="$T/bin:$PATH" nohup sh "$H" run b m >/dev/null 2>&1 &
sleep 2
check "运行中" "$(sh "$H" wait b 1)" "running"
check "stop 运行中的任务" "$(sh "$H" stop b)" "stopped"
check "stop 后 wait" "$(sh "$H" wait b 5)" "done 143"
check "stop 后无残留进程" "$(left)" "no"

PATH="$T/bin:$PATH" nohup sh "$H" run c m >/dev/null 2>&1 &
sleep 2
kill "$(cat .farm/c.pid)"
sleep 2
check "kill 外层 sh 后无残留进程" "$(left)" "no"
check "kill 外层 sh 后 wait" "$(sh "$H" wait c 5)" "done 143"

PATH="$T/bin:$PATH" nohup sh "$H" run d m >/dev/null 2>&1 &
sleep 2
kill -9 "$(cat .farm/d.pid)"
sleep 1
check "外层 sh 被 KILL 后 wait" "$(sh "$H" wait d 5)" "dead"
check "dead 后 stop 清残留" "$(sh "$H" stop d)" "stopped"
check "dead 后无残留进程" "$(left)" "no"

PATH="$T/bin-stubborn:$PATH" nohup sh "$H" run e m >/dev/null 2>&1 &
sleep 2
check "忽略 TERM 的 worker" "$(sh "$H" stop e)" "killed"
check "KILL 后 wait" "$(sh "$H" wait e 5)" "done 137"
check "KILL 后无残留进程" "$(left)" "no"

if command -v tmux >/dev/null; then
  tmux new-session -d -s "farm-smoke-$$" -c "$T/proj" "PATH='$T/bin':\$PATH sh '$H' run f m"
  sleep 2
  tmux kill-session -t "farm-smoke-$$"
  sleep 2
  check "关 tmux 会话后无残留进程" "$(left)" "no"
else
  echo "SKIP tmux 未安装"
fi

pkill -9 -f "$T/" 2>/dev/null
rm -rf "$T"
[ "$fail" = 0 ] && echo "smoke: ok" || { echo "smoke: FAIL"; exit 1; }
