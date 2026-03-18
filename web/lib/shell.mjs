import http from "node:http";

const sharedStyles = `
      :root {
        color-scheme: dark;
      }

      body {
        font-family: system-ui, sans-serif;
        margin: 0;
        background:
          radial-gradient(circle at top left, rgba(90, 116, 255, 0.24), transparent 30%),
          radial-gradient(circle at top right, rgba(69, 214, 157, 0.16), transparent 32%),
          #0b1020;
        color: #f5f7fb;
      }

      main {
        max-width: 1040px;
        margin: 0 auto;
        padding: 72px 24px 88px;
      }

      .card {
        background: rgba(255, 255, 255, 0.06);
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 28px;
        padding: 34px;
        box-shadow: 0 24px 80px rgba(0, 0, 0, 0.28);
        backdrop-filter: blur(14px);
      }

      .eyebrow {
        margin: 0 0 12px;
        font-size: 0.8rem;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: rgba(255, 255, 255, 0.66);
      }

      h1 {
        margin: 0 0 14px;
        font-size: clamp(2.4rem, 5vw, 4.6rem);
        line-height: 0.98;
      }

      p {
        margin: 0 0 14px;
        line-height: 1.65;
        max-width: 68ch;
        color: rgba(245, 247, 251, 0.88);
      }

      .muted {
        color: rgba(245, 247, 251, 0.66);
      }

      .grid {
        display: grid;
        gap: 16px;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        margin-top: 24px;
      }

      .metric {
        border-radius: 20px;
        padding: 18px 20px;
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.08);
      }

      .metric-label {
        display: block;
        font-size: 0.78rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: rgba(255, 255, 255, 0.58);
        margin-bottom: 8px;
      }

      .metric-value {
        display: block;
        font-size: 1.4rem;
        font-weight: 650;
      }

      .link {
        color: #8dc5ff;
        text-decoration: none;
      }

      .link:hover {
        text-decoration: underline;
      }
`;

function pageShell(title, body) {
  return `<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>${title}</title>
    <style>${sharedStyles}</style>
  </head>
  <body>${body}</body>
</html>`;
}

function rootBody() {
  return `<main>
      <section class="card">
        <p class="eyebrow">Proof slice</p>
        <h1>RADE web shell</h1>
        <p>
          This shell stays intentionally thin while the deterministic report pipeline
          remains the source of truth.
        </p>
        <p class="muted">
          The active web runtime is this shell server. The <code>web/app/</code>
          directory is a dormant scaffold until a real Next.js runtime is adopted.
        </p>
        <div class="grid" aria-label="Current proof summary">
          <div class="metric">
            <span class="metric-label">Current mode</span>
            <span class="metric-value">Shell first</span>
          </div>
          <div class="metric">
            <span class="metric-label">Primary proof</span>
            <span class="metric-value">Deterministic reports</span>
          </div>
          <div class="metric">
            <span class="metric-label">Next surface</span>
            <span class="metric-value">Report review</span>
          </div>
        </div>
      </section>
    </main>`;
}

function reportBody() {
  return `<main>
      <section class="card">
        <p class="eyebrow">Sample report</p>
        <h1>Modernization report</h1>
        <p>
          This preview path exists to give the web shell a concrete report-view smoke
          target before any real framework migration is approved and implemented.
        </p>
        <div class="grid" aria-label="Sample report summary">
          <div class="metric">
            <span class="metric-label">Screens</span>
            <span class="metric-value">2</span>
          </div>
          <div class="metric">
            <span class="metric-label">Recommendations</span>
            <span class="metric-value">3</span>
          </div>
          <div class="metric">
            <span class="metric-label">State</span>
            <span class="metric-value">Deterministic</span>
          </div>
        </div>
        <p class="muted">
          <a class="link" href="/">Back to the shell</a>
        </p>
      </section>
    </main>`;
}

function notFoundBody(pathname) {
  return `<main>
      <section class="card">
        <p class="eyebrow">Not found</p>
        <h1>Unknown route</h1>
        <p>The shell only serves <code>/</code> and <code>/report</code> for now.</p>
        <p class="muted">Requested path: <code>${pathname}</code></p>
        <p class="muted"><a class="link" href="/">Return home</a></p>
      </section>
    </main>`;
}

export function renderShellDocument(pathname) {
  if (pathname === "/") {
    return {
      statusCode: 200,
      html: pageShell("RADE", rootBody()),
    };
  }

  if (pathname === "/report") {
    return {
      statusCode: 200,
      html: pageShell("RADE report", reportBody()),
    };
  }

  return {
    statusCode: 404,
    html: pageShell("RADE", notFoundBody(pathname)),
  };
}

export function createShellServer() {
  return http.createServer((request, response) => {
    const url = new URL(request.url ?? "/", "http://127.0.0.1");
    const document = renderShellDocument(url.pathname);

    response.writeHead(document.statusCode, {
      "Content-Type": "text/html; charset=utf-8",
      "Content-Length": Buffer.byteLength(document.html),
    });
    response.end(document.html);
  });
}
