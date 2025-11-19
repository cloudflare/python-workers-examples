# 13-js-api-pygments – Python RPC Server & TS Client

This example shows how to use **JS RPC** to connect a **Python Worker** (server) to a **TypeScript Worker** (client).

The Python Worker exposes a Pygments-powered `highlight_code` RPC method. The TS Worker calls this method to syntax-highlight code on the server side and renders the result as HTML.

## Project Layout

- `py/`
  - Python Worker (RPC server)
  - Exposes `HighlighterRpcService.highlight_code()` over RPC using Pygments
- `ts/`
  - TypeScript Worker (RPC client)
  - Calls the Python Worker via a `PYTHON_RPC` service binding and renders the highlighted code

## Prerequisites

- `uv` installed for Python dependency management
- Node.js + npm

## How to Run

### 1. Install and run the Python RPC server

```bash
cd 13-js-api-pygments/py
uv run pywrangler dev
```

This starts the Python Worker defined in `py/wrangler.jsonc`.

### 2. Install and run the TypeScript RPC client

Open a **second terminal**:

```bash
cd 13-js-api-pygments/ts
npm run dev
```

This starts the TypeScript Worker defined in `ts/wrangler.jsonc`, which has a `services` binding:

```jsonc
"services": [
  {
    "binding": "PYTHON_RPC",
    "service": "py-rpc-server"
  }
]
```

### 3. Try it out

- Visit the URL printed by `npm run dev` (usually `http://localhost:8787/`).
- The TS Worker will:
  - Call the Python Worker via RPC
  - Have Pygments highlight a sample TypeScript snippet
  - Return a full HTML page with highlighted code and styling

If you change the Python RPC method or the sample code in `ts/src/index.ts`, just reload the page to see the new output.
