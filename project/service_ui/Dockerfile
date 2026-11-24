FROM python:3.13

# Install system dependencies required to run the EnergyPlus binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd app
USER app

# --host 0.0.0.0 opening to requests, port 8080
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080" ]