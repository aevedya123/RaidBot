FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir discord.py requests

CMD ["python", "main.py"]
