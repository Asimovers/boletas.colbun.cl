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
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analiza esta factura o boleta y extrae la información toda la información de la factura. Responde de manera estructurada y clara, usando viñetas para cada dato."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{imagen_base64}"
                            }
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

def analizar_texto_con_openai(texto, historial_mensajes=None, es_correccion=False):
    """Analiza el texto usando OpenAI."""
    try:
        if "Error al procesar" in texto:
            return "No se puede analizar debido a un error en el procesamiento del documento"
        
        if historial_mensajes is None:
            mensajes = [{"role": "user", "content": texto}]
        else:
            if es_correccion:
                prompt = f"""Basándote en el análisis anterior y la corrección proporcionada: '{texto}',
                genera un nuevo análisis completo y actualizado de la factura.
                Mantén el mismo formato estructurado con viñetas, pero incorpora la corrección indicada.
                Menciona específicamente qué dato se ha corregido."""
            else:
                prompt = texto
            mensajes = historial_mensajes + [{"role": "user", "content": prompt}]
        
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



        # Verificar si la API de OpenAI está disponible
        api_ok, mensaje = verificar_api()
        if not api_ok:
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
                        with st.spinner('🤖 Analizando con GPT...'):
                            analisis = analizar_texto_con_openai(texto_extraido)
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
                                respuesta = analizar_texto_con_openai(
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
