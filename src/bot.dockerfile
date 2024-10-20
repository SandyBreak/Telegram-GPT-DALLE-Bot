# -*- coding: UTF-8 -*-
    
FROM python:3.10.12-alpine

WORKDIR /src/

COPY requirements.txt /tmp/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r /tmp/requirements.txt

COPY . .

CMD ["python", "/src/main.py"]
