#!/bin/bash

set -e

SERVICE_FILE="api_finance.service"

if [ ! -f "$SERVICE_FILE" ]; then
    echo "Service file '$SERVICE_FILE' not found!"
    exit 1
fi

echo "Copying $SERVICE_FILE to /etc/systemd/system/"
sudo cp "$SERVICE_FILE" /etc/systemd/system/

echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling service..."
sudo systemctl enable "$SERVICE_FILE"

echo "Starting service..."
sudo systemctl start "$SERVICE_FILE"

echo "Service installed and started successfully."