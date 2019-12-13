FROM python:3.7.1

LABEL Author="Gines Garcia Aviles"
LABEL E-mail="gigarcia@it.uc3m.es"
LABEL version="0.1b"

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev

WORKDIR /

COPY ./requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

RUN mkdir uploaded_files

RUN mkdir ftp_flask

ADD ./app /ftp_flask/app
ADD ./ftp_app.py /ftp_flask
ADD ./keycloak.json /ftp_flask/app/keycloak

WORKDIR /ftp_flask

CMD [ "python3", "ftp_app.py" ]