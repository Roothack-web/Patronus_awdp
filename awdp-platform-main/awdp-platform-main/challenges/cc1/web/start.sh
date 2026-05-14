#!/bin/sh
# ============================================================
# AWDP CC1 Challenge Startup Script
# ============================================================
# Write FLAG to /flag for dynamic flag verification.
# ============================================================

echo "$FLAG" > /flag

# Start Tomcat in foreground
catalina.sh run
