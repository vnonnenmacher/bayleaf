#!/bin/sh

echo "Aguardando o banco de dados ficar disponível..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Banco de dados pronto!"

# Aplicar migrações
echo "Rodando migrações..."
python3 manage.py makemigrations
python3 manage.py migrate

# Coletar arquivos estáticos (opcional)
echo "Coletando arquivos estáticos..."
python3 manage.py collectstatic --noinput

# # Remover socket antigo, se existir
# rm -f /run/gunicorn/gunicorn.sock

# Criar diretório do socket (caso não exista)
mkdir -p /run/gunicorn
chown -R root:www-data /run/gunicorn
chmod -R 775 /run/gunicorn

# Iniciar Gunicorn na porta 8000
echo "Iniciando Gunicorn..."
exec gunicorn --preload vesalus.wsgi:application \
    --workers 5 \
    --bind 0.0.0.0:8000 \
    --timeout 0 \
    --access-logfile /var/log/gunicorn_access.log \
    --error-logfile /var/log/gunicorn_error.log \
    --log-level debug
