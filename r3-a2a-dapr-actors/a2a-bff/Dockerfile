FROM python:3.13-alpine

# Create non-root user
RUN addgroup -S appuser && adduser -S appuser -G appuser

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /code

# Install uv
RUN pip install --no-cache-dir uv

# Copy dependency files and app code
COPY pyproject.toml uv.lock* ./
COPY . ./

# Install deps with uv (no build deps installed)
RUN uv sync --no-dev

# Set permissions
RUN chown -R appuser:appuser /code
USER appuser

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]