FROM python:3.13

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Current active folder for following commands
WORKDIR /usr/local/app

# Dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8003

# User (not root)
RUN useradd app
USER app

CMD [ "python", "main.py" ]