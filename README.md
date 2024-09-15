# OBS Twitch Title Stream Countdown

Appends a countdown timer to your Twitch stream title.

## Setup

1. Create a Twitch application at https://dev.twitch.tv/console/apps
   - OAuth Redirect URL: http://localhost:8000
   - Category: Application Integration
2. Place `obs_twitch_countdown.py` in your OBS scripts folder.
        `C:\Program Files\obs-studio\data\obs-plugins\frontend-tools\scripts`
3. Open `obs_twitch_countdown.py` in a text editor and add your Twitch app credentials:
   ```python
   client_id = "your_client_id_here"
   client_secret = "your_client_secret_here"
   ```
4. In OBS, go to Tools > Scripts and add the script.
5. Configure the script settings:
   - Set stream duration
   - Enter your Twitch channel name
   - Click "Login to Twitch" to authenticate

## Usage

**Enable Script** Toggles the script on/off.

For issues, please open a GitHub issue.
