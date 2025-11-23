FROM postgres
ENV POSTGRES_DB=s \
  POSTGRES_USER=postgres \
  POSTGRES_PASSWORD=s

COPY init.sql /docker-entrypoint-initdb.d/
EXPOSE 5432
CMD ["postgres"]
