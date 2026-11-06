FROM python:3.13

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Current active folder for following commands
WORKDIR /usr/local/app

# Dependencies-> as the CONTEXT in pipeline is set to ROOT (".") here should be
#               specified the paths from that ROOT (PORTFOLIO)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Dependencies-> as the CONTEXT in pipeline is set to ROOT (".") here should be
#               specified the paths from that ROOT (PORTFOLIO)
COPY . .
# internal container port (not public)
EXPOSE 8003

# User (not root)
RUN useradd app
USER app

CMD [ "python", "main.py"]