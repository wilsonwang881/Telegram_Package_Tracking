#!/bin/bash

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

echo "Remember to set USPS_TOKEN and TELEGRAM_BOT_TOKEN!"