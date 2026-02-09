# Python Workers Examples

This is a collection of examples for [writing Cloudflare Workers in Python](https://developers.cloudflare.com/workers/languages/python). Use these examples to learn how Python Workers work.

## Get started

1. `git clone https://github.com/cloudflare/python-workers-examples`
2. `cd 01-hello`
3. `uvx --from workers-py pywrangler dev`
4. Press the `b` key to open a browser tab, and make a request to your Worker

You can run `uvx --from workers-py pywrangler dev` in any example project directory to run a local development server using [Pywrangler](https://github.com/cloudflare/workers-py), the CLI for Cloudflare Python Workers. This local development server is powered by [workerd](https://github.com/cloudflare/workerd), the open-source Workers runtime.

Need to deploy your Worker to Cloudflare? Python Workers are in open beta and have a few [limitations](#open-beta-and-limits).

## Examples

- [**`01-hello/`**](01-hello) — the most basic Python Worker
- [**`02-binding/`**](02-binding) — shows how [bindings](https://developers.cloudflare.com/workers/configuration/bindings/) work in Python Workers. Put a key into Workers KV, and then read it.
- [**`03-fastapi/`**](03-fastapi) — demonstrates how to use the [FastAPI](https://fastapi.tiangolo.com/) package with Python Workers
- [**`04-query-d1/`**](04-query-d1) - shows how to query D1 with Python Workers
- [**`05-langchain/`**](05-langchain) — demonstrates how to use the [LangChain](https://pypi.org/project/langchain/) package with Python Workers. Currently broken.
- [**`06-assets/`**](06-assets) — An example with an assets binding.
- [**`07-durable-objects/`**](07-durable-objects) — An example with storing state in a [Durable Object](https://developers.cloudflare.com/durable-objects/).
- [**`08-cron/`**](08-cron) — shows a simple [cron job](https://developers.cloudflare.com/workers/configuration/cron-triggers/).
- [**`09-workers-ai/`**](09-workers-ai) makes a call [Workers AI](https://developers.cloudflare.com/workers-ai/) to run inference on Cloudflare's Global Network.
- [**`10-workflows/`**](10-workflows) — shows a durable [Workflows](https://developers.cloudflare.com/workflows/) example.
- [**`11-opengraph/`**](11-opengraph) — shows how to use [HTMLRewriter](https://developers.cloudflare.com/workers/runtime-apis/html-rewriter/) to generate OpenGraph images with Python Workers.
- [**`12-image-gen/`**](12-image-gen) — shows how to use [Pillow](https://pillow.readthedocs.io/en/stable/) to generate images with Python Workers.
- [**`13-js-api-pygments/`**](13-js-api-pygments) — shows how to use [Pygments](https://pygments.org/) to highlight code with Python Workers.
- [**`14-websocket-stream-consumer/`**](14-websocket-stream-consumer) — shows how to use [WebSocket](https://developers.cloudflare.com/workers/runtime-apis/websockets/) to consume a stream of data with Python Workers.
- [**`15-chatroom/`**](15-chatroom) - A real-time chatroom using WebSocket.



## Open Beta and Limits

- You must add the `python_workers` compatibility flag to your Worker while Python Workers are in open beta.

We’d love your feedback. Join the `#python-workers channel` in the [Cloudflare Developers Discord](https://discord.cloudflare.com/) and let us know what you’d like to see next.

## License

The [Apache 2.0 license](LICENSE.md).
