CREATE TABLE IF NOT EXISTS menus_comedor (
    mes TEXT PRIMARY KEY, -- Format YYYY-MM
    imagen TEXT NOT NULL
);

-- Optional: Move existing current menu from config to current month if exists (Python side might be easier, or just ignore previous ephemeral test data)
