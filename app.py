import os
import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
app.secret_key = 'clave-secreta-para-desarrollo'
DB_FILE = 'ciudad_maderas.db'


# Inicialización segura de la base de datos nativa (SQLite)
def init_db():
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prospectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                email TEXT NOT NULL,
                telefono TEXT NOT NULL,
                tipo_solicitud TEXT DEFAULT 'Suscripción',
                fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")


# Llamamos a la inicialización al arrancar
init_db()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/prospectos', methods=['POST'])
def registrar_prospecto():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Datos vacíos"}), 400

        nombre = data.get('nombre')
        email = data.get('email')
        telefono = data.get('telefono')
        tipo = data.get('tipo', 'Suscripción')

        if not nombre or not email or not telefono:
            return jsonify({"status": "error", "message": "Todos los campos son requeridos"}), 400

        # Guardado en base de datos nativa
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO prospectos (nombre, email, telefono, tipo_solicitud)
            VALUES (?, ?, ?, ?)
        ''', (nombre, email, telefono, tipo))
        conn.commit()
        conn.close()

        return jsonify({"status": "success", "message": "¡Registro completado con éxito!"}), 201

    except Exception as e:
        print(f"Error en el servidor: {e}")
        return jsonify({"status": "error", "message": "Error interno del servidor."}), 500


if __name__ == '__main__':
    # Usamos el puerto 8080 para evitar conflictos con otros servicios del sistema
    print("Iniciando servidor en http://127.0.0.1:8080")
    app.run(host='127.0.0.1', port=8080, debug=True)