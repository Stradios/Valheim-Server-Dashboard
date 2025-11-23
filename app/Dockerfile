FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose panel port
EXPOSE 8000

# Default envs – override in compose
ENV VALHEIM_PORT_RANGE_START=24560
ENV VALHEIM_PORT_RANGE_END=24660
ENV VALHEIM_PORT_BLOCK_SIZE=3
ENV DATA_ROOT=/vh_data

CMD ["python", "app.py"]

