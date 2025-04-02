import streamlit as st
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
from ollama import Client
import io
import sys
import logging
import requests
from datetime import datetime
from db import LecturasDB

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Ollama
OLLAMA_HOST = "http://localhost:11434"
client = Client(host=OLLAMA_HOST)

def verificar_ollama():
    """Verifica si Ollama está disponible y si el modelo Gemma está instalado."""
    try:
        response = requests.get(f"{OLLAMA_HOST}/api/tags")
        if response.status_code != 200:
            return False, "No se puede conectar al servidor de Ollama"
        
        modelos = response.json().get('models', [])
        if not any(modelo.get('name', '') == 'gemma3:12b' for modelo in modelos):
            return False, "El modelo Gemma3 12B no está instalado. Ejecuta 'ollama pull gemma3:12b'"
        
        return True, "Ollama y Gemma están disponibles"
    except Exception as e:
        return False, f"Error al conectar con Ollama: {str(e)}"

def procesar_imagen(imagen_bytes):
    """Procesa una imagen y extrae el texto usando pytesseract."""
    try:
        imagen = Image.open(io.BytesIO(imagen_bytes))
        texto = pytesseract.image_to_string(imagen, lang='spa')
        if not texto.strip():
            logger.warning("No se pudo extraer texto de la imagen")
            return "No se pudo extraer texto de la imagen"
        return texto
    except Exception as e:
        logger.error(f"Error al procesar la imagen: {str(e)}")
        return f"Error al procesar la imagen: {str(e)}"

def procesar_pdf(pdf_bytes):
    """Convierte PDF a imágenes y extrae el texto."""
    try:
        try:
            imagenes = convert_from_bytes(pdf_bytes)
        except Exception as e:
            if "poppler" in str(e).lower():
                error_msg = "Error: Poppler no está instalado. Por favor, ejecuta 'brew install poppler' en la terminal."
                logger.error(error_msg)
                return error_msg
            raise e
            
        texto_completo = []
        for imagen in imagenes:
            texto = pytesseract.image_to_string(imagen, lang='spa')
            texto_completo.append(texto)
        resultado = '\n'.join(texto_completo)
        if not resultado.strip():
            logger.warning("No se pudo extraer texto del PDF")
            return "No se pudo extraer texto del PDF"
        return resultado
    except Exception as e:
        logger.error(f"Error al procesar el PDF: {str(e)}")
        return f"Error al procesar el PDF: {str(e)}"

def analizar_texto_con_gemma(texto, historial_mensajes=None, es_correccion=False):
    """Analiza el texto extraído usando el modelo Gemma en Ollama."""
    try:
        if "Error al procesar" in texto:
            return "No se puede analizar debido a un error en el procesamiento del documento"
        
        if historial_mensajes is None:
            prompt = f"""Analiza la siguiente factura o boleta y extrae la información relevante como:
            - Fecha
            - Monto total
            - Productos o servicios
            - Información del vendedor
            
            Texto de la factura:
            {texto}
            
            Responde de manera estructurada y clara, usando viñetas para cada dato.
            """
            mensajes = [{'role': 'user', 'content': prompt}]
        else:
            if es_correccion:
                prompt = f"""Basándote en el análisis anterior y la corrección proporcionada: '{texto}',
                genera un nuevo análisis completo y actualizado de la factura.
                Mantén el mismo formato estructurado con viñetas, pero incorpora la corrección indicada.
                Menciona específicamente qué dato se ha corregido."""
            else:
                prompt = texto
            mensajes = historial_mensajes + [{'role': 'user', 'content': prompt}]
        
        logger.info("Enviando texto a Gemma para análisis")
        try:
            response = client.chat(model='gemma3:12b', messages=mensajes)
            return response.message.content
        except Exception as e:
            logger.error(f"Error en la comunicación con Ollama: {str(e)}")
            return f"Error al comunicarse con Ollama: {str(e)}"
    except Exception as e:
        logger.error(f"Error al analizar con Gemma: {str(e)}")
        return f"Error al analizar con Gemma: {str(e)}"

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
    """Muestra la interfaz del historial de lecturas."""
    st.title("📚 Historial de Lecturas")
    
    # Obtener todas las lecturas
    lecturas = db.obtener_lecturas()
    
    if not lecturas:
        st.info("No hay lecturas guardadas en el historial.")
        return
    
    # Crear una tabla con las lecturas
    lecturas_data = []
    for lectura in lecturas:
        id, nombre, texto, analisis, fecha, tipo, _ = lectura  # Ignorar contenido_archivo en la tabla
        fecha_formateada = datetime.strptime(fecha, '%Y-%m-%d %H:%M:%S').strftime('%d/%m/%Y %H:%M')
        lecturas_data.append({
            "ID": id,
            "Archivo": nombre,
            "Fecha": fecha_formateada,
            "Tipo": tipo or "No especificado"
        })
    
    # Mostrar tabla con las lecturas
    st.dataframe(
        lecturas_data,
        column_config={
            "ID": st.column_config.NumberColumn("ID", width="small"),
            "Archivo": st.column_config.TextColumn("Nombre del Archivo"),
            "Fecha": st.column_config.TextColumn("Fecha de Lectura"),
            "Tipo": st.column_config.TextColumn("Tipo de Documento")
        },
        hide_index=True
    )
    
    # Selector de lectura para ver detalles
    lectura_seleccionada = st.selectbox(
        "Selecciona una lectura para ver los detalles:",
        options=[l[0] for l in lecturas],
        format_func=lambda x: f"Lectura #{x} - {next((l[1] for l in lecturas if l[0] == x), '')}"
    )
    
    if lectura_seleccionada:
        lectura = db.obtener_lectura(lectura_seleccionada)
        if lectura:
            _, nombre, texto, analisis, fecha, tipo, contenido_archivo = lectura
            
            # Mostrar el documento y el análisis en columnas
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.subheader("🖼️ Documento")
                if contenido_archivo:
                    mostrar_documento(contenido_archivo, tipo)
                else:
                    st.warning("No se encontró el documento original")
                
                with st.expander("📝 Texto Extraído", expanded=False):
                    st.text(texto)
            
            with col2:
                st.subheader("📊 Análisis")
                st.write(analisis)
            
            # Botón para eliminar la lectura
            if st.button("🗑️ Eliminar esta lectura", key=f"delete_{lectura_seleccionada}"):
                if db.eliminar_lectura(lectura_seleccionada):
                    st.success("Lectura eliminada correctamente")
                    st.rerun()
                else:
                    st.error("Error al eliminar la lectura")

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
        
        if pagina == "Historial de Lecturas":
            mostrar_historial(db)
            return
        
        # Página principal - Nueva Lectura
        st.title("📄 Lector de Facturas y Boletas")
        st.markdown("""
        Sube una imagen o PDF de tu factura o boleta para analizarla automáticamente.
        El sistema extraerá la información relevante usando OCR y la analizará con IA.
        Puedes hacer preguntas o solicitar correcciones sobre los datos extraídos.
        """)
        
        # Inicializar variables de estado en la sesión
        if 'texto_extraido' not in st.session_state:
            st.session_state.texto_extraido = ""
        if 'historial_chat' not in st.session_state:
            st.session_state.historial_chat = []
        if 'analisis_actual' not in st.session_state:
            st.session_state.analisis_actual = ""

        # Verificar si Tesseract está instalado
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            st.error("Error: Tesseract no está instalado. Por favor, instálalo usando 'brew install tesseract'")
            return

        # Verificar si Ollama está disponible
        ollama_ok, mensaje = verificar_ollama()
        if not ollama_ok:
            st.error(f"Error: {mensaje}")
            return
        else:
            st.success(mensaje)

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
                        texto_extraido = procesar_pdf(archivo_bytes)
                    else:
                        texto_extraido = procesar_imagen(archivo_bytes)
                    
                    with st.expander("Ver texto extraído", expanded=False):
                        st.text(texto_extraido)
                    
                    if not "Error al procesar" in texto_extraido:
                        st.session_state.texto_extraido = texto_extraido
                        with st.spinner('🤖 Analizando con Gemma...'):
                            analisis = analizar_texto_con_gemma(texto_extraido)
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
                                respuesta = analizar_texto_con_gemma(
                                    pregunta,
                                    st.session_state.historial_chat,
                                    es_correccion
                                )
                                
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
