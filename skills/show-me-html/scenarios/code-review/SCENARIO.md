# 场景 · code-review — 会话续期逻辑改动

配方：`code-review`（评审者视角）。版心默认 60rem。

## 读者任务

评审者在合并前确认这次改动安全：滑动过期窗口修复 + 事件补发。

## 冻结材料（mock diff）

改动摘要：2 文件，+42 −13，风险等级中（涉及鉴权路径）。

结构 diff：

```diff
 src/auth/
 ├── session.ts        # 续期窗口从固定改为滑动
-└── events.ts
+└── events/           # 拆出 emitter，补发逻辑单独可测
+    └── emitter.ts
```

`src/auth/session.ts`（+28 −9）：

```diff
- const RENEW_AFTER = 3600; // 固定一小时后续期
+ const RENEW_WINDOW = 0.2; // 活跃度超过窗口剩余时间 20% 即续期
  function shouldRenew(session) {
-   return now() - session.issuedAt > RENEW_AFTER;
+   return session.lastSeen > session.issuedAt + session.ttl * RENEW_WINDOW;
  }
```

`src/auth/events/emitter.ts`（新增 +14 −4）：断线重连后补发缓冲事件，
缓冲上限 100 条，超出丢最旧并打点。

待确认问题（评审勾选）：

- [ ] `lastSeen` 时钟源与 `issuedAt` 一致吗（NTP 漂移下 20% 窗口会不会提前触发）
- [ ] 补发缓冲 100 条上限对多标签页浏览器是否够
- [ ] 灰度计划里旧客户端收不到补发事件，是否可接受

## 通过标准

- build.py ERROR = 0；diff 行用 .d-add / .d-del 着色
- 每文件一个折叠，summary 含文件名与增删数
- 待确认问题可勾选（真 checkbox）
- 结构 diff 在按文件 diff 之前
