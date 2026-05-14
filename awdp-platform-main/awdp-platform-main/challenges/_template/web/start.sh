#!/bin/sh

# ============================================================
# AWDP Challenge Startup Script
# ============================================================
# The platform injects $FLAG environment variable when creating
# containers. Write it to a file so your challenge code can
# read it for dynamic flag verification.
# ============================================================

# Write flag to a known location
echo "$FLAG" > /flag

# Start any background services here (MySQL, etc.)
# mysqld_safe --user=mysql &
# sleep 3

# Initialize database if needed
# php /var/www/html/init_db.php

# Start Apache in foreground
apache2-foreground
