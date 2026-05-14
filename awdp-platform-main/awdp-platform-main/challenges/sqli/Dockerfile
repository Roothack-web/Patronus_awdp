FROM php:8.1-apache

# Install MariaDB and PHP mysqli extension
RUN apt-get update && apt-get install -y mariadb-server \
    && docker-php-ext-install mysqli \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy web application and start script
COPY web/ /var/www/html/
RUN chmod +x /var/www/html/start.sh

EXPOSE 80

VOLUME /var/lib/mysql

CMD ["/var/www/html/start.sh"]
