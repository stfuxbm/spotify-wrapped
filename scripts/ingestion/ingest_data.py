import os
import csv
from datetime import datetime
import spotipy
from spotipy.exceptions import SpotifyException


def fetch_top_tracks():
    """
    Fetches the top 50 tracks of the user in the last 4 weeks,
    retrieves information about each track and saves it to a CSV file.
    """
    try:
        # Coba ambil token dari Airflow Variables
        try:
            from airflow.models import Variable

            ACCESS_TOKEN = Variable.get("SPOTIFY_ACCESS_TOKEN")
            print("Successfully retrieved token from Airflow Variables")
        except Exception as e:
            print(f"Error retrieving token from Airflow Variables: {e}")
            # Fallback ke environment variable jika gagal
            from dotenv import load_dotenv

            load_dotenv()
            ACCESS_TOKEN = os.getenv("SPOTIFY_ACCESS_TOKEN")
            print("Falling back to .env file for token")

        # Pastikan token ada
        if not ACCESS_TOKEN:
            print("Error: Access token not found in Airflow Variables or .env file.")
            return None

        # Initialize Spotify client
        sp = spotipy.Spotify(auth=ACCESS_TOKEN)

        # Define the path for saving the CSV file
        # Check if running in Airflow container
        if os.path.exists("/opt/airflow"):
            # Airflow container path
            DATA_DIR = "/opt/airflow/data"
        else:
            # Local development path
            CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
            PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "../../"))
            DATA_DIR = os.path.join(PROJECT_ROOT, "data")

        # Ensure the directory exists
        os.makedirs(DATA_DIR, exist_ok=True)
        print(f"Using data directory: {DATA_DIR}")

        # Debug periksa apakah direktori dapat ditulis
        print(f"Data directory exists: {os.path.exists(DATA_DIR)}")
        print(f"Data directory is writable: {os.access(DATA_DIR, os.W_OK)}")

        # Remove all existing files before adding new ones
        remove_existing_files(DATA_DIR)

        # Fetch top 50 tracks from Spotify
        top_tracks = sp.current_user_top_tracks(limit=50, time_range="short_term")

        # Collect track data in a list of dictionaries
        top_tracks_data = []
        for idx, track in enumerate(top_tracks["items"], start=1):
            artist_names = ", ".join([artist["name"] for artist in track["artists"]])
            artist_id = track["artists"][0]["id"]
            artist_info = sp.artist(artist_id)
            genres = ", ".join(artist_info["genres"])
            track_info = {
                "rank": idx,
                "track_name": track["name"],
                "artists": artist_names,
                "genres": genres,
            }
            top_tracks_data.append(track_info)

        # Save the data to a CSV file with a timestamp
        timestamp = datetime.now().strftime("%d%m%Y_%H%M%S")
        filename = os.path.join(DATA_DIR, f"top_tracks_{timestamp}.csv")

        # Write track data to the CSV file
        with open(filename, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(
                file, fieldnames=["rank", "track_name", "artists", "genres"]
            )
            writer.writeheader()  # Write header once
            writer.writerows(top_tracks_data)

        print(f"Data saved successfully to: {filename}")
        print(f"Saving data to: {DATA_DIR}")
        return filename  # Return the filename for debugging or further use

    except SpotifyException as e:
        # Handle different types of Spotify API exceptions
        if e.http_status == 401:
            print("Error: Invalid or expired access token.")
            print(
                "Tip: Refresh your token using the refresh_token in your .env file or update Airflow Variable."
            )
        else:
            print(f"Error: An unexpected Spotify error occurred - {e}")
        return None

    except Exception as e:
        # Catch any other unforeseen exceptions
        print(f"Error: An unexpected error occurred - {e}")
        print(f"Error type: {type(e)}")
        import traceback

        print(f"Traceback: {traceback.format_exc()}")
        return None


def remove_existing_files(directory):
    """
    Remove all files from the specified directory.
    """
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if os.path.isfile(file_path):
            print(f"Removing existing file: {file_path}")
            os.remove(file_path)
