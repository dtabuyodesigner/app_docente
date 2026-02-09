-- Add tipo column if not exists (SQLite doesn't support IF NOT EXISTS for columns in older versions, but we can just add it)
-- We will use a python script to run this safely or just try/except in app startup, but here is the raw SQL for reference.
ALTER TABLE horario ADD COLUMN tipo TEXT DEFAULT 'clase';
