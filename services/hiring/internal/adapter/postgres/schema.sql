-- Hiring Service schema (ADR-003: PostgreSQL is the system of record). Applied on every start,
-- so every statement must be idempotent.

CREATE TABLE IF NOT EXISTS job_openings (
    id                   text        PRIMARY KEY,
    -- Insertion order, so List returns openings in the order they were created.
    seq                  bigint      GENERATED ALWAYS AS IDENTITY UNIQUE,
    title                text        NOT NULL CHECK (btrim(title) <> ''),
    description          text        NOT NULL,
    expected_time_to_fill interval   NOT NULL CHECK (expected_time_to_fill > interval '0'),
    status               text        NOT NULL CHECK (status IN ('open', 'paused', 'closed')),
    opened_at            timestamptz NOT NULL,
    -- Set exactly when the opening is closed (FR-1.8).
    outcome              text        CHECK (outcome IN ('filled', 'cancelled')),
    CHECK ((status = 'closed') = (outcome IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS job_opening_criteria (
    job_opening_id text    NOT NULL REFERENCES job_openings (id) ON DELETE CASCADE,
    position       integer NOT NULL,
    name           text    NOT NULL CHECK (btrim(name) <> ''),
    classification text    NOT NULL CHECK (classification IN ('must-have', 'nice-to-have')),
    weight         integer NOT NULL CHECK (weight > 0),
    PRIMARY KEY (job_opening_id, position)
);
