# LangChain Example

This example shows how to use LangChain with Cloudflare Workers AI binding.

## How to Run

First ensure that `uv` is installed:
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

Now, if you run `uv run pywrangler dev` within this directory, it should use the config
in `wrangler.jsonc` to run the example.

You can also run `uv run pywrangler deploy` to deploy the example.

Because this example uses a remote Workers AI binding, local development requires
`npx wrangler login`.

## Notes

- If you want the lower-level direct binding example, see [`09-workers-ai/`](../09-workers-ai).
