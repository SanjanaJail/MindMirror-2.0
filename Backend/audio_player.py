# audio_player.py - Advanced audio playback system
import os
import time
import threading
from datetime import datetime

try:
    from database import get_db_connection
except ImportError:
    # Fallback for testing
    def get_db_connection():
        return None

class AudioPlayer:
    def __init__(self):
        self.current_track = None
        self.is_playing = False
        self.playback_position = 0
        self.playback_start_time = None
        self.playback_thread = None
        self.playback_callbacks = {
            'on_start': None,
            'on_pause': None,
            'on_stop': None,
            'on_progress': None,
            'on_complete': None
        }
    
    def play_content(self, content_item, user_id=None):
        """Play audio/video content with progress tracking"""
        if self.is_playing:
            self.stop_playback()
        
        self.current_track = content_item
        self.is_playing = True
        self.playback_position = 0
        self.playback_start_time = datetime.now()
        
        # Start playback thread
        self.playback_thread = threading.Thread(target=self._playback_worker)
        self.playback_thread.start()
        
        # Call start callback
        if self.playback_callbacks['on_start']:
            self.playback_callbacks['on_start'](content_item)
        
        # Log playback start
        if user_id:
            self._log_playback_start(user_id, content_item)
    
    def _playback_worker(self):
        """Simulate playback progress"""
        duration = self.current_track.get('duration_minutes', 10) * 60  # Convert to seconds
        
        while self.is_playing and self.playback_position < duration:
            time.sleep(1)  # Update every second
            self.playback_position += 1
            
            # Call progress callback
            if self.playback_callbacks['on_progress']:
                progress_percent = (self.playback_position / duration) * 100
                self.playback_callbacks['on_progress'](progress_percent, self.playback_position)
        
        # Playback complete
        if self.is_playing and self.playback_position >= duration:
            self.is_playing = False
            if self.playback_callbacks['on_complete']:
                self.playback_callbacks['on_complete'](self.current_track)
    
    def pause_playback(self):
        """Pause current playback"""
        if self.is_playing:
            self.is_playing = False
            if self.playback_callbacks['on_pause']:
                self.playback_callbacks['on_pause'](self.current_track, self.playback_position)
    
    def resume_playback(self):
        """Resume paused playback"""
        if not self.is_playing and self.current_track:
            self.is_playing = True
            self.playback_thread = threading.Thread(target=self._playback_worker)
            self.playback_thread.start()
    
    def stop_playback(self):
        """Stop playback completely"""
        self.is_playing = False
        if self.playback_callbacks['on_stop']:
            self.playback_callbacks['on_stop'](self.current_track, self.playback_position)
        self.current_track = None
        self.playback_position = 0
    
    def seek_playback(self, position_seconds):
        """Seek to specific position"""
        if self.current_track:
            self.playback_position = max(0, position_seconds)
    
    def get_playback_info(self):
        """Get current playback information"""
        if not self.current_track:
            return None
        
        return {
            'track': self.current_track,
            'is_playing': self.is_playing,
            'position': self.playback_position,
            'duration': self.current_track.get('duration_minutes', 10) * 60,
            'progress_percent': (self.playback_position / (self.current_track.get('duration_minutes', 10) * 60)) * 100
        }
    
    def set_callback(self, event, callback_function):
        """Set callback function for playback events"""
        if event in self.playback_callbacks:
            self.playback_callbacks[event] = callback_function
    
    def _log_playback_start(self, user_id, content_item):
        """Log playback session to database"""
        try:
            conn = get_db_connection()
            conn.execute('''
            INSERT INTO user_playback_sessions 
            (user_id, content_id, content_type, started_at, duration_planned)
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, content_item.get('id'), content_item.get('content_type'), 
                  datetime.now(), content_item.get('duration_minutes', 10)))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Playback logging error: {e}")