// build.py 的 Chrome 运行器：一个无头 Chrome 实例依次跑完一批页面任务（CDP）。
//   node scripts/render.mjs <jobs.json>
// jobs.json：{"chrome": "<Chrome 路径>", "jobs": [任务, …]}。任务字段：
//   url      页面地址（file://…，可带 ?query）
//   width    视口宽，默认 1280；height 视口高，默认 900；dpr 像素比，默认 1
//   mobile   是否按手机模拟（触屏、viewport meta 生效），默认 width < 500
//   theme    "light" / "dark"：页面加载前写 localStorage 的 show-me-theme，并模拟同色的 prefers-color-scheme；
//            不给时只模拟浅色系统配色（本机是暗色外观也一样）
//   reduced  true 时模拟 prefers-reduced-motion: reduce
//   budget   虚拟时间预算（毫秒），默认 4000。有网络请求未完成时虚拟时间暂停（同 --virtual-time-budget）：
//            字体到齐、页面计时器跑满预算才往下走，结果不随网速变
//   eval     预算用完后求值的 JS 表达式，结果放进 value
//   slices   {"prefix": 路径前缀, "height": 每片高}：先把数据图全部画出来，再按整页高度切片截图，存为 前缀-01.png …
//   shot     路径：截当前视口
//   pdf      路径：先把数据图全部画出来，再按页面的 @page 尺寸打印成 PDF（show-me.css 定为 A4），无页眉页脚、不打背景
//   timeout  每个任务的真实时间上限（毫秒），默认 90000
// stdout：与任务一一对应的 JSON 数组，每项 {value, slices: [{path, top, height}], shot, pdf, errors: [页面 JS 异常], error: "哪一步失败"}，
// 没用到的字段不出现。退出码：0 正常；2 Chrome 起不来或运行器自身出错，原因写在 stderr 最后一行；
// 3 这个 node 没有内置 WebSocket（早于 22），build.py 按「没有 node」处理。
import { readFileSync, writeFileSync } from "node:fs";
import { launch } from "./cdp.mjs";

const spec = JSON.parse(readFileSync(process.argv[2], "utf8"));
let cdp;
try {
  cdp = await launch(spec.chrome);
} catch (e) {
  console.error(String(e.message || e));
  process.exit(typeof WebSocket === "undefined" ? 3 : 2);
}
const { send, until, on, close } = cdp;
const results = [];
let failed = "";
try {
  for (const job of spec.jobs) results.push(await run(job));
} catch (e) {
  failed = String(e.message || e);
}
await close();
if (failed) {
  console.error(failed);
  process.exit(2);
}
// 写管道在 macOS 上是异步的：等写完再退出，否则 64 KB 之后的部分会丢
process.stdout.write(JSON.stringify(results), () => process.exit(0));

async function run(job) {
  const width = job.width || 1280;
  const mobile = job.mobile ?? width < 500;
  const out = { errors: [] };
  const { targetId } = await send("Target.createTarget", {
    url: "about:blank",
  });
  const { sessionId } = await send("Target.attachToTarget", {
    targetId,
    flatten: true,
  });
  const S = (method, params) => send(method, params, sessionId);
  const off = on((m) => {
    if (m.sessionId !== sessionId || m.method !== "Runtime.exceptionThrown")
      return;
    const d = m.params.exceptionDetails;
    out.errors.push(
      ((d.exception && d.exception.description) || d.text || "").split("\n")[0]
    );
  });
  const ev = async (expression) => {
    const r = await S("Runtime.evaluate", {
      expression,
      returnByValue: true,
      awaitPromise: true,
    });
    if (r.exceptionDetails)
      throw new Error(
        r.exceptionDetails.exception?.description || r.exceptionDetails.text
      );
    return r.result.value;
  };
  // 数据图滚入视口才画（charts.js 的 reveal）：截切片、打印前先把首屏以外的图也画出来
  const drawAll = async () => {
    await ev(
      "document.querySelectorAll('figure[data-chart] svg').forEach(function(s){ if (s._replay) s._replay(); }), 1"
    );
    await new Promise((r) => setTimeout(r, 300));
  };
  let step = "打开页面";
  try {
    await S("Page.enable");
    await S("Runtime.enable");
    await S("Emulation.setDeviceMetricsOverride", {
      width,
      height: job.height || 900,
      deviceScaleFactor: job.dpr || 1,
      mobile,
    });
    if (mobile)
      await S("Emulation.setTouchEmulationEnabled", { enabled: true });
    // 系统配色也按主题模拟（没给主题按浅色）：没有防闪烁脚本的页面跟随系统配色，结果不随本机外观变
    await S("Emulation.setEmulatedMedia", {
      features: [
        {
          name: "prefers-reduced-motion",
          value: job.reduced ? "reduce" : "no-preference",
        },
        {
          name: "prefers-color-scheme",
          value: job.theme === "dark" ? "dark" : "light",
        },
      ],
    });
    if (job.theme)
      await S("Page.addScriptToEvaluateOnNewDocument", {
        source: `try{localStorage.setItem("show-me-theme",${JSON.stringify(job.theme)})}catch(e){}`,
      });
    step = "等页面稳定";
    await S("Emulation.setVirtualTimePolicy", { policy: "pause" });
    await S("Page.navigate", { url: job.url });
    const settled = until("Emulation.virtualTimeBudgetExpired", {
      sessionId,
      timeout: job.timeout || 90000,
    });
    await S("Emulation.setVirtualTimePolicy", {
      policy: "pauseIfNetworkFetchesPending",
      budget: job.budget || 4000,
    });
    await settled;
    // 预算用完后回到真实时间：截图要等真实的绘制帧
    await S("Emulation.setVirtualTimePolicy", { policy: "advance" });
    if (job.eval) {
      step = "求值";
      out.value = await ev(job.eval);
    }
    if (job.slices) {
      step = "切片截图";
      await drawAll();
      const total = await ev("document.documentElement.scrollHeight");
      out.slices = [];
      for (let top = 0, k = 1; top < total; top += job.slices.height, k++) {
        const height = Math.min(job.slices.height, total - top);
        const shot = await S("Page.captureScreenshot", {
          format: "png",
          captureBeyondViewport: true,
          clip: { x: 0, y: top, width, height, scale: 1 },
        });
        const path = `${job.slices.prefix}-${String(k).padStart(2, "0")}.png`;
        writeFileSync(path, Buffer.from(shot.data, "base64"));
        out.slices.push({ path, top, height });
      }
    }
    if (job.shot) {
      step = "截图";
      const shot = await S("Page.captureScreenshot", { format: "png" });
      writeFileSync(job.shot, Buffer.from(shot.data, "base64"));
      out.shot = job.shot;
    }
    if (job.pdf) {
      step = "打印 PDF";
      await drawAll();
      // 不传 preferCSSPageSize 时 Chrome 按 Letter 出，show-me.css 的 @page { size: A4 } 不生效
      const { data } = await S("Page.printToPDF", { preferCSSPageSize: true });
      writeFileSync(job.pdf, Buffer.from(data, "base64"));
      out.pdf = job.pdf;
    }
  } catch (e) {
    out.error = `${step}：${e.message || e}`;
  } finally {
    off();
    await send("Target.closeTarget", { targetId }).catch(() => {});
  }
  return out;
}
