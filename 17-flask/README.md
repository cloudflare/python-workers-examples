# Flask Hello World

A minimal [Flask](https://flask.palletsprojects.com/) example app running on a
Python Worker via the WSGI adapter (`wsgi.fetch`).

## How to Run

First ensure that `uv` is installed:
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

Now, if you run `uv run pywrangler dev` within this directory, it should use the config
in `wrangler.jsonc` to run the example.

You can also run `uv run pywrangler deploy` to deploy the example.
