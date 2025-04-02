# Lector de Facturas y Boletas 📄

Aplicación web para procesar y analizar facturas y boletas usando OCR y el modelo de IA Gemma3 12B. La aplicación extrae automáticamente información relevante como fechas, montos, productos y datos del vendedor, permitiendo hacer consultas y correcciones de manera interactiva.

## Características ✨

- Procesa imágenes (PNG, JPG) y documentos PDF
- Extracción de texto usando OCR (Tesseract)
- Análisis automático usando Gemma3 12B
- Interfaz interactiva para hacer preguntas y correcciones
- Historial de lecturas con vista previa de documentos
- Base de datos SQLite para almacenamiento persistente

## Requisitos Previos 💻

1. Python 3.10 o superior
2. Poetry (gestor de dependencias)
3. Tesseract OCR
4. Poppler (para procesar PDFs)
5. Ollama con el modelo Gemma3 12B

### Instalación de Dependencias del Sistema

```bash
# Instalar Tesseract OCR
brew install tesseract

# Instalar Poppler para procesar PDFs
brew install poppler

# Instalar y configurar Ollama
brew install ollama
ollama pull gemma3:12b
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
- Ver texto extraído y análisis automático
- Hacer preguntas sobre el documento
- Corregir datos mal extraídos

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
- **OCR**: Tesseract
- **IA**: Ollama (Gemma3 12B)
- **Base de Datos**: SQLite
- **Procesamiento de PDFs**: pdf2image + Poppler
- **Gestión de Dependencias**: Poetry

## Autor 👨‍💻

Felipe Mancini - felipe@asimov.cl
