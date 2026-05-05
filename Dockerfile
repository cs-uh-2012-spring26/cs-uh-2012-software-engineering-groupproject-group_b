
FROM python:3.10-alpine

WORKDIR /app

COPY . .

RUN pip install -r requirements-dev.txt

EXPOSE 8000 

RUN chmod +x gunicorn_starter.sh 

ENTRYPOINT [ "sh", "./gunicorn_starter.sh"]