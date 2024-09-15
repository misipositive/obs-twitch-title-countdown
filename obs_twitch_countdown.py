import obspython as obs
import time
import json
import os
import requests
import webbrowser
import threading
import http.server
import socketserver
import socket

# Global variables 
# Add your Twitch application credentials here
client_id = ""  # Your Twitch application client ID
client_secret = ""  # Your Twitch application client secret
redirect_uri = "http://localhost:8000"
access_token = None
channel_name = ""
end_time = 0
update_interval = 60  # 60 seconds interval
auth_initiated = False
script_enabled = False
timer_handle = None

def script_log(message):
    print(f"[Twitch Title Updater] {message}")

def script_description():
    return "Twitch Title Updater"

def script_update(settings):
    global end_time, channel_name, script_enabled
    duration = obs.obs_data_get_int(settings, "duration")
    channel_name = obs.obs_data_get_string(settings, "channel_name")
    script_enabled = obs.obs_data_get_bool(settings, "enable_script")
    end_time = time.time() + (duration * 60)
    toggle_timer(script_enabled)

def script_properties():
    props = obs.obs_properties_create()
    obs.obs_properties_add_int(props, "duration", "Stream Duration (minutes)", 1, 1440, 1)
    obs.obs_properties_add_text(props, "channel_name", "Twitch Channel Name", obs.OBS_TEXT_DEFAULT)
    obs.obs_properties_add_bool(props, "enable_script", "Enable Script")
    obs.obs_properties_add_button(props, "login", "Login to Twitch", login_button_clicked)
    return props

def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('client_id'), config.get('client_secret')
        except json.JSONDecodeError:
            script_log("Error: config.json is not a valid JSON file.")
        except IOError:
            script_log("Error: Unable to read config.json file.")
    else:
        script_log("Config file not found. Please create a config.json file with your client_id and client_secret.")
    return None, None

def script_load(settings):
    global client_id, client_secret, access_token
    client_id, client_secret = load_config()
    if not client_id or not client_secret:
        script_log("Failed to load configuration. Script disabled.")
        return
    access_token = load_access_token()
    script_log("Twitch Title Updater script loaded")

def login_button_clicked(props, prop):
    global auth_initiated
    if not auth_initiated:
        auth_initiated = True
        threading.Thread(target=start_oauth_server).start()
        start_auth()
    else:
        script_log("Authentication already in progress. Please check your browser.")
    return True

def start_auth():
    auth_url = f"https://id.twitch.tv/oauth2/authorize?client_id={client_id}&redirect_uri={redirect_uri}&response_type=code&scope=channel:manage:broadcast"
    webbrowser.open(auth_url)

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

def start_oauth_server():
    global redirect_uri
    port = find_free_port()
    redirect_uri = f"http://localhost:{port}"
    with socketserver.TCPServer(("", port), OAuthHandler) as httpd:
        script_log(f"OAuth server started on port {port}")
        httpd.serve_forever()

class OAuthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if "code=" in self.path:
            code = self.path.split("code=")[1].split("&")[0]
            get_access_token(code)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Authentication successful! You can close this window.")
            threading.Thread(target=self.server.shutdown).start()

    def log_message(self, format, *args):
        script_log(f"{self.address_string()} - - [{self.log_date_time_string()}] {format%args}")

def get_access_token(code):
    global access_token
    token_url = "https://id.twitch.tv/oauth2/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": redirect_uri
    }
    try:
        response = requests.post(token_url, data=data)
        response.raise_for_status()
        access_token = response.json()["access_token"]
        save_access_token(access_token)
        script_log("Successfully logged in!")
    except requests.exceptions.RequestException as e:
        script_log(f"Failed to obtain access token: {e}")

def save_access_token(token):
    token_path = os.path.join(os.path.dirname(__file__), 'access_token.json')
    with open(token_path, 'w') as f:
        json.dump({"access_token": token}, f)

def load_access_token():
    token_path = os.path.join(os.path.dirname(__file__), 'access_token.json')
    if os.path.exists(token_path):
        with open(token_path, 'r') as f:
            data = json.load(f)
            return data.get("access_token")
    return None

def update_title():
    global end_time, access_token
    if not access_token:
        script_log("Not logged in. Please use the Login button to authenticate.")
        return

    remaining = int(end_time - time.time())
    if remaining <= 0:
        toggle_timer(False)
        return

    hours, remainder = divmod(remaining, 3600)
    minutes, seconds = divmod(remainder, 60)
    countdown = f" — Stream ends {hours:02d}:{minutes:02d}:{seconds:02d}"

    user_id = get_user_id()
    if not user_id:
        script_log("Failed to get user ID. Cannot update title.")
        return

    url = f"https://api.twitch.tv/helix/channels?broadcaster_id={user_id}"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Get the current title
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        current_title = response.json()["data"][0]["title"]
    except requests.exceptions.RequestException as e:
        script_log(f"Failed to get current title: {e}")
        return

    # Remove any existing countdown from the current title
    if " — Stream ends" in current_title:
        current_title = current_title.split(" — Stream ends")[0]

    new_title = current_title + countdown

    data = {"title": new_title}
    try:
        response = requests.patch(url, headers=headers, json=data)
        response.raise_for_status()
        script_log(f"Successfully updated title to: {new_title}")
    except requests.exceptions.RequestException as e:
        script_log(f"Failed to update title: {e}")

def get_user_id():
    global channel_name, access_token, client_id
    if not channel_name or not access_token:
        script_log("Channel name or access token not set.")
        return None

    url = f"https://api.twitch.tv/helix/users?login={channel_name}"
    headers = {
        "Client-ID": client_id,
        "Authorization": f"Bearer {access_token}"
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        if data["data"]:
            return data["data"][0]["id"]
        else:
            script_log(f"No user found with username: {channel_name}")
    except requests.exceptions.RequestException as e:
        script_log(f"Failed to get user ID: {e}")
    return None

def toggle_timer(enable):
    global timer_handle
    if enable and timer_handle is None:
        timer_handle = obs.timer_add(update_title, update_interval * 1000)
    elif not enable and timer_handle is not None:
        obs.timer_remove(timer_handle)
        timer_handle = None

def script_unload():
    toggle_timer(False)