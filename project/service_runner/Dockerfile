FROM python:3.13

WORKDIR /usr/local/app

# Install system dependencies needed to download and install EnergyPlus
RUN apt-get update && apt-get install -y \
    wget \
    gdebi-core \
    && rm -rf /var/lib/api/lists/*

# Download and install EnergyPlus 24.1.0 (or your preferred version)
# Replace URL with the official GitHub release link for your target version
RUN wget https://github.com/NatLabRockies/EnergyPlus/releases/tag/v23.1.0/EnergyPlus-23.1.0-87ed9199d4-Linux-Ubuntu22.04-x86_64.tar.gz \
    && apt-get update && apt-get install -y ./EnergyPlus-23.1.0-87ed9199d4-Linux-Ubuntu22.04-x86_64.tar.gz \
    && rm EnergyPlus-23.1.0-87ed9199d4-Linux-Ubuntu22.04-x86_64.tar.gz

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8002

RUN useradd app
USER app

CMD [ "python", "service_runner/main.py" ]