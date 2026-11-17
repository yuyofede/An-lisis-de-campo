# Imagen Docker para desplegar el servicio de Streamlit en Vercel
# (Container Runtime) o en cualquier otro registry compatible con OCI.
#
# Notas de uso:
# - La app se ejecuta con `streamlit run app.py`.
# - Vercel espera que el server HTTP escuche en el puerto indicado por la
#   variable PORT (default 80 para contenedores en Vercel).
# - `--server.headless true` evita intentar abrir un browser en el contenedor.

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=80

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 80

CMD ["sh", "-c", "streamlit run app.py --server.port ${PORT} --server.address 0.0.0.0 --server.headless true"]
