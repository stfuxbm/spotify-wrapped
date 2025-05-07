#!/bin/bash
# Create necessary directories
mkdir -p ./dags ./logs ./plugins ./config

# Create .env file with current user's UID
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Change ownership and permissions to allow Docker access
sudo chown -R $(id -u):$(id -g) ./dags ./logs ./plugins ./config
sudo chmod -R 775 ./dags ./logs ./plugins ./config

echo "Setup completed! Directories and .env file created."
echo "You can now run: docker compose up -d"
