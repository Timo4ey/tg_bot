FROM python:3

WORKDIR /app   

COPY . .



RUN apt update -y && pip install poetry && make install

CMD ["make", "start"]
