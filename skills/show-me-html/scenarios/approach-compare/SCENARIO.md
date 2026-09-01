# 场景 · approach-compare — 任务队列选型

配方：`approach-compare`。版心默认 60rem。

## 读者任务

平台组在三方案里选一个做异步任务底座，本页给判据与推荐。

## 冻结材料（mock）

推荐：Postgres SKIP LOCKED —— 已有运维与备份，当前量级下最省；规模翻两番再评估 NATS。

判据（三列）：运维成本 / 吞吐上限 / 语义保证 / 团队熟悉度 / 迁移代价。

方案 A · Redis Streams

- 代码：`XADD` / `XREADGROUP`，消费者组原生
- 优点：吞吐 5 万 msg/s 实测；延迟毫秒级
- 代价：持久化靠 AOF，最坏丢最近秒级数据；团队只有一人深度用过

方案 B · Postgres SKIP LOCKED

- 代码：`SELECT … FOR UPDATE SKIP LOCKED` 轮询
- 优点：与主库同套备份、监控、权限；exactly-once 由事务保证
- 代价：轮询间隔 2s 起步，吞吐实测 3 千 msg/s 上限；连接占用高

方案 C · NATS JetStream

- 代码：publish / pull consumer
- 优点：水平扩展最好；at-least-once + 去重窗口
- 代价：新增一套中间件运维；K8s 内无现成 operator

当前量级：峰值 800 msg/s，任务允许 5 分钟延迟。

## 通过标准

- build.py ERROR = 0；推荐卡恰好一张（边框 primary）
- 判据表三列齐全，✓/✗ 用 badge
- 每方案卡含代码片段（language-sql / language-bash 等）
- 摘要块在首屏，一句话推荐 + 一句话理由
