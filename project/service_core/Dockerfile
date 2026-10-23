FROM python:3.13

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Current active folder for following commands
WORKDIR /usr/local/app

# Dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Download ONLY the Energy+.idd schema file directly from GitHub (v23.1.0)
RUN mkdir -p /app/assets && \
    wget -O energyplus.tar.gz https://github.com/NREL/EnergyPlus/releases/download/v23.1.0/EnergyPlus-23.1.0-87ed9199d4-Linux-Ubuntu22.04-x86_64.tar.gz && \
    tar -xzf energyplus.tar.gz --wildcards '*/Energy+.idd' --strip-components=1 && \
    mv Energy+.idd /app/assets/Energy+.idd && \
    rm energyplus.tar.gz

# Point eppy directly to this file via environment variable
ENV EPLUS_IDD_PATH=/app/assets/Energy+.idd

# COPY source dest
COPY . .
# internal container port (not public)
EXPOSE 8001

# User (not root)
RUN useradd app
USER app

CMD [ "python", "main.py" ]
