# Lector de Facturas y Boletas 📄

Aplicación web para procesar y analizar facturas y boletas usando el modelo GPT-4o. La aplicación extrae automáticamente toda la información relevante del documento, permitiendo hacer consultas y correcciones de manera interactiva.

## Características ✨

- Procesa imágenes (PNG, JPG) y documentos PDF
- Análisis automático usando GPT-4o
- Extracción y análisis directo de información sin OCR
- Interfaz interactiva para hacer preguntas y correcciones
- Historial de lecturas con vista previa de documentos
- Base de datos SQLite para almacenamiento persistente

## Requisitos Previos 💻

1. Python 3.10 o superior
2. Poetry (gestor de dependencias)
3. Poppler (para procesar PDFs)
4. Clave de API de OpenAI

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
- Obtener análisis automático detallado
- Hacer preguntas sobre el documento
- Corregir datos mal interpretados

#### Historial de Lecturas 📚
- Ver todas las lecturas realizadas
- Previsualizar documentos originales
- Acceder al análisis completo
- Eliminar lecturas antiguas

## Estructura del Proyecto 📂

```
lector_facturas/
├── app.py         # Aplicación principal Streamlit
├── db.py          # Manejo de base de datos SQLite
└── lecturas.db    # Base de datos de lecturas (creada automáticamente)
```

## Tecnologías Utilizadas 🛠️

- **Frontend**: Streamlit
- **IA**: OpenAI GPT-4o
- **Base de Datos**: SQLite
- **Procesamiento de PDFs**: pdf2image + Poppler
- **Gestión de Dependencias**: Poetry

## Autor 👨‍💻

Felipe Mancini - felipe@asimov.cl
