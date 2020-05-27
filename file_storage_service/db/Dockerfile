FROM postgres:11.1
COPY init.sql /docker-entrypoint-initdb.d/1.sql
COPY data.sql /docker-entrypoint-initdb.d/2.sql
CMD ["postgres"]