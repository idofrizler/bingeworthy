FROM python:3.11-slim
WORKDIR /app
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

RUN --mount=type=cache,target=/var/cache/apt \
  apt-get update && apt-get install -y --no-install-recommends curl
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache \
  pip install -r requirements.txt

COPY main.py .
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=true"]
