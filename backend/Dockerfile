FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_DEFAULT_TIMEOUT=45 \
    PIP_RETRIES=3

WORKDIR /app

COPY requirements.txt /app/requirements.txt

# Some development networks/VPNs cannot reliably reach pypi.org from
# Docker BuildKit. Try the official index first, then trusted mirrors.
RUN set -eux; \
    python -m pip install --no-cache-dir --index-url https://pypi.org/simple -r /app/requirements.txt \
    || python -m pip install --no-cache-dir --index-url https://mirrors.aliyun.com/pypi/simple -r /app/requirements.txt \
    || python -m pip install --no-cache-dir --index-url https://pypi.tuna.tsinghua.edu.cn/simple -r /app/requirements.txt

COPY . /app

EXPOSE 8000
