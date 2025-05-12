import base64
import requests
import urllib.parse
import webbrowser
import os
from dotenv import load_dotenv


load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SCOPE = "user-top-read"
ENV_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"
)


def generate_auth_url():
    """
    Generates the Spotify authorization URL with the required parameters.
    Returns the URL as a string.
    """
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": SCOPE,
        "show_dialog": "true",
    }
    return "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)


def get_authorization_code():
    """
    Directs the user to the authorization URL and asks them to input the authorization code
    after logging in via their browser.
    """
    auth_url = generate_auth_url()
    print("Please open the URL in your browser to log in and authorize Spotify access:")
    print(auth_url)

    try:
        webbrowser.open(auth_url)
    except Exception as e:
        print(f"Failed to open browser automatically: {e}")

    print("\nAfter logging in, you will be redirected to the callback URL.")
    code = input(
        "Please copy the 'code' parameter from the callback URL and paste it here: "
    ).strip()
    return code


def exchange_code_for_token(code):
    """
    Exchanges the authorization code for an access token and a refresh token from Spotify.
    Returns the token response as a dictionary.
    """
    token_url = "https://accounts.spotify.com/api/token"
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()

    headers = {
        "Authorization": f"Basic {auth_header}",
        "Content-Type": "application/x-www-form-urlencoded",
    }

    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
    }

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code != 200:
        print(f"Failed to get token. Status code: {response.status_code}")
        print("Response:", response.text)
        response.raise_for_status()

    return response.json()


def update_env_file(access_token, refresh_token):
    """
    Updates the .env file with the new access token and refresh token.
    If the variables already exist, it will update them; otherwise, it will add them.
    """
    lines = []
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE, "r") as file:
            lines = file.readlines()

    def set_or_update(var_name, var_value):
        nonlocal lines
        found = False
        for i, line in enumerate(lines):
            if line.startswith(f"{var_name}="):
                lines[i] = f'{var_name}="{var_value}"\n'
                found = True
                break
        if not found:
            lines.append(f'{var_name}="{var_value}"\n')

    set_or_update("SPOTIFY_ACCESS_TOKEN", access_token)
    set_or_update("SPOTIFY_REFRESH_TOKEN", refresh_token)

    with open(ENV_FILE, "w") as file:
        file.writelines(lines)

    print(f"Tokens successfully saved to {ENV_FILE}")


def load_tokens_from_env():
    """
    Loads the access token and refresh token from the .env file and prints them.
    """
    load_dotenv(override=True)
    access_token = os.getenv("SPOTIFY_ACCESS_TOKEN")
    refresh_token = os.getenv("SPOTIFY_REFRESH_TOKEN")

    if access_token and refresh_token:
        print("Tokens loaded from .env file:")
        print(f"Access Token: {access_token}")
        print(f"Refresh Token: {refresh_token}")
    else:
        print("Failed to load tokens from .env file.")

    return access_token, refresh_token


def main():
    """
    Main function that orchestrates the Spotify authorization flow and token management.
    """
    code = get_authorization_code()
    token_info = exchange_code_for_token(code)

    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")

    if not access_token:
        print("Access token not found in the response.")
        return

    print(f"Access token received:\n{access_token}")
    print(f"\nRefresh token:\n{refresh_token}")

    update_env_file(access_token, refresh_token)
    load_tokens_from_env()


if __name__ == "__main__":
    main()
