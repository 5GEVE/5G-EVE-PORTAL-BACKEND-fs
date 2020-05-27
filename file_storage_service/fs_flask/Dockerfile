FROM python:3.7.1

LABEL Author="Gines Garcia Aviles"
LABEL E-mail="gigarcia@it.uc3m.es"
LABEL version="0.1b"

RUN apt-get update -y && \
    apt-get install -y python3-pip python3-dev

WORKDIR /

COPY ./requirements.txt /requirements.txt
RUN pip3 install -r requirements.txt

RUN mkdir authservice_flask

ADD ./app /authservice_flask/app
ADD ./auth_app.py /authservice_flask
#ADD ./keycloak.json /authservice_flask/app/keycloak

WORKDIR /authservice_flask

CMD [ "python3", "auth_app.py" ]