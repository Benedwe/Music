document.addEventListener("DOMContentLoaded", function () {
    const socket = io();
    const audioPlayer = document.getElementById("audio-player");
    const currentSong = document.getElementById("current-song");
    const playlistList = document.getElementById("playlist-list");
    const searchResults = document.getElementById("search-results");
    const songList = document.getElementById("song-list");
    let songQueue = [];
    let isPlaying = false;

    function loadPlaylists() {
        fetch("/get_playlists")
            .then(response => response.json())
            .then(data => {
                playlistList.innerHTML = data.shared.map(song => `<li data-src="${song.url}" onclick="playSong(event)">${song.title}</li>`).join("");
            })
            .catch(error => console.error("Error loading playlists:", error));
    }

    function playSong(event) {
        const songSrc = event.target.getAttribute('data-src');
        const songTitle = event.target.textContent;

        if (songSrc) {
            audioPlayer.src = songSrc;
            audioPlayer.play();
            currentSong.textContent = `Now Playing: ${songTitle}`;
        } else {
            alert('Audio source not found!');
        }
    }
    function addToQueue(songSrc, songTitle) {
        songQueue.push({ src: songSrc, title: songTitle });
        alert(`Added "${songTitle}" to the queue.`);
        if (!isPlaying) {
            playNextSong();
        }
    }
    function playNextSong() {
        if (songQueue.length === 0) {
            isPlaying = false;
            currentSong.textContent = "No song playing";
            audioPlayer.src = "";
            return;
        }
        const nextSong = songQueue.shift();
        audioPlayer.src = nextSong.src;
        audioPlayer.play();
        currentSong.textContent = `Now Playing: ${nextSong.title}`;
        isPlaying = true;
    }

    audioPlayer.addEventListener("ended", playNextSong);
    function playPlaylist(playlistName) {
        fetch(`/get_playlist_songs?playlist_name=${encodeURIComponent(playlistName)}`)
            .then(response => response.json())
            .then(data => {
                if (data.songs && data.songs.length > 0) {
                    playSongFromPlaylist(data.songs, 0);
                } else {
                    alert(data.error || "No songs in this playlist.");
                }
            })
            .catch(error => console.error('Error loading playlist:', error));
    }

    function playSongFromPlaylist(playlistSongs, index) {
        if (index >= playlistSongs.length) {
            alert("End of playlist.");
            return;
        }
        const song = playlistSongs[index];
        audioPlayer.src = song.url;
        audioPlayer.play();
        currentSong.textContent = `Now Playing: ${song.title} - ${song.artist}`;
        audioPlayer.onended = () => playSongFromPlaylist(playlistSongs, index + 1);
    }
    function searchSongs() {
        const query = document.getElementById("search-query").value;
        fetch(`/search_songs?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                searchResults.innerHTML = "";
                data.spotify_songs.forEach(song => {
                    const div = document.createElement("div");
                    div.textContent = `${song.title} - ${song.artist}`;
                    div.setAttribute("data-src", song.url);
                    div.onclick = playSong;
                    searchResults.appendChild(div);
                });
                data.youtube_songs.forEach(song => {
                    const div = document.createElement("div");
                    div.textContent = song.title;
                    div.setAttribute("data-src", song.url);
                    div.onclick = playSong;
                    searchResults.appendChild(div);
                });
            });
    }
    function addToPlaylist(trackId) {
        const playlistId = prompt('Enter the Spotify Playlist ID:');
        if (!playlistId) {
            alert('Playlist ID is required.');
            return;
        }
        fetch('/add_to_playlist', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ playlist_id: playlistId, track_id: trackId })
        })
            .then(response => response.json())
            .then(data => {
                alert(data.message || 'Error adding track to playlist.');
            })
            .catch(error => console.error('Error adding track to playlist:', error));
    }
    function downloadPlaylist(playlistName) {
        fetch(`/download_playlist/${encodeURIComponent(playlistName)}?user=example_user`)
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    alert(data.message);
                } else if (data.error) {
                    alert(`Error: ${data.error}`);
                }
            })
            .catch(error => console.error("Error downloading playlist:", error));
    }
    function savePlaylist() {
        const playlistName = document.getElementById("playlist-name").value.trim();
        const playlistSongs = Array.from(document.getElementById("playlist-songs").children).map(song => ({
            title: song.textContent,
            src: song.getAttribute("data-src")
        }));

        if (!playlistName || playlistSongs.length === 0) {
            alert("Please enter a playlist name and add songs.");
            return;
        }

        fetch("/save_playlist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ playlist_name: playlistName, songs: playlistSongs })
        })
            .then(response => response.json())
            .then(data => {
                alert(data.message || "Error saving playlist.");
            })
            .catch(error => console.error("Error saving playlist:", error));
    }

    function uploadAudio() {
        const fileInput = document.getElementById('audio-file');
        const file = fileInput.files[0];
        const formData = new FormData();
        formData.append('file', file);

        fetch('/upload_audio', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                const message = document.getElementById('upload-message');
                if (data.error) {
                    message.textContent = `Error: ${data.error}`;
                    message.style.color = 'red';
                } else {
                    message.textContent = data.message;
                    message.style.color = 'green';
                }
            })
            .catch(error => console.error('Error uploading file:', error));
    }

    function loadAvailableSongs() {
        fetch('/available_songs')
            .then(response => response.json())
            .then(data => {
                songList.innerHTML = '';
                data.songs.forEach(song => {
                    const li = document.createElement('li');
                    li.textContent = `${song.title} - ${song.artist}`;
                    li.setAttribute('data-src', song.url);
                    li.addEventListener('click', playSong);
                    songList.appendChild(li);
                });
            })
            .catch(error => console.error('Error loading songs:', error));
    }

    
    function sharePlaylist() {
        const playlistName = document.getElementById("share-playlist-name").value;
        const shareType = document.getElementById("share-type").value;

        fetch("/share_playlist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user: "example_user", 
                playlist_name: playlistName,
                share_type: shareType
            })
        })
            .then(response => response.json())
            .then(data => {
                const message = document.getElementById("share-message");
                if (data.message) {
                    message.textContent = data.message;
                    if (data.link) {
                        message.innerHTML += ` <a href="${data.link}" target="_blank">Open Link</a>`;
                    }
                } else {
                    message.textContent = data.error;
                }
                loadPublicPlaylists();
            })
            .catch(error => console.error("Error sharing playlist:", error));
    }

    function loadPublicPlaylists() {
        fetch("/public_playlists")
            .then(response => response.json())
            .then(data => {
                const publicPlaylistList = document.getElementById("public-playlist-list");
                publicPlaylistList.innerHTML = "";
                data.public_playlists.forEach(playlist => {
                    const li = document.createElement("li");
                    li.textContent = playlist.name;
                    publicPlaylistList.appendChild(li);
                });
            })
            .catch(error => console.error("Error loading public playlists:", error));
    }

    function collaborate() {
        const playlistName = document.getElementById("playlist-name").value;
        const contributor = document.getElementById("collaborator-name").value;

        fetch("/collaborate_playlist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ playlist_name: playlistName, contributor })
        })
            .then(response => response.json())
            .then(data => alert(data.message || data.error));
    }

    loadPlaylists();
    loadPublicPlaylists();
    loadAvailableSongs();
    window.searchSongs = searchSongs;
    window.downloadPlaylist = downloadPlaylist;
    window.sharePlaylist = sharePlaylist;
    window.playSong = playSong;
    window.addToPlaylist = addToPlaylist;
    window.addToQueue = addToQueue;
    window.playPlaylist = playPlaylist;
    window.savePlaylist = savePlaylist;
    window.uploadAudio = uploadAudio;
    window.collaborate = collaborate;
});