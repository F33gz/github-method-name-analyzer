FROM python:3.11-slim
WORKDIR /app
COPY requeriments.txt .
RUN pip install --no-cache-dir -r requeriments.txt
COPY visualizer.py .
COPY templates/ ./templates/
EXPOSE 5000
CMD ["python", "-u", "visualizer.py"]
