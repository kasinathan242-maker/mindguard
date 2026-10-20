# syntax=docker/dockerfile:1.7
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# The safety classifier's sentence encoder, pinned to a revision and baked into the image so
# containers never download at runtime and work fully offline. Keep in sync with
# app/safety/download_models.py (a test checks this).
ENV HF_HOME=/app/.hf
ARG ENCODER=intfloat/multilingual-e5-small
ARG ENCODER_REVISION=614241f622f53c4eeff9890bdc4f31cfecc418b3
RUN /app/.venv/bin/python -c "from huggingface_hub import snapshot_download; snapshot_download('${ENCODER}', revision='${ENCODER_REVISION}', allow_patterns=['config.json', 'model.safetensors', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'sentencepiece.bpe.model'])" \
    && chmod -R a+rX /app/.hf
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

COPY alembic.ini ./
COPY app ./app

RUN useradd --create-home --uid 10001 mindguard
USER mindguard

ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000

# start-period covers loading the sentence encoder on first boot.
HEALTHCHECK --interval=15s --timeout=3s --start-period=60s --retries=5 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=2).status == 200 else 1)"

CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
