# day-6-mcp — Local Web Search Gateway (MVP)

This container exposes a tiny HTTP gateway that implements a single "tool" for web search, consumable from the Android app during Agent 1's clarification loop.

- Endpoint base: `http://localhost:8765/`
- Android emulator base: `http://10.0.2.2:8765/`
- Endpoints:
  - `GET /healthz` → `{ "ok": true }`
  - `GET /tools` → `{ "tools": [{"name":"web.search"}] }`
  - `POST /search` → body `{ "query": "kotlin mcp sdk", "top_k": 5 }` → results list

Under the hood it queries one of:
- Brave Search API (if `BRAVE_API_KEY` is provided), or
- SerpAPI (if `SERPAPI_KEY` is provided), or
- DuckDuckGo Instant Answer (no key; fallback, limited)

It is not a full MCP server; it is an HTTP bridge exposing a stable shape consumed by the app. You can replace it later with a true MCP bridge without changing the app.

## Build and Run

```bash
# From repo root
cd day-6-mcp

# Build
docker build -t mcp-web-gateway .

# Run (no API key; uses DuckDuckGo fallback)
docker run --rm -p 8765:8765 --name mcp-web-gateway mcp-web-gateway

# Or with Brave Search (recommended)
docker run --rm -p 8765:8765 \
  -e BRAVE_API_KEY=your_brave_key \
  --name mcp-web-gateway mcp-web-gateway

# Or with SerpAPI
# docker run --rm -p 8765:8765 -e SERPAPI_KEY=your_serpapi_key --name mcp-web-gateway mcp-web-gateway
```

## Quick Test

```bash
curl -s http://localhost:8765/healthz | jq
curl -s http://localhost:8765/tools | jq
curl -s -X POST http://localhost:8765/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"kotlin mcp client", "top_k": 5}' | jq
```

Expected response (shape):
```json
{
  "results": [
    { "title": "...", "url": "https://...", "snippet": "..." }
  ]
}
```

## Android Configuration (NextGen app)
- Debug builds automatically use `http://10.0.2.2:8765/` via `BuildConfig.MCP_BRIDGE_URL`.
- The repository will call `/search` when Agent 1 outputs `ACTION: web.search` with `ARGS`.

## Notes
- No secrets are stored in the repo. Provide search keys via env vars when running the container.
- Replace this gateway with a proper MCP bridge later without touching the Android app.



