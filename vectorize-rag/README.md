# Vectorize RAG in Python

This example shows how to build a very simple Vectorized document retrieval system using Cloudflare's Vectorize service and Python workers.

> **Note:** This example uses remote Workers AI and Vectorize resources, which are billable, even in local development.

## Local development

```bash
npx wrangler login
# Select the intended account if Wrangler prompts for one.
npx wrangler vectorize create python-rag-index --dimensions=768 --metric=cosine
uv run pywrangler dev
```

### Seeding

```bash
curl -X POST http://localhost:8787/seed
```

Seed the four-document to the Vectorize index.

### Querying

```bash
curl -X POST http://localhost:8787/query \
  -H 'content-type: application/json' \
  --data '{"question":"What does Vectorize store?"}'
```

## Endpoints

- `GET /` describes the setup and models.
- `POST /seed` embeds and upserts the documents.
- `POST /query` accepts `{"question":"..."}` and returns a grounded `answer` plus match IDs, titles, scores, and citations.
