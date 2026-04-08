import sqlite3
import os
import sys
from flask import g

def get_app_data_dir():
    """Devuelve el directorio base para guardar los datos de la aplicación de forma persistente."""
    if sys.platform == "win32":
        # Windows: C:\Users\<Usuario>\AppData\Roaming\CuadernoDelTutor
        base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
        app_dir = os.path.join(base_dir, "CuadernoDelTutor")
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/CuadernoDelTutor
        base_dir = os.path.expanduser("~/Library/Application Support")
        app_dir = os.path.join(base_dir, "CuadernoDelTutor")
    else:
        # Linux / Otros: ~/.cuadernodeltutor
        app_dir = os.path.expanduser("~/.cuadernodeltutor")
        
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

# For retrocompatibility during migration, we look first in the project folder
# Then we fallback to the persistent app data dir
_LEGACY_DB = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app_evaluar.db")
_NEW_DB = os.path.join(get_app_data_dir(), "app_evaluar.db")

# Move legacy DB to new location if it exists
if os.path.exists(_LEGACY_DB) and not os.path.exists(_NEW_DB):
    try:
        import shutil
        shutil.copy2(_LEGACY_DB, _NEW_DB)
        print(f"Migrando base de datos de {_LEGACY_DB} a {_NEW_DB}")
        # We rename the old one just in case as backup
        os.rename(_LEGACY_DB, _LEGACY_DB + ".bak")
    except Exception as e:
        print(f"Error migrando BD: {e}")

def get_db_path():
    """Determina la ruta de la base de datos priorizando la ubicación persistente con datos."""
    env_path = os.environ.get("DATABASE_PATH")
    if env_path:
        return env_path

    # Verificar si existen y tienen contenido
    new_exists = os.path.exists(_NEW_DB) and os.path.getsize(_NEW_DB) > 0
    legacy_exists = os.path.exists(_LEGACY_DB) and os.path.getsize(_LEGACY_DB) > 0

    if new_exists:
        return _NEW_DB
    if legacy_exists:
        return _LEGACY_DB
    
    # Fallback por defecto (se usará la nueva ubicación)
    return _NEW_DB

def run_migrations():
    """Aplica migraciones automáticas para BDs antiguas."""
    path = get_db_path()
    if not os.path.exists(path):
        return
    
    conn = sqlite3.connect(path)
    migrated = []

    migrations = [
        # --- gestor_tareas ---
        ("ALTER TABLE gestor_tareas ADD COLUMN completado INTEGER DEFAULT 0", "gestor_tareas.completado"),
        ("ALTER TABLE gestor_tareas ADD COLUMN profesor_id INTEGER", "gestor_tareas.profesor_id"),
        # --- programacion_diaria ---
        ("ALTER TABLE programacion_diaria ADD COLUMN completado INTEGER DEFAULT 0", "programacion_diaria.completado"),
        ("ALTER TABLE programacion_diaria ADD COLUMN criterio_id INTEGER REFERENCES criterios(id)", "programacion_diaria.criterio_id"),
        # --- etapas ---
        ("ALTER TABLE etapas ADD COLUMN activa INTEGER DEFAULT 1", "etapas.activa"),
        # --- informe_grupo ---
        ("ALTER TABLE informe_grupo ADD COLUMN grupo_id INTEGER", "informe_grupo.grupo_id"),
        ("ALTER TABLE informe_grupo ADD COLUMN equipo_docente TEXT", "informe_grupo.equipo_docente"),
        ("ALTER TABLE informe_grupo ADD COLUMN dificultades TEXT", "informe_grupo.dificultades"),
        # --- alumnos ---
        ("ALTER TABLE alumnos ADD COLUMN deleted_at DATETIME", "alumnos.deleted_at"),
        ("ALTER TABLE alumnos ADD COLUMN tiene_ayuda_material INTEGER DEFAULT 0", "alumnos.tiene_ayuda_material"),
        ("ALTER TABLE alumnos ADD COLUMN fecha_nacimiento DATE", "alumnos.fecha_nacimiento"),
        ("ALTER TABLE alumnos ADD COLUMN direccion TEXT", "alumnos.direccion"),
        ("ALTER TABLE alumnos ADD COLUMN madre_nombre TEXT", "alumnos.madre_nombre"),
        ("ALTER TABLE alumnos ADD COLUMN madre_telefono TEXT", "alumnos.madre_telefono"),
        ("ALTER TABLE alumnos ADD COLUMN madre_email TEXT", "alumnos.madre_email"),
        ("ALTER TABLE alumnos ADD COLUMN padre_nombre TEXT", "alumnos.padre_nombre"),
        ("ALTER TABLE alumnos ADD COLUMN padre_telefono TEXT", "alumnos.padre_telefono"),
        ("ALTER TABLE alumnos ADD COLUMN padre_email TEXT", "alumnos.padre_email"),
        ("ALTER TABLE alumnos ADD COLUMN personas_autorizadas TEXT", "alumnos.personas_autorizadas"),
        ("ALTER TABLE alumnos ADD COLUMN observaciones_generales TEXT", "alumnos.observaciones_generales"),
        # --- grupos ---
        ("ALTER TABLE grupos ADD COLUMN equipo_docente TEXT", "grupos.equipo_docente"),
        ("ALTER TABLE grupos ADD COLUMN coordinador_ciclo TEXT", "grupos.coordinador_ciclo"),
        # --- areas ---
        ("ALTER TABLE areas ADD COLUMN es_personalizada BOOLEAN DEFAULT 1", "areas.es_personalizada"),
        # --- criterios ---
        ("ALTER TABLE criterios ADD COLUMN comentario_base TEXT", "criterios.comentario_base"),
        # --- sda ---
        ("ALTER TABLE sda ADD COLUMN codigo_sda TEXT", "sda.codigo_sda"),
        ("ALTER TABLE sda ADD COLUMN duracion_semanas INTEGER", "sda.duracion_semanas"),
        # --- horario ---
        ("ALTER TABLE horario ADD COLUMN tipo TEXT DEFAULT 'clase'", "horario.tipo"),
        # --- reuniones ---
        ("ALTER TABLE reuniones ADD COLUMN ciclo_id INTEGER REFERENCES config_ciclo(id)", "reuniones.ciclo_id"),
        ("ALTER TABLE reuniones ADD COLUMN dificultades TEXT", "reuniones.dificultades"),
        ("ALTER TABLE reuniones ADD COLUMN propuestas_mejora TEXT", "reuniones.propuestas_mejora"),
        # --- evaluaciones ---
        ("ALTER TABLE evaluaciones ADD COLUMN nota REAL", "evaluaciones.nota"),
        # --- usuarios ---
        ("ALTER TABLE usuarios ADD COLUMN pregunta_seguridad TEXT", "usuarios.pregunta_seguridad"),
        ("ALTER TABLE usuarios ADD COLUMN respuesta_seguridad_hash TEXT", "usuarios.respuesta_seguridad_hash"),
        # --- Tablas nuevas ---
        ("""CREATE TABLE IF NOT EXISTS diplomas_entregados (
            alumno_id INTEGER PRIMARY KEY,
            cantidad INTEGER DEFAULT 0,
            fecha_ultimo DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
        )""", "tabla diplomas_entregados"),
        ("""CREATE TABLE IF NOT EXISTS informe_observaciones (
            alumno_id INTEGER NOT NULL,
            trimestre INTEGER NOT NULL,
            texto TEXT,
            PRIMARY KEY (alumno_id, trimestre),
            FOREIGN KEY (alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
        )""", "tabla informe_observaciones"),
        ("""CREATE TABLE IF NOT EXISTS sesiones_actividad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            actividad_id INTEGER NOT NULL,
            numero_sesion INTEGER NOT NULL,
            descripcion TEXT,
            fecha DATE,
            FOREIGN KEY(actividad_id) REFERENCES actividades_sda(id) ON DELETE CASCADE
        )""", "tabla sesiones_actividad"),
        ("""CREATE TABLE IF NOT EXISTS criterios_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            criterio_id INTEGER,
            keyword TEXT,
            FOREIGN KEY(criterio_id) REFERENCES criterios(id)
        )""", "tabla criterios_keywords"),
        ("""CREATE TABLE IF NOT EXISTS ficha_alumno (
            alumno_id INTEGER PRIMARY KEY,
            fecha_nacimiento TEXT,
            direccion TEXT,
            madre_nombre TEXT,
            madre_telefono TEXT,
            padre_nombre TEXT,
            padre_telefono TEXT,
            observaciones_generales TEXT,
            personas_autorizadas TEXT,
            madre_email TEXT,
            padre_email TEXT,
            FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
        )""", "tabla ficha_alumno"),
        ("""CREATE TABLE IF NOT EXISTS encargados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL UNIQUE,
            alumno_id INTEGER NOT NULL,
            estado TEXT DEFAULT 'realizado',
            FOREIGN KEY(alumno_id) REFERENCES alumnos(id) ON DELETE CASCADE
        )""", "tabla encargados"),
    ]

    for sql, name in migrations:
        try:
            conn.execute(sql)
            conn.commit()
            migrated.append(name)
        except Exception:
            pass  # Ya existe o no aplica

    # Datos iniciales obligatorios
    try:
        conn.execute("INSERT OR IGNORE INTO etapas (id, nombre, activa) VALUES (1, 'Infantil', 1)")
        conn.execute("INSERT OR IGNORE INTO etapas (id, nombre, activa) VALUES (2, 'Primaria', 1)")
        conn.execute("INSERT OR IGNORE INTO etapas (id, nombre, activa) VALUES (3, 'Secundaria', 1)")
        conn.commit()
    except Exception:
        pass

    # Áreas por defecto si no hay ninguna
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM areas")
        count = cur.fetchone()[0]
        if count == 0:
            areas_infantil = [
                ("Conocimiento de sí mismo y autonomía personal", 1, "INFANTIL_NI_EP_C"),
                ("Conocimiento del entorno", 1, "INFANTIL_NI_EP_C"),
                ("Educación emocional", 1, "INFANTIL_NI_EP_C"),
                ("Lenguajes: Comunicación y representación", 1, "INFANTIL_NI_EP_C"),
                ("Música", 1, "INFANTIL_NI_EP_C"),
                ("Segunda Lengua Extranjera", 1, "INFANTIL_NI_EP_C"),
            ]
            areas_primaria = [
                # --- ÁREAS COMUNES LOMLOE (todas las CCAA) ---
                ("Conocimiento del Medio Natural, Social y Cultural", 2, "NUMERICA_1_4"),
                ("Lengua Castellana y Literatura", 2, "NUMERICA_1_4"),
                ("Matemáticas", 2, "NUMERICA_1_4"),
                ("Educación Artística", 2, "NUMERICA_1_4"),
                ("Educación Física", 2, "NUMERICA_1_4"),
                ("Lengua Extranjera", 2, "NUMERICA_1_4"),
                ("Segunda Lengua Extranjera", 2, "NUMERICA_1_4"),
                ("Educación en Valores Cívicos y Éticos", 2, "NUMERICA_1_4"),
                ("Religión", 2, "NUMERICA_1_4"),
                ("Atención Educativa", 2, "NUMERICA_1_4"),
                # --- DESDOBLAMIENTOS OPTATIVOS ---
                ("Ciencias de la Naturaleza", 2, "NUMERICA_1_4"),
                ("Ciencias Sociales", 2, "NUMERICA_1_4"),
                ("Educación Plástica y Visual", 2, "NUMERICA_1_4"),
                ("Música y Danza", 2, "NUMERICA_1_4"),
                # --- CANARIAS ---
                ("Educación Emocional y para la Creatividad", 2, "NUMERICA_1_4"),
                # --- MADRID ---
                ("Tecnología y Robótica", 2, "NUMERICA_1_4"),
                ("Digitalización", 2, "NUMERICA_1_4"),
                # --- CCAA CON LENGUA COOFICIAL ---
                ("Lengua Catalana y Literatura", 2, "NUMERICA_1_4"),       # Cataluña / Baleares
                ("Lengua Gallega y Literatura", 2, "NUMERICA_1_4"),         # Galicia
                ("Lengua Vasca y Literatura (Euskera)", 2, "NUMERICA_1_4"), # País Vasco / Navarra
                ("Lengua Valenciana y Literatura", 2, "NUMERICA_1_4"),      # Comunidad Valenciana
                ("Llingua Asturiana y Literatura", 2, "NUMERICA_1_4"),      # Asturias
            ]
            for nombre, etapa_id, escala in areas_infantil + areas_primaria:
                conn.execute(
                    "INSERT INTO areas (nombre, etapa_id, tipo_escala, es_oficial, activa) VALUES (?, ?, ?, 1, 1)",
                    (nombre, etapa_id, escala)
                )
            conn.commit()
            migrated.append("áreas por defecto")
    except Exception as e:
        pass

    if migrated:
        print(f"[Migraciones aplicadas]: {', '.join(migrated)}")

    conn.close()


def init_db_if_not_exists():
    """Initializes the SQLite database from schema.sql if it doesn't exist yet."""
    path = get_db_path()
    if not os.path.exists(path):
        print(f"[{path}] No existe. Inicializando base de datos en blanco...")
        conn = sqlite3.connect(path)
        
        # Determine the absolute path to schema.sql in the project root
        schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')
        
        if os.path.exists(schema_path):
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_script = f.read()
                # Run the script
                conn.executescript(schema_script)
            print(f"[{path}] Base de datos inicializada correctamente con schema.sql.")
        else:
            print(f"[PELIGRO] Archivo schema.sql no encontrado en {schema_path}.")
            
        conn.commit()
        conn.close()

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row  # Access columns by name
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def nivel_a_nota(nivel, escala=None):
    """Convierte un nivel en una nota numérica.
    
    Escala NUMERICA_1_4: 1→2.5, 2→5.0, 3→7.5, 4→10.0
    Escala INFANTIL_NI_EP_C: 1(NI)→1, 2(EP)→2, 3(C)→3
    """
    if (escala and escala.startswith("INFANTIL_")):
        # Nivel 1=NI, 2=EP, 3=C — se guarda internamente como 1,2,3
        mapping = {1: 1, 2: 2, 3: 3}
    else:
        # Escala numérica 1-4 estándar
        mapping = {1: 2.5, 2: 5.0, 3: 7.5, 4: 10.0}
    return mapping.get(nivel, 0.0)

def infantil_nivel_a_texto(nivel):
    """Devuelve el texto legible para una evaluación Infantil (Combinado)."""
    mapping = {
        1: "NI - Poco adecuado", 
        2: "EP - Adecuado", 
        3: "CO - Muy adecuado"
    }
    return mapping.get(nivel, "—")
