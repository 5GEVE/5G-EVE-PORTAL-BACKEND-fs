FROM python:3.7.1

LABEL Author="Gines Garcia Aviles"
LABEL E-mail="gigarcia@it.uc3m.es"
LABEL version="0.1b"

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev

WORKDIR /

COPY ./requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

RUN mkdir fs_flask
RUN mkdir -p /storage/files_storage

ADD ./app /fs_flask/app
ADD ./fs_app.py /fs_flask

WORKDIR /fs_flask

CMD [ "python3", "fs_app.py" ]
