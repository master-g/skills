## The Format That Makes It Work

> **关于排版约定**:游戏原文是纯文本 + 颜色编码的 UI(技能用青色、检定用括号、内陆帝国的物品声音另有颜色)。在 markdown / 终端里没有颜色,所以本 skill 用**加粗**(技能)、_斜体_(物品/世界之声)、`> 引用块`(玩家向内的声音)来还原那套视觉分层。这是本 skill 的呈现约定,不是游戏原文格式——但请严格遵守它,因为读者要靠它一眼认出"谁在说话"。

### Skill Check Lines

The game uses Chinese full-width brackets `【】`, not `[]`. **Skill names are always bold:**

```
**技能名称**【难度:结果】 — 正文内容
```

Or without difficulty when it's a passive check:

```
**技能名称**【成功】 — 正文内容
```

Or just the skill name when it's providing ongoing commentary:

```
**技能名称** — 正文内容
```

**五感发达** always tags the specific sense. 母本里实际出现的标注感官是**视觉 / 听觉 / 嗅觉 / 味觉**(按出现频次,视觉最多、味觉最少;"触觉"几乎不带标注,需要触感时直接写裸句即可):

```
**五感发达**(视觉)【成功】 — ...
**五感发达**(听觉)【成功】 — ...
**五感发达**(嗅觉)【成功】 — ...
**五感发达**(味觉)【成功】 — ...
```

**被动检定 vs 主动检定**:脑中大多数声音是**被动检定**——自动触发、玩家无从选择,所以它们多半只显示 `【成功】`/`【失败】`,不带难度(这也是游戏文本里满屏 `【成功】` 的原因)。**主动检定**是主角咬牙决定"要不要去试"一件有风险的事,这时才显示难度。

**Difficulty levels**(官方阶梯,由易到难,仅主动检定显示): 微不足道 → 简单 → 中等 → 有挑战性 → 艰巨 → 传奇 → 英雄 → 神级 → 不可能。(注:旧版写的"困难/地狱"不是官方档名。)

**Results**: 成功 / 失败。**大成功 / 大失败**(即"严重成功/严重失败",掷出双 6 / 双 1 的暴击)极其稀有——只在最戏剧化的转折点动用一次,滥用会让它失去分量。

**红色检定 vs 白色检定**(改写现实抉择时极有用的一对):

- **白色检定** — 失败了还能再来。可以练一项技能、改一版方案、再约一次谈话后重试。适合"还有退路"的处境。
- **红色检定** — 一次性,不可逆。说出口的话、按下的发送键、错过的航班。把它留给叙事里真正回不了头的那一下,**无论成败都不许重来**。

需要点明检定类型时可写 `**技能名**【红色检定·失败】 — ...`(这是本 skill 的标注约定,游戏靠颜色区分)。

### Player Voice

The game constantly interweaves the player's voice. **Player voice always uses a blockquote** — visually "going inward". But there are **two distinct forms**, and the difference is who can hear it (母本统计:说出口的话 11439 行,内心与动作 3413 行——两者都是主角的声音,别只用一种):

**说出口的话** — 带中文引号。世界听得见,会产生后果,无法撤回:

```
> **你** — “愿意跟我一起走走吗?”
```

**内心与动作** — 不带引号,或用括号包一个动作。只有你和那 24 个声音听得见:

```
> **你** — 等等,这意味着什么?
> **你** — (重新跳入无形的深渊。)
> **你** — 浏览那堆跟威勒尔有关的商品。
```

**说谎要标记** — 说出口的话如果与事实不符,加 `(撒谎)` 前缀。这是给读者和技能们的信号:故弄玄虚会点评你的演技,疑神疑鬼会担心你被拆穿:

```
> **你** — (撒谎)“我从来没有怀疑过他。”
```

母本开场的玩家声音几乎全是括号动作——主角在黑暗里做的那些微小决定,比他说出口的任何话都更诚实:

```
**逻辑思维**【成功】 — 楼上的巨大财产损失与此有关吗?

> **你** — 等等,这意味着什么?

**内陆帝国** — *你知道这意味着什么。你一直都知道。*

> **你** — (闭上眼睛。)

**平心定气**【有挑战性:成功】 — 但你必须知道。
```

The `> **你** —` lines are the protagonist (the user) responding to their own inner voices. They can be confused, defiant, self-deprecating, or darkly funny. Use them to break up skill monologues and create conversational rhythm — and remember that silence and small actions (`(闭上眼睛。)`) are also responses.

### Objects as Speakers

内陆帝国 gives inanimate objects their own voice. **Object names are italic** — they come from the world outside, not from inside the head:

```
*恐怖领带* — 别担心，兄弟。拉斐尔·安普罗修斯·库斯托是个很有格调的名字。
*镜子* — 所有关于你是谁的记忆都已经被血液中的酒精海给淹没。
*吊扇* — 这是个严重的错误!马上把灯关掉!
*带腐肉的靴子* — 你永远也不会知道成为他那样的人是什么感觉。
```

When the narrative involves objects the user interacts with (a screen, a phone, a cup of coffee, a resignation letter), give them voices. They know things. They judge. They sometimes comfort.

### Markdown Visual Rules

Three voices, three visual languages — readers should identify who's speaking at a glance:

| 声音类型        | 格式                          | 说明                   |
| --------------- | ----------------------------- | ---------------------- |
| 技能 / 技能检定 | `**技能名称**【结果】 — 内容` | 名称加粗，视觉主体     |
| 玩家声音        | `> **你** — 内容`             | 引用块，象征"向内陷入" |
| 物品声音        | `*物品名称* — 内容`           | 斜体，来自世界而非内心 |

**Multi-line content**: when a skill speaks more than two lines, put the skill name on its own line, then content below:

```
**逻辑思维**【中等:成功】

有三种可能：
1. API 改了字段名
2. 在不同环境运行
3. 从未在真实数据上测试过
```

**Major beat shifts**: use `---` when the narrative pivots sharply between voices:

```
**食髓知味**【失败】 — *卖！卖！卖！*

---

**平心定气**【有挑战性:成功】 — *停。*
```

---
