import fs from "node:fs";

import { renderShellDocument } from "../lib/shell.mjs";

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

function assertDocument(pathname, expectedStatus, expectedTitle, expectedText) {
  const document = renderShellDocument(pathname);

  assert(document.statusCode === expectedStatus, `expected ${expectedStatus} for ${pathname}`);
  assert(document.html.includes(`<title>${expectedTitle}</title>`), `expected title ${expectedTitle} for ${pathname}`);
  assert(document.html.includes(expectedText), `expected content ${expectedText} for ${pathname}`);
}

assertDocument("/", 200, "RADE", "RADE web shell");
assertDocument("/", 200, "RADE", "web/app/");
assertDocument("/report", 200, "RADE report", "Modernization report");
assertDocument("/missing", 404, "RADE", "Unknown route");

const dormantPage = fs.readFileSync(new URL("../app/page.tsx", import.meta.url), "utf8");
assert(dormantPage.includes("Dormant scaffold"), "web/app/page.tsx must be marked as dormant");
assert(
  dormantPage.includes("web/lib/shell.mjs"),
  "web/app/page.tsx must point to the active shell runtime",
);

console.log("RADE web shell lint passed");
