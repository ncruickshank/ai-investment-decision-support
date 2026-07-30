FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:0.5.0 /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md .python-version ./

RUN uv sync --dev

COPY . .

CMD ["uv", "run", "pytest"]
