# Imagen minima para ejecutar el CLI sin instalar nada en la maquina.
# El objetivo no es "dockerizar por dockerizar": es que quien vea el video
# pueda clonar y ejecutar con un comando, sin pelearse con Python.
FROM python:3.12-slim

WORKDIR /app

# Las dependencias primero: esta capa se cachea y no se reconstruye
# cada vez que cambia el codigo.
COPY pyproject.toml README.md ./
COPY src/ ./src/
RUN pip install --no-cache-dir --no-compile . && \
    useradd --create-home --uid 1000 app

# Los nichos y los datos se montan como volumen: se editan desde fuera
# sin reconstruir la imagen.
COPY niches/ ./niches/

USER app
ENTRYPOINT ["python", "-m", "facelessyt"]
CMD ["--help"]
