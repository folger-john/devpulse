#!/bin/bash
cd /home/ubuntu/devpulse
set -a; source .env 2>/dev/null; set +a
exec python3 -m uvicorn main:app --host 127.0.0.1 --port 8090 --workers 2
