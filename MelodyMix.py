from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import random
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask_socketio import SocketIO, emit
from uuid import uuid4
import requests
from werkzeug.security import generate_password_hash, check_password_hash
import googleapiclient.discovery
from textblob import TextBlob
import re
from spotipy.exceptions import SpotifyException  
import os
from werkzeug.utils import secure_filename

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'your-default-secret')
socketio = SocketIO(app)

UPLOAD_FOLDER = 'static/audio'
ALLOWED_EXTENSIONS = {'mp3', 'mp4'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

SPOTIPY_CLIENT_ID = os.environ.get('SPOTIPY_CLIENT_ID')
SPOTIPY_CLIENT_SECRET = os.environ.get('SPOTIPY_CLIENT_SECRET')
SPOTIPY_REDIRECT_URI = os.environ.get('SPOTIPY_REDIRECT_URI', 'http://127.0.0.1:5000/callback')

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIPY_CLIENT_ID,
    client_secret=SPOTIPY_CLIENT_SECRET,
    redirect_uri=SPOTIPY_REDIRECT_URI,
    scope="user-library-read user-read-playback-state user-modify-playback-state"
))

LASTFM_API_KEY = os.environ.get('LASTFM_API_KEY')
LASTFM_API_URL = "https://ws.audioscrobbler.com/2.0/"

YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"

def fetch_lastfm_data(method, params):
    params["api_key"] = LASTFM_API_KEY
    params["format"] = "json"
    params["method"] = method
    response = requests.get(LASTFM_API_URL, params=params)
    
    print(f"Request URL: {response.url}") 
    print(f"Response Status Code: {response.status_code}") 
    print(f"Response Content: {response.text}") 

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to fetch data from Last.fm: {response.status_code}"}

def search_youtube(query):
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey='AIzaSyBtsXjdbjQAsSZRNv_Gljs7pcgx2B7FOfs')
    request = youtube.search().list(
        part="snippet",
        q=query,
        type="video",
        maxResults=10
    )
    response = request.execute()
    results = []
    for item in response["items"]:
        results.append({
            "title": item["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}",
            "thumbnail": item["snippet"]["thumbnails"]["default"]["url"]
        })
    return results

def correct_spelling(query):
    blob = TextBlob(query)
    return str(blob.correct())

users = {}


recommended_music = [
    {"title": "HIGHEST IN THE ROOM", "artist": "Travis Scott"},
    {"title": "Like That", "artist": "Tatiana Manois"},
    {"title": "Jeje", "artist": "Diamond Platnumz"},
    {"title": "Mi Gente", "artist": "J Balvin"}
]

playlists = {}
user_preferences = {}
public_playlists = []
comments = {}

available_songs = [
    {"title": "Jealous", "artist": "DJ Khaled Ft Chris Brown, Big Sean, Lil Wayne", "url": "/static/audio/DJ_Khaled_Ft_Chris_Brown_Big_Sean_Lil_Wayne_-_Jealous_Offblogmedia.com (1) - Copy - Copy.mp3"},
    {"title": "Bailadila", "artist": "O2SRK Remix", "url": "/static/audio/04. Bailadila - O2SRK Remix.mp3"},
    {"title": "Desi Girl", "artist": "DJ VASIM", "url": "/static/audio/8. DESI GIRL (REMIX) - DJ VASIM.mp3"},
    {"title": "It's Time to Disco", "artist": "DJ VASIM", "url": "/static/audio/10. ITS TIME TO DISCO (REMIX) - DJ VASIM.mp3"},
    {"title": "Glock in My Lap", "artist": "21 Savage & Metro Boomin", "url": "/static/audio/21_Savage_Metro_Boomin_-_Glock_in_My_Lap_Offblogmedia.com.mp3"},
    {"title": "Runnin", "artist": "21 Savage & Metro Boomin", "url": "/static/audio/21_Savage_Metro_Boomin_-_Runnin_Offblogmedia.com.mp3"},
    {"title": "Baby By Me", "artist": "50 Cent Ft Ne-Yo", "url": "/static/audio/50_Cent_Ft_Ne-Yo_-_Baby_By_Me_Offblogmedia.com - Copy - Copy.mp3"},
    {"title": "Candy Shop", "artist": "50 Cent Ft Olivia", "url": "/static/audio/50_Cent_Ft_Olivia_-_Candy_Shop_Offblogmedia.com.mp3"},
    {"title": "Me Too", "artist": "Abigail Chams & Harmonize", "url": "/static/audio/Abigail_Chams_Harmonize_-_Me_Too_Offblogmedia.com.mp3"},
    {"title": "Body 2 Body", "artist": "Ace Hood Ft Chris Brown", "url": "/static/audio/Ace_Hood_Ft_Chris_Brown_-_Body_2_Body_Offblogmedia.com - Copy - Copy.mp3"},
    {"title": "Drunk in Love", "artist": "Beyoncé Ft Jay-Z", "url": "/static/audio/Beyonc_Ft_Jay-Z_-_Drunk_in_Love_Offblogmedia.com.mp3"},
    {"title": "Upgrade U", "artist": "Beyoncé Ft Jay-Z", "url": "/static/audio/Beyonc_Ft_JAY-Z_-_Upgrade_U_Offblogmedia.com.mp3"},
    {"title": "Baby Boy", "artist": "Beyoncé Ft Sean Paul", "url": "/static/audio/Beyonc_Ft_Sean_Paul_-_Baby_Boy_Offblogmedia.com.mp3"},
    {"title": "Can't Leave Em Alone", "artist": "Ciara Ft 50 Cent", "url": "/static/audio/Ciara_Ft_50_Cent_-_Cant_Leave_Em_Alone_Offblogmedia.com.mp3"},
    {"title": "Nimekubali", "artist": "Diamond Platnumz", "url": "/static/audio/Diamond-Platnumz-Nimekubali-(Vistanaij.com).mp3"}
]

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        #
        if password != confirm_password:
            return "Passwords do not match!", 400

        
        if username in users:
            return "Username already exists!", 400

        
        users[username] = {
            'email': email,
            'password': generate_password_hash(password)
        }

    
        return redirect(url_for('dashboard'))

    return render_template('Signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        
        user = users.get(username)
        if not user or not check_password_hash(user['password'], password):
            return "Invalid username or password!", 400

        
        session['username'] = username
        return redirect(url_for('dashboard'))

    return render_template('Login.html')

@app.route('/dashboard')
def dashboard():
    
    if 'username' in session:
        return f"Welcome to MelodyMix, {session['username']}! Here is your app content."

    
    if len(users) > 0:
        return "Welcome to MelodyMix! You can access the app content as a guest since you have signed up."

    
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/recommend', methods=['GET'])
def recommend_music():
    return jsonify(recommended_music)

@app.route('/create_playlist', methods=['POST'])
def create_playlist():
    data = request.json
    user = data.get("user")
    playlist_name = data.get("playlist_name")

    if not user or not playlist_name:
        return jsonify({"error": "Invalid data"}), 400

    playlists.setdefault(user, []).append({"name": playlist_name, "songs": []})
    return jsonify({"message": "Playlist created successfully!"})

@app.route('/add_to_playlist', methods=['POST'])
def add_to_playlist():
    data = request.json
    user = data.get("user")
    playlist_name = data.get("playlist_name")
    song = data.get("song")

    if not user or not playlist_name or not song:
        return jsonify({"error": "Invalid data"}), 400

    user_playlists = playlists.setdefault(user, [])
    for playlist in user_playlists:
        if playlist["name"] == playlist_name:
            playlist["songs"].append(song)
            return jsonify({"message": f"Song '{song['title']}' added to playlist '{playlist_name}'!"})

    return jsonify({"error": "Playlist not found"}), 404

@app.route('/generate_smart_playlist', methods=['POST'])
def generate_smart_playlist():
    data = request.json
    mood = data.get("mood")
    activity = data.get("activity")

    
    generated_playlist = [
        {"title": "Uplifting Song 1", "artist": "Artist A", "url": "/static/audio/song1.mp3"},
        {"title": "Relaxing Song 2", "artist": "Artist B", "url": "/static/audio/song2.mp3"},
        {"title": "Energetic Song 3", "artist": "Artist C", "url": "/static/audio/song3.mp3"}
    ]

    return jsonify({"playlist": generated_playlist})

@app.route('/collaborate_playlist', methods=['POST'])


 
@app.route('/shared_listening', methods=['GET'])
def shared_listening():
    shared_playlist = random.sample(recommended_music, min(len(recommended_music), 5))
    return jsonify({"shared_playlist": shared_playlist})

@app.route('/live_preview', methods=['POST'])
def live_preview():
    data = request.json
    song = data.get("song")
    return jsonify({"message": f"Now previewing: {song}"})

@app.route('/track_analytics', methods=['GET'])
def track_analytics():
    analytics = {
        "most_played": "Song 1",
        "total_playtime": "3 hours 45 minutes"
    }
    return jsonify(analytics)

@app.route('/sync_cross_platform', methods=['POST'])
def sync_cross_platform():
    return jsonify({"message": "Playlists synced across platforms"})

@app.route('/playlist_challenges', methods=['GET'])
def playlist_challenges():
    challenges = ["Create a 10-song workout playlist", "Find 3 songs from new artists"]
    return jsonify(challenges)

@app.route('/share_playlist', methods=['POST'])
def share_playlist():
    data = request.json
    user = data.get("user")
    playlist_name = data.get("playlist_name")
    share_type = data.get("share_type")

    if not user or not playlist_name or not share_type:
        return jsonify({"error": "Invalid data"}), 400

    user_playlists = playlists.get(user, [])
    for playlist in user_playlists:
        if playlist["name"] == playlist_name:
            if share_type == "public":
                public_playlists.append(playlist)
                return jsonify({"message": f"Playlist '{playlist_name}' shared publicly!"})
            elif share_type == "private":
                share_id = str(uuid4())
                return jsonify({"message": f"Shareable link created!", "link": f"http://localhost:5000/shared_playlist/{share_id}"})

    return jsonify({"error": "Playlist not found"}), 404

@app.route('/shared_playlist/<share_id>', methods=['GET'])
def shared_playlist(share_id):
    
    return jsonify({"message": f"Accessing shared playlist with ID: {share_id}"})

@app.route('/share_playlist/<playlist_id>', methods=['GET'])
def share_playlist_get(playlist_id):
    playlist = playlists.get(playlist_id)
    if not playlist:
        return jsonify({"error": "Playlist not found"}), 404
    return jsonify({"playlist": playlist})

@app.route('/voice_control', methods=['POST'])
def voice_control():
    return jsonify({"message": "Voice command received!"})

@app.route('/voice_playlist', methods=['POST'])
def voice_playlist():
    data = request.json
    command = data.get("command")

    if not command:
        return jsonify({"error": "No voice command provided"}), 400

    
    if "happy" in command:
        mood = "happy"
    elif "relaxed" in command:
        mood = "relaxed"
    else:
        mood = "default"

   
    generated_playlist = [
        {"title": "Happy Song 1", "artist": "Artist A", "url": "/static/audio/song1.mp3"},
        {"title": "Happy Song 2", "artist": "Artist B", "url": "/static/audio/song2.mp3"}
    ] if mood == "happy" else [
        {"title": "Relaxing Song 1", "artist": "Artist C", "url": "/static/audio/song3.mp3"}
    ]

    return jsonify({"playlist": generated_playlist})

@app.route('/advanced_search', methods=['GET'])
def advanced_search():
    return jsonify({"message": "Advanced search results displayed!"})

@app.route('/offline_mode', methods=['POST'])
def offline_mode():
    return jsonify({"message": "Offline mode activated!"})

@app.route('/dynamic_cover_art', methods=['GET'])
def dynamic_cover_art():
    return jsonify({"message": "Custom animated playlist artwork applied!"})

@app.route('/lyrics_integration', methods=['GET'])
def lyrics_integration():
    return jsonify({"message": "Lyrics displayed!"})

@app.route('/music_gamification', methods=['GET'])
def music_gamification():
    return jsonify({"message": "Achievements unlocked!"})

@app.route('/search_songs', methods=['GET'])
def search_songs():
    query = request.args.get('query')

    if not query or query.strip() == "":
        return jsonify({"error": "Query parameter is required"}), 400

    # Search on Spotify
    spotify_results = sp.search(q=query, type='track', limit=5)
    spotify_songs = [
        {
            "title": item['name'],
            "artist": ", ".join(artist['name'] for artist in item['artists']),
            "url": item['external_urls']['spotify'],
            "id": item['id']
        }
        for item in spotify_results['tracks']['items']
    ]

    # Search on YouTube
    youtube_results = search_youtube(query)
    youtube_songs = [
        {
            "title": item['title'],
            "url": item['url'],
            "thumbnail": item['thumbnail']
        }
        for item in youtube_results
    ]

    return jsonify({"spotify_songs": spotify_songs, "youtube_songs": youtube_songs})

@app.route('/playlist_analytics', methods=['GET'])
def playlist_analytics():
    user = request.args.get('user')
    if not user or user not in playlists:
        return jsonify({"error": "User not found"}), 404

    user_playlists = playlists[user]
    analytics = []
    for playlist in user_playlists:
        total_songs = len(playlist["songs"])
        total_playtime = f"{total_songs * 3} minutes" 
        analytics.append({
            "playlist_name": playlist["name"],
            "total_songs": total_songs,
            "total_playtime": total_playtime
        })

    return jsonify({"analytics": analytics})

@app.route('/download_playlist/<playlist_name>', methods=['GET'])
def download_playlist(playlist_name):
    user = request.args.get('user')
    if not user or user not in playlists:
        return jsonify({"error": "User not found"}), 404

    user_playlists = playlists[user]
    for playlist in user_playlists:
        if playlist["name"] == playlist_name:
           
            downloaded_songs = playlist["songs"]
            return jsonify({"message": f"Playlist '{playlist_name}' downloaded successfully!", "songs": downloaded_songs})

    return jsonify({"error": "Playlist not found"}), 404

@app.route('/public_playlists', methods=['GET'])
def get_public_playlists():
    return jsonify({"public_playlists": public_playlists})

@app.route('/artist_info', methods=['GET'])
def artist_info():
    artist = request.args.get('artist')

    if not artist:
        return jsonify({"error": "Artist is required"}), 400

    
    corrected_artist = correct_spelling(artist)
    print(f"Original Artist: {artist}, Corrected Artist: {corrected_artist}")

    
    data = fetch_lastfm_data("artist.getInfo", {"artist": corrected_artist})
    
    if "error" in data:
        return jsonify({"error": data["error"]}), 500  

    return jsonify({"artist_info": data, "corrected_artist": corrected_artist})

@app.route('/track_metadata', methods=['GET'])
def track_metadata():
    track = request.args.get('track')
    artist = request.args.get('artist')

    if not track or not artist:
        return jsonify({"error": "Track and artist are required"}), 

   
    data = fetch_lastfm_data("track.getInfo", {"track": track, "artist": artist})
    return jsonify(data)

@app.route('/search_web', methods=['GET'])
def search_web():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 

    youtube_results = search_youtube(query)
    return jsonify({"youtube_results": youtube_results})

@app.route('/search_youtube', methods=['GET'])
def search_youtube_route():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}),

    youtube_results = search_youtube(query)  
    return jsonify({"youtube_results": youtube_results})

@app.route('/get_playlists', methods=['GET'])
def get_playlists():
   
    return jsonify({"playlists": []}), 

@app.route('/embed_playlist/<playlist_name>', methods=['GET'])
def embed_playlist(playlist_name):
    user = request.args.get('user')
    if not user or user not in playlists:
        return jsonify({"error": "User not found"}), 

    user_playlists = playlists[user]
    for playlist in user_playlists:
        if playlist["name"] == playlist_name:
            embed_code = f"""
            <iframe src="http://localhost:5000/shared_playlist/{playlist_name}" width="300" height="380" frameborder="0" allow="autoplay; clipboard-write; encrypted-media; picture-in-picture"></iframe>
            """
            return jsonify({"embed_code": embed_code})
    comment = request.args.get('comment')
    if not playlist_name or not comment:
        return jsonify({"error": "Invalid data"}), 400

    comments.setdefault(playlist_name, []).append(comment)
    return jsonify({"message": "Comment added successfully!"})

@app.route('/get_comments/<playlist_name>', methods=['GET'])
def get_comments(playlist_name):
    return jsonify({"comments": comments.get(playlist_name, [])})

@app.route('/search_spotify', methods=['GET'])
def search_spotify():
    query = request.args.get('query')
    if not query:
        return jsonify({"error": "Query parameter is required"}), 400

    results = sp.search(q=query, type='track', limit=10)
    tracks = []
    for item in results['tracks']['items']:
        tracks.append({
            "title": item['name'],
            "artist": ", ".join(artist['name'] for artist in item['artists']),
            "url": item['external_urls']['spotify'],
            "id": item['id']
        })
    return jsonify({"tracks": tracks})

@app.route('/play_track', methods=['POST'])
def play_track():
    data = request.json
    track_uri = data.get('track_uri')

    if not track_uri:
        return jsonify({"error": "Track URI is required"}), 400

    try:
        sp.start_playback(uris=[track_uri])
        return jsonify({"message": "Track is now playing!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/save_playlist', methods=['POST'])
def save_playlist():
    data = request.json
    playlist_name = data.get('playlist_name')
    songs = data.get('songs')

    if not playlist_name or not songs:
        return jsonify({"error": "Playlist name and songs are required"}), 400

    
    if playlist_name in playlists:
        return jsonify({"error": "Playlist with this name already exists"}), 400

    playlists[playlist_name] = songs
    return jsonify({"message": f"Playlist '{playlist_name}' saved successfully!"})

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({"message": f"File '{filename}' uploaded successfully!"}), 200

    return jsonify({"error": "Invalid file type. Only MP3 and MP4 files are allowed."}), 400

@app.route('/available_songs', methods=['GET'])
def get_available_songs():
    available_songs = [
        {"title": "Millionaire", "artist": "O2SRK Mashup", "url": "/static/audio/03. Millionaire - O2SRK Mashup.mp3"},
        {"title": "Glock in My Lap", "artist": "21 Savage & Metro Boomin", "url": "/static/audio/21_Savage_Metro_Boomin_-_Glock_in_My_Lap_Offblogmedia.com.mp3"},
        {"title": "LOVE", "artist": "Kendrick Lamar Ft Zacari", "url": "/static/audio/Kendrick_Lamar_Ft_Zacari_-_LOVE_Offblogmedia.com.mp3"},
        {"title": "Main Nikla Gaddi Leke (Remix)", "artist": "DJ Volcanik", "url": "/static/audio/Main Nikla Gaddi Leke (Remix) - DJ Volcanik.mp3"},
        {"title": "Me Too", "artist": "Abigail Chams & Harmonize", "url": "/static/audio/Abigail_Chams_Harmonize_-_Me_Too_Offblogmedia.com.mp3"},
        {"title": "Drunk in Love", "artist": "Beyoncé Ft Jay-Z", "url": "/static/audio/Beyonc_Ft_Jay-Z_-_Drunk_in_Love_Offblogmedia.com.mp3"},
        {"title": "Knife Talk", "artist": "Drake Ft 21 Savage & Project Pat", "url": "/static/audio/Drake_Ft_21_Savage_Project_Pat_-_Knife_Talk_Offblogmedia.com.mp3"},
        {"title": "Not Like Us", "artist": "Kendrick Lamar", "url": "/static/audio/Kendrick_Lamar_-_Not_Like_Us_Offblogmedia.com.mp3"},
        {"title": "Bailadila", "artist": "O2SRK Remix", "url": "/static/audio/04. Bailadila - O2SRK Remix.mp3"},
        {"title": "Desi Girl", "artist": "DJ VASIM", "url": "/static/audio/8. DESI GIRL (REMIX) - DJ VASIM.mp3"},
        {"title": "Bollywood Remix", "artist": "DJ VASIM", "url": "/static/audio/9. DJ VASIM - BOLLYWOOD REMIX.mp3"},
        {"title": "Nimekubali", "artist": "Diamond Platnumz", "url": "/static/audio/Diamond-Platnumz-Nimekubali-(Vistanaij.com).mp3"}
    ]
    return jsonify({"songs": available_songs})

@app.route('/validate_audio_files', methods=['GET'])
def validate_audio_files():
    audio_files = os.listdir(app.config['UPLOAD_FOLDER'])
    missing_files = []

    
    expected_files = ['song1.mp3', 'song2.mp4', 'song3.mp3']

    for file in expected_files:
        if file not in audio_files:
            missing_files.append(file)

    if missing_files:
        return jsonify({"error": "Missing files", "missing_files": missing_files}), 404

    return jsonify({"message": "All audio files are properly inserted!"}), 200

@app.route('/get_playlist_songs', methods=['GET'])
def get_playlist_songs():
    user = request.args.get('user')
    playlist_name = request.args.get('playlist_name')
    if not user or user not in playlists:
        return jsonify({"error": "User not found"}), 404

    user_playlists = playlists[user]
    for playlist in user_playlists:
        if playlist["name"] == playlist_name:
            return jsonify({"songs": playlist["songs"]})
    return jsonify({"error": "Playlist not found"}), 404

def playlist_add_items(self, playlist_id, items, position=None):
    url_match = re.match(r'spotify:(?P<type>[a-zA-Z]+):(?P<id>[a-zA-Z0-9]+)', playlist_id)
    if not url_match:
        raise SpotifyException(400, -1, "Invalid Spotify URL or URI.")
    url_match_groups = url_match.groupdict()
    if url_match_groups['type'] != type:
        raise SpotifyException(400, -1, "Unexpected Spotify URL type.")
    return url_match_groups['id']

    if re.search(self._regex_base62, id) is not None:
        return id

    raise SpotifyException(400, -1, "Unsupported URL / URI.")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

