#!/usr/bin/env node
// 检查技能文档的交叉引用：相对链接必须指向存在的文件；章节按标题名引用，不按编号。
// 用法: node scripts/check-skills.mjs（在仓库根目录运行）。有问题时逐条打印 file:line 并以 1 退出。
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, join, resolve } from "node:path";

// deprecated 是历史档案；assets 是产出模板，里面的链接指向目标项目的文件
const SKIP = new Set(["deprecated", "node_modules", "assets"]);

function markdownFiles(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((e) => {
    if (e.isDirectory())
      return SKIP.has(e.name) ? [] : markdownFiles(join(dir, e.name));
    return e.name.endsWith(".md") ? [join(dir, e.name)] : [];
  });
}

const problems = [];
const files = [...markdownFiles("skills"), "README.md", "CLAUDE.md"].filter(
  (f) => existsSync(f)
);

for (const file of files) {
  let fenced = false;
  readFileSync(file, "utf8")
    .split("\n")
    .forEach((raw, i) => {
      if (/^\s*(```|~~~)/.test(raw)) fenced = !fenced;
      if (fenced) return;
      const line = raw.replace(/`[^`]*`/g, "");

      for (const [, target] of line.matchAll(/\]\(([^)\s]+)\)/g)) {
        if (/^([a-z][a-z0-9+.-]*:|#)/i.test(target) || /[<{]/.test(target))
          continue;
        const path = decodeURI(target.split("#")[0]);
        if (!existsSync(resolve(dirname(file), path)))
          problems.push(`${file}:${i + 1}: 链接目标不存在: ${target}`);
      }

      // 「第 3 节」这种带引号的写法是在举例，不是引用
      const numbered = line.match(/(?<!「)第 ?\d+(?:、\d+)* ?节/);
      if (numbered)
        problems.push(
          `${file}:${i + 1}: 按编号引用章节「${numbered[0]}」，改为按标题名引用`
        );
    });
}

if (problems.length) {
  console.error(problems.join("\n"));
  console.error(`\n${problems.length} 处问题，共检查 ${files.length} 个文件`);
  process.exit(1);
}
console.log(`技能文档引用检查通过（${files.length} 个文件）`);
