import sqlite3
from datetime import datetime
import json

class LecturasDB:
    def __init__(self, db_path="lecturas.db"):
        self.db_path = db_path
        self.crear_tablas()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def crear_tablas(self):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS lecturas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nombre_archivo TEXT NOT NULL,
                    texto_extraido TEXT NOT NULL,
                    analisis TEXT NOT NULL,
                    modelo TEXT NOT NULL,
                    fecha_lectura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tipo_documento TEXT,
                    contenido_archivo BLOB NOT NULL
                )
            ''')
            conn.commit()
            # Migración: agregar columna modelo si no existe en esquemas antiguos
            try:
                cursor.execute("ALTER TABLE lecturas ADD COLUMN modelo TEXT NOT NULL DEFAULT 'GPT-4o (OpenAI)'")
                conn.commit()
            except sqlite3.OperationalError:
                pass
        finally:
            conn.close()
    
    def guardar_lectura(self, nombre_archivo, texto_extraido, analisis, modelo, tipo_documento=None, contenido_archivo=None):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lecturas (nombre_archivo, texto_extraido, analisis, modelo, tipo_documento, contenido_archivo)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (nombre_archivo, texto_extraido, analisis, modelo, tipo_documento, contenido_archivo))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def obtener_lecturas(self, limit=100):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nombre_archivo, texto_extraido, analisis, fecha_lectura, modelo, tipo_documento, contenido_archivo
                FROM lecturas
                ORDER BY fecha_lectura DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
        finally:
            conn.close()
    
    def obtener_lectura(self, lectura_id):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nombre_archivo, texto_extraido, analisis, fecha_lectura, modelo, tipo_documento, contenido_archivo
                FROM lecturas
                WHERE id = ?
            ''', (lectura_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def actualizar_analisis(self, lectura_id, nuevo_analisis):
        """Actualiza el análisis de una lectura existente."""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('UPDATE lecturas SET analisis = ? WHERE id = ?', (nuevo_analisis, lectura_id))
            conn.commit()
        finally:
            conn.close()

    def eliminar_lectura(self, lectura_id):
        """Elimina una lectura de la base de datos por su ID."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('DELETE FROM lecturas WHERE id = ?', (lectura_id,))
            conn.commit()
            # logger.info(f"Lectura ID {lectura_id} eliminada.") # Descomentar si se usa logger
            return True
        except Exception as e:
            # logger.error(f"Error al eliminar lectura {lectura_id}: {e}") # Descomentar si se usa logger
            conn.rollback() # Deshacer cambios si hay error
            return False
        finally:
            conn.close()
