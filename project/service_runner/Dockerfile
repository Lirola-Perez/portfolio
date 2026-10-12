FROM python:3.13

WORKDIR /usr/local/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY service_runner ./service_runner
EXPOSE 8002

RUN useradd app
USER app

