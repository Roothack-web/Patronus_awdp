FROM php:8.1-apache

# Configure Apache for dual ports
# web1 (SSRF proxy) on port 80, web2 (ThinkPHP RCE) on port 8080
RUN echo "Listen 8080" >> /etc/apache2/ports.conf

# web1 - SSRF frontend (port 80)
COPY web1/index.php /var/www/html/
COPY web1/robots.txt /var/www/html/

# web2 - ThinkPHP backend (port 8080)
RUN mkdir -p /var/www/html2
COPY web2/ /var/www/html2/

# Add virtual host for port 8080 pointing to web2
RUN { \
    echo '<VirtualHost *:8080>'; \
    echo '    DocumentRoot /var/www/html2'; \
    echo '    <Directory /var/www/html2>'; \
    echo '        Options Indexes FollowSymLinks'; \
    echo '        AllowOverride All'; \
    echo '        Require all granted'; \
    echo '    </Directory>'; \
    echo '</VirtualHost>'; \
} > /etc/apache2/sites-enabled/010-ssrf-web2.conf

# Flag file location (same as original)
RUN mkdir -p /home/ctf
COPY start.sh /
RUN chmod +x /start.sh

EXPOSE 80
CMD ["/start.sh"]
