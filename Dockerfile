
# Usa una imagen base oficial de Python
FROM python:3-slim

# Instala Poppler y dependencias del sistema
RUN apt-get update && apt-get install -y poppler-utils && rm -rf /var/lib/apt/lists/*

# Instala Poetry
RUN pip install poetry

# Establece el directorio de trabajo
WORKDIR /app

# Copia los archivos de dependencias y README.md
COPY pyproject.toml poetry.lock README.md ./

# Instala las dependencias con Poetry
RUN poetry install --no-root
#RUN poetry config virtualenvs.create false \
#  && poetry install --no-interaction --no-ansi

# Copia el resto del código fuente
COPY lector_facturas/ ./lector_facturas

# Expone el puerto si tu app es web (ajusta si es necesario)
EXPOSE 8501

# Comando para ejecutar la app (ajusta si usas otro archivo)
CMD ["poetry", "run", "streamlit", "run", "lector_facturas/app.py"]