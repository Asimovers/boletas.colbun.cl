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
                    fecha_lectura TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tipo_documento TEXT,
                    contenido_archivo BLOB NOT NULL
                )
            ''')
            conn.commit()
        finally:
            conn.close()
    
    def guardar_lectura(self, nombre_archivo, texto_extraido, analisis, tipo_documento=None, contenido_archivo=None):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lecturas (nombre_archivo, texto_extraido, analisis, tipo_documento, contenido_archivo)
                VALUES (?, ?, ?, ?, ?)
            ''', (nombre_archivo, texto_extraido, analisis, tipo_documento, contenido_archivo))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def obtener_lecturas(self, limit=100):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, nombre_archivo, texto_extraido, analisis, fecha_lectura, tipo_documento, contenido_archivo
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
                SELECT id, nombre_archivo, texto_extraido, analisis, fecha_lectura, tipo_documento, contenido_archivo
                FROM lecturas
                WHERE id = ?
            ''', (lectura_id,))
            return cursor.fetchone()
        finally:
            conn.close()
    
    def eliminar_lectura(self, lectura_id):
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM lecturas WHERE id = ?', (lectura_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
