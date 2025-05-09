# Lector de Facturas y Boletas 📄

Aplicación web para procesar y analizar facturas y boletas usando modelos de IA como GPT-4o o Gemma3:12b (local). La aplicación extrae automáticamente toda la información relevante del documento, permitiendo hacer consultas y correcciones de manera interactiva.

## Características ✨

- Procesa imágenes (PNG, JPG) y documentos PDF
- Análisis automático usando GPT-4o (OpenAI) o Gemma3:12b (local vía Ollama)
- Extracción y análisis directo de información sin OCR externo
- Interfaz interactiva para hacer preguntas y correcciones
- Historial de lecturas con vista previa de documentos
- Capacidad para eliminar registros del historial
- Base de datos SQLite para almacenamiento persistente

## Requisitos Previos 💻

1. Python 3.10 o superior
2. Poetry (gestor de dependencias)
3. Poppler (para procesar PDFs)
4. Clave de API de OpenAI (para usar GPT-4o)
5. Ollama (opcional, para usar Gemma3:12b local)

### Instalación de Dependencias del Sistema

```bash
# Instalar Poppler para procesar PDFs
brew install poppler
```

### Configuración de OpenAI

1. Crea un archivo `.env` en la raíz del proyecto
2. Agrega tu clave de API de OpenAI:
```bash
OPENAI_API_KEY=tu_api_key_aqui
```

### Configuración de Ollama (opcional)

1. Instala Ollama desde [ollama.ai](https://ollama.ai)
2. Descarga el modelo Gemma3:12b:
```bash
ollama pull gemma3:12b
```
3. Asegúrate de que el servidor Ollama esté en ejecución antes de usar el modelo local

## Instalación 💾

1. Clonar el repositorio:
```bash
git clone [URL_DEL_REPOSITORIO]
cd app_lectura_boletas_facturas
```

2. Instalar dependencias usando Poetry:
```bash
poetry install
```

## Uso 📃

1. Iniciar la aplicación:
```bash
poetry run streamlit run lector_facturas/app.py
```

2. Abrir el navegador en `http://localhost:8501`

### Funcionalidades Principales

#### Nueva Lectura 📄
- Subir imagen o PDF de factura/boleta
- Seleccionar entre modelo OpenAI (GPT-4o) o modelo local (Gemma3:12b)
- Obtener análisis automático detallado en formato estructurado
- Hacer preguntas sobre el documento
- Corregir datos mal interpretados

#### Historial de Lecturas 📚
- Ver todas las lecturas realizadas
- Previsualizar documentos originales
- Acceder al análisis completo
- Eliminar lecturas individuales
- Ver qué modelo se utilizó para cada análisis

## Estructura del Proyecto 📂

```
lector_facturas/
├── app.py         # Aplicación principal Streamlit
├── db.py          # Manejo de base de datos SQLite
└── lecturas.db    # Base de datos de lecturas (creada automáticamente)
```

## Tecnologías Utilizadas 🛠️

- **Frontend**: Streamlit
- **IA**: 
  - OpenAI GPT-4o (API)
  - Gemma3:12b (local vía Ollama API)
- **Base de Datos**: SQLite
- **Procesamiento de PDFs**: pdf2image + Poppler
- **Gestión de Dependencias**: Poetry
- **API**: Requests para comunicación con Ollama

## Autor 👨‍💻

Felipe Mancini - felipe@asimov.cl
