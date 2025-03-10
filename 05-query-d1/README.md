# Query a D1 Database with Cloudflare Workers Example

Warning: Python support in Workers is experimental and things will break. This demo is meant for reference only right now; you should be prepared to update your code between now and official release time as APIs may change.

Currently, Python Workers using packages cannot be deployed and will only work in local development for the time being.

### How to Run

Download this quotes file from [Hugging Face in SQL form](https://huggingface.co/datasets/lizziepika/quotes_sql/blob/main/data.sql)

Create a new D1 database by running on the command line `npx wrangler d1 create {D1-NAME}`. Copy and paste the output into your `wrangler.toml` to bind your D1 database to your Python Worker.

Ingest the SQL file you've downloaded by running:

```
npx wrangler d1 execute {D1-NAME} --local --file=./data.sql
```

Ensure that your Wrangler version is up to date (3.30.0 and above).

```
$ wrangler -v
 ⛅️ wrangler 3.30.0
```

Now, if you run `wrangler dev` within this directory, it should use the config in `wrangler.toml` to run the demo.

You can also run `wrangler deploy` to deploy the demo (though you'll need to repeat the ingestion step above for the remote DB).

Finally, get a random quote from the database by visiting your deployed worker in the browser!<img width="1421" alt="deployed app" src="https://github.com/user-attachments/assets/131a2836-2305-4b73-a54a-50dac039108f">
