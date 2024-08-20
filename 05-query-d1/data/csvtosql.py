# script to convert CSV to SQL to upload to Cloudflare D1
# after running this python script, run on the command line -> npx wrangler d1 execute {your db name} --remote --file=data/data.sql
import csv
from pathlib import Path

p = Path(__file__).with_name('quotes.csv')

# Path to the uploaded CSV file
csv_file_path = 'quotes.csv'

# Initialize list to store SQL insert statements
sql_statements = []

# Open and read the CSV file
with p.open('r') as file:
    reader = csv.reader(file)
    header = next(reader)  # Skip header row if present
    
    # Loop through each row in the CSV
    for i, row in enumerate(reader, start=1):
        # Extract quote and author, assuming they are in the first two columns
        quote, author = row[0].replace("'", "''"), row[1].replace("'", "''")
        
        # Create the SQL insert statement
        sql_statements.append(f"INSERT INTO qtable (id, quote, author) VALUES ('{i}', '{quote}', '{author}');")

# Combine the CREATE TABLE statement with the insert statements
sql_script = """
CREATE TABLE IF NOT EXISTS qtable (
  id VARCHAR(50),
  quote VARCHAR(50),
  author VARCHAR(50)
);
""" + "\n".join(sql_statements)

# Path to the uploaded CSV file
p2 = Path(__file__).with_name('data.sql')

# Write the SQL script to a file
with p2.open('w') as file:
    file.write(sql_script)