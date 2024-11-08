#! /usr/bin/env python3
# Author: Sotirios Roussis <root@xtonousou.com>

import os
import base64
import requests
import json


config = {
    "spotify": {
        "client_creds": f'{os.getenv("SPOTIFY_CLIENT_ID").strip()}:{os.getenv("SPOTIFY_CLIENT_SECRET").strip()}',
        "playlist_id": os.getenv("SPOTIFY_PLAYLIST_ID").strip(),
    },
    "deemix": {
        "host": os.getenv("DEEMIX_HOST", "http://localhost:6595").strip().lower(),
        "tls_verify": True if os.getenv("DEEMIX_TLS_VERIFY", "yes").strip().lower() in ("yes", "y", "1", "t", "true", "enabled", "on", ) else False,
    },
}

spotify_tracks = []

with requests.Session() as spotify_session:
    token_url = "https://accounts.spotify.com/api/token"
    token_data = {"grant_type": "client_credentials", }
    token_headers = {"Authorization": f"Basic {base64.b64encode(config['spotify']['client_creds'].encode()).decode()}", }

    token_response = spotify_session.post(token_url, data=token_data, headers=token_headers)
    token_response.raise_for_status()

    spotify_access_token = token_response.json()["access_token"]

    playlists_url = f"https://api.spotify.com/v1/playlists/{config['spotify']['playlist_id']}/tracks"
    playlists_params = {"limit": 100, }
    playlists_header = {"Authorization": f"Bearer {spotify_access_token}", }

    playlists_response = spotify_session.get(playlists_url, params=playlists_params, headers=playlists_header)
    playlists_response.raise_for_status()

    print(json.dumps(playlists_response.json()))