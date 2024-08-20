### Query a D1 Database with Cloudflare Workers in Python

1. Create a new Cloudflare Worker from the command line with `npm create cloudflare@latest`. When prompted, give your project a name, select `Hello World example`, `Hello World Worker template`, and `Python (beta)` when asked about language.

OR

1. `git clone https://github.com/cloudflare/python-workers-examples
cd python-workers-examples/01-hello
npx wrangler@latest dev`

3. Replace the boilerplate code in a `src/entry.py` with this `src/entry.py` code.

4. Download this `quotes.csv` file from https://www.kaggle.com/datasets/manann/quotes-500k?select=quotes.csv

5. Save it to a directory called `data` in the root directory here

6. Run `python3 data/csvtosql.py` to convert the CSV file to SQL

7. Create a new D1 database by running on the command line `npx wrangler d1 create {D1-NAME}`. Copy and paste the output into your wrangler.toml to bind your D1 database to your Python Worker.

8. Import the new SQL file to D1 with `npx wrangler d1 execute {YOUR-DATABASE-NAME} --remote --file=data.sql`

9. Deploy your Worker with `npx wrangler@latest deploy`

10. Get a random quote from the database by visiting your deployed worker in the browser!<img width="1421" alt="deployed app" src="https://github.com/user-attachments/assets/131a2836-2305-4b73-a54a-50dac039108f">