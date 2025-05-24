# Using a Python base image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy the application files into the container
COPY . .

# Install system prerequisites for building Python libs
RUN apt update
RUN apt install libldap2-dev libsasl2-dev -y

# pip update
RUN pip install --upgrade pip

# Install OpenSSL so that we can build secrets library metadata
RUN pip install pyOpenSSL==25.0.0


# # Copy SSL certificates into the container
# COPY ssl/server.crt /etc/nginx/ssl/server.crt
# COPY ssl/server.key /etc/nginx/ssl/server.key


# Installs project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set Django environment variable for production
ENV DJANGO_SETTINGS_MODULE=vesalus.settings

# Create the socket directory for communication with Nginx
# RUN mkdir -p /run/gunicorn

RUN apt-get update && apt-get install -y netcat-traditional


# Permission for input script
RUN chmod +x /app/entrypoint.sh

# Exposes the Django port (optional, since we will use socket)
# EXPOSE 8000

# Define the entry script
ENTRYPOINT ["/app/entrypoint.sh"]
