#!/bin/bash
# DevPulse Uptime Monitor - runs via cron every 5 minutes
HEALTH_URL="http://127.0.0.1:8090/health"
ALERT_EMAIL="sidewinder181@gmail.com"
STATUS_FILE="/tmp/devpulse_status"

response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$HEALTH_URL" 2>/dev/null)

if [ "$response" != "200" ]; then
    # Check if we already sent an alert (avoid spam)
    if [ ! -f "$STATUS_FILE" ] || [ "$(cat $STATUS_FILE)" != "down" ]; then
        echo "down" > "$STATUS_FILE"
        # Try to restart first
        sudo systemctl restart devpulse
        sleep 3
        # Check again
        response2=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$HEALTH_URL" 2>/dev/null)
        if [ "$response2" != "200" ]; then
            # Send alert email
            python3 -c "
import smtplib
from email.mime.text import MIMEText
msg = MIMEText('DevPulse is DOWN. HTTP status: $response. Auto-restart attempted. Check: http://15.204.93.98:8091')
msg['From'] = 'monitor@byteoven.com'
msg['To'] = '$ALERT_EMAIL'
msg['Subject'] = 'ALERT: DevPulse is DOWN'
with smtplib.SMTP('127.0.0.1', 25, timeout=10) as s:
    s.sendmail(msg['From'], [msg['To']], msg.as_string())
print('Alert sent')
"
        else
            echo "up" > "$STATUS_FILE"
        fi
    fi
else
    if [ -f "$STATUS_FILE" ] && [ "$(cat $STATUS_FILE)" = "down" ]; then
        # Service recovered - send recovery notice
        python3 -c "
import smtplib
from email.mime.text import MIMEText
msg = MIMEText('DevPulse is back UP and responding normally.')
msg['From'] = 'monitor@byteoven.com'
msg['To'] = '$ALERT_EMAIL'
msg['Subject'] = 'RECOVERED: DevPulse is back UP'
with smtplib.SMTP('127.0.0.1', 25, timeout=10) as s:
    s.sendmail(msg['From'], [msg['To']], msg.as_string())
print('Recovery notice sent')
"
    fi
    echo "up" > "$STATUS_FILE"
fi
