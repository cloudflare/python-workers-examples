# Flask Todo Backend

A Python Flask implementation of the [Todo-Backend](https://todobackend.com) spec, running on Cloudflare Workers with D1 for storage.

## Development

Initialize the local D1 database and start the dev server:

```sh
uv run pywrangler d1 execute todos --local --file db_init.sql
uv run pywrangler dev
```

## Testing with the Todo-Backend spec runner

Start the dev server, then open the spec runner pointing at your local instance:

```
https://todobackend.com/specs/index.html?http://localhost:8787/todos
```

You can also use the Todo-Backend client app:

```
https://todobackend.com/client/index.html?http://localhost:8787/todos
```

## API

| Method   | Path             | Description        |
| -------- | ---------------- | ------------------ |
| `GET`    | `/todos`         | List all todos     |
| `POST`   | `/todos`         | Create a todo      |
| `DELETE` | `/todos`         | Delete all todos   |
| `GET`    | `/todos/{id}`    | Get a single todo  |
| `PATCH`  | `/todos/{id}`    | Update a todo      |
| `DELETE` | `/todos/{id}`    | Delete a todo      |
