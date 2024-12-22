### File: anime_scraper.py
import requests
from typing import Optional, List, Dict, Any
import time
from datetime import datetime

class JikanAnimeScraper:
    BASE_URL = "https://api.jikan.moe/v4"
    MIN_MEMBERS = 10000
    
    def __init__(self):
        # Jikan has a rate limit of 3 requests per second
        self.last_request_time = 0
        self.rate_limit_delay = 0.4  # 400ms between requests to be safe
    
    def _handle_rate_limit(self):
        """Ensure we don't exceed Jikan API rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last_request)
        self.last_request_time = time.time()

    def fetch_seasonal_anime(self, season: str, year: int) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch seasonal anime using the Jikan API
        
        Args:
            season (str): Season (winter, spring, summer, fall)
            year (int): Year
            
        Returns:
            Optional[List[Dict]]: List of anime entries or None if request fails
        """
        self._handle_rate_limit()
        
        # Validate season
        valid_seasons = ['winter', 'spring', 'summer', 'fall']
        if season.lower() not in valid_seasons:
            raise ValueError(f"Invalid season. Must be one of: {', '.join(valid_seasons)}")
        
        # Build URL
        url = f"{self.BASE_URL}/seasons/{year}/{season.lower()}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            if 'data' not in data:
                print(f"Error: Unexpected API response format")
                return None
                
            anime_list = []
            for anime in data['data']:
                # Check if meets minimum member threshold
                members = anime.get('members', 0)
                if members < self.MIN_MEMBERS:
                    continue
                
                # Format genres
                genres = [genre['name'] for genre in anime.get('genres', [])]
                
                # Create anime entry
                anime_entry = {
                    'title': anime.get('title', ''),
                    'date': self._format_date(anime.get('aired', {}).get('from', '')),
                    'genres': genres,
                    'synopsis': self._truncate_synopsis(anime.get('synopsis', 'No synopsis')),
                    'rssUrl': self._format_rss_url(anime.get('title', '')),
                    'members': members,
                    'score': anime.get('score', None),
                    'episodes': anime.get('episodes', None),
                    'status': anime.get('status', ''),
                    'image_url': anime.get('images', {}).get('jpg', {}).get('image_url', '')
                }
                anime_list.append(anime_entry)
                
            return anime_list
            
        except requests.RequestException as e:
            print(f"Error fetching from Jikan API: {e}")
            return None
            
    def _format_date(self, date_str: str) -> str:
        """Format the date string from API response"""
        if not date_str:
            return "Unknown"
        try:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return date_obj.strftime("%b %d, %Y")
        except (ValueError, TypeError):
            return "Unknown"
    
    def _truncate_synopsis(self, synopsis: str, max_length: int = 300) -> str:
        """Truncate synopsis to specified length"""
        if not synopsis:
            return "No synopsis"
        if len(synopsis) <= max_length:
            return synopsis
        return synopsis[:max_length].rsplit(' ', 1)[0] + '...'
    
    def _format_rss_url(self, title: str) -> str:
        """Format RSS URL for nyaa.si"""
        return f"https://nyaa.si/?page=rss&q=-batch+ember+{title.replace(' ', '+')}&c=0_0&f=0"

# Function to maintain compatibility with existing code
def scrape_anime_season(season: str, year: int) -> Optional[List[Dict[str, Any]]]:
    scraper = JikanAnimeScraper()
    return scraper.fetch_seasonal_anime(season, year)

if __name__ == "__main__":
    # Example usage
    scraper = JikanAnimeScraper()
    anime_list = scraper.fetch_seasonal_anime("winter", 2024)
    if anime_list:
        print(f"Found {len(anime_list)} anime")
        for anime in anime_list:
            print(f"\nTitle: {anime['title']}")
            print(f"Date: {anime['date']}")
            print(f"Genres: {', '.join(anime['genres'])}")