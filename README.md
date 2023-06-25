# Spotify Controller for ChatGPT

This is a plugin for ChatGPT that allows it to control Spotify. You can play and pause music, search for songs, artists, or albums, add tracks to playlists, and more.

## Installation

1. Clone the repository:
   - `git clone https://github.com/olxver/Spotify-Plugin.git`
2. Navigate to the cloned repository:
   - `cd Spotify-Plugin`
3. Follow the steps in the "Setup" section to configure the plugin.

## Setup

1. **Create a Spotify app**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Click on 'Create an App'
   - Make sure to have the Redirect URI as 'chat.openai.com' or it won't work
   - Fill in the necessary details and create your app

2. **Edit the main.py file**
   - Replace the `SPOTIPY_CLIENT_ID` and `SPOTIPY_CLIENT_SECRET` with your app's Client ID and Client Secret respectively. You can find these in your Spotify app settings.

3. **Run the main.py file**
   - In your terminal, navigate to the directory containing the main.py file and run it using the command `python main.py`

4. **Add the Spotify Plugin to ChatGPT**
   - Go to [ChatGPT](https://chat.openai.com)
   - Click on 'GPT-4 > Plugins'
   - Click on 'Plugin Store'
   - Click on 'Develop Your Own Plugin'
   - Enter 'localhost:5005' and click on 'Install Localhost Plugin'

At this point, the plugin is installed but not yet authenticated with Spotify.

5. **Authenticate the Plugin**
   - In the ChatGPT interface, try a command (e.g., 'pause')
   - You will be redirected to a Spotify authentication page
   - Scroll down and click on 'Agree'
   - You will be redirected back to ChatGPT
   - Copy the entire URL from the address bar. It should look something like this: 'https://chat.openai.com/?code=code_here'
   - Go back to your terminal where you ran the main.py file
   - It should be saying 'Enter the URL you were redirected to:'
   - Paste the URL you copied and press enter

Congratulations! The plugin is now authenticated with Spotify and ready to use. You can ask ChatGPT what it can do with the plugin.

## Issues

If you encounter any bugs or issues, kindly open an issue [here](link-to-your-github-repo-issues).

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)
