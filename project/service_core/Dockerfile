FROM python:3.13

# Current active folder for following commands
WORKDIR /usr/local/app

# Dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# COPY source dest
COPY . .
EXPOSE 8001

# User (not root)
RUN useradd app
USER app

CMD [ "python", "service_code/main.py" ]
