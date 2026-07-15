import { createServer } from "node:http";
import { request as httpRequest } from "node:http";
import { request as httpsRequest } from "node:https";
import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const here = fileURLToPath(new URL(".", import.meta.url));

function loadLocalEnv() {
  const envPath = join(here, ".env");
  if (!existsSync(envPath)) return;

  const lines = readFileSync(envPath, "utf8").split(/\r?\n/);
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;

    const index = trimmed.indexOf("=");
    if (index === -1) continue;

    const key = trimmed.slice(0, index).trim();
    const value = trimmed
      .slice(index + 1)
      .trim()
      .replace(/^['"]|['"]$/g, "");
    if (key && process.env[key] == null) process.env[key] = value;
  }
}

loadLocalEnv();

const port = Number(process.env.LOCAL_GATEWAY_PORT || 18080);

const requiredEnvVars = ["API_TARGET", "AI_TARGET", "MEDIA_TARGET"];
const missing = requiredEnvVars.filter((key) => !process.env[key]);
if (missing.length > 0) {
  console.warn(
    `[local-gateway] Missing required env vars: ${missing.join(", ")}. ` +
      `Please set them in ${join(here, ".env")} or as environment variables.`,
  );
  process.exit(1);
}

const routes = [
  { prefix: "/api", target: process.env.API_TARGET },
  { prefix: "/ai", target: process.env.AI_TARGET },
  { prefix: "/media", target: process.env.MEDIA_TARGET },
];

function setCorsHeaders(response) {
  response.setHeader("Access-Control-Allow-Origin", "*");
  response.setHeader(
    "Access-Control-Allow-Methods",
    "GET,POST,PUT,PATCH,DELETE,OPTIONS",
  );
  response.setHeader(
    "Access-Control-Allow-Headers",
    "Content-Type, Authorization, X-Requested-With",
  );
  response.setHeader("Access-Control-Max-Age", "86400");
}

function findRoute(pathname) {
  return routes.find(
    (route) =>
      pathname === route.prefix || pathname.startsWith(`${route.prefix}/`),
  );
}

function buildTargetUrl(route, requestUrl) {
  const incoming = new URL(requestUrl, "http://local-runtime");
  const strippedPath = incoming.pathname.replace(route.prefix, "") || "/";
  const target = new URL(route.target);
  target.pathname =
    `${target.pathname.replace(/\/$/, "")}/${strippedPath.replace(/^\//, "")}`.replace(
      /\/+/g,
      "/",
    );
  target.search = incoming.search;
  return target;
}

function proxyRequest(clientRequest, clientResponse, route) {
  const targetUrl = buildTargetUrl(route, clientRequest.url || "/");
  const transport =
    targetUrl.protocol === "https:" ? httpsRequest : httpRequest;

  const headers = { ...clientRequest.headers };
  headers.host = targetUrl.host;

  const upstreamRequest = transport(
    targetUrl,
    {
      method: clientRequest.method,
      headers,
    },
    (upstreamResponse) => {
      setCorsHeaders(clientResponse);
      clientResponse.writeHead(
        upstreamResponse.statusCode || 502,
        upstreamResponse.headers,
      );
      upstreamResponse.pipe(clientResponse);
    },
  );

  upstreamRequest.on("error", (error) => {
    setCorsHeaders(clientResponse);
    clientResponse.writeHead(502, {
      "Content-Type": "application/json; charset=utf-8",
    });
    clientResponse.end(
      JSON.stringify({
        message: "本地接口网关转发失败",
        target: targetUrl.origin,
        detail: error.message,
      }),
    );
  });

  clientRequest.pipe(upstreamRequest);
}

const server = createServer((request, response) => {
  setCorsHeaders(response);

  if (request.method === "OPTIONS") {
    response.writeHead(204);
    response.end();
    return;
  }

  const pathname = new URL(request.url || "/", "http://local-runtime").pathname;
  const route = findRoute(pathname);

  if (!route) {
    response.writeHead(200, {
      "Content-Type": "application/json; charset=utf-8",
    });
    response.end(
      JSON.stringify({
        name: "smart-class-monitor-local-runtime",
        routes: routes.map((item) => ({
          prefix: item.prefix,
          target: item.target,
        })),
      }),
    );
    return;
  }

  proxyRequest(request, response, route);
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Local runtime gateway: http://127.0.0.1:${port}`);
  for (const route of routes) {
    console.log(`${route.prefix} -> ${route.target}`);
  }
});
