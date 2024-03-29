# Langchain Example

Warning: Python support in Workers is experimental and things will break. This
demo is meant for reference only right now; you should be prepared to update
your code between now and official release time as APIs may change.

## How to Run

First ensure that your Wrangler version is up to date (3.30.0 and above).

```bash
$ wrangler -v
 ⛅️ wrangler 3.30.0
```

Now, if you run `wrangler dev` within this directory, it should use the config
in `wrangler.toml` to run the demo.

This demo uses a [Workers secret](https://developers.cloudflare.com/workers/configuration/secrets/)
to configure the API key. Before deployment you must set this key using the
Wrangler CLI:

```bash
$ wrangler secret put API_KEY
```

You can now run `wrangler deploy` to deploy the demo.