# Lector de Facturas y Boletas

Esta aplicación permite leer y analizar facturas o boletas en formato imagen o PDF utilizando OCR (Reconocimiento Óptico de Caracteres) y el modelo Gemma3 12B a través de Ollama para el análisis del contenido.

## Requisitos previos

1. Python 3.10 o superior
2. Poetry para la gestión de dependencias
3. Tesseract OCR instalado en el sistema
4. Ollama instalado con el modelo Gemma3 12B

### Instalación de Tesseract en macOS
```bash
brew install tesseract
brew install tesseract-lang  # Para soporte de idiomas adicionales
```

### Instalación de Ollama y el modelo Gemma3 12B
1. Instalar Ollama desde https://ollama.ai
2. Ejecutar:
```bash
ollama pull gemma3:12b
```

## Instalación

1. Clonar el repositorio
2. Instalar las dependencias:
```bash
poetry install
```

## Uso

1. Activar el entorno virtual:
```bash
poetry shell
```

2. Ejecutar la aplicación:
```bash
streamlit run lector_facturas/app.py
```

3. Abrir el navegador en la dirección indicada por Streamlit
4. Subir una imagen o PDF de una factura o boleta
5. La aplicación extraerá el texto y lo analizará usando el modelo Gemma3 12B
