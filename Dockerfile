FROM debian:bookworm-slim
WORKDIR /app
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

RUN --mount=type=cache,target=/var/cache/apt \
  --mount=type=cache,target=/var/lib/apt/lists \
  apt-get update && apt-get install -y --no-install-recommends \
    curl \
    python3 \
    python3-altair \
    python3-cryptography \
    python3-dotenv \
    python3-pandas \
    python3-pip \
    python3-requests

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache \
  pip install --break-system-packages \
  beautifulsoup4 \
  opencensus-ext-azure \
  streamlit

COPY main.py .
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=true"]
