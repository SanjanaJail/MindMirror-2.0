# analytics_engine.py - New file for advanced analytics

import json
from datetime import datetime, timedelta
import numpy as np
from database import get_db_connection

class AnalyticsEngine:
    def __init__(self):
        self.conn = get_db_connection()
    
    def calculate_user_baseline(self, user_id, days=14):
        """Calculate baseline metrics for a user - FIXED VERSION"""
        try:
            # Get ALL entries regardless of date for testing
            entries = self.conn.execute('''
                SELECT * FROM mindmirror_entries 
                WHERE user_id = ? 
                ORDER BY timestamp DESC
            ''', (user_id,)).fetchall()
            
            print(f"🔍 Found {len(entries)} entries for user {user_id}")  # Debug
            
            if len(entries) < 1:  # Lowered threshold
                print("❌ Not enough entries for baseline")
                return None
            
            # Calculate average mood score
            mood_scores = [entry['mood_score'] for entry in entries if entry['mood_score'] is not None]
            print(f"📈 Mood scores found: {mood_scores}")  # Debug
            
            if not mood_scores:
                print("❌ No mood scores available")
                return None
                
            avg_mood = np.mean(mood_scores)
            
            baseline_data = {
                'voice_energy_baseline': 0.7,  # Placeholder
                'speech_rate_baseline': 150,    # Placeholder
                'avg_mood_score': float(avg_mood),
                'data_points_used': len(entries),
                'calculation_date': datetime.now().isoformat(),
                'debug_mood_scores': mood_scores  # For debugging
            }
            
            print(f"✅ Baseline calculated: {baseline_data}")  # Debug
            return baseline_data
            
        except Exception as e:
            print(f"❌ Error calculating baseline: {e}")
            return None
    
    def detect_temporal_patterns(self, user_id):
        """Detect weekly and time-of-day patterns - FIXED VERSION"""
        try:
            entries = self.conn.execute('''
                SELECT * FROM mindmirror_entries 
                WHERE user_id = ? 
                ORDER BY timestamp DESC
            ''', (user_id,)).fetchall()
            
            print(f"🔍 Pattern detection: Found {len(entries)} entries")  # Debug
            
            if len(entries) < 2:  # Lowered from 10 to 2
                print("❌ Not enough entries for pattern detection")
                return None
            
            patterns = {
                'weekly': self._analyze_weekly_patterns(entries),
                'time_of_day': self._analyze_time_patterns(entries)
            }
            
            print(f"✅ Patterns detected: {patterns}")  # Debug
            return patterns
            
        except Exception as e:
            print(f"❌ Error detecting patterns: {e}")
            return None
    
    def _analyze_weekly_patterns(self, entries):
        """Analyze day-of-week patterns - FIXED VERSION"""
        day_patterns = {0: [], 1: [], 2: [], 3: [], 4: [], 5: [], 6: []}  # Mon-Sun
        
        for entry in entries:
            if entry['mood_score'] is not None:
                try:
                    # Handle different date formats safely
                    if 'T' in entry['timestamp']:
                        # ISO format: 2025-10-28T11:16:21
                        weekday = datetime.fromisoformat(entry['timestamp']).weekday()
                    else:
                        # SQLite format: 2025-10-28 11:16:21
                        weekday = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S').weekday()
                    
                    day_patterns[weekday].append(entry['mood_score'])
                    print(f"📅 Added mood {entry['mood_score']} to weekday {weekday}")  # Debug
                except Exception as e:
                    print(f"⚠️ Could not parse date: {entry['timestamp']} - {e}")
                    continue
        
        weekly_avg = {}
        for day, scores in day_patterns.items():
            if scores:
                weekly_avg[day] = float(np.mean(scores))
                print(f"📊 Weekday {day} average: {weekly_avg[day]}")  # Debug
        
        return weekly_avg
    
    def _analyze_time_patterns(self, entries):
        """Analyze time-of-day patterns - FIXED VERSION"""
        time_slots = {'morning': [], 'afternoon': [], 'evening': [], 'night': []}
        
        for entry in entries:
            if entry['mood_score'] is not None:
                try:
                    # Handle different date formats safely
                    if 'T' in entry['timestamp']:
                        # ISO format
                        hour = datetime.fromisoformat(entry['timestamp']).hour
                    else:
                        # SQLite format
                        hour = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S').hour
                    
                    if 5 <= hour < 12:
                        time_slots['morning'].append(entry['mood_score'])
                        print(f"🌅 Added mood {entry['mood_score']} to morning")  # Debug
                    elif 12 <= hour < 17:
                        time_slots['afternoon'].append(entry['mood_score'])
                        print(f"☀️ Added mood {entry['mood_score']} to afternoon")  # Debug
                    elif 17 <= hour < 22:
                        time_slots['evening'].append(entry['mood_score'])
                        print(f"🌆 Added mood {entry['mood_score']} to evening")  # Debug
                    else:
                        time_slots['night'].append(entry['mood_score'])
                        print(f"🌙 Added mood {entry['mood_score']} to night")  # Debug
                except Exception as e:
                    print(f"⚠️ Could not parse time: {entry['timestamp']} - {e}")
                    continue
        
        time_avg = {}
        for slot, scores in time_slots.items():
            if scores:
                time_avg[slot] = float(np.mean(scores))
                print(f"⏰ {slot} average: {time_avg[slot]}")  # Debug
        
        return time_avg
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()