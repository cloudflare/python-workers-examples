# Python Workers Examples

This is a collection of examples for [writing Cloudflare Workers in Python](https://developers.cloudflare.com/workers/languages/python). Use these examples to learn how Python Workers work.

## Get started

1. `git clone https://github.com/cloudflare/python-workers-examples`
2. `cd hello`
3. `npx wrangler@latest dev`
4. Press the `b` key to open a browser tab, and make a request to your Worker

You can run `npx wrangler@latest dev` in any example project directory to run a local development server using [Wrangler](https://developers.cloudflare.com/workers/wrangler/), the CLI for Cloudflare Workers. This local development server is powered by [workerd](https://github.com/cloudflare/workerd), the open-source Workers runtime.

Need to deploy your Worker to Cloudflare? Python Workers are in open beta and have a few [limitations](#open-beta-and-limits).

## Examples

- [**`01-hello/`**](01-hello) — the most basic Python Worker
- [**`02-binding/`**](02-binding) — shows how [bindings](https://developers.cloudflare.com/workers/configuration/bindings/) work in Python Workers. Put a key into Workers KV, and then read it.
- [**`03-fastapi/`**](03-fastapi) — demonstrates how to use the [FastAPI](https://fastapi.tiangolo.com/) package with Python Workers
- [**`04-langchain/`**](04-langchain) — demonstrates how to use the [LangChain](https://pypi.org/project/langchain/) package with Python Workers

## Open Beta and Limits

- Python Workers are in open beta. Currently, you can only deploy Python Workers that use the standard library. [Packages](https://developers.cloudflare.com/workers/languages/python/packages/#supported-packages) **cannot be deployed** and will only work in local development for the time being.
- You must add the `python_workers` compatibility flag to your Worker, while Python Workers are in open beta.

We’d love your feedback. Join the `#python-workers channel` in the [Cloudflare Developers Discord](https://discord.cloudflare.com/) and let us know what you’d like to see next.

## License

The [Apache 2.0 license](LICENSE).
