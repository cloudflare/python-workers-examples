# Image Redraw — FastAPI + R2 + Queues + Workflows + Workers AI

[![Deploy to Cloudflare](https://deploy.workers.cloudflare.com/button)](https://deploy.workers.cloudflare.com/?url=https://github.com/cloudflare/python-workers-examples/tree/main/20-image-redraw)

Upload a picture and get it back redrawn as a wobbly MS Paint doodle.

This example demonstrates how to leverage multiple Cloudflare services to
create a full-featured image processing pipeline using Python Workers.

- [Python Workers / FastAPI](https://fastapi.tiangolo.com/) - For API server
- [R2](https://developers.cloudflare.com/r2/) - Storing images
- [Workers AI](https://developers.cloudflare.com/workers-ai/) - Image-to-image inference
- [Queues](https://developers.cloudflare.com/queues/) - Work queue
- [Workflows](https://developers.cloudflare.com/workflows/) - Durable execution

```mermaid
flowchart LR
    Browser["Browser"]

    subgraph Worker["Python Worker"]
        Assets["Static Assets"]
        API["FastAPI<br/>/api/*"]
        Consumer["Queue consumer"]
        Workflow["RedrawWorkflow<br/>durable steps"]
    end

    Queue[["Queue<br/>image-redraw-jobs"]]
    Originals[("R2<br/>originals/{jobId}")]
    Outputs[("R2<br/>outputs/{jobId}")]
    AI["Workers AI<br/>image-to-image"]

    Browser -->|"GET /"| Assets
    Browser -->|"POST /api/jobs"| API
    API -->|"1. put image bytes"| Originals
    API -->|"2. send jobId only"| Queue
    API -->|"3. 202 Accepted + jobId"| Browser
    Queue -->|"batch of jobId only"| Consumer
    Consumer -->|"instance id = jobId"| Workflow
    Originals -->|"read original"| Workflow
    Workflow -->|"multipart reference image"| AI
    AI -->|"base64 PNG or JPEG"| Workflow
    Workflow -->|"store bytes + content type"| Outputs
    Browser -->|"poll GET /api/jobs/{jobId}"| API
    Outputs -->|"status + redrawn bytes"| API
```

The uploaded image is stored in R2 and the job ID is enqueued to the queue. The
queue consumer turns each batch of messages into Workflow instances.
Workflows call the Workers AI API to redraw the image and stores the result in R2.

## Setup

First ensure that `uv` is installed:
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

**Workers AI is a remote binding, even during local development.** `wrangler.jsonc`
declares `"ai": { "binding": "AI", "remote": true }`, so inference always runs on
Cloudflare's network and bills against your account. Log in before starting the
dev server:

```sh
uv run pwrangler login
```

## How to Run

```sh
uv run pywrangler dev
```

Then open http://localhost:8787/ in your browser.

## How to deploy

```sh
uv run pywrangler deploy
```
