"""Scrape mappings for artist to genres and genre to artists."""
import requests
import time
import json
import logging
from bs4 import BeautifulSoup
from src.constants import GENRE_ARTIST_MAPPING_FP, ARTIST_GENRE_MAPPING_FP, LOG_FMT

def main():
    logger = logging.getLogger(__name__)
    
    # Request HTML
    r = requests.get("http://everynoise.com/engenremap.html")

    # Parse Genre HTML Elements
    soup = BeautifulSoup(r.content, "html.parser")
    allGenreDivs = soup.find_all("div", "genre scanme")
    logger.info(f'Total number of genres: {len(allGenreDivs)}')
    
    # Cycle through genres and go to that genres page
    artist_mapping = {}
    genre_mapping = {}
    genreCnt = 0

    for genreDiv in allGenreDivs:
        # Print progress status
        if (genreCnt % 10) == 0:
            logger.info("Pulling genre #" + str(genreCnt))
            
        # Get genre
        genre = genreDiv.text.strip().replace('»', '')
        if genre not in genre_mapping:
            genre_mapping[genre] = []
            
        # Build URL for current genre
        genrePage = "http://everynoise.com/engenremap-" + str.replace(genre," ", "") + ".html"

        # Pull artists from genre page
        r2 = requests.get(
            genrePage,
            headers={'User-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36'},
            timeout=120
        )
        soup2 = BeautifulSoup(r2.content, "html.parser")
        allArtistDivs = soup2.find_all("div", "genre scanme")

        # Add artist and genre to both artist-genre and genre-artist mappings
        for artist in allArtistDivs:
            artistName = artist.text.strip().replace('»', '')
            
            if not(artistName.isspace()):
                
                if artistName not in artist_mapping:
                    artist_mapping[artistName] = [genre]
                else:
                    artist_mapping[artistName].append(genre)
                    
                genre_mapping[genre].append(artistName) 
                
        genreCnt = genreCnt+1
        
        # Give the server a rest before making another request
        time.sleep(2)
        
    # Save data
    with open(GENRE_ARTIST_MAPPING_FP, 'w') as fp:
        json.dump(genre_mapping, fp)
        
    with open(ARTIST_GENRE_MAPPING_FP, 'w') as fp:
        json.dump(artist_mapping, fp)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format=LOG_FMT)
    
    main()