# Usando uma imagem base do Python
FROM python:3.11

# Define o diretório de trabalho
WORKDIR /app

# Copia os arquivos da aplicação para dentro do container
COPY . .

# Install system prerequisites for building Python libs
RUN apt update
RUN apt install libldap2-dev libsasl2-dev -y

# Atualiação do pip
RUN pip install --upgrade pip

# Install OpenSSL so that we can build secrets library metadata
RUN pip install pyOpenSSL==25.0.0


# # Copiar os certificados SSL para dentro do container
# COPY ssl/server.crt /etc/nginx/ssl/server.crt
# COPY ssl/server.key /etc/nginx/ssl/server.key


# Instala as dependências do projeto
RUN pip install --no-cache-dir -r requirements.txt

# Define a variável de ambiente do Django para produção
ENV DJANGO_SETTINGS_MODULE=vesalus.settings

# Cria o diretório do socket para comunicação com o Nginx
# RUN mkdir -p /run/gunicorn

RUN apt-get update && apt-get install -y netcat-traditional


# Permissão para o script de entrada
RUN chmod +x /app/entrypoint.sh

# Expõe a porta do Django (opcional, pois vamos usar socket)
# EXPOSE 8000

# Define o script de entrada
ENTRYPOINT ["/app/entrypoint.sh"]
