import { chromium } from "playwright";

import { createShellServer } from "../lib/shell.mjs";

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

async function listenOnPort(server, host, port) {
  await new Promise((resolve) => {
    server.listen(port, host, resolve);
  });

  const address = server.address();
  assert(address && typeof address === "object" && "port" in address, "server did not bind a port");
  return address.port;
}

async function smokeRoute(page, url, expectedTitle, expectedHeading, expectedText) {
  await page.goto(url, { waitUntil: "domcontentloaded" });
  const title = await page.title();
  assert(title === expectedTitle, `expected title ${expectedTitle} for ${url}`);
  await page.getByRole("heading", { name: expectedHeading }).waitFor();
  if (expectedText) {
    await page.getByText(expectedText, { exact: false }).waitFor();
  }
}

async function main() {
  const server = createShellServer();
  const host = "127.0.0.1";
  const port = await listenOnPort(server, host, 0);
  const baseUrl = `http://${host}:${port}`;
  let browser;

  try {
    browser = await chromium.launch();
    const page = await browser.newPage();
    await smokeRoute(
      page,
      `${baseUrl}/`,
      "RADE",
      "RADE web shell",
      "deterministic report pipeline"
    );
    await smokeRoute(
      page,
      `${baseUrl}/report`,
      "RADE report",
      "Modernization report",
      "report-view smoke target"
    );
    console.log(`RADE web shell smoke test passed against ${baseUrl}`);
  } finally {
    if (browser) {
      await browser.close();
    }
    await new Promise((resolve) => {
      server.close(resolve);
    });
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
