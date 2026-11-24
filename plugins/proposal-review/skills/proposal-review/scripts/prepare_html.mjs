import { existsSync } from "node:fs";
import { mkdir, writeFile } from "node:fs/promises";
import { homedir } from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [sourceArg, outputArg] = process.argv.slice(2);
if (!sourceArg || !outputArg) {
  console.error("node prepare_html.mjs <source.html> <working-directory>");
  process.exit(2);
}

const source = path.resolve(sourceArg);
const output = path.resolve(outputArg);
const bundled = path.join(homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs");
const playwright = process.env.PROPOSAL_PLAYWRIGHT || (existsSync(bundled) ? bundled : null);
const { chromium } = playwright ? await import(pathToFileURL(playwright).href) : await import("playwright");
const executablePath = [
  process.env.PROPOSAL_CHROME,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/chromium",
  "/usr/bin/google-chrome",
].find(candidate => candidate && existsSync(candidate));

function readSlide(slide) {
  const bounds = slide.getBoundingClientRect();
  const normalize = value => value.replace(/\s+/g, " ").trim();
  const round = number => Math.round(number * 10000) / 10000;
  const blocks = [];
  const seen = new Set();
  for (const element of slide.querySelectorAll("h1,h2,h3,h4,p,li,th,td,.problem,.decision,.module,.stage,.node")) {
    if (!element.getClientRects().length) continue;
    const text = normalize(element.innerText);
    if (!text || text.length > 310) continue;
    const range = element.ownerDocument.createRange();
    range.selectNodeContents(element);
    const box = range.getBoundingClientRect();
    if (box.width < 4 || box.height < 4) continue;
    const tolerance = 2;
    if (box.left < bounds.left - tolerance || box.top < bounds.top - tolerance ||
        box.right > bounds.right + tolerance || box.bottom > bounds.bottom + tolerance) continue;
    let hidden = false;
    for (let parent = element.parentElement; parent && parent !== slide; parent = parent.parentElement) {
      const style = parent.ownerDocument.defaultView.getComputedStyle(parent);
      const clip = parent.getBoundingClientRect();
      const clips = value => /^(auto|scroll|hidden|clip)$/.test(value);
      if ((clips(style.overflowY) && (box.top < clip.top - tolerance || box.bottom > clip.bottom + tolerance)) ||
          (clips(style.overflowX) && (box.left < clip.left - tolerance || box.right > clip.right + tolerance))) {
        hidden = true;
        break;
      }
    }
    if (hidden) continue;
    const x = Math.max(0, (box.left - bounds.left - 3) / bounds.width);
    const y = Math.max(0, (box.top - bounds.top - 2) / bounds.height);
    const w = Math.min(1 - x, (box.right - bounds.left + 3) / bounds.width - x);
    const h = Math.min(1 - y, (box.bottom - bounds.top + 2) / bounds.height - y);
    const rect = [x, y, w, h].map(round);
    const key = JSON.stringify([text, ...rect]);
    if (seen.has(key)) continue;
    seen.add(key);
    blocks.push({ id: "b" + (blocks.length + 1), text, rect });
  }
  return {
    title: normalize(slide.querySelector("h1, h2")?.innerText ?? slide.dataset.title ?? ""),
    text: slide.innerText.trim(),
    blocks,
    aspect: round(bounds.width / bounds.height),
  };
}

const sourceUrl = pathToFileURL(source).href;
await mkdir(output, { recursive: true });
const browser = await chromium.launch({ executablePath, headless: true });
try {
  const context = await browser.newContext({ viewport: { width: 1720, height: 1120 }, deviceScaleFactor: 1, serviceWorkers: "block" });
  // The supported decks embed their resources. Keep rendering on the local file.
  await context.route("**/*", route => {
    const url = route.request().url();
    return url === sourceUrl || /^(?:data|blob|about):/.test(url) ? route.continue() : route.abort();
  });
  const browserPage = await context.newPage();
  await browserPage.goto(sourceUrl);
  await browserPage.locator("iframe.current").contentFrame().locator(".slide.active").waitFor();
  const jump = browserPage.locator("#jump");
  const count = await jump.locator("option").count();
  if (!count) throw new Error("找不到模板的翻页控件。请使用逐页图像或导出的 PDF。");
  const pages = [];
  for (let number = 1; number <= count; number++) {
    await jump.selectOption(String(number - 1));
    await browserPage.waitForFunction(number => document.querySelector("#count")?.textContent.trim().startsWith(number + " /"), number);
    const frame = browserPage.locator("iframe.current").contentFrame();
    const slide = frame.locator(".slide.active");
    await slide.waitFor();
    await slide.evaluate(node => node.ownerDocument.fonts.ready.then(() => null));
    const content = await slide.evaluate(readSlide);
    const image = "page-" + String(number).padStart(2, "0") + ".png";
    await slide.screenshot({ path: path.join(output, image), animations: "disabled" });
    const visibleNotes = await browserPage.locator("#method-notes").innerText().catch(() => "");
    pages.push({ page: number, image, ...content, methodologyNotes: visibleNotes.trim() });
  }
  await writeFile(path.join(output, "pages.json"), JSON.stringify({ source: path.basename(source), pages }, null, 2));
  console.log("已读取 " + pages.length + " 页，逐页截图和定位数据保存在 " + output);
} finally {
  await browser.close();
}
