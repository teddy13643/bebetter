FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

RUN pip install --no-cache-dir \
    "httpx>=0.27.0" \
    "sxtwl==2.0.6" \
    "ephem==4.1.5" \
    "numpy" \
    "openai>=1.58.1" \
    "python-dotenv>=1.0.1" \
    "kerykeion>=5.0.0" \
    && pip install --no-cache-dir --no-deps "kinqimen==0.0.6.6" \
    && pip install --no-cache-dir "kinliuren==0.1.2.9" \
    && pip install --no-cache-dir "kintaiyi==0.2.3"

# build context 是 repo 根目錄，所以路徑從根目錄算
COPY core/ ./core/
COPY cli/actions.py cli/cli.py ./

ENTRYPOINT ["python", "cli.py"]
