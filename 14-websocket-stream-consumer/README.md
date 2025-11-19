# WebSocket Stream Consumer - Bluesky Firehose

This example demonstrates a long-running Durable Object that connects to the Bluesky firehose (via Jetstream) and filters for post events, with rate limiting to print at most 1 per second.

## How to Run

First ensure that `uv` is installed:
https://docs.astral.sh/uv/getting-started/installation/#standalone-installer

Now, if you run `uv run pywrangler dev` within this directory, it should use the config
in `wrangler.jsonc` to run the example.

You can also run `uv run pywrangler deploy` to deploy the example.

## Testing the Firehose Consumer

1. Start the worker: `uv run pywrangler dev`
2. Make any request to initialize the DO: `curl "http://localhost:8787/status"`
3. Watch the logs to see filtered Bluesky post events in real-time (rate limited to 1/sec)!

The Durable Object automatically connects to Jetstream when first accessed. It will maintain a persistent WebSocket connection and print out post events to the console, including the author DID, post text (truncated to 100 chars), and timestamp. Posts are rate limited to display at most 1 per second to avoid overwhelming the logs.

**Available endpoints:**
- `/status` - Check connection status