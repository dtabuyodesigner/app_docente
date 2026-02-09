CREATE TABLE IF NOT EXISTS informe_grupo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trimestre INTEGER NOT NULL UNIQUE,
    observaciones TEXT,
    propuestas_mejora TEXT,
    conclusion TEXT,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP
);
