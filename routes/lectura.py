from flask import Blueprint, request, jsonify, send_from_directory
from utils.db import get_db
from datetime import datetime, date
import os
import csv
import io
import requests as http_requests

lectura_bp = Blueprint('lectura', __name__)

# ====================================================
# GESTIÓN DE LIBROS (CRUD)
# ====================================================

@lectura_bp.route("/libros", methods=["GET"])
def get_libros():
    conn = get_db()
    cur = conn.cursor()

    genero = request.args.get('genero')
    nivel = request.args.get('nivel')
    activos_solo = request.args.get('activos', 'true').lower() == 'true'

    query = "SELECT * FROM libros WHERE 1=1"
    params = []

    if activos_solo:
        query += " AND activo = 1"
    if genero:
        query += " AND genero = ?"
        params.append(genero)
    if nivel:
        query += " AND nivel_lectura = ?"
        params.append(nivel)

    query += " ORDER BY titulo ASC"
    cur.execute(query, params)
    libros = [dict(row) for row in cur.fetchall()]
    return jsonify(libros)


@lectura_bp.route("/libros/<int:lid>", methods=["GET"])
def get_libro(lid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM libros WHERE id = ?", (lid,))
    libro = cur.fetchone()
    if not libro:
        return jsonify({"ok": False, "error": "Libro no encontrado"}), 404
    return jsonify(dict(libro))


@lectura_bp.route("/libros", methods=["POST"])
def post_libro():
    data = request.get_json(silent=True) or {}
    titulo = data.get("titulo", "").strip()
    autor = data.get("autor", "").strip()
    cantidad_total = int(data.get("cantidad_total", 1))

    if not titulo or not autor:
        return jsonify({"ok": False, "error": "Título y autor son requeridos"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO libros
            (titulo, autor, isbn, editorial, año_publicacion, nivel_lectura,
             genero, cantidad_total, cantidad_disponible, descripcion, portada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            titulo, autor,
            data.get("isbn", ""), data.get("editorial", ""),
            data.get("año_publicacion"),
            data.get("nivel_lectura", ""), data.get("genero", ""),
            cantidad_total, cantidad_total,
            data.get("descripcion", ""), data.get("portada", "")
        ))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid,
                        "mensaje": f"Libro '{titulo}' creado exitosamente"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@lectura_bp.route("/libros/<int:lid>", methods=["PUT"])
def put_libro(lid):
    data = request.get_json(silent=True) or {}
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM libros WHERE id = ?", (lid,))
    libro_actual = cur.fetchone()
    if not libro_actual:
        return jsonify({"ok": False, "error": "Libro no encontrado"}), 404

    campos = ["titulo", "autor", "isbn", "editorial", "año_publicacion",
              "nivel_lectura", "genero", "cantidad_total", "descripcion", "portada", "activo"]
    updates, params = [], []
    for campo in campos:
        if campo in data:
            updates.append(f"{campo} = ?")
            params.append(data[campo])

    # Si cambia cantidad_total, recalcular cantidad_disponible
    if "cantidad_total" in data:
        nuevo_total = int(data["cantidad_total"])
        # Préstamos activos actuales del libro
        cur.execute(
            "SELECT COUNT(*) as n FROM prestamos_libros WHERE libro_id = ? AND estado = 'activo'",
            (lid,)
        )
        prestamos_activos = cur.fetchone()["n"]
        nueva_disponible = max(0, nuevo_total - prestamos_activos)
        updates.append("cantidad_disponible = ?")
        params.append(nueva_disponible)

    if not updates:
        return jsonify({"ok": False, "error": "No hay campos para actualizar"}), 400

    params.append(lid)
    try:
        cur.execute(f"UPDATE libros SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
        return jsonify({"ok": True, "mensaje": "Libro actualizado exitosamente"})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@lectura_bp.route("/libros/<int:lid>", methods=["DELETE"])
def delete_libro(lid):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("UPDATE libros SET activo = 0 WHERE id = ?", (lid,))
        conn.commit()
        return jsonify({"ok": True, "mensaje": "Libro eliminado exitosamente"})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


# ====================================================
# GESTIÓN DE PRÉSTAMOS
# ====================================================

@lectura_bp.route("/prestamos", methods=["POST"])
def post_prestamo():
    data = request.get_json(silent=True) or {}
    alumno_id = data.get("alumno_id")
    libro_id = data.get("libro_id")
    fecha_prestamo = data.get("fecha_prestamo", str(date.today()))

    if not alumno_id or not libro_id:
        return jsonify({"ok": False, "error": "alumno_id y libro_id son requeridos"}), 400

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT nombre FROM alumnos WHERE id = ?", (alumno_id,))
    alumno = cur.fetchone()
    if not alumno:
        return jsonify({"ok": False, "error": "Alumno no encontrado"}), 404

    cur.execute("SELECT titulo, cantidad_disponible FROM libros WHERE id = ?", (libro_id,))
    libro = cur.fetchone()
    if not libro:
        return jsonify({"ok": False, "error": "Libro no encontrado"}), 404
    if libro["cantidad_disponible"] <= 0:
        return jsonify({"ok": False, "error": "No hay copias disponibles del libro"}), 400

    try:
        cur.execute("""
            INSERT INTO prestamos_libros (alumno_id, libro_id, fecha_prestamo, estado)
            VALUES (?, ?, ?, 'activo')
        """, (alumno_id, libro_id, fecha_prestamo))
        cur.execute("UPDATE libros SET cantidad_disponible = cantidad_disponible - 1 WHERE id = ?", (libro_id,))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid,
                        "mensaje": f"Préstamo registrado. Alumno: {alumno['nombre']}, Libro: {libro['titulo']}"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@lectura_bp.route("/prestamos/<int:pid>/devolver", methods=["POST"])
def devolver_prestamo(pid):
    data = request.get_json(silent=True) or {}
    fecha_devolucion = data.get("fecha_devolucion", str(date.today()))
    observaciones = data.get("observaciones", "")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM prestamos_libros WHERE id = ?", (pid,))
    prestamo = cur.fetchone()

    if not prestamo:
        return jsonify({"ok": False, "error": "Préstamo no encontrado"}), 404
    if prestamo["estado"] == "devuelto":
        return jsonify({"ok": False, "error": "Este préstamo ya fue devuelto"}), 400

    try:
        fecha_prest = datetime.strptime(prestamo["fecha_prestamo"], "%Y-%m-%d")
        fecha_dev = datetime.strptime(fecha_devolucion, "%Y-%m-%d")
        dias_lectura = (fecha_dev - fecha_prest).days

        cur.execute("""
            UPDATE prestamos_libros SET fecha_devolucion = ?, estado = 'devuelto', observaciones = ?
            WHERE id = ?
        """, (fecha_devolucion, observaciones, pid))
        cur.execute("UPDATE libros SET cantidad_disponible = cantidad_disponible + 1 WHERE id = ?",
                    (prestamo["libro_id"],))
        conn.commit()
        return jsonify({"ok": True, "dias_lectura": dias_lectura,
                        "mensaje": f"Devolución registrada. El alumno tuvo el libro {dias_lectura} días."})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@lectura_bp.route("/prestamos/<int:pid>/reactivar", methods=["POST"])
def reactivar_prestamo(pid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM prestamos_libros WHERE id = ?", (pid,))
    prestamo = cur.fetchone()

    if not prestamo:
        return jsonify({"ok": False, "error": "Préstamo no encontrado"}), 404
    if prestamo["estado"] == "activo":
        return jsonify({"ok": False, "error": "El préstamo ya está activo"}), 400

    # Ensure book is still available to be "re-borrowed"
    cur.execute("SELECT cantidad_disponible, titulo FROM libros WHERE id = ?", (prestamo["libro_id"],))
    libro = cur.fetchone()
    if not libro:
        return jsonify({"ok": False, "error": "Libro no encontrado"}), 404
    if libro["cantidad_disponible"] <= 0:
        return jsonify({"ok": False, "error": f"No hay copias disponibles de '{libro['titulo']}' para reactivar el préstamo"}), 400

    try:
        cur.execute("""
            UPDATE prestamos_libros SET fecha_devolucion = NULL, estado = 'activo'
            WHERE id = ?
        """, (pid,))
        cur.execute("UPDATE libros SET cantidad_disponible = cantidad_disponible - 1 WHERE id = ?", (prestamo["libro_id"],))
        conn.commit()
        return jsonify({"ok": True, "mensaje": "Préstamo reactivado correctamente"})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@lectura_bp.route("/prestamos/<int:pid>", methods=["GET"])
def get_prestamo(pid):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT pl.*, a.nombre as alumno_nombre, l.titulo as libro_titulo
        FROM prestamos_libros pl
        JOIN alumnos a ON pl.alumno_id = a.id
        JOIN libros l ON pl.libro_id = l.id
        WHERE pl.id = ?
    """, (pid,))
    row = cur.fetchone()
    if not row:
        return jsonify({"ok": False, "error": "Préstamo no encontrado"}), 404
    return jsonify({"ok": True, "prestamo": dict(row)})


@lectura_bp.route("/prestamos/<int:pid>", methods=["PUT"])
def put_prestamo(pid):
    """Edit a loan: alumno, libro, fecha_prestamo, observaciones."""
    data = request.get_json(silent=True) or {}
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM prestamos_libros WHERE id = ?", (pid,))
    prestamo = cur.fetchone()
    if not prestamo:
        return jsonify({"ok": False, "error": "Préstamo no encontrado"}), 404

    nuevo_libro_id = data.get("libro_id")
    nuevo_alumno_id = data.get("alumno_id")
    nueva_fecha = data.get("fecha_prestamo", prestamo["fecha_prestamo"])
    nuevas_obs = data.get("observaciones", prestamo["observaciones"] or "")

    try:
        # If changing book and loan is still active, adjust disponible
        if nuevo_libro_id and nuevo_libro_id != prestamo["libro_id"] and prestamo["estado"] == "activo":
            # Restore old book
            cur.execute("UPDATE libros SET cantidad_disponible = cantidad_disponible + 1 WHERE id = ?",
                        (prestamo["libro_id"],))
            # Check new book availability
            cur.execute("SELECT cantidad_disponible, titulo FROM libros WHERE id = ?", (nuevo_libro_id,))
            nuevo_libro = cur.fetchone()
            if not nuevo_libro:
                return jsonify({"ok": False, "error": "Libro nuevo no encontrado"}), 404
            if nuevo_libro["cantidad_disponible"] <= 0:
                return jsonify({"ok": False, "error": f"No hay copias disponibles de '{nuevo_libro['titulo']}'"}), 400
            cur.execute("UPDATE libros SET cantidad_disponible = cantidad_disponible - 1 WHERE id = ?",
                        (nuevo_libro_id,))

        campos = {"libro_id": nuevo_libro_id or prestamo["libro_id"],
                  "alumno_id": nuevo_alumno_id or prestamo["alumno_id"],
                  "fecha_prestamo": nueva_fecha,
                  "observaciones": nuevas_obs}

        cur.execute("""
            UPDATE prestamos_libros
            SET libro_id=?, alumno_id=?, fecha_prestamo=?, observaciones=?
            WHERE id=?
        """, (campos["libro_id"], campos["alumno_id"], campos["fecha_prestamo"],
              campos["observaciones"], pid))
        conn.commit()
        return jsonify({"ok": True, "mensaje": "Préstamo actualizado correctamente"})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500


@lectura_bp.route("/prestamos/<int:pid>", methods=["DELETE"])
def delete_prestamo(pid):
    """Permanently delete a loan record and restore book availability if active."""
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM prestamos_libros WHERE id = ?", (pid,))
    prestamo = cur.fetchone()
    if not prestamo:
        return jsonify({"ok": False, "error": "Préstamo no encontrado"}), 404

    try:
        # Restore disponible if loan was active
        if prestamo["estado"] == "activo":
            cur.execute("UPDATE libros SET cantidad_disponible = cantidad_disponible + 1 WHERE id = ?",
                        (prestamo["libro_id"],))
        cur.execute("DELETE FROM prestamos_libros WHERE id = ?", (pid,))
        conn.commit()
        return jsonify({"ok": True, "mensaje": "Préstamo eliminado correctamente"})
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500



@lectura_bp.route("/alumnos/<int:alumno_id>/prestamos", methods=["GET"])
def get_prestamos_alumno(alumno_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            pl.id, l.titulo as libro_titulo, l.autor as libro_autor,
            pl.fecha_prestamo, pl.fecha_devolucion, pl.estado, pl.observaciones,
            CAST((julianday(COALESCE(pl.fecha_devolucion, date('now'))) -
                  julianday(pl.fecha_prestamo)) AS INTEGER) as dias_lectura
        FROM prestamos_libros pl
        JOIN libros l ON pl.libro_id = l.id
        WHERE pl.alumno_id = ?
        ORDER BY pl.fecha_prestamo DESC
    """, (alumno_id,))
    return jsonify([dict(row) for row in cur.fetchall()])


@lectura_bp.route("/prestamos/activos", methods=["GET"])
def get_prestamos_activos():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            pl.id, a.nombre as alumno_nombre, l.titulo as libro_titulo,
            pl.fecha_prestamo,
            CAST((julianday(date('now')) - julianday(pl.fecha_prestamo)) AS INTEGER) as dias_transcurridos,
            pl.estado
        FROM prestamos_libros pl
        JOIN alumnos a ON pl.alumno_id = a.id
        JOIN libros l ON pl.libro_id = l.id
        WHERE pl.estado = 'activo'
        ORDER BY pl.fecha_prestamo ASC
    """)
    return jsonify([dict(row) for row in cur.fetchall()])


@lectura_bp.route("/prestamos/historial", methods=["GET"])
def get_historial_prestamos():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT
            pl.id, a.nombre as alumno_nombre, l.titulo as libro_titulo,
            pl.fecha_prestamo, pl.fecha_devolucion, pl.estado, pl.observaciones,
            CAST((julianday(COALESCE(pl.fecha_devolucion, date('now'))) -
                  julianday(pl.fecha_prestamo)) AS INTEGER) as dias_lectura
        FROM prestamos_libros pl
        JOIN alumnos a ON pl.alumno_id = a.id
        JOIN libros l ON pl.libro_id = l.id
        ORDER BY pl.fecha_prestamo DESC
        LIMIT 200
    """)
    return jsonify([dict(row) for row in cur.fetchall()])


@lectura_bp.route("/estadisticas/lectura", methods=["GET"])
def estadisticas_lectura():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) as total FROM libros WHERE activo = 1")
    total_libros = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM prestamos_libros")
    total_prestamos = cur.fetchone()["total"]

    cur.execute("SELECT COUNT(*) as total FROM prestamos_libros WHERE estado = 'activo'")
    prestamos_activos = cur.fetchone()["total"]

    cur.execute("""
        SELECT a.nombre, COUNT(*) as total_lecturas
        FROM prestamos_libros pl JOIN alumnos a ON pl.alumno_id = a.id
        GROUP BY pl.alumno_id ORDER BY total_lecturas DESC LIMIT 1
    """)
    top_lector = cur.fetchone()

    cur.execute("""
        SELECT l.titulo, COUNT(*) as total_prestamos
        FROM prestamos_libros pl JOIN libros l ON pl.libro_id = l.id
        GROUP BY pl.libro_id ORDER BY total_prestamos DESC LIMIT 1
    """)
    libro_popular = cur.fetchone()

    return jsonify({
        "total_libros": total_libros,
        "total_prestamos": total_prestamos,
        "prestamos_activos": prestamos_activos,
        "top_lector": dict(top_lector) if top_lector else None,
        "libro_popular": dict(libro_popular) if libro_popular else None
    })


@lectura_bp.route("/ranking/lectura", methods=["GET"])
def ranking_lectura():
    conn = get_db()
    cur = conn.cursor()
    # Count both active and returned loans as "read" books
    cur.execute("""
        SELECT a.nombre, COUNT(*) as total_lecturas
        FROM prestamos_libros pl
        JOIN alumnos a ON pl.alumno_id = a.id
        GROUP BY pl.alumno_id
        ORDER BY total_lecturas DESC
    """)
    ranking = [dict(row) for row in cur.fetchall()]
    return jsonify(ranking)


# ====================================================
# ALERTAS DE RETRASO
# ====================================================

@lectura_bp.route("/alertas/retrasos", methods=["GET"])
def alertas_retrasos():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT pl.id, a.nombre, l.titulo, pl.fecha_prestamo,
            CAST((julianday(date('now')) - julianday(pl.fecha_prestamo)) AS INTEGER) as dias
        FROM prestamos_libros pl
        JOIN alumnos a ON pl.alumno_id = a.id
        JOIN libros l ON pl.libro_id = l.id
        WHERE pl.estado = 'activo'
        AND (julianday(date('now')) - julianday(pl.fecha_prestamo)) > 14
        ORDER BY dias DESC
    """)
    return jsonify([dict(row) for row in cur.fetchall()])


# ====================================================
# IMPORTACIÓN CSV / EXCEL
# ====================================================

ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@lectura_bp.route("/libros/importar/csv", methods=["POST"])
def importar_libros_csv():
    if 'file' not in request.files:
        return jsonify({"ok": False, "error": "No se proporcionó archivo"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"ok": False, "error": "Archivo vacío"}), 400
    if not allowed_file(file.filename):
        return jsonify({"ok": False, "error": "Formato no permitido. Use CSV, XLS o XLSX"}), 400

    try:
        conn = get_db()
        cur = conn.cursor()
        rows = []

        if file.filename.lower().endswith('.csv'):
            content = file.stream.read()
            # Try UTF-8, fallback to latin-1
            try:
                text = content.decode('utf-8-sig')
            except Exception:
                text = content.decode('latin-1')
            reader = csv.DictReader(io.StringIO(text))
            rows = list(reader)
        else:
            import openpyxl
            workbook = openpyxl.load_workbook(file)
            worksheet = workbook.active
            headers = [cell.value for cell in worksheet[1]]
            for row in worksheet.iter_rows(min_row=2, values_only=True):
                rows.append(dict(zip(headers, row)))

        if not rows:
            return jsonify({"ok": False, "error": "El archivo está vacío"}), 400

        libros_importados = 0
        errores = []

        for idx, row in enumerate(rows, start=2):
            try:
                titulo = str(row.get('titulo', '')).strip() if row.get('titulo') else None
                if not titulo:
                    errores.append(f"Fila {idx}: Falta el título")
                    continue

                autor = str(row.get('autor', '')).strip() if row.get('autor') else ''
                isbn = str(row.get('isbn', '')).strip() if row.get('isbn') else ''
                editorial = str(row.get('editorial', '')).strip() if row.get('editorial') else ''
                nivel_lectura = str(row.get('nivel_lectura', 'Primaria')).strip() if row.get('nivel_lectura') else 'Primaria'
                genero = str(row.get('genero', 'Ficción')).strip() if row.get('genero') else 'Ficción'
                descripcion = str(row.get('descripcion', '')).strip() if row.get('descripcion') else ''

                año_publicacion = None
                if row.get('año_publicacion'):
                    try:
                        año_publicacion = int(str(row.get('año_publicacion')).split('.')[0])
                    except Exception:
                        año_publicacion = None

                cantidad_total = 1
                if row.get('cantidad_total'):
                    try:
                        cantidad_total = int(str(row.get('cantidad_total')).split('.')[0])
                    except Exception:
                        cantidad_total = 1

                cur.execute("""
                    INSERT INTO libros
                    (titulo, autor, isbn, editorial, año_publicacion, nivel_lectura,
                     genero, cantidad_total, cantidad_disponible, descripcion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (titulo, autor, isbn, editorial, año_publicacion, nivel_lectura,
                      genero, cantidad_total, cantidad_total, descripcion))
                libros_importados += 1
            except Exception as e:
                errores.append(f"Fila {idx}: {str(e)}")

        conn.commit()
        return jsonify({
            "ok": True,
            "libros_importados": libros_importados,
            "total_filas": len(rows),
            "errores": errores if errores else None,
            "mensaje": f"Se importaron {libros_importados} libros exitosamente"
        }), 201

    except Exception as e:
        return jsonify({"ok": False, "error": f"Error al procesar archivo: {str(e)}"}), 500


@lectura_bp.route("/libros/descargar-plantilla", methods=["GET"])
def descargar_plantilla():
    return send_from_directory('templates', 'plantilla_libros.csv', as_attachment=True)


# ====================================================
# GOOGLE BOOKS API
# ====================================================

@lectura_bp.route("/libros/buscar-google", methods=["GET"])
def buscar_google_books():
    titulo = request.args.get('titulo', '').strip()
    if not titulo:
        return jsonify({"ok": False, "error": "Título requerido"}), 400

    api_key = os.getenv('GOOGLE_BOOKS_API_KEY', '')
    url = "https://www.googleapis.com/books/v1/volumes"
    params = {'q': titulo, 'maxResults': 5}
    if api_key:
        params['key'] = api_key

    try:
        response = http_requests.get(url, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        if 'items' not in data:
            return jsonify({"ok": True, "resultados": [], "mensaje": "No se encontraron libros"})

        resultados = []
        for item in data['items']:
            vol = item.get('volumeInfo', {})
            libro = {
                'titulo': vol.get('title', ''),
                'autor': ', '.join(vol.get('authors', [])),
                'isbn': None,
                'editorial': vol.get('publisher', ''),
                'año_publicacion': vol.get('publishedDate', '')[:4] if vol.get('publishedDate') else None,
                'descripcion': vol.get('description', '')[:300] if vol.get('description') else '',
                'portada': vol.get('imageLinks', {}).get('thumbnail', '').replace('http://', 'https://'),
                'google_books_id': item.get('id')
            }
            for identifier in vol.get('industryIdentifiers', []):
                if identifier['type'] == 'ISBN_13':
                    libro['isbn'] = identifier['identifier']
                    break
                elif identifier['type'] == 'ISBN_10' and not libro['isbn']:
                    libro['isbn'] = identifier['identifier']
            resultados.append(libro)

        return jsonify({"ok": True, "resultados": resultados, "total": len(resultados)})
    except http_requests.exceptions.RequestException as e:
        return jsonify({"ok": False, "error": f"Error al conectar con Google Books: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@lectura_bp.route("/libros/importar-google", methods=["POST"])
def importar_libro_google():
    data = request.get_json(silent=True) or {}
    # Accept direct book data from search results
    titulo = data.get('titulo', '').strip()
    if not titulo:
        return jsonify({"ok": False, "error": "Título requerido"}), 400

    conn = get_db()
    cur = conn.cursor()
    cantidad_total = int(data.get('cantidad_total', 1))

    try:
        cur.execute("""
            INSERT INTO libros
            (titulo, autor, isbn, editorial, año_publicacion, descripcion, portada,
             cantidad_total, cantidad_disponible, nivel_lectura, genero)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            titulo,
            data.get('autor', ''),
            data.get('isbn', ''),
            data.get('editorial', ''),
            data.get('año_publicacion'),
            data.get('descripcion', ''),
            data.get('portada', ''),
            cantidad_total,
            cantidad_total,
            data.get('nivel_lectura', 'Primaria'),
            data.get('genero', 'Ficción')
        ))
        conn.commit()
        return jsonify({"ok": True, "id": cur.lastrowid,
                        "mensaje": f"Libro '{titulo}' importado exitosamente"}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({"ok": False, "error": str(e)}), 500
