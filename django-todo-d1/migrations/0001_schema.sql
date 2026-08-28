CREATE TABLE todos (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT '',
    completed INTEGER NOT NULL DEFAULT 0,
    "order" INTEGER
);
