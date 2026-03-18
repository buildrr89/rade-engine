import { createShellServer } from "../lib/shell.mjs";

const host = process.env.WEB_HOST ?? "127.0.0.1";
const port = Number(process.env.WEB_PORT ?? "3000");
const server = createShellServer();

server.listen(port, host, () => {
  const address = server.address();
  const actualPort =
    address && typeof address === "object" && "port" in address ? address.port : port;
  console.log(`RADE web shell listening on http://${host}:${actualPort}`);
});
