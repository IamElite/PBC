FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --upgrade pip \
    && pip3 install --upgrade -r requirements.txt

COPY . .

CMD ["bash", "start"]
