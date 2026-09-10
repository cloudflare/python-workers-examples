# MCP Server with D1

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/cloudflare/python-workers-examples/tree/main/mcp-server)

This example shows how to create a simple [Model Context Protocol](https://modelcontextprotocol.io/) server.
It uses the official [Python MCP SDK](https://py.sdk.modelcontextprotocol.io/) and a D1 database.

It implements 3 tools, as a simple incident management system:

- `open_incident(title, severity)`
- `add_update(id, note)`
- `list_open_incidents()`

This is based on the stateless MCP protocol version `2026-07-28`.

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then
initialize local D1 and start the Worker:

```sh
uv run pywrangler d1 migrations apply mcp-incidents --local
uv run pywrangler dev
```

Use modern JSON-RPC requests with the protocol header. For example, discover
the server and list its tools:

```sh
curl -X POST http://localhost:8787/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: server/discover' \
  --data '{"jsonrpc":"2.0","id":1,"method":"server/discover","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}}}}'

curl -X POST http://localhost:8787/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -H 'MCP-Protocol-Version: 2026-07-28' \
  -H 'Mcp-Method: tools/call' \
  -H 'Mcp-Name: open_incident' \
  --data '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28","io.modelcontextprotocol/clientCapabilities":{}},"name":"open_incident","arguments":{"title":"API latency","severity":"high"}}}'
```

You can also use your favorite MCP client to test the server. For example, if you are using VS Code, add the following to your settings:

```json
{
  "servers": {
    "incident-server": {
      "type": "http",
      "url": "http://localhost:8787/mcp"
    }
  }
}
```

and your MCP client should be able to discover and use the server.
