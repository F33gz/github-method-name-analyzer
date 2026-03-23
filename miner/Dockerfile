FROM python:3.11-slim
WORKDIR /app
COPY requeriments.txt .
RUN pip install --no-cache-dir -r requeriments.txt
COPY miner.py .
CMD ["python", "-u", "miner.py"]
