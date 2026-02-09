CREATE TABLE IF NOT EXISTS rubricas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    criterio_id INTEGER NOT NULL,
    nivel INTEGER NOT NULL CHECK(nivel BETWEEN 1 AND 4),
    descriptor TEXT NOT NULL,
    UNIQUE(criterio_id, nivel),
    FOREIGN KEY(criterio_id) REFERENCES criterios(id)
);
