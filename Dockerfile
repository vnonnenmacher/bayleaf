# Usar a imagem oficial do Python como base
FROM python:3.10

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

# Definir o diretório de trabalho
WORKDIR /usr/src/app

# Copiar o arquivo de requisitos e instalar as dependências
COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

# Copiar o restante do código do projeto
COPY . .

# Expor a porta em que o Django estará rodando
EXPOSE 8000

# Comando para rodar o servidor Django em modo de desenvolvimento
# CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]