# Usar a imagem oficial do Python como base
FROM python:3.10

ENV PYTHONUNBUFFERED=1 \
    APP_HOME=/usr/src/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev \
  && rm -rf /var/lib/apt/lists/*

# Definir o diretório de trabalho
WORKDIR $APP_HOME

# Copiar o arquivo de requisitos e instalar as dependências
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código do projeto
COPY . .

# Entrypoint que escolhe runserver/uwsgi
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

# Defaults: prod mode; dev will override via compose profile
ENV RUN_MODE=prod
ENV DJANGO_SETTINGS_MODULE=config.settings.prod

CMD ["/entrypoint.sh"]
