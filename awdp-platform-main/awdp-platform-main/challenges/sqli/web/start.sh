#!/bin/sh

# Make sqli_db resolve to localhost (PHP code uses 'sqli_db' hostname)
echo "127.0.0.1 sqli_db" >> /etc/hosts

# Write the AWDP flag to /flag for webshell to read
echo "$FLAG" > /flag

# Initialize MariaDB data directory if empty
if [ ! -d "/var/lib/mysql/mysql" ]; then
    mysql_install_db --user=mysql --datadir=/var/lib/mysql > /dev/null 2>&1
fi

# Start MariaDB
mysqld_safe --user=mysql &
# Wait for socket to be ready
for i in $(seq 1 30); do
    [ -S /run/mysqld/mysqld.sock ] && break
    sleep 1
done

# Create database and user for the application
mysql -u root <<'EOSQL'
CREATE DATABASE IF NOT EXISTS news_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'sroot'@'localhost' IDENTIFIED BY 'Sr00t_P@ssw0rd_2024!';
GRANT ALL PRIVILEGES ON news_db.* TO 'sroot'@'localhost';
FLUSH PRIVILEGES;
EOSQL

# Initialize application tables and data
php /var/www/html/init_db.php

# Start Apache (foreground)
apache2-foreground
