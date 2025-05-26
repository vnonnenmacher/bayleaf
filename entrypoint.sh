#!/bin/bash

apt-get update && apt-get install -y netcat-openbsd

# Espera o banco de dados estar pronto
echo "Aguardando o banco de dados..."

while ! nc -z $DB_HOST $DB_PORT; do
  sleep 1
done

echo "Banco de dados está pronto!"

# Rodar migrações
python3 manage.py migrate

# Coletar arquivos estáticos
# python3 manage.py collectstatic --noinput

# Iniciar o Gunicorn
exec gunicorn bayleaf.wsgi:application --bind 0.0.0.0:8000