FROM python:3.13

WORKDIR /usr/local/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY neuronal_network ./neuronal_network
EXPOSE 8004

RUN useradd app
USER app