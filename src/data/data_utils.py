import time
import math
import requests
import pandas as pd
from typing import Union
from bs4 import BeautifulSoup


# Helper functions
def get_user_playlists(sp, user: str):
    """Gets all user-made playlists for a given username.
    
    Args:
        user (str): Username of interest
        
    Returns:
        playlist_dict (dict): Dictionary containing all playlists made by the given user
    """
    playlist_dict = {}
    for playlist in sp.user_playlists(user=user).get('items'):
        playlist_name = playlist.get('name')
        playlist_dict[playlist_name] = {}
        playlist_dict[playlist_name]['id'] = playlist.get('id')
        playlist_dict[playlist_name]['total_tracks'] = playlist.get('tracks').get('total')
        
    return playlist_dict


def get_playlist_track_ids(sp, user: str, playlist_id: Union[str, list], playlist_id_name_map: dict):
    """Given a username and one or more playlist IDs, get the tracks in the playlist(s).
    
    Args:
        user (str): Username who created playlist
        playlist_id (str or list): Playlist(s) of interest
        playlist_id_name_map (dict): Dictionary that maps playlist id to playlist name
    
    Returns:
        playlist_tracks (dict): Dictionary containing all tracks in the given playlist(s)
        track_to_idx_map (dict): Dictionary that maps track ID to keys in the playlist_tracks dictionary
    """
    # Convert string to list if a string is given for playlist_id
    if isinstance(playlist_id, str):
        playlist_id = [playlist_id]
        
    playlist_tracks = {}
    track_to_idx_map = {}
    
    # Loop through list of playlist IDs
    for pl_idx, _id in enumerate(playlist_id):
        
        # Get tracks from spotipy API
        r = sp.user_playlist_tracks(user=user, playlist_id=_id)
        t = r['items']
        
        # API only returns 100 tracks max in a single response, so need to get the rest
        while r['next']:
            r = sp.next(r)
            t.extend(r['items'])
            
        print(f'Total tracks in {playlist_id_name_map[_id]}: {len(t)}')
        
        # Loop through each track
        for t_idx, s in enumerate(t):
            track_id = s["track"]["id"]
            
            # track_id can be None, skip if it is
            if track_id is None:
                continue
                
            # Otherwise, get the track's information and store in dict
            else:
                playlist_tracks[f"{pl_idx}{t_idx}"] = {
                    'track_id': track_id,
                    'playlist_name': playlist_id_name_map[_id],
                    'playlist_date_added': s["added_at"],
                    'name': s["track"]["name"],
                    'artist': s['track']['artists'][0]['name'],
                    'artist_id': s['track']['artists'][0]['id'],
                    'popularity': s['track']['popularity']
                }
                
                # Create a mapping for track ID to keys of the playlist_tracks dict
                # Will need this to link track_features_dict in later function to playlist_tracks dict
                if track_id not in track_to_idx_map:
                    track_to_idx_map[track_id] = [f"{pl_idx}{t_idx}"]
                else:
                    track_to_idx_map[track_id].append(f"{pl_idx}{t_idx}")

    return playlist_tracks, track_to_idx_map


def get_playlist_track_features(sp, playlist_tracks: dict, track_to_idx_map: dict):
    """Gets the Spotify audio features of tracks in the playlist_tracks dictionary ouputted from get_playlist_track_ids().
    
    Args:
        playlist_tracks (dict): Output dictionary from get_playlist_track_ids() containing all tracks in the given playlist(s)
        track_to_idx_map (dict): Output dictionary from get_playlist_track_ids() that maps track ID to keys in the playlist_tracks dictionary
        
    Returns:
        df (pd.DataFrame): Pandas DataFrame of tracks' audio features and artist & playlist information
    """
    # Dictionary to cast end pandas DataFrame to correct dtypes
    cast_dict = {
        'danceability': float,
        'energy': float,
        'key': int,
        'loudness': float,
        'speechiness': float,
        'acousticness': float,
        'instrumentalness': float,
        'liveness': float,
        'valence': float,
        'tempo': float,
        'time_signature': int
    }
    
    # Get tracks IDs from the input dictionary containing all tracks of playlists
    tracks = [playlist_tracks[idx]['track_id'] for idx in playlist_tracks]
    
    # Partition the list into multiple lists containing 100 tracks each
    # This is because Spotify's API can only handle 100 max in one request
    track_lists = [tracks[0+i*100:100+i*100] for i in range(math.ceil(len(tracks)/100))]
    
    track_features_dict = {}
    
    # Loop through each partition
    for _, track_list in enumerate(track_lists):
        
        # Get audio features for the tracks
        feature_list = sp.audio_features(track_list)
        
        # Put in dictionary
        for track_id, features in zip(track_list, feature_list):
            track_features_dict[track_id] = features
    
    # Convert dictionary into dataframe and drop unneeded columns
    df = pd.DataFrame.from_records(track_features_dict).T.reset_index(drop=True)
    df = df.drop(columns=['type', 'uri', 'track_href', 'analysis_url'])
    
    # Get playlist-track index from dictionary made in previous steps
    df['playlist_track_id'] = df['id'].map(track_to_idx_map)
    
    # Multi-to-one mapping between tracks so need to explode list and drop duplicate rows
    df = (df
          .explode('playlist_track_id')
          .drop_duplicates(subset=['id', 'playlist_track_id'])
          .reset_index(drop=True)
         )
    
    # Get playlist & track artist info from dictionary made in previous steps
    for col in ['name', 'popularity', 'artist', 'artist_id', 'playlist_name', 'playlist_date_added']:
        df[col] = df['playlist_track_id'].apply(lambda x: playlist_tracks[x][col])
    
    # Cast columns to appropriate dtype
    for col in cast_dict:
        df[col] = df[col].astype(cast_dict.get(col))
        
    return df


def get_artist_genres(artist_id: str, artist_genre_map: dict=None):
    """Given a Spotify artist ID, goes to their page on https://everynoise.com and gets their genres.
    
    Args:
        artist_id (str): Spotify artist ID
        artist_genre_map (Optional, dict): Artist-to-genre dictionary mapping
    
    Returns:
        genres (list): List of genres of an artist
        artist_genre_map (Optional, dict): Updated artist-to-genre dictionary mapping if given
    """
    BASE_URL = 'https://everynoise.com/artistprofile.cgi'
    r = requests.get(f"{BASE_URL}?id={artist_id}")
    soup = BeautifulSoup(r.content, "html.parser")
    
    discocell_td = soup.find('td', 'discocell')
    assert(discocell_td is not None), "This is a show-stopper, they must've changed their website. This function needs updating."
    
    try:
        genres_div = discocell_td.find('div', 'genres')
    except AttributeError:
        print(artist_id)
        return None, artist_genre_map
    
    try:
        title_dv = discocell_td.find('div', 'title')
    except AttributeError:
        print(artist_id)
        return None, artist_genre_map
        
    assert(title_dv is not None), "Can't find artists' name, this shouldn't happen"
    
    artist_name = title_dv.text.strip()
    
    if genres_div is not None:
        genres = genres_div.text.split(', ')
    else:
        genres = None    
    
    # Let's be kind to the servers and wait a sec before sending another request
    time.sleep(1)
    
    if artist_genre_map is not None:
        artist_genre_map[artist_name] = genres
        return genres, artist_genre_map
    
    else:
        return genres