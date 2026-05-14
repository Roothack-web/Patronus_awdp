#!/bin/sh

# Write flag to the challenge's expected file path
echo "$FLAG" > /Th1s_12_f10g

# For compatibility with environment variable reads
export NSSFLAG="$FLAG"

# Start Apache (serves both port 80 and 8080)
apache2-foreground
