# 场景 · concept-explainer — 缓存命中率与 TTL

配方：`concept-explainer`。版心 46rem（长文）。

## 读者任务

后端新人拖动滑块，理解 TTL 变长为什么命中率上升、为什么收益递减、
以及过期风暴在哪个参数组合下出现。

## 冻结材料（模型先于图）

模型函数（页面必须先写它，图与正文数字全部由它派生）：

```js
// 均匀 keyspace 近似：命中率 = 1 - miss 率；miss 率 = qps * ttl / keyspace（封顶 1）
// 过期风暴强度 = 每秒过期数 / qps 超过 1 时线性恶化
function hitRate(qps, ttl, keyspace) {
  const miss = Math.min(1, (qps * ttl) / keyspace);
  return 1 - miss;
}
function storm(qps, ttl, keyspace) {
  return keyspace / ttl / qps; // >1 表示每秒过期条数超过写入条数
}
```

冻结参数域：qps 50–2000（默认 400）；ttl 30–3600s（默认 600）；
keyspace 冻结 100 万条。

交互要求：

- 两个滑块（qps、ttl），实时更新命中率大数字与曲线
- 一张命中率随 ttl 变化的曲线（当前 qps 下），当前点高亮
- storm > 1 时出现警示（badge destructive），正文解释原因

正文骨架：直觉（三个问句）→ 可拖模型 → 形式化（两个公式）→ 边界情形
（keysize 装不下整个 keyspace 时命中率封顶）。

## 通过标准

- build.py ERROR = 0；滑块外观为骨架样式（非系统蓝色轨道）
- 正文里的每个数字（如「TTL 600s 时命中率 76%」）由模型函数算出
- prefers-reduced-motion 下无自动动效
- 图头有操作提示（「拖动滑块」），图注是能独立成立的结论
