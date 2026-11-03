FROM python:3.13

# Install system dependencies required to run the EnergyPlus binary
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    ca-certificates \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/local/app

# Dependencies-> as the CONTEXT in pipeline is set to ROOT (".") here should be
#               specified the paths from that ROOT (PORTFOLIO)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download and extract the full EnergyPlus engine
RUN wget -O energyplus.tar.gz https://github.com/NREL/EnergyPlus/releases/download/v23.1.0/EnergyPlus-23.1.0-87ed9199d4-Linux-Ubuntu22.04-x86_64.tar.gz && \
    tar -xzf energyplus.tar.gz && \
    mv EnergyPlus-23.1.0-87ed9199d4-Linux-Ubuntu22.04-x86_64 /usr/local/EnergyPlus-23.1.0 && \
    rm energyplus.tar.gz

ENV EPLUS_IDD_PATH=/usr/local/EnergyPlus-23.1.0/Energy+.idd

# Dependencies-> as the CONTEXT in pipeline is set to ROOT (".") here should be
#               specified the paths from that ROOT (PORTFOLIO)
COPY . .
# internal container port (not public)
EXPOSE 8002

RUN useradd app
USER app

CMD [ "python", "main.py" ]