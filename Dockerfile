FROM python:3.8-slim-buster

WORKDIR /app
RUN chmod 777 /app

COPY ./requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt

COPY ./start.py ./start.py
COPY ./communication ./communication
COPY ./db ./db
COPY ./telegram ./telegram
COPY ./ws ./ws
COPY ./helpers ./helpers

CMD ["python3", "start.py"]
