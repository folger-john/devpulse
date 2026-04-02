#!/bin/bash
cd /home/ubuntu/devpulse
exec python3 -m uvicorn main:app --host 127.0.0.1 --port 8090 --workers 2
