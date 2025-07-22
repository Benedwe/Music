document.addEventListener("DOMContentLoaded", function () {
    const socket = io();
    const audioPlayer = document.getElementById("audio-player");
    const currentSong = document.getElementById("current-song");
    const playlistList = document.getElementById("playlist-list");
    const moodList = document.getElementById("mood-list");
    const savedList = document.getElementById("saved-list");
    const searchResults = document.getElementById("search-results");
    const analyticsResults = document.getElementById("analytics-results");
    const songList = document.getElementById("song-list");

    // Load playlists from the server
    function loadPlaylists() {
        fetch("/get_playlists")
            .then(response => response.json())
            .then(data => {
                playlistList.innerHTML = data.shared.map(song => `<li onclick="playSong('${song}')">${song}</li>`).join("");
                moodList.innerHTML = Object.keys(data.mood).map(mood => `<li>${mood}: ${data.mood[mood].join(", ")}</li>`).join("");
                savedList.innerHTML = Object.keys(data.saved).map(name => `<li>${name}: ${data.saved[name].join(", ")}</li>`).join("");
            })
            .catch(error => console.error("Error loading playlists:", error));
    }

    // Fetch available songs from the backend
    function loadAvailableSongs() {
        fetch('/available_songs')
            .then(response => response.json())
            .then(data => {
                songList.innerHTML = ''; // Clear the list before adding songs
                data.songs.forEach(song => {
                    const li = document.createElement('li');
                    li.textContent = `${song.title} - ${song.artist}`;
                    li.setAttribute('data-src', song.url);
                    li.setAttribute('draggable', 'true');
                    li.setAttribute('ondragstart', 'drag(event)');
                    li.addEventListener('click', playSong);
                    songList.appendChild(li);
                });
            })
            .catch(error => console.error('Error loading songs:', error));
    }

    // Play a selected song
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

    // Search for songs
    function searchSongs() {
        const query = document.getElementById('search-query').value.trim();

        if (!query) {
            alert('Please enter a search query.');
            return;
        }

        // Proceed with the fetch request
        fetch(`/search_songs?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                // Handle the response
            })
            .catch(error => console.error('Error fetching songs:', error));
    }

    // Download a playlist
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

    // Download playlist for offline mode
    function downloadOffline() {
        const playlistName = document.getElementById("offline-playlist-name").value;

        fetch("/offline_mode", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ playlist_name: playlistName, user: "example_user" })
        })
            .then(response => response.json())
            .then(data => {
                const message = document.getElementById("offline-message");
                message.textContent = data.message || data.error;
            })
            .catch(error => console.error("Error downloading playlist for offline:", error));
    }

    // Generate cover art for a playlist
    function generateCoverArt() {
        const playlistName = document.getElementById("cover-art-playlist-name").value;

        fetch("/generate_cover_art", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ playlist_name: playlistName })
        })
            .then(response => response.json())
            .then(data => {
                const coverArtImage = document.getElementById("cover-art-image");
                coverArtImage.src = data.cover_art;
                coverArtImage.style.display = "block";
            })
            .catch(error => console.error("Error generating cover art:", error));
    }

    // Fetch playlist analytics
    function fetchAnalytics() {
        fetch(`/playlist_analytics?user=example_user`)
            .then(response => response.json())
            .then(data => {
                analyticsResults.innerHTML = "";
                if (data.analytics) {
                    data.analytics.forEach(playlist => {
                        const li = document.createElement("li");
                        li.innerHTML = `<strong>${playlist.playlist_name}</strong>: 
                                        ${playlist.total_songs} songs, ${playlist.total_playtime}`;
                        analyticsResults.appendChild(li);
                    });
                } else {
                    analyticsResults.innerHTML = `<li>${data.error}</li>`;
                }
            })
            .catch(error => console.error("Error fetching analytics:", error));
    }

    // Handle real-time playlist updates
    socket.on("update_playlist", function () {
        loadPlaylists();
    });

    // Drag-and-drop functionality for playlist creation
    function allowDrop(event) {
        event.preventDefault();
    }

    function drag(event) {
        const songName = event.target.innerText;
        const songSrc = event.target.getAttribute("data-src");
        event.dataTransfer.setData("text", JSON.stringify({ name: songName, src: songSrc }));
    }

    function drop(event) {
        event.preventDefault();
        const songData = JSON.parse(event.dataTransfer.getData("text"));
        const li = document.createElement("li");
        li.innerHTML = `<strong>${songData.name}</strong> 
                        <audio controls>
                            <source src="${songData.src}" type="audio/mpeg">
                            Your browser does not support the audio element.
                        </audio>`;
        document.getElementById("playlist-songs").appendChild(li);
    }

    // Share a playlist
    function sharePlaylist() {
        const playlistName = document.getElementById("share-playlist-name").value;
        const shareType = document.getElementById("share-type").value;

        fetch("/share_playlist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user: "example_user", // Replace with actual user
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
                // Reload public playlists after sharing
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

    // Start voice command for playlist generation
    function startVoiceCommand() {
        // Simulate voice command processing
        fetch("/voice_playlist", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ command: "happy playlist" }) // Replace with actual voice input
        })
            .then(response => response.json())
            .then(data => {
                const results = document.getElementById("voice-playlist-results");
                results.innerHTML = "";
                data.playlist.forEach(song => {
                    const li = document.createElement("li");
                    li.innerHTML = `<strong>${song.title}</strong> by ${song.artist} 
                                    <a href="${song.url}" target="_blank">Listen</a>`;
                    results.appendChild(li);
                });
            })
            .catch(error => console.error("Error generating voice playlist:", error));
    }

    // Fetch track metadata
    function fetchTrackMetadata() {
        const track = document.getElementById("track-name").value;
        const artist = document.getElementById("artist-name").value;

        fetch(`/track_metadata?track=${encodeURIComponent(track)}&artist=${encodeURIComponent(artist)}`)
            .then(response => response.json())
            .then(data => {
                const result = document.getElementById("track-metadata-result");
                result.textContent = JSON.stringify(data, null, 2);
            })
            .catch(error => console.error("Error fetching track metadata:", error));
    }

    // Fetch artist info
    function fetchArtistInfo() {
        const artist = document.getElementById("artist-info-name").value;

        fetch(`/artist_info?artist=${encodeURIComponent(artist)}`)
            .then(response => response.json())
            .then(data => {
                const result = document.getElementById("artist-info-result");
                result.textContent = JSON.stringify(data, null, 2);
            })
            .catch(error => console.error("Error fetching artist info:", error));
    }

    // Search songs by mood
    document.getElementById('search-button').addEventListener('click', function () {
        const mood = document.getElementById('mood-input').value.trim();

        if (!mood) {
            alert('Please enter a mood to search for songs.');
            return;
        }

        // Fetch songs based on the mood
        fetch(`/search_songs?mood=${encodeURIComponent(mood)}`)
            .then(response => response.json())
            .then(data => {
                const resultsContainer = document.getElementById('song-results');
                resultsContainer.innerHTML = ''; // Clear previous results

                if (data.error) {
                    resultsContainer.innerHTML = `<li>${data.error}</li>`;
                    return;
                }

                // Display the songs with links
                data.songs.forEach(song => {
                    const li = document.createElement('li');
                    li.innerHTML = `<a href="${song.url}" target="_blank">${song.title} - ${song.artist}</a>`;
                    resultsContainer.appendChild(li);
                });
            })
            .catch(error => {
                console.error('Error fetching songs:', error);
                alert('An error occurred while searching for songs.');
            });
    });

    // Load playlists on page load
    loadPlaylists();

    // Load public playlists on page load
    loadPublicPlaylists();

    // Load available songs on page load
    loadAvailableSongs();

    // Expose functions to the global scope for use in HTML
    window.searchSongs = searchSongs;
    window.downloadPlaylist = downloadPlaylist;
    window.fetchAnalytics = fetchAnalytics;
    window.allowDrop = allowDrop;
    window.drag = drag;
    window.drop = drop;
    window.sharePlaylist = sharePlaylist;
    window.playSong = playSong;
    window.startVoiceCommand = startVoiceCommand;
    window.downloadOffline = downloadOffline;
    window.generateCoverArt = generateCoverArt;
    window.fetchTrackMetadata = fetchTrackMetadata;
    window.fetchArtistInfo = fetchArtistInfo;
});
