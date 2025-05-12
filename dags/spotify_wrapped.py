from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime
import os
import sys

# Tentukan path untuk import
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from scripts.ingestion.ingest_data import fetch_top_tracks


# Debug task untuk melihat lingkungan
def debug_environment():
    import os
    import sys

    print(f"Current directory: {os.getcwd()}")
    print(f"Python path: {sys.path}")
    print(f"Environment variables: {dict(os.environ)}")
    print(f"/opt/airflow exists: {os.path.exists('/opt/airflow')}")
    print(f"/opt/airflow/data exists: {os.path.exists('/opt/airflow/data')}")

    # Coba akses Airflow variable
    try:
        from airflow.models import Variable

        token = Variable.get("SPOTIFY_ACCESS_TOKEN", default_var=None)
        print(f"Token exists in Airflow variables: {bool(token)}")
    except Exception as e:
        print(f"Error accessing Airflow variables: {e}")


# Task untuk inisialisasi
def initialization():
    """Initialize the environment for data ingestion"""
    # Pastikan direktori data ada
    data_dir = "/opt/airflow/data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"Created data directory: {data_dir}")
    else:
        print(f"Data directory already exists: {data_dir}")

    # Periksa token Spotify
    try:
        from airflow.models import Variable

        token = Variable.get("SPOTIFY_ACCESS_TOKEN")
        if token:
            print("Spotify access token verified in Airflow variables")
            return {"status": "success"}
        else:
            print("Spotify access token is empty in Airflow variables")
            return {"status": "error", "message": "Empty Spotify token"}
    except Exception as e:
        print(f"Error verifying Spotify access token: {e}")
        return {"status": "error", "message": str(e)}


# Task untuk menyimpan data ke staging area
def save_to_staging(**context):
    """Save the data to staging area"""
    # Mendapatkan path file CSV dari task sebelumnya
    ti = context["ti"]
    csv_path = ti.xcom_pull(task_ids="fetch_top_tracks_task")

    if not csv_path:
        print("No CSV file path received from fetch_top_tracks_task")
        return {"status": "error", "message": "No CSV file path"}

    print(f"Received CSV file path: {csv_path}")

    # Periksa apakah file CSV ada
    if not os.path.exists(csv_path):
        print(f"CSV file does not exist: {csv_path}")
        return {"status": "error", "message": "CSV file not found"}

    # Disini Anda dapat menambahkan logika untuk memindahkan atau memproses file
    # ke staging area (misalnya database, S3, dll)
    print(f"Processing {csv_path} to staging area...")

    # Contoh: hanya mengkonfirmasi file telah dibaca
    with open(csv_path, "r", encoding="utf-8") as f:
        rows_count = sum(1 for _ in f) - 1  # Kurangi 1 untuk header

    print(f"Successfully processed {rows_count} tracks to staging area")
    return {"status": "success", "rows_processed": rows_count}


default_args = {
    "owner": "braiyenmassora",
    "start_date": datetime(2025, 5, 12),
    "retries": 1,
}

dag = DAG(
    "spotify_wrapped",
    default_args=default_args,
    description="Fetch top tracks from Spotify",
    schedule_interval=None,
    catchup=False,
)

# Debug task
debug_task = PythonOperator(
    task_id="debug_environment",
    python_callable=debug_environment,
    dag=dag,
)

# Initialization task
initialization_task = PythonOperator(
    task_id="initialization_task",
    python_callable=initialization,
    dag=dag,
)

# Fetch task
fetch_top_tracks_task = PythonOperator(
    task_id="fetch_top_tracks_task",
    python_callable=fetch_top_tracks,
    dag=dag,
)

# Save to staging task
save_to_staging_task = PythonOperator(
    task_id="save_to_staging_task",
    python_callable=save_to_staging,
    provide_context=True,
    dag=dag,
)

# Set task dependencies
debug_task >> initialization_task >> fetch_top_tracks_task >> save_to_staging_task
