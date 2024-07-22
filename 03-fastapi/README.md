# FastAPI Example

Warning: Python support in Workers is experimental and things will break. This
demo is meant for reference only right now; you should be prepared to update
your code between now and official release time as APIs may change.

Currently, Python Workers using [packages](https://developers.cloudflare.com/workers/languages/python/packages/#supported-packages)
**cannot be deployed** and will only work in local development for the time being.

## How to Run

First ensure that your Wrangler version is up to date (3.30.0 and above).

```bash
$ wrangler -v
 ⛅️ wrangler 3.30.0
```

Now, if you run `wrangler dev` within this directory, it should use the config
in `wrangler.toml` to run the demo.

You can also run `wrangler deploy` to deploy the demo.