import streamlit as st
from PIL import Image
from pdf2image import convert_from_bytes
import io
import sys
import logging
import os
import base64
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
from db import LecturasDB
import subprocess
from pdfminer.high_level import extract_text
import requests

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de OpenAI
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def verificar_api():
    """Verifica si la API de OpenAI está configurada correctamente."""
    try:
        if not os.getenv('OPENAI_API_KEY'):
            return False, "No se ha configurado la clave de API de OpenAI. Por favor, configura OPENAI_API_KEY en el archivo .env"
        
        # Hacer una llamada de prueba a la API
        client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        
        return True, "API de OpenAI configurada correctamente"
    except Exception as e:
        return False, f"Error al conectar con OpenAI: {str(e)}"

def procesar_imagen(imagen_bytes):
    """Procesa una imagen usando GPT-4 Vision."""
    try:
        # Convertir la imagen a base64
        imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
        
        # Crear el mensaje para GPT-4 Vision
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "Responde únicamente con análisis estructurado en viñetas, sin saludos niS mensajes de cortesía."},
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analiza esta factura o boleta y extrae toda la información de la factura de manera estructurada y clara, usando viñetas para cada dato."},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{imagen_base64}"}
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error al procesar la imagen: {str(e)}")
        return f"Error al procesar la imagen: {str(e)}"

def procesar_pdf(pdf_bytes):
    """Convierte PDF a imágenes y procesa con GPT-4 Vision."""
    try:
        try:
            imagenes = convert_from_bytes(pdf_bytes)
        except Exception as e:
            if "poppler" in str(e).lower():
                error_msg = "Error: Poppler no está instalado. Por favor, ejecuta 'brew install poppler' en la terminal."
                logger.error(error_msg)
                return error_msg
            raise e
            
        resultados = []
        for imagen in imagenes:
            # Convertir imagen PIL a bytes
            img_byte_arr = io.BytesIO()
            imagen.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()
            
            # Procesar cada imagen con GPT-4 Vision
            resultado = procesar_imagen(img_byte_arr)
            resultados.append(resultado)
            
        return '\n\n---\n\n'.join(resultados)
    except Exception as e:
        logger.error(f"Error al procesar el PDF: {str(e)}")
        return f"Error al procesar el PDF: {str(e)}"

def procesar_imagen_local_modelo(imagen_bytes):
    """Envía imagen (base64) al modelo local via API REST de Ollama."""
    try:
        imagen_base64 = base64.b64encode(imagen_bytes).decode('utf-8')
        ollama_api_url = "http://localhost:11434/api/generate" 
        
        # Prompt textual (sin la imagen)
        prompt_text = "Analiza esta factura o boleta y extrae toda la información de la factura de manera estructurada y clara, usando bullets para cada dato, indicando toda la información del documento, cantidades, codigos, etc, sin saludos ni mensajes de cortesía.\nAnaliza esta factura o boleta y extrae toda la información de manera estructurada usando viñetas."

        payload = {
            "model": "gemma3:12b", # Asegúrate que este modelo esté disponible en tu Ollama
            "prompt": prompt_text,
            "images": [imagen_base64], # La imagen como lista de strings base64
            "stream": False # Para obtener respuesta completa, no streaming
        }

        response = requests.post(ollama_api_url, json=payload)
        response.raise_for_status() # Lanza excepción para errores HTTP (4xx o 5xx)

        response_data = response.json()
        
        # Verificar si la respuesta contiene el campo 'response' esperado
        if 'response' in response_data:
             return response_data['response']
        else:
             # Podría haber un error específico en la respuesta JSON de Ollama
             error_msg = response_data.get('error', 'Respuesta inesperada de la API de Ollama')
             logger.error(f"Error en respuesta de API Ollama: {error_msg}")
             return f"Error en API Ollama: {error_msg}"

    except requests.exceptions.ConnectionError:
        logger.error("Error: No se pudo conectar a la API de Ollama. ¿Está Ollama corriendo?")
        return "Error: No se pudo conectar a Ollama. Verifica que esté en ejecución."
    except requests.exceptions.RequestException as e:
        logger.error(f"Error en la solicitud a la API de Ollama: {str(e)}")
        return f"Error en API Ollama: {str(e)}"
    except Exception as e:
        logger.error(f"Error procesando imagen con modelo local (API): {str(e)}")
        return f"Error procesando imagen local (API): {str(e)}"

def procesar_pdf_local_modelo(pdf_bytes):
    """Extrae texto del PDF y envía al modelo local Gemma3:12B."""
    try:
        texto = extract_text(io.BytesIO(pdf_bytes))
    except Exception as e:
        logger.error(f"Error al extraer texto del PDF: {str(e)}")
        return f"Error al extraer texto del PDF: {str(e)}"
    instruction = "Responde únicamente con análisis estructurado en viñetas, sin saludos ni mensajes de cortesía."
    prompt = f"{instruction}\n{texto}"
    completed = subprocess.run(
        ["ollama", "run", "gemma3:12b"],
        input=prompt,
        capture_output=True,
        text=True
    )
    if completed.returncode != 0:
        logger.error(f"Error al ejecutar modelo local: {completed.stderr}")
        return f"Error al ejecutar modelo local: {completed.stderr}"
    return completed.stdout

def analizar_texto_con_openai(texto, historial_mensajes=None, es_correccion=False):
    """Analiza el texto usando OpenAI."""
    try:
        if "Error al procesar" in texto:
            return "No se puede analizar debido a un error en el procesamiento del documento"
        
        # Sistema: respuestas solo con análisis estructurado en viñetas
        system_msg = {"role": "system", "content": "Responde únicamente con análisis estructurado en viñetas, sin saludos ni mensajes de cortesía."}
        if historial_mensajes is None:
            mensajes = [system_msg, {"role": "user", "content": texto}]
        else:
            if es_correccion:
                prompt = f"Basándote en el análisis anterior y la corrección proporcionada: '{texto}', genera un nuevo análisis completo y actualizado de la factura. Mantén el formato de viñetas, sin mensajes de cortesía."  # correcciones
            else:
                prompt = texto
            mensajes = [system_msg] + historial_mensajes + [{"role": "user", "content": prompt}]
        
        logger.info("Enviando consulta a OpenAI")
        try:
            respuesta = client.chat.completions.create(
                model="gpt-4o",
                messages=mensajes,
                temperature=0.7,
                max_tokens=1000
            )
            return respuesta.choices[0].message.content
        except Exception as e:
            logger.error(f"Error al comunicarse con OpenAI: {str(e)}")
            return f"Error al analizar con OpenAI: {str(e)}"
    except Exception as e:
        logger.error(f"Error en el análisis: {str(e)}")
        return f"Error en el análisis: {str(e)}"

def analizar_texto_local(texto, historial_mensajes=None, es_correccion=False):
    """Analiza el texto usando modelo local Gemma3:12B con Ollama."""
    try:
        if "Error al procesar" in texto:
            return "No se puede analizar debido a un error en el procesamiento del documento"
        instruction = "Responde únicamente con análisis estructurado en viñetas, sin saludos ni mensajes de cortesía.\n\n"
        if historial_mensajes is None:
            prompt = instruction + texto
        else:
            if es_correccion:
                prompt = instruction + f"Basándote en el análisis anterior y la corrección proporcionada: '{texto}', genera un nuevo análisis completo y actualizado de la factura, en viñetas."
            else:
                historial_texto = "\n".join([f"{m['role']}: {m['content']}" for m in historial_mensajes])
                prompt = instruction + historial_texto + "\nuser: " + texto
        cmd = ["ollama", "run", "gemma3:12b", prompt]
        completed = subprocess.run(cmd, capture_output=True, text=True)
        if completed.returncode != 0:
            logger.error(f"Error al correr modelo local: {completed.stderr}")
            return f"Error al ejecutar el modelo local: {completed.stderr}"
        return completed.stdout
    except Exception as e:
        logger.error(f"Error en el modelo local: {str(e)}")
        return f"Error en modelo local: {str(e)}"

def mostrar_documento(contenido_archivo, tipo_documento):
    """Muestra un documento (imagen o PDF) en la interfaz."""
    try:
        if tipo_documento == 'application/pdf':
            imagenes = convert_from_bytes(contenido_archivo)
            for i, imagen in enumerate(imagenes):
                st.image(imagen, caption=f"Página {i+1}", use_container_width=True)
        else:
            imagen = Image.open(io.BytesIO(contenido_archivo))
            st.image(imagen, caption="Documento", use_container_width=True)
    except Exception as e:
        st.error(f"Error al mostrar el documento: {str(e)}")

def mostrar_historial(db):
    """Muestra la interfaz del historial de lecturas con opción de eliminar."""
    st.title("📚 Historial de Lecturas")

    # Placeholder para mensajes de éxito/error de eliminación
    placeholder = st.empty()

    # Obtener todas las lecturas (ID, Nombre, Fecha, Tipo, Modelo)
    # Asegúrate que db.obtener_lecturas() devuelva estas columnas
    try:
        lecturas = db.obtener_lecturas()
    except Exception as e:
        st.error(f"Error al obtener lecturas de la base de datos: {e}")
        return

    if not lecturas:
        st.info("Aún no hay lecturas en el historial.")
        return

    # Mostrar lista con opción de eliminar
    st.subheader("Registros Guardados")
    # Define las columnas y sus cabeceras
    cols_header = st.columns((1, 4, 2, 2, 2, 1.5)) # Ajustar anchos: ID, Nombre, Fecha, Tipo, Modelo, Acciones
    headers = ['ID', 'Nombre Archivo', 'Fecha', 'Tipo Doc', 'Modelo', 'Acciones']
    for col, header in zip(cols_header, headers):
        col.write(f'**{header}**')

    st.markdown("---") # Separador bajo cabeceras

    # Iterar sobre las lecturas y mostrar en filas con botón
    for lectura_item in lecturas:
        try:
             # Desempacar la tupla/lista de la lectura
             # Ajusta esto según lo que realmente devuelve db.obtener_lecturas()
             lectura_id, nombre_archivo, _, _, fecha_str, modelo, tipo_doc, _ = lectura_item
 
             # Formatear fecha (opcional, mejora legibilidad)
             try:
                 # Intenta parsear si viene como string YYYY-MM-DD HH:MM:SS...
                 fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S.%f') # Ajusta el formato si es necesario
             except (ValueError, TypeError):
                 try:
                      fecha_dt = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
                 except (ValueError, TypeError):
                      fecha_dt = None # No se pudo parsear

             fecha_formateada = fecha_dt.strftime('%d/%m/%Y %H:%M') if fecha_dt else fecha_str

        except ValueError as e:
             st.error(f"Error procesando registro de historial: {lectura_item}. Detalle: {e}")
             continue # Saltar esta lectura si el formato es incorrecto

        cols_row = st.columns((1, 4, 2, 2, 2, 1.5)) # Mismos anchos que las cabeceras
        cols_row[0].write(str(lectura_id))
        cols_row[1].write(nombre_archivo)
        cols_row[2].write(fecha_formateada)
        cols_row[3].write(tipo_doc if tipo_doc else "N/A")
        cols_row[4].write(modelo)

        # Columna de acciones con el botón "Eliminar"
        button_placeholder = cols_row[5].empty()
        if button_placeholder.button("Eliminar", key=f"del_{lectura_id}", help=f"Eliminar registro ID {lectura_id}"):
            if db.eliminar_lectura(lectura_id):
                placeholder.success(f"Lectura ID {lectura_id} eliminada correctamente.")
                # Opcional: Pausa breve para que el usuario vea el mensaje
                # import time
                # time.sleep(2)
                st.rerun() # Recarga la página para actualizar la lista
            else:
                placeholder.error(f"Error al intentar eliminar la lectura ID {lectura_id}.")

        st.markdown("---") # Separador visual entre filas

    # --- SECCIÓN OPCIONAL PARA VER DETALLES (Puedes mantenerla o quitarla) ---
    st.subheader("🔍 Ver/Corregir Detalles de Lectura")
    # Obtener IDs disponibles para el selectbox
    ids_disponibles = [l[0] for l in lecturas]
    if not ids_disponibles:
        st.info("No hay lecturas disponibles para ver detalles.")
        return # Salir si no hay IDs

    lectura_id_seleccionada = st.selectbox(
        "Selecciona una lectura para ver los detalles:",
        options=ids_disponibles,
        format_func=lambda x: f"Lectura #{x} - {next((l[1] for l in lecturas if l[0] == x), 'Desconocido')}",
        key="select_detalle_historial",
        index=None, # Para que no haya selección por defecto
        placeholder="Elige un ID..."
    )

    if lectura_id_seleccionada:
        # Obtener datos completos de la lectura seleccionada (incluyendo contenido y análisis)
        # Asegúrate que este método exista y devuelva todas las columnas necesarias
        lectura_completa_data = db.obtener_lectura(lectura_id_seleccionada)

        if lectura_completa_data:
            # Mapear columnas a diccionario (asegúrate que el orden coincida con la tabla)
            columnas_db = ['id', 'nombre_archivo', 'texto_extraido', 'analisis', 'modelo', 'fecha_lectura', 'tipo_documento', 'contenido_archivo']
            lectura_dict = dict(zip(columnas_db, lectura_completa_data))

            st.markdown(f"**Archivo:** {lectura_dict['nombre_archivo']} | **Fecha:** {str(lectura_dict['fecha_lectura']).split('.')[0]} | **Modelo:** {lectura_dict['modelo']}")

            col1, col2 = st.columns([1, 1])
            with col1:
                st.subheader("🖼️ Documento")
                if lectura_dict['contenido_archivo']:
                    mostrar_documento(lectura_dict['contenido_archivo'], lectura_dict['tipo_documento'])
                else:
                    st.warning("No se encontró el contenido del documento original.")

                with st.expander("📝 Texto Extraído", expanded=False):
                     st.text_area("Texto Extraído", lectura_dict['texto_extraido'], height=200, key=f"text_{lectura_dict['id']}")

            with col2:
                st.subheader("📊 Análisis")
                st.markdown(lectura_dict['analisis']) # Usar markdown para formato

            # Opción para corregir análisis (si se mantiene)
            st.subheader("✏️ Corregir Análisis")
            correccion = st.text_area("Ingresa tu corrección aquí:", key=f"correccion_{lectura_dict['id']}")
            if st.button("Re-analizar con Corrección", key=f"reanalizar_{lectura_dict['id']}"):
                 with st.spinner("🧠 Re-analizando..."):
                     # Preparar historial como antes
                     historial_previo = [
                         {"role": "user", "content": lectura_dict['texto_extraido']},
                         {"role": "assistant", "content": lectura_dict['analisis']}
                     ]
                     nuevo_analisis = "Error: Re-análisis no implementado completamente aún." # Placeholder
                     if lectura_dict['modelo'] == 'GPT-4o (OpenAI)':
                         nuevo_analisis = analizar_texto_con_openai(correccion, historial_mensajes=historial_previo, es_correccion=True)
                     else:
                         st.warning("Re-análisis con corrección aún no implementado para modelos locales.")
                         # Aquí iría la llamada a analizar_texto_local si se adapta para historial

                     if not nuevo_analisis.startswith("Error"):
                         db.actualizar_analisis(lectura_dict['id'], nuevo_analisis)
                         st.success("Análisis actualizado con éxito!")
                         # Mostrar el nuevo análisis inmediatamente
                         st.markdown("**Nuevo Análisis:**")
                         st.markdown(nuevo_analisis)
                         # Opcional: un botón para cerrar/limpiar en lugar de rerun
                         # st.rerun() # Recarga toda la sección
                     else:
                         st.error(f"Error al re-analizar: {nuevo_analisis}")

        else:
            st.warning(f"No se pudieron cargar los detalles para la lectura ID {lectura_id_seleccionada}.")

def main():
    try:
        # Configuración de la página
        st.set_page_config(layout="wide")
        
        # Inicializar la base de datos
        db = LecturasDB()
        
        # Barra lateral para navegación
        with st.sidebar:
            st.title("📑 Navegación")
            pagina = st.radio(
                "Selecciona una página:",
                ["Nueva Lectura", "Historial de Lecturas"]
            )
            modelo = st.radio(
                "Selecciona modelo AI:",
                ["GPT-4o (OpenAI)", "Gemma3:12b (local)"]
            )
            st.session_state['modelo'] = modelo
        
        if pagina == "Historial de Lecturas":
            mostrar_historial(db)
            return
        
        # Página principal - Nueva Lectura
        st.title("📄 Descriptor de Documentos con IA")
        st.markdown("""
        Sube una imagen del documento para analizarlo automáticamente.
        El sistema extraerá toda la información relevante y la analizará con IA.
        Puedes hacer preguntas o solicitar correcciones sobre los datos extraídos.
        """)
        
        # Inicializar variables de estado en la sesión
        if 'texto_extraido' not in st.session_state:
            st.session_state.texto_extraido = ""
        if 'historial_chat' not in st.session_state:
            st.session_state.historial_chat = []
        if 'analisis_actual' not in st.session_state:
            st.session_state.analisis_actual = ""
        
        # Verificar API solo para GPT-4o
        if st.session_state['modelo'] == 'GPT-4o (OpenAI)':
            api_ok, mensaje = verificar_api()
            if not api_ok:
                st.error(f"Error: {mensaje}")
                return
            else:
                st.success(mensaje)
        else:
            st.info("Usando modelo local Gemma3:12b; no se usa la API de OpenAI")

        # Crear dos columnas
        col1, col2 = st.columns([3, 2])

        with col1:
            archivo = st.file_uploader("📎 Selecciona un archivo", type=['png', 'jpg', 'jpeg', 'pdf'])
            
            if archivo is not None:
                st.info(f"📝 Procesando: {archivo.name}")
                
                texto_extraido = ""
                try:
                    archivo_bytes = archivo.read()
                    if archivo.type == 'application/pdf':
                        if st.session_state['modelo'] == 'GPT-4o (OpenAI)':
                            texto_extraido = procesar_pdf(archivo_bytes)
                        else:
                            texto_extraido = procesar_pdf_local_modelo(archivo_bytes)
                    else:
                        if st.session_state['modelo'] == 'GPT-4o (OpenAI)':
                            texto_extraido = procesar_imagen(archivo_bytes)
                        else:
                            texto_extraido = procesar_imagen_local_modelo(archivo_bytes)
                    
                    with st.expander("Ver texto extraído", expanded=False):
                        st.text(texto_extraido)
                    
                    if not "Error al procesar" in texto_extraido:
                        st.session_state.texto_extraido = texto_extraido
                        with st.spinner('🤖 Analizando con IA...'):
                            if st.session_state['modelo'] == 'GPT-4o (OpenAI)':
                                analisis = analizar_texto_con_openai(texto_extraido)
                            else:
                                analisis = analizar_texto_local(texto_extraido)
                            st.session_state.analisis_actual = analisis
                            st.session_state.historial_chat = [
                                {'role': 'user', 'content': texto_extraido},
                                {'role': 'assistant', 'content': analisis}
                            ]
                            
                            # Guardar la lectura en la base de datos
                            db.guardar_lectura(
                                nombre_archivo=archivo.name,
                                texto_extraido=texto_extraido,
                                analisis=analisis,
                                modelo=st.session_state['modelo'],
                                tipo_documento=archivo.type,
                                contenido_archivo=archivo_bytes
                            )
                        
                        # Área de análisis actualizado
                        st.subheader("📊 Análisis Actual")
                        st.write(st.session_state.analisis_actual)
                        
                        # Área de chat para preguntas y correcciones
                        st.subheader("💬 Chat para Preguntas y Correcciones")
                        
                        # Selector para tipo de interacción
                        tipo_interaccion = st.radio(
                            "Tipo de interacción:",
                            ["Hacer una pregunta", "Realizar una corrección"],
                            horizontal=True
                        )
                        
                        placeholder = (
                            "Ejemplo: '¿Cuál es el monto total?' o '¿Qué productos se compraron?'"
                            if tipo_interaccion == "Hacer una pregunta" else
                            "Ejemplo: 'El monto total es 15.000' o 'La fecha correcta es 15 de marzo 2024'"
                        )
                        
                        pregunta = st.text_input(
                            "Escribe tu consulta",
                            placeholder=placeholder
                        )
                        
                        if st.button("Enviar", key="enviar_pregunta") and pregunta:
                            with st.spinner('🤖 Procesando tu consulta...'):
                                es_correccion = tipo_interaccion == "Realizar una corrección"
                                if st.session_state['modelo'] == 'GPT-4o (OpenAI)':
                                    respuesta = analizar_texto_con_openai(pregunta, st.session_state.historial_chat, es_correccion)
                                else:
                                    respuesta = analizar_texto_local(pregunta, st.session_state.historial_chat, es_correccion)
                                
                                st.session_state.historial_chat.extend([
                                    {'role': 'user', 'content': pregunta},
                                    {'role': 'assistant', 'content': respuesta}
                                ])
                                
                                # Actualizar el análisis si es una corrección
                                if es_correccion:
                                    st.session_state.analisis_actual = respuesta
                                    st.rerun()
                        
                        # Mostrar historial del chat
                        if len(st.session_state.historial_chat) > 2:  # Si hay más mensajes después del análisis inicial
                            with st.expander("Ver historial de conversación", expanded=True):
                                for mensaje in st.session_state.historial_chat[2:]:  # Excluir el análisis inicial
                                    if mensaje['role'] == 'user':
                                        st.markdown(f"**👤 Tú:** {mensaje['content']}")
                                    else:
                                        st.markdown(f"**🤖 Asistente:** {mensaje['content']}")
                except Exception as e:
                    st.error(f"❌ Error al procesar el archivo: {str(e)}")
                    logger.error(f"Error en el procesamiento principal: {str(e)}")

        # Mostrar la imagen en la columna derecha
        with col2:
            if archivo is not None:
                st.subheader("🖼️ Vista previa del documento")
                try:
                    if archivo.type == 'application/pdf':
                        imagenes = convert_from_bytes(archivo_bytes)
                        for i, imagen in enumerate(imagenes):
                            st.image(imagen, caption=f"Página {i+1}", use_container_width=True)
                    else:
                        imagen = Image.open(io.BytesIO(archivo_bytes))
                        st.image(imagen, caption="Documento subido", use_container_width=True)
                except Exception as e:
                    st.error(f"❌ Error al mostrar la vista previa: {str(e)}")
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")
        logger.error(f"Error inesperado en main: {str(e)}")

if __name__ == "__main__":
    main()
