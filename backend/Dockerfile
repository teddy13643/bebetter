FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app
# requirements.txt 由 compose volume mount 進來，這裡先 COPY 裝依賴
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --no-deps kinqimen==0.0.6.6 && \
    pip install --no-cache-dir kinliuren==0.1.2.9 && \
    pip install --no-cache-dir kintaiyi==0.2.3
# kerykeion 已在 requirements.txt 中，不需要額外裝
# 不 COPY 程式碼，由 compose volume mount

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
