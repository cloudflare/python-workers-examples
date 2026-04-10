FROM python:3.12-slim

WORKDIR /app
RUN pip install --no-cache-dir pillow
COPY server.py .

EXPOSE 8080

CMD ["python", "-u", "server.py"]
