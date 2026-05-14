FROM php:8.1-apache

# Install dependencies your challenge needs
RUN apt-get update && apt-get install -y \
    mariadb-server \
    && docker-php-ext-install mysqli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy challenge source code
COPY web/ /var/www/html/
RUN chmod +x /var/www/html/start.sh

EXPOSE 80

CMD ["/var/www/html/start.sh"]
