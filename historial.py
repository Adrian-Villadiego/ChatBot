
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

DB_PATH = Path(__file__).resolve().parent / "chatmind_historial.db"


def conectar():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_base_datos():
    with conectar() as conexion:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS historial_emocional (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                tipo_mensaje TEXT NOT NULL,
                emocion TEXT NOT NULL,
                fecha TEXT NOT NULL
            )
        """)

        conexion.execute("""
            CREATE INDEX IF NOT EXISTS idx_historial_usuario_fecha
            ON historial_emocional (usuario_id, fecha)
        """)


def guardar_analisis(usuario_id, tipo_mensaje, emocion):
    fecha = datetime.now(timezone.utc).isoformat()

    with conectar() as conexion:
        conexion.execute("""
            INSERT INTO historial_emocional
            (usuario_id, tipo_mensaje, emocion, fecha)
            VALUES (?, ?, ?, ?)
        """, (usuario_id, tipo_mensaje, emocion, fecha))


def consultar_historial(usuario_id, limite=10):
    with conectar() as conexion:
        registros = conexion.execute("""
            SELECT tipo_mensaje, emocion, fecha
            FROM historial_emocional
            WHERE usuario_id = ?
            ORDER BY fecha DESC, id DESC
            LIMIT ?
        """, (usuario_id, limite)).fetchall()

    return [dict(registro) for registro in registros]



def obtener_estadisticas(usuario_id):
    from datetime import timedelta

    fecha_inicio = (
        datetime.now(timezone.utc) - timedelta(days=7)
    ).isoformat()

    with conectar() as conexion:
        registros = conexion.execute("""
            SELECT emocion, COUNT(*) AS cantidad
            FROM historial_emocional
            WHERE usuario_id = ?
              AND fecha >= ?
            GROUP BY emocion
            ORDER BY cantidad DESC, emocion ASC
        """, (usuario_id, fecha_inicio)).fetchall()

    return [dict(registro) for registro in registros]



def eliminar_historial(usuario_id):
    with conectar() as conexion:
        cursor = conexion.execute("""
            DELETE FROM historial_emocional
            WHERE usuario_id = ?
        """, (usuario_id,))

        return cursor.rowcount


if __name__ == "__main__":
    crear_base_datos()
    print("Base de datos creada correctamente.")
