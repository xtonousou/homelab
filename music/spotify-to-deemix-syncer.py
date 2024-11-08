#! /usr/bin/env python3
# Author: Sotirios Roussis <root@xtonousou.com>

import os
import base64
import logging
import requests

# temp
import json
import sys

# Enforce IPv4 connections
requests.packages.urllib3.util.connection.HAS_IPV6 = False

# Debug logging for requests
if int(os.getenv("APP_DEBUG", "0")) == 1:
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("urllib3").setLevel(logging.DEBUG)
    logging.getLogger("requests").setLevel(logging.DEBUG)

###########
# SPOTIFY #
###########

spotify_session = requests.Session()

# Get token grant from Spotify
token_url = "https://accounts.spotify.com/api/token"
token_client_creds = f'{os.getenv("SPOTIFY_CLIENT_ID").strip()}:{os.getenv("SPOTIFY_CLIENT_SECRET").strip()}'
token_response = spotify_session.post(token_url, data={"grant_type": "client_credentials", }, headers={
    "Authorization": f"Basic {base64.b64encode(token_client_creds.encode()).decode()}",
    "Content-Type": "application/x-www-form-urlencoded",
})
token_response.raise_for_status()
spotify_access_token = token_response.json()["access_token"]

spotify_tracks = {}
playlist_url = f"https://api.spotify.com/v1/playlists/{os.getenv('SPOTIFY_PLAYLIST_ID', '3velA1Xmo387hl79f2xFKs').strip()}/tracks"
playlist_header = {"Authorization": f"Bearer {spotify_access_token}", }

playlist_offset, playlist_limit, playlist_total = 0, 100, -1
while playlist_offset >= 0:
    playlist_params = {
        "limit": playlist_limit,
        "offset": playlist_offset,
        "fields": "total,limit,offset,items(track(name,href))",
    }
    playlist_response = spotify_session.get(playlist_url, params=playlist_params, headers=playlist_header)
    playlist_response.raise_for_status()
    playlist_data = playlist_response.json()

    # Populate local data struct with track data
    for track in playlist_data.get("items", []):
        spotify_tracks[track["track"]["href"]] = track["track"]["name"]

    # Handle pagination
    playlist_offset += 100
    playlist_total = playlist_data["total"]
    if playlist_offset > playlist_total:
        playlist_offset = -1

##########
# DEEMIX #
##########

deemix_session = requests.Session()
deemix_host = os.getenv("DEEMIX_HOST", "http://localhost:6595").strip().lower()
deemix_tls_verify = True if os.getenv("DEEMIX_TLS_VERIFY", "yes").strip().lower() in ("yes", "y", "1", "t", "true", "enabled", "on", ) else False
deemix_username, deemix_password = os.getenv("DEEMIX_USERNAME", "").strip(), os.getenv("DEEMIX_PASSWORD", "").strip()

deemix_headers = {
    "Content-Type": "application/json",
    "User-Agent": "python",
}
if deemix_username and deemix_password:
    deemix_creds = f"{deemix_username.strip()}:{deemix_password.strip()}"
    deemix_headers["Authorization"] = f"Basic {base64.b64encode(deemix_creds.encode()).decode()}"

# # Grab the ARL
# deemix_connect_url = f"{deemix_host}/api/connect"
# deemix_response = deemix_session.get(deemix_connect_url, headers=deemix_headers)
# deemix_response.raise_for_status()
# print(deemix_response.text)

# deezer_arl = deemix_response.json().get("singleUser", {}).get("arl")
# if not deezer_arl:
#     raise Exception("[deemix] Cannot proceed further because Deezer ARL is missing!")

# # Login to Deezer via Deemix
# deemix_login_arl_url = f"{deemix_host}/api/loginArl"
# deemix_response = deemix_session.post(deemix_login_arl_url, headers=deemix_headers, json={
#     "arl": deezer_arl,
#     "child": 0,
#     "force": True,
# })
# deemix_response.raise_for_status()

# Download Spotify tracks via Deemix
deemix_download_url = f"{deemix_host}/api/addToQueue"
for track_href, track_name in spotify_tracks.items():
    print(f"[deemix] Queueing spotify track '{track_name}' for download: {track_href}")
    deemix_response = deemix_session.post(deemix_download_url, headers=deemix_headers, json={
        # "bitrate": None,
        "url": track_href,
    })
    print(deemix_response.text)
    deemix_response.raise_for_status()
