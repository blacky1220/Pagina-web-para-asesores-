import io
import csv
import os
from datetime import datetime
from flask import Flask, render_template, request, send_file, jsonify, redirect
import pandas as pd
import urllib.parse  # Librería nativa para formatear texto para enlaces web

app = Flask(__name__)

# Nombre del archivo donde se guardarán los prospectos que se registren en la web
ARCHIVO_PROSPECTOS = 'prospectos.csv'

# =======================================================
# CONFIGURACIÓN DE TU NÚMERO DE WHATSAPP
# =======================================================
# Coloca tu número a 10 dígitos con el código de país (52 para México) sin espacios ni signos +
TELEFONO_ASESOR = "525628013593"


def leer_csv_seguro(file_upload):
    bytes_data = file_upload.read()
    try:
        text = bytes_data.decode('utf-8-sig')
    except UnicodeDecodeError:
        try:
            text = bytes_data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = bytes_data.decode('latin-1')
            except UnicodeDecodeError:
                text = bytes_data.decode('cp1252', errors='ignore')

    sep = ','
    if text.startswith('sep='):
        line_end = text.find('\n')
        sep_line = text[:line_end].strip()
        sep = sep_line.split('=')[1]
        text = text[line_end + 1:]
    else:
        first_line = text.split('\n')[0]
        if first_line.count(';') > first_line.count(','):
            sep = ';'
        else:
            sep = ','

    df = pd.read_csv(io.StringIO(text), sep=sep, encoding='utf-8', engine='python')
    return df


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file_base = request.files.get('file_base')
        file_nuevo = request.files.get('file_nuevo')
        criterio = request.form.get('criterio')

        if file_base and file_nuevo:
            try:
                df_base = leer_csv_seguro(file_base)
                df_nuevo = leer_csv_seguro(file_nuevo)

                df_base.columns = df_base.columns.str.strip()
                df_nuevo.columns = df_nuevo.columns.str.strip()

                combined_df = pd.concat([df_base, df_nuevo], ignore_index=True)

                if criterio == 'correo' and 'correo' in combined_df.columns:
                    combined_df.drop_duplicates(subset=['correo'], keep='first', inplace=True)
                elif criterio == 'telefono' and 'telefono' in combined_df.columns:
                    combined_df.drop_duplicates(subset=['telefono'], keep='first', inplace=True)
                else:
                    combined_df.drop_duplicates(keep='first', inplace=True)

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    combined_df.to_excel(writer, index=False, sheet_name='Clientes')
                output.seek(0)

                return send_file(
                    output,
                    as_attachment=True,
                    download_name="clientes_actualizados.xlsx",
                    mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                return f"Error al procesar: {e}", 400

    return render_template('index.html')


# =======================================================
# RUTA MODAL: GUARDA EN CSV Y REDIRIGE AL CLIENTE A TU WHATSAPP
# =======================================================
@app.route('/enviar-cotizacion', methods=['POST'])
def enviar_cotizacion():
    try:
        modelo = request.form.get('modelo_interes')
        nombre = request.form.get('nombre')
        telefono_cliente = request.form.get('telefono')
        correo = request.form.get('correo')
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 1. Guardar localmente en tu archivo CSV (Mantiene tu base de datos al día)
        archivo_existe = os.path.exists(ARCHIVO_PROSPECTOS)
        with open(ARCHIVO_PROSPECTOS, mode='a', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            if not archivo_existe:
                writer.writerow(['Fecha', 'Nombre', 'Telefono', 'Correo', 'Modelo Interes'])
            writer.writerow([fecha, nombre, telefono_cliente, correo, modelo])

        # 2. Construir el mensaje personalizado que el cliente te enviará
        texto_mensaje = (
            f"Hola, acabo de registrar mis datos en tu sitio web.\n"
            f"Me interesa recibir la cotización y corrida financiera del *{modelo}*.\n\n"
            f"Mis datos de registro:\n"
            f"👤 Nombre: {nombre}\n"
            f"✉️ Correo: {correo}"
        )

        # Codificamos el texto para que sea válido dentro de una URL (convierte espacios y saltos de línea)
        texto_codificado = urllib.parse.quote(texto_mensaje)

        # Enlace final de WhatsApp directo a tu chat
        enlace_whatsapp = f"https://wa.me/{TELEFONO_ASESOR}?text={texto_codificado}"

        # 3. Vista intermedia de éxito que lanza la redirección automática a los 2 segundos
        return f"""
        <div style="text-align: center; font-family: 'Segoe UI', sans-serif; padding-top: 100px; color: #111827;">
            <h2 style="font-size: 2rem; margin-bottom: 10px;">¡Datos recibidos correctamente!</h2>
            <p style="color: #6b7280; margin-bottom: 25px;">Para agilizar tu cotización, te estamos redirigiendo a nuestro canal de WhatsApp...</p>
            <div style="margin-top: 20px;">
                <a href="{enlace_whatsapp}" style="background-color: #25D366; color: white; padding: 14px 30px; text-decoration: none; border-radius: 25px; font-weight: 600; font-size: 1.1rem; box-shadow: 0 4px 10px rgba(37,211,102,0.3);">
                    Continuar a WhatsApp de inmediato
                </a>
            </div>
            <script>
                setTimeout(function(){{
                    window.location.href = "{enlace_whatsapp}";
                }}, 2500);
            </script>
        </div>
        """

    except Exception as e:
        return f"Error interno al procesar la solicitud: {e}", 500


@app.route('/api/prospectos', methods=['POST'])
def guardar_prospecto():
    try:
        datos = request.get_json()
        nombre = datos.get('nombre')
        correo = datos.get('email')
        telefono = datos.get('telefono')
        tipo_solicitud = datos.get('tipo', 'Registro Web')
        fecha = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        archivo_existe = os.path.exists(ARCHIVO_PROSPECTOS)
        with open(ARCHIVO_PROSPECTOS, mode='a', newline='', encoding='utf-8-sig') as file:
            writer = csv.writer(file)
            if not archivo_existe:
                writer.writerow(['Fecha', 'Nombre', 'Telefono', 'Correo', 'Modelo Interes'])
            writer.writerow([fecha, nombre, telefono, correo, tipo_solicitud])

        return jsonify({"message": "¡Gracias! Tus datos se han registrado correctamente."}), 200

    except Exception as e:
        return jsonify({"message": f"Error interno en el servidor: {str(e)}"}), 500


@app.route('/modelos')
def modelos():
    return render_template('modelos.html')


if __name__ == '__main__':
    app.run(debug=True)