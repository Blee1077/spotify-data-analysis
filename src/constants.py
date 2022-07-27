"""Constants for data scripts"""

# Format for logging
LOG_FMT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

# Save filepaths
FIG_SAVE_PATH  = r"C:\Users\Brandon\git\spotify-recommender-system\reports\figures"
DATA_RAW_PATH = r'C:\Users\Brandon\git\spotify-recommender-system\data\raw'
DATA_PROC_PATH = r'C:\Users\Brandon\git\spotify-recommender-system\data\processed'
GENRE_ARTIST_MAPPING_FP = f'{DATA_RAW_PATH}\genre_artist_mapping.json'
ARTIST_GENRE_MAPPING_FP = f'{DATA_RAW_PATH}\artist_genre_mapping.json'
PROCESSED_DATA_FP = f'{DATA_PROC_PATH}\spotify_playlist_track_features.csv'

# Mapping for last day of each month
MONTH_LAST_DATE_DICT = {
    1: 31,
    2: 28, # Beware of leap years
    3: 31,
    4: 30,
    5: 31,
    6: 30,
    7: 31,
    8: 31,
    9: 30,
    10: 31,
    11: 30,
    12: 31
}

# Mapping of month to name
MONTH_NAME_DICT = {
    1: 'Jan',
    2: 'Feb',
    3: 'Mar',
    4: 'Apr',
    5: 'May',
    6: 'Jun',
    7: 'Jul',
    8: 'Aug',
    9: 'Sep',
    10: 'Oct',
    11: 'Nov',
    12: 'Dec'
}

# List of audio feature columns
AUDIO_FEAT_COLS = [
    'danceability',
    'energy',
    'loudness',
    'speechiness',
    'acousticness',
    'instrumentalness',
    'liveness',
    'valence',
    'tempo',
]