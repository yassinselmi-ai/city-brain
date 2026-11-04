FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the whole project skeleton so both API and consumer work
COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
COPY mocks ./mocks
COPY models ./models

RUN pip install --upgrade pip && pip install -e ".[dev]"

RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "city_brain.main:app", "--host", "0.0.0.0", "--port", "8000"]