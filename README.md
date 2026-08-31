# Python Workers Examples

This is a collection of examples for [writing Cloudflare Workers in Python](https://developers.cloudflare.com/workers/languages/python). Use these examples to learn how Python Workers work.

## Get started

1. `git clone https://github.com/cloudflare/python-workers-examples`
2. `cd hello`
3. `uvx --from workers-py pywrangler dev`
4. Press the `b` key to open a browser tab, and make a request to your Worker

You can run `uvx --from workers-py pywrangler dev` in any example project directory to run a local development server using [Pywrangler](https://github.com/cloudflare/workers-py), the CLI for Cloudflare Python Workers. This local development server is powered by [workerd](https://github.com/cloudflare/workerd), the open-source Workers runtime.

Need to deploy your Worker to Cloudflare? Python Workers are in open beta and have a few [limitations](#open-beta-and-limits).

## Examples

- [**`hello/`**](hello) — the most basic Python Worker
- [**`binding/`**](binding) — shows how [bindings](https://developers.cloudflare.com/workers/configuration/bindings/) work in Python Workers. Put a key into Workers KV, and then read it.
- [**`fastapi/`**](fastapi) — demonstrates how to use the [FastAPI](https://fastapi.tiangolo.com/) package with Python Workers
- [**`query-d1/`**](query-d1) - shows how to query D1 with Python Workers
- [**`langchain/`**](langchain) — demonstrates how to use the [LangChain](https://pypi.org/project/langchain/) package with Python Workers. Currently broken.
- [**`assets/`**](assets) — An example with an assets binding.
- [**`durable-objects/`**](durable-objects) — An example with storing state in a [Durable Object](https://developers.cloudflare.com/durable-objects/).
- [**`cron/`**](cron) — shows a simple [cron job](https://developers.cloudflare.com/workers/configuration/cron-triggers/).
- [**`workers-ai/`**](workers-ai) makes a call [Workers AI](https://developers.cloudflare.com/workers-ai/) to run inference on Cloudflare's Global Network.
- [**`workflows/`**](workflows) — shows a durable [Workflows](https://developers.cloudflare.com/workflows/) example.
- [**`opengraph/`**](opengraph) — shows how to use [HTMLRewriter](https://developers.cloudflare.com/workers/runtime-apis/html-rewriter/) to generate OpenGraph images with Python Workers.
- [**`image-gen/`**](image-gen) — shows how to use [Pillow](https://pillow.readthedocs.io/en/stable/) to generate images with Python Workers.
- [**`js-api-pygments/`**](js-api-pygments) — shows how to use [Pygments](https://pygments.org/) to highlight code with Python Workers.
- [**`websocket-stream-consumer/`**](websocket-stream-consumer) — shows how to use [WebSocket](https://developers.cloudflare.com/workers/runtime-apis/websockets/) to consume a stream of data with Python Workers.
- [**`chatroom/`**](chatroom) - A real-time chatroom using WebSocket.
- [**`sync-http-clients/`**](sync-http-clients) — demonstrates outbound HTTP with synchronous Python clients (`requests`, `urllib3`, and `httpx.Client`).
- [**`dynamic-py-py/`**](dynamic-py-py) — shows how to load and run a Python Worker dynamically at runtime using a [Worker Loader](https://developers.cloudflare.com/workers/runtime-apis/bindings/worker-loader/) binding.
- [**`django/`**](django) — runs a naive Django WSGI application directly on Python Workers.
- [**`django-todo-d1/`**](django-todo-d1) — implements the Todo-Backend API with Django and D1.
- [**`image-redraw/`**](image-redraw) — an example that combines [FastAPI](https://fastapi.tiangolo.com/), [R2](https://developers.cloudflare.com/r2/), [Queues](https://developers.cloudflare.com/queues/), [Workflows](https://developers.cloudflare.com/workflows/) and [Workers AI](https://developers.cloudflare.com/workers-ai/) to redraw uploaded images.


## Open Beta and Limits

- You must add the `python_workers` compatibility flag to your Worker while Python Workers are in open beta.

We’d love your feedback. Join the `#python-workers channel` in the [Cloudflare Developers Discord](https://discord.cloudflare.com/) and let us know what you’d like to see next.

## License

The [Apache 2.0 license](LICENSE.md).
