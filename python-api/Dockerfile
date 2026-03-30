FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY python_api.py .

RUN pip install --no-cache-dir flask flask-cors akshare pandas

EXPOSE 5001

CMD ["python", "python_api.py"]
