CREATE TABLE reaction_stats (
    room_id TEXT NOT NULL,
    reaction TEXT NOT NULL CHECK (reaction IN ('heart', 'laugh', 'fire')),
    count BIGINT NOT NULL DEFAULT 0 CHECK (count >= 0),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (room_id, reaction)
);
