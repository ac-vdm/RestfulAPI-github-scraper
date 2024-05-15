#!/usr/bin/env bash
SCRIPT="github_api.py"
TIMEOUT=30
PORT=23467
export GITHUB_API_PORT=$PORT
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python $SCRIPT &
while ! $(curl -s localhost:$PORT > /dev/null) && [ $TIMEOUT -gt 0 ]
do sleep 1; ((TIMEOUT--)); done
pkill -f $SCRIPT
deactivate
if [ $TIMEOUT -gt 0 ]; then echo "Verified"; else echo "Failed"; fi