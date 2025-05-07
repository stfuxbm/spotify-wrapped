#!/bin/bash
# Create necessary directories
mkdir -p ./dags ./logs ./plugins ./config

# Create .env file with current user's UID
echo -e "AIRFLOW_UID=$(id -u)" > .env

echo "Setup completed! Directories and .env file created."
echo "You can now run: docker compose up -d"