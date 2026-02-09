-- Table for manual schedule entries
CREATE TABLE IF NOT EXISTS horario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dia INTEGER NOT NULL, -- 0=Mon, 4=Fri
    hora_inicio TEXT NOT NULL, -- HH:MM
    hora_fin TEXT NOT NULL, -- HH:MM
    asignatura TEXT NOT NULL,
    detalles TEXT
);

-- Table for key-value configuration (e.g., image paths)
CREATE TABLE IF NOT EXISTS config (
    clave TEXT PRIMARY KEY,
    valor TEXT
);

-- Insert default empty values for image paths if they don't exist
INSERT OR IGNORE INTO config (clave, valor) VALUES ('horario_img_path', NULL);
INSERT OR IGNORE INTO config (clave, valor) VALUES ('menu_comedor_img_path', NULL);
