FROM python:3.10.10

WORKDIR /opt/etl

COPY requirements.txt requirements.txt

RUN  pip install --upgrade pip \
     && pip install -r requirements.txt --no-cache-dir

COPY . .

LABEL org.opencontainers.image.source=https://github.com/noviksv/movies_etl

CMD ["python", "load_data.py"]

