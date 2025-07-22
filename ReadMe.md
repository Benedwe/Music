# MelodyMix

MelodyMix is a collaborative music playlist web app that lets users search for songs from Spotify and YouTube, create and share playlists, and invite friends to collaborate in real time.

## Features

- **Spotify & YouTube Integration:** Search and add songs from Spotify and YouTube.
- **User Playlists:** Create, edit, and manage your own playlists.
- **Collaboration:** Invite friends to contribute to shared playlists.
- **Real-time Updates:** See playlist changes instantly with Socket.IO.
- **Sharing:** Share playlists publicly or privately with a link.

## Setup

### Prerequisites

- Python 3.8+
- [Spotify Developer Account](https://developer.spotify.com/)
- [YouTube Data API Key](https://console.developers.google.com/)

### Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/melodymix.git
    cd melodymix
    ```

2. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Create a `.env` file in the project root and add your credentials:
    ```
    FLASK_SECRET_KEY=your_flask_secret
    SPOTIPY_CLIENT_ID=your_spotify_client_id
    SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
    SPOTIPY_REDIRECT_URI=http://127.0.0.1:5000/callback
    YOUTUBE_API_KEY=your_youtube_api_key
    LASTFM_API_KEY=your_lastfm_api_key
    ```

4. Run the app:
    ```sh
    python MelodyMix.py
    ```

5. Open your browser and go to [http://127.0.0.1:5000](http://127.0.0.1:5000)

## Deployment

- For production, use a WSGI server like Gunicorn or Waitress.
- Set all secrets as environment variables.
- Disable debug mode.

## Folder Structure

```
MelodyMix/
│
├── static/           # Static files (CSS, JS, audio)
├── templates/        # HTML templates
├── MelodyMix.py      # Main Flask app
├── requirements.txt
└── README.md
```

## License

MIT License

---

**Enjoy creating and sharing music with MelodyMix!**