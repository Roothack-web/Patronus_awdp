FROM php:8.1-apache

# Install python3 for defense evaluation exploit
RUN apt-get update && apt-get install -y python3 && rm -rf /var/lib/apt/lists/*

# Copy web files
COPY web/ /var/www/html/
RUN chmod +x /var/www/html/start.sh

EXPOSE 80

CMD ["/var/www/html/start.sh"]
