import { chromium } from "playwright";

function assert(condition, message) {
  if (!condition) throw new Error(message);
}

async function main() {
  const url = process.argv[2];
  const maxElementsRaw = process.argv[3];
  assert(url, "missing url argument");

  const maxElements = Math.max(1, parseInt(maxElementsRaw || "256", 10));

  const browser = await chromium.launch();
  try {
    const page = await browser.newPage();
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 30000 });
    // A short settle window helps computed styles (fonts/layout) stabilize.
    await page.waitForTimeout(750);

    await page.evaluate((maxN) => {
      const selector = [
        "button",
        "a",
        "input",
        "textarea",
        "select",
        "nav",
        "header",
        "footer",
        "section",
        "article",
        "aside",
        "main",
        "div",
        "span",
        "ul",
        "ol",
        "li",
        "img",
        "svg",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "p",
      ].join(",");

      const nodes = Array.from(document.querySelectorAll(selector));
      let seen = 0;
      for (const el of nodes) {
        if (seen >= maxN) break;
        seen += 1;

        const cs = window.getComputedStyle(el);
        if (!cs) continue;

        // Dataset keys become: data-rade-token-<kebab-case>.
        el.dataset.radeTokenColor = cs.color || "";
        el.dataset.radeTokenBackgroundColor = cs.backgroundColor || "";
        el.dataset.radeTokenFontFamily = cs.fontFamily || "";
        el.dataset.radeTokenFontWeight = cs.fontWeight || "";
        el.dataset.radeTokenPadding = cs.padding || "";
        el.dataset.radeTokenMargin = cs.margin || "";
        el.dataset.radeTokenGap = cs.gap || "";
        el.dataset.radeTokenLineHeight = cs.lineHeight || "";
      }
    }, maxElements);

    // Return final DOM with injected computed-style tokens.
    const html = await page.content();
    process.stdout.write(html);
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  // Non-zero exit will be converted into RuntimeError by the caller.
  console.error(err);
  process.exitCode = 1;
});

