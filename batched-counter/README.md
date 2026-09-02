# Batched Counter with Durable Objects and Hyperdrive

This example shows how to use Durable Objects and Hyperdrive to build a unique counter
for multiple users.

1. It assigns one Python Durable Object to each room.
2. Reactions that increase the count are kept in an in-memory dictionary for fast aggregation first,
   and persisted to Durable Object storage until an alarm flushes them to PostgreSQL through Hyperdrive every five seconds.

## Prerequisites

- [Docker Compose](https://docs.docker.com/compose/) - for local PostgreSQL
- [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Run locally

Start PostgreSQL, install the Python dependencies, then start the Worker:

```sh
docker compose up --build -d --wait
uv run pywrangler dev
```

Open `http://localhost:8787` to join a room, send reactions, and watch each
five-second batch move from the Durable Object to PostgreSQL.

```sh
curl -X POST http://localhost:8787/rooms/concert/reactions/heart
curl -X POST http://localhost:8787/rooms/concert/reactions/laugh
curl http://localhost:8787/rooms/concert/stats
```

The stats response separates accepted `totals`, PostgreSQL `persisted` totals, and the
currently buffered `pending` counts.

## Deploy

Apply `schema.sql` to the production PostgreSQL database first. Then create a Hyperdrive
configuration for that database, replace the placeholder `id` in `wrangler.jsonc` with
its Hyperdrive ID, and run:

```sh
uv run pywrangler deploy
```
