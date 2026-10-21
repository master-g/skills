# bench

`bench/` 项目的术语。bench 是一套在自己的使用场景里比较不同大模型的测试套件，与仓库里的技能并列；技能自身的术语不收在这里。

## Language

**选手**:
被比较的单位：一个 agent CLI 连同本机的实际配置（登录、扩展、插件），加上所选的模型与推理档位。
_Avoid_: 模型（只在指模型本身时用）、agent、参赛者

**场景**:
一类使用情境，如修 issue、用 tufte-reader 写读本；任务按场景归类。
_Avoid_: 类别、benchmark

**任务**:
某个场景下的一道具体题目，包含给选手的输入和评判依据。
_Avoid_: case、eval

**运行**:
一个选手做一个任务的一次尝试，连同它的产物。
_Avoid_: trial、rollout、session

**隐藏测试**:
SWE 任务的评判依据：取自真实修复提交、不给选手看的测试，分修复前失败修复后通过的 F2P 与修复前后都通过的 P2P 两组。
_Avoid_: oracle 测试、hidden tests

**已解决**:
一次 SWE 运行的隐藏测试 F2P 与 P2P 全部通过。
_Avoid_: 通过、resolved、pass
