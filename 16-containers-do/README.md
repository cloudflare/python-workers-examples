# Containers-backed Durable Objects Example

A Python Worker that proxies requests to a [container-backed Durable Object](https://developers.cloudflare.com/containers/). The container runs a Pillow-based image generation server — every request returns a random abstract art PNG.

## Architecture

```
Request → Python Worker → Durable Object → Container (Pillow image server on port 8080)
```

The Worker forwards all requests to a single container-backed DO instance. The DO starts the container on first access and proxies HTTP to it.

## Usage

```sh
# Generate a random 512x512 image
curl -o art.png https://<your-worker>.workers.dev/

# Custom size
curl -o art.png "https://<your-worker>.workers.dev/?w=800&h=600"

# Reproducible output with a seed
curl -o art.png "https://<your-worker>.workers.dev/?seed=42"
```
