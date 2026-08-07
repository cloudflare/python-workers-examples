# Flask Notes

Example todo notes app with D1 as the database.

## How it works

Uses the `workers.wsgi` adaptor to run flask and `src/d1.py` provides a
synchronous wrapper for d1.

## Layout

```
migrations/0001_create_notes.sql   D1 schema
public/                            Static frontend (served from the edge)
src/entry.py                       Worker entrypoint (async → WSGI)
src/app.py                         Flask app: routes, validation, errors
src/d1.py                          Synchronous D1 wrapper
wrangler.jsonc                     Worker config, assets + D1 binding
```

## Run locally

```bash
uv sync
uv run pywrangler d1 migrations apply flask-notes --local
uv run pywrangler dev
```


## Deploy

1. Create the database and copy the id it prints:

   ```bash
   uv run pywrangler d1 create flask-notes
   ```

2. Put that id in `wrangler.jsonc` under `d1_databases[0].database_id`,
   replacing `REPLACE_WITH_YOUR_DATABASE_ID`.

3. Apply the schema to the real database and deploy:

   ```bash
   uv run pywrangler d1 migrations apply flask-notes --remote
   uv run pywrangler deploy
   ```
