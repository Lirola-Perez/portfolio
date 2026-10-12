FROM python:3.13

WORKDIR /usr/local/app

# Dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# COPY source dest
COPY service_code ./service_code
EXPOSE 8001

# User (not root)
RUN useradd app
USER app
