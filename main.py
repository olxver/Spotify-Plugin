
import asyncio
import quart
import quart_cors
import os
from quart import request
import requests

import spotipy
from spotipy.oauth2 import SpotifyOAuth

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")
os.environ["SPOTIPY_CLIENT_ID"] = "ENTER_YOUR_APPS_CLIENT_ID_HERE"
os.environ["SPOTIPY_REDIRECT_URI"] = "https://chat.openai.com"
os.environ["SPOTIPY_CLIENT_SECRET"] = "ENTER_YOUR_APPS_CLIENT_SECRET_HERE"
scope = [
    "ugc-image-upload",
    "user-read-recently-played",
    "user-top-read",
    "user-read-playback-position",
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "app-remote-control",
    "streaming",
    "playlist-modify-public",
    "playlist-modify-private",
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-follow-modify",
    "user-follow-read",
    "user-library-modify",
    "user-library-read",
    "user-read-email",
    "user-read-private"
]


class spotipy_client(spotipy.Spotify):
    def set_volume(self, volume, device_id=None, confirm=None):
        """ Sets the volume for the given device.
        
        Parameters:
            - volume - the volume to set. Must be a value from 0 to 100 inclusive.
            - device_id - the id of the device this command is targeting. 
                        If not supplied, the user's currently active device is the target.
            - confirm - a confirmation to set the volume above 75. Must be 'y' to confirm.
        """
        if volume > 75 and confirm != 'y':
            return {"warning": "WARNING: Setting the user's volume to over 75% could possibly damage their ears. Please confirm this with the user. If confirmed, use 'confirm=y' in your request. ALWAYS check."}

        if not device_id:
            device_id = self.current_playback()['device']['id']
        self._put(f"me/player/volume?volume_percent={volume}&device_id={device_id}")
        return {}  # return an empty dictionary if there's no warning




sp = spotipy_client(auth_manager=SpotifyOAuth(scope=scope))

from quart import redirect
sp_oauth = sp.auth_manager
_TOKENS = {}
def save_access_token(username, access_token):
    # This is a simple in-memory dictionary to store tokens. In a real application, 
    # you'd want to use a secure and persistent storage for these tokens.
    if username not in _TOKENS:
        _TOKENS[username] = []
    _TOKENS[username].append(access_token)


@app.route('/callback')
async def callback():
    error = request.args.get('error')
    code = request.args.get('code')
    if error is not None:
        # Handle the error in your own way
        print(f"Error in Spotify OAuth: {error}")
        return redirect('http://chat.openai.com')
    if code is not None:
        # Exchange the code for a token
        token_info = sp_oauth.get_access_token(code)
        access_token = token_info['access_token']
        # Save this access token in your server for future requests
        save_access_token(access_token)
        return redirect('http://chat.openai.com')
    else:
        print("No code or error received from Spotify OAuth")
        return redirect('http://chat.openai.com')
    

@app.get("/track_info")
async def track_info():
    try:
        # Get the current playing track from Spotify
        current_track = sp.current_user_playing_track()

        # If there's no track currently playing, return an error
        if current_track is None or current_track['item'] is None:
            return quart.Response(response='No track is currently playing', status=400)

        # Get the Spotify ID of the current track
        track_id = current_track['item']['id']

        # Use the Spotify Web API to get more information about the track
        track_info = sp.track(track_id)

        # Return the track information
        return quart.jsonify(track_info)

    except Exception as e:
        print(f"Exception while getting track info: {e}")
        return quart.Response(response=str(e), status=500)


@app.post("/resume")
async def resume():
    try:
        sp.start_playback()

        return quart.Response(response='OK', status=200)
    except Exception as exc:
        return quart.Response(response=str(exc), status=400)

@app.post("/search")
async def search():
    data = await request.get_json()
    query = data.get('query', None)
    if not query:
        return quart.Response(response='No query provided', status=400)

    try:
        # Search for the track, artist, and album on Spotify
        results = sp.search(q=query, type='track,artist,album', limit=5)  # We're asking for up to 5 results

        # Extract the track, artist, and album details
        tracks = [{"name": track["name"], 
                   "artist": track["artists"][0]["name"], 
                   "album": track["album"]["name"],
                   "uri": track["uri"]} for track in results['tracks']['items']]

        artists = [{"name": artist["name"], 
                    "uri": artist["uri"]} for artist in results['artists']['items']]

        albums = [{"name": album["name"], 
                   "artist": album["artists"][0]["name"], 
                   "uri": album["uri"]} for album in results['albums']['items']]

        return quart.jsonify({"tracks": tracks, "artists": artists, "albums": albums})

    except Exception as e:
        print(f"Exception while searching: {e}")
        return quart.Response(response=str(e), status=500)

@app.post("/playlists/<playlist_id>/tracks")
async def add_track_to_playlist(playlist_id: str):
    data = await request.get_json()
    track_uri = data.get('track_uri', None)
    if not track_uri:
        return quart.Response(response='No track URI provided. Ask the user what song, then search for it.', status=400)

    try:
        # Add the track to the playlist
        sp.user_playlist_add_tracks(user='spotify', playlist_id=playlist_id, tracks=[track_uri])
        return quart.jsonify({"message": "Track added to playlist successfully"})

    except Exception as e:
        # Print the full exception stack trace
        import traceback
        print(traceback.format_exc())

        # Log the request details
        print(f"Request details: playlist_id={playlist_id}, track_uri={track_uri}")

        return quart.Response(response=str(e), status=500)

@app.get("/playlists")
async def get_playlists():
    try:
        # Get the user's playlists
        playlists = sp.current_user_playlists()
        return quart.jsonify(playlists)

    except Exception as e:
        print(f"Exception while getting playlists: {e}")
        return quart.Response(response=str(e), status=500)


@app.post("/skip")
async def skip():
    try:
        sp.next_track()
        await asyncio.sleep(3)
        # Get the current playing track from Spotify
        current_track = sp.current_playback()

        # If there's no track currently playing, return an error
        if current_track is None or current_track['item'] is None:
            return quart.Response(response='No track is currently playing', status=400)

        # Add extra information for the assistant
        extra_info = "The song was successfully skipped. Here is the current track now playing."

        # Return the entire current_track information along with the extra information
        return quart.jsonify({"current_track": current_track, "extra_information_to_assistant": extra_info})
    except Exception as e:
        print(f"Exception while skipping track: {e}")
        return quart.Response(response=str(e), status=500)


@app.post("/set_volume")
async def set_volume():
    data = await request.get_json()
    volume = data.get('volume', None)
    device_id = data.get('device_id', None)
    confirm = data.get('confirm', None)

    if volume is None:
        return quart.Response(response='No volume provided', status=400)

    try:
        response = sp.set_volume(volume, device_id, confirm)
        if "warning" in response:
            return quart.jsonify(response), 400
        return quart.Response(response=f'Set volume to {volume}', status=200)
    
    except Exception as e:
        print(f"Exception while setting volume: {e}")
        return quart.Response(response=str(e), status=500)


    
@app.post("/previous")
async def previous():
    try:
        sp.previous_track()
        return quart.Response(response='OK', status=200)
    except Exception as e:
        print(f"Exception while going to previous track: {e}")
        return quart.Response(response=str(e), status=500)

@app.get("/currently_playing")
async def currently_playing():
    try:
        # Get the current playing track from Spotify
        current_track = sp.current_playback()

        # If there's no track currently playing, return an error
        if current_track is None or current_track['item'] is None:
            return quart.Response(response='No track is currently playing', status=400)

        # Add extra information for the assistant
        extra_info = "Tell the user the device playing the song, the song's name, album, artist, length (in minutes:seconds), current timestamp (in minutes:seconds), and remember the uri for later use, incase. Make sure to hyperlink the song, and artist to Spotify's links."

        # Return the entire current_track information along with the extra information
        return quart.jsonify({"current_track": current_track, "extra_information_to_assistant": extra_info})

    except Exception as e:
        print(f"Exception while getting current playing track: {e}")
        return quart.Response(response=str(e), status=500)





@app.post("/playplaylist")
async def playplaylist():
    data = await request.get_json()
    context_uri = data.get('context_uri', None)
    try:
        if context_uri:
            sp.start_playback(context_uri=context_uri)
            return quart.Response(response='OK', status=200)
        else:
            return quart.Response(response='No playlist provided', status=400)
    except Exception as e:
        print(f"Exception while playing playlist: {e}")
        return quart.Response(response=str(e), status=500)


@app.get("/track")
async def get_track():
    track_id = request.args.get('track_id', None)
    if not track_id:
        return quart.Response(response='No track id provided', status=400)

    try:
        # Get the track from Spotify
        track = sp.track(track_id)

        # Extract the track name, artist, and album
        track_name = track['name']
        artist_name = track['artists'][0]['name']
        album_name = track['album']['name']

        return quart.jsonify({
            "track_name": track_name,
            "artist_name": artist_name,
            "album_name": album_name
        })

    except Exception as e:
        print(f"Exception while getting track: {e}")
        return quart.Response(response=str(e), status=500)



@app.post("/playsong")
async def playsong():
    data = await request.get_json()
    print(data)
    context_uri = data.get('context_uri', None)
    print(context_uri)
    try:
        if context_uri:
            print("Context URI:", context_uri) # print the context_uri
            response = sp.start_playback(uris=[context_uri])  
        else:
            response = sp.start_playback()
        print(response)
        return quart.Response(response='OK', status=200)
    except Exception as e:
        print(f"Exception while starting playback: {e}")
        return quart.Response(response=str(e), status=500)




@app.post("/pause")
async def pause():
    sp.pause_playback()
    return quart.Response(response='OK', status=200)

@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")

def main():
    app.run(debug=True, host="0.0.0.0", port=5005)

if __name__ == "__main__":
    main()
