# Twitch Title Updater for OBS

This script automatically updates your Twitch stream title with a countdown to the end of your stream.

## Setup

1. Ensure you have a `config.json` file in this folder with your Twitch API credentials:
   ```json
   {
     "client_id": "your_client_id_here",
     "client_secret": "your_client_secret_here"
   }
   ```

2. In OBS, go to Tools > Scripts and add this script.

3. Set your stream duration and Twitch channel name in the script properties.

4. Click the "Login to Twitch" button to authenticate.

## Usage

Once set up, the script will automatically update your stream title with the remaining time.