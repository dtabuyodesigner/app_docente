-- Crear tabla para observaciones y propuestas de mejora del grupo por trimestre
CREATE TABLE IF NOT EXISTS informe_grupo (
    trimestre INTEGER PRIMARY KEY,
    observaciones TEXT,
    propuestas_mejora TEXT
);
