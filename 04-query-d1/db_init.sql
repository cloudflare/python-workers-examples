CREATE TABLE IF NOT EXISTS qtable (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quote TEXT,
    author Text
);

INSERT INTO qtable (quote, author)
SELECT * FROM (
    VALUES
        ("This is a very cool quote", "Hood Chatham"),
        ("Some words of wisdom", "Dominik Picheta"),
        ("The sense 'fragment of verbal expression', attested from the 17th century", "Wikipedia")
) WHERE NOT EXISTS (SELECT 1 FROM qtable);
