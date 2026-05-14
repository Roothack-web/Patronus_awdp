#!/bin/bash
# Write dynamic flag from environment variable
echo "<?php \$flag = \"${FLAG}\";" > /var/www/html/flag.php

# Start Apache in foreground
apache2-foreground
