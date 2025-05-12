FROM apache/airflow:2.10.5

# Install system dependencies without root user
USER airflow

# Install system dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Ensure the airflow directories exist and have proper permissions
RUN mkdir -p /opt/airflow/{dags,logs,plugins,config,scripts} \
    && chmod -R 775 /opt/airflow

# Set environment variables
ENV PYTHONPATH=/opt/airflow
WORKDIR /opt/airflow

# Install any python packages 
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Switch back to airflow user (if needed)
USER airflow
