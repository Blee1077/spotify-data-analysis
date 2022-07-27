"""Download and process raw spotify data."""
import json
import os
import click
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from data_utils import get_user_playlists, get_playlist_track_ids, get_playlist_track_features, get_artist_genres
from src.constants import ARTIST_GENRE_MAPPING_FP, PROCESSED_DATA_FP

@click.command()
@click.option('--fill_genres', default=False, type=bool, help="Fills in the artist-genre mapping created in notebook 0A_scrape_everynoiseatonce with missing artists present in user's playlists.")
def main(fill_genres):
    # Load in the artist-genre mapping file
    with open(ARTIST_GENRE_MAPPING_FP) as f:
        artist_genre_map = json.load(f)
        
    # Set up spotify authorisation for this session
    # Note that all my parameters are set-up in my user environment variables - follow the spotipy user documentation guide
    user = os.getenv('SPOTIPY_USER')
    scope = "user-library-read,user-top-read,user-read-recently-played"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope, redirect_uri=os.getenv('SPOTIPY_REDIRECT_URI')))
        
    # Get all playlists created by a given user
    playlist_dict = get_user_playlists(sp, user=user)
    inv_playlist_dict = {v['id']:k for k,v in playlist_dict.items()} # Inverse mapping of playlist ID to playlist name

    # Get all track IDs of specified playlists
    playlist_ids = [playlist_dict.get(playlist_name).get('id') for playlist_name in list(playlist_dict.keys())]
    playlist_tracks, track_to_idx_map = get_playlist_track_ids(sp, user=user, playlist_id=playlist_ids, playlist_id_name_map=inv_playlist_dict)

    # Get features of each track
    df = get_playlist_track_features(sp, playlist_tracks, track_to_idx_map)

    # Map artist to genres
    df['genres'] = df['artist'].map(artist_genre_map)

    # Check if this step needs to be done
    if fill_genres:

        # Get artists with missing genres
        genre_missing_artists = df[df['genres'].isna()].drop_duplicates(subset=['artist_id'])['artist_id'].tolist()

        # Fill in artist_genre_map dictionary mapping with missing artists
        for idx, artist_id in enumerate(genre_missing_artists, 1):    
            _, artist_genre_map = get_artist_genres(artist_id=artist_id, artist_genre_map=artist_genre_map)
            
            # Progress checker
            if (idx % 10) == 0:
                click.echo(f'Done {idx} out of {len(genre_missing_artists)}')

        # Overwrite existing file
        with open(ARTIST_GENRE_MAPPING_FP, 'w') as fp:
            json.dump(artist_genre_map, fp)

        # Map again once more
        df['genres'] = df['artist'].map(artist_genre_map)
        
    # Save processed file to data folder as CSV file
    df.to_csv(PROCESSED_DATA_FP, index=False)


if __name__ == '__main__':
    main()