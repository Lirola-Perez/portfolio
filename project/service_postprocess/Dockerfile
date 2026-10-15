FROM python:3.13

# Current active folder for following commands
WORKDIR /usr/local/app

# Dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 8003

CMD [ "python", "service_postprocess/main.py" ]