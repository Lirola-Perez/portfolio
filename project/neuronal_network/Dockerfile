FROM python:3.13

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files and automatic ownership to root
COPY . .
# internal container port (not public)
EXPOSE 8004

RUN useradd app
USER app

CMD [ "python", "main.py" ]