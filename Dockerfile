FROM python:3.8-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc supervisor nginx && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY server_config/supervisord.conf /supervisord.conf
COPY server_config/nginx /etc/nginx/sites-available/default
COPY server_config/docker-entrypoint.sh /entrypoint.sh
COPY requirements.txt /app/requirements.txt
COPY FeatureCloud /app/FeatureCloud

RUN pip3 install --user --upgrade pip && \
    pip3 install --user -r ./app/requirements.txt && \
    pip3 cache purge

WORKDIR /app/FeatureCloud
RUN pip install .
WORKDIR /

COPY . /app

EXPOSE 9000 9001
ENTRYPOINT ["sh", "/entrypoint.sh"]
