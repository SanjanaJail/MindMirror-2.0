# youtube_integration.py - YouTube API integration for content
import os
import requests
from datetime import datetime

class YouTubeIntegration:
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY', 'YOUR_YOUTUBE_API_KEY')
        self.base_url = "https://www.googleapis.com/youtube/v3"
    
    def search_videos(self, query, max_results=5):
        """Search YouTube videos by query"""
        try:
            url = f"{self.base_url}/search"
            params = {
                'part': 'snippet',
                'q': query,
                'type': 'video',
                'maxResults': max_results,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            videos = []
            for item in data.get('items', []):
                video = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails']['default']['url'],
                    'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}",
                    'channel': item['snippet']['channelTitle'],
                    'published_at': item['snippet']['publishedAt']
                }
                videos.append(video)
            
            return videos
        except Exception as e:
            print(f"YouTube API Error: {e}")
            return []
    
    def get_video_duration(self, video_id):
        """Get video duration"""
        try:
            url = f"{self.base_url}/videos"
            params = {
                'part': 'contentDetails',
                'id': video_id,
                'key': self.api_key
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if data.get('items'):
                duration_str = data['items'][0]['contentDetails']['duration']
                return self.parse_duration(duration_str)
            
            return 0
        except Exception as e:
            print(f"Duration fetch error: {e}")
            return 0
    
    def parse_duration(self, duration_str):
        """Parse YouTube duration format (PT1H30M15S) to minutes"""
        import re
        hours = minutes = seconds = 0
        
        hour_match = re.search(r'(\d+)H', duration_str)
        minute_match = re.search(r'(\d+)M', duration_str)
        second_match = re.search(r'(\d+)S', duration_str)
        
        if hour_match:
            hours = int(hour_match.group(1))
        if minute_match:
            minutes = int(minute_match.group(1))
        if second_match:
            seconds = int(second_match.group(1))
        
        total_minutes = hours * 60 + minutes + (1 if seconds > 30 else 0)
        return total_minutes