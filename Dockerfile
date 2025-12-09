FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update -y \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --upgrade pip \
    && pip3 install --upgrade -r requirements.txt

COPY . .

CMD ["bash", "start"]