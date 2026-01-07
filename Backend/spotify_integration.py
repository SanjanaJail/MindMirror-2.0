# spotify_integration.py - Spotify API integration for music
import os
import requests
import base64

class SpotifyIntegration:
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID', 'YOUR_SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET', 'YOUR_SPOTIFY_CLIENT_SECRET')
        self.access_token = None
        self.base_url = "https://api.spotify.com/v1"
    
    def get_access_token(self):
        """Get Spotify access token"""
        try:
            auth_string = f"{self.client_id}:{self.client_secret}"
            auth_bytes = auth_string.encode('utf-8')
            auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
            
            url = "https://accounts.spotify.com/api/token"
            headers = {
                'Authorization': f'Basic {auth_base64}',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            data = {'grant_type': 'client_credentials'}
            
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            
            self.access_token = result.get('access_token')
            return self.access_token
        except Exception as e:
            print(f"Spotify auth error: {e}")
            return None
    
    def search_tracks(self, query, max_results=10):
        """Search Spotify tracks by query"""
        try:
            if not self.access_token:
                self.get_access_token()
            
            url = f"{self.base_url}/search"
            headers = {'Authorization': f'Bearer {self.access_token}'}
            params = {
                'q': query,
                'type': 'track',
                'limit': max_results,
                'market': 'US'
            }
            
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            tracks = []
            for item in data.get('tracks', {}).get('items', []):
                track = {
                    'track_id': item['id'],
                    'name': item['name'],
                    'artist': item['artists'][0]['name'],
                    'album': item['album']['name'],
                    'preview_url': item.get('preview_url'),
                    'external_url': item['external_urls']['spotify'],
                    'duration_ms': item['duration_ms'],
                    'popularity': item['popularity'],
                    'album_image': item['album']['images'][0]['url'] if item['album']['images'] else None
                }
                tracks.append(track)
            
            return tracks
        except Exception as e:
            print(f"Spotify search error: {e}")
            return []
    
    def get_audio_features(self, track_ids):
        """Get audio features for tracks"""
        try:
            if not self.access_token:
                self.get_access_token()
            
            url = f"{self.base_url}/audio-features"
            headers = {'Authorization': f'Bearer {self.access_token}'}
            params = {'ids': ','.join(track_ids)}
            
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            return data.get('audio_features', [])
        except Exception as e:
            print(f"Audio features error: {e}")
            return []
    
    def get_recommendations(self, seed_tracks, max_results=10):
        """Get track recommendations based on seed tracks"""
        try:
            if not self.access_token:
                self.get_access_token()
            
            url = f"{self.base_url}/recommendations"
            headers = {'Authorization': f'Bearer {self.access_token}'}
            params = {
                'seed_tracks': ','.join(seed_tracks),
                'limit': max_results,
                'market': 'US'
            }
            
            response = requests.get(url, headers=headers, params=params)
            data = response.json()
            
            return data.get('tracks', [])
        except Exception as e:
            print(f"Recommendations error: {e}")
            return []