# quest_system.py - Gamified therapeutic quest system
import json
import random
from datetime import datetime, timedelta
from database import get_db_connection

class QuestSystem:
    def __init__(self):
        self.conn = get_db_connection()
    
    def generate_daily_quests(self, user_id):
        """Generate daily therapeutic quests based on user's emotional patterns"""
        print(f"🎯 Generating daily quests for user {user_id}")
        
        # Get user's recent emotional state
        recent_emotion = self._get_recent_emotion(user_id)
        
        # Define quest templates for different emotions
        quest_templates = {
            'sadness': [
                {
                    'title': 'Gratitude Hunt',
                    'description': 'Find and write down 3 things you\'re grateful for today',
                    'type': 'mindfulness',
                    'difficulty': 'easy',
                    'points': 10,
                    'emoji': '🙏',
                    'action': 'journal'
                },
                {
                    'title': 'Sunlight Seeker',
                    'description': 'Spend 15 minutes outside in sunlight',
                    'type': 'physical',
                    'difficulty': 'easy',
                    'points': 15,
                    'emoji': '☀️',
                    'action': 'outdoor'
                },
                {
                    'title': 'Connection Call',
                    'description': 'Call or message someone you care about',
                    'type': 'social',
                    'difficulty': 'medium',
                    'points': 20,
                    'emoji': '📞',
                    'action': 'social'
                }
            ],
            'anxiety': [
                {
                    'title': 'Breathing Break',
                    'description': 'Practice 5 minutes of deep breathing exercises',
                    'type': 'mindfulness',
                    'difficulty': 'easy',
                    'points': 10,
                    'emoji': '🌬️',
                    'action': 'breathing'
                },
                {
                    'title': 'Grounding Exercise',
                    'description': 'Name 5 things you can see, 4 you can touch, 3 you can hear, 2 you can smell, 1 you can taste',
                    'type': 'mindfulness',
                    'difficulty': 'easy',
                    'points': 15,
                    'emoji': '🌍',
                    'action': 'grounding'
                },
                {
                    'title': 'Digital Detox',
                    'description': 'Take a 30-minute break from all screens',
                    'type': 'lifestyle',
                    'difficulty': 'medium',
                    'points': 25,
                    'emoji': '📵',
                    'action': 'detox'
                }
            ],
            'anger': [
                {
                    'title': 'Energy Release',
                    'description': 'Do 10 minutes of vigorous exercise',
                    'type': 'physical',
                    'difficulty': 'medium',
                    'points': 20,
                    'emoji': '💪',
                    'action': 'exercise'
                },
                {
                    'title': 'Cool Down',
                    'description': 'Practice progressive muscle relaxation',
                    'type': 'mindfulness',
                    'difficulty': 'easy',
                    'points': 15,
                    'emoji': '❄️',
                    'action': 'relaxation'
                },
                {
                    'title': 'Perspective Shift',
                    'description': 'Write about the situation from someone else\'s viewpoint',
                    'type': 'cognitive',
                    'difficulty': 'hard',
                    'points': 30,
                    'emoji': '👁️',
                    'action': 'journal'
                }
            ],
            'joy': [
                {
                    'title': 'Joy Multiplier',
                    'description': 'Share something positive with 3 people',
                    'type': 'social',
                    'difficulty': 'easy',
                    'points': 15,
                    'emoji': '✨',
                    'action': 'sharing'
                },
                {
                    'title': 'Celebration Dance',
                    'description': 'Dance to your favorite upbeat song',
                    'type': 'physical',
                    'difficulty': 'easy',
                    'points': 10,
                    'emoji': '💃',
                    'action': 'dance'
                },
                {
                    'title': 'Future Planning',
                    'description': 'Plan one fun activity for the upcoming week',
                    'type': 'cognitive',
                    'difficulty': 'medium',
                    'points': 20,
                    'emoji': '📅',
                    'action': 'planning'
                }
            ],
            'neutral': [
                {
                    'title': 'Mindful Moment',
                    'description': 'Spend 5 minutes in silent meditation',
                    'type': 'mindfulness',
                    'difficulty': 'easy',
                    'points': 10,
                    'emoji': '🧘',
                    'action': 'meditation'
                },
                {
                    'title': 'Learning Spark',
                    'description': 'Learn something new for 15 minutes',
                    'type': 'cognitive',
                    'difficulty': 'medium',
                    'points': 20,
                    'emoji': '🎓',
                    'action': 'learning'
                },
                {
                    'title': 'Random Act of Kindness',
                    'description': 'Do something nice for someone unexpectedly',
                    'type': 'social',
                    'difficulty': 'medium',
                    'points': 25,
                    'emoji': '🤝',
                    'action': 'kindness'
                }
            ]
        }
        
        # Select 3 quests based on current emotion
        emotion_quests = quest_templates.get(recent_emotion, quest_templates['neutral'])
        selected_quests = random.sample(emotion_quests, min(3, len(emotion_quests)))
        
        # Add quest IDs and status
        for i, quest in enumerate(selected_quests):
            quest['id'] = f"quest_{user_id}_{datetime.now().strftime('%Y%m%d')}_{i}"
            quest['completed'] = False
            quest['created_at'] = datetime.now().isoformat()
        
        # Save quests to database
        self._save_quests_to_db(user_id, selected_quests)
        
        return selected_quests
    
    def _get_recent_emotion(self, user_id):
        """Get user's most recent emotion from database"""
        try:
            cursor = self.conn.execute('''
                SELECT final_emotion FROM mindmirror_entries 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 1
            ''', (user_id,))
            
            result = cursor.fetchone()
            if result:
                emotion = result[0].lower() if result[0] else 'neutral'
                valid_emotions = ['sadness', 'anxiety', 'anger', 'joy', 'neutral']
                return emotion if emotion in valid_emotions else 'neutral'
            
            return 'neutral'
        except Exception as e:
            print(f"Error getting recent emotion: {e}")
            return 'neutral'
    
    def _save_quests_to_db(self, user_id, quests):
        """Save generated quests to database"""
        try:
            # Clear previous day's quests
            self.conn.execute('''
                DELETE FROM user_quests 
                WHERE user_id = ? AND date(created_at) = date('now')
            ''', (user_id,))
            
            # Insert new quests
            for quest in quests:
                self.conn.execute('''
                    INSERT INTO user_quests 
                    (user_id, quest_id, title, description, quest_type, difficulty, points, emoji, action_type, completed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    user_id, quest['id'], quest['title'], quest['description'],
                    quest['type'], quest['difficulty'], quest['points'],
                    quest['emoji'], quest['action'], False
                ))
            
            self.conn.commit()
            print(f"✅ Saved {len(quests)} quests to database for user {user_id}")
            
        except Exception as e:
            print(f"Error saving quests to database: {e}")
    
    def complete_quest(self, user_id, quest_id):
        """Mark a quest as completed and award points"""
        try:
            # Get quest details
            cursor = self.conn.execute('''
                SELECT * FROM user_quests 
                WHERE user_id = ? AND quest_id = ? AND completed = 0
            ''', (user_id, quest_id))
            
            quest = cursor.fetchone()
            if not quest:
                return {'success': False, 'message': 'Quest not found or already completed'}
            
            # Mark as completed
            self.conn.execute('''
                UPDATE user_quests 
                SET completed = 1, completed_at = datetime('now')
                WHERE user_id = ? AND quest_id = ?
            ''', (user_id, quest_id))
            
            # Award points
            points = quest[7]  # points column
            self._award_points(user_id, points, f"Completed quest: {quest[3]}")  # quest[3] is title
            
            # Check for level up
            level_up = self._check_level_up(user_id)
            
            self.conn.commit()
            
            return {
                'success': True,
                'message': f'Quest completed! +{points} points!',
                'points_earned': points,
                'level_up': level_up
            }
            
        except Exception as e:
            print(f"Error completing quest: {e}")
            return {'success': False, 'message': 'Could not complete quest'}
    
    def _award_points(self, user_id, points, reason):
        """Award points to user"""
        try:
            # Get current points
            cursor = self.conn.execute('''
                SELECT points, level FROM user_progress 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if result:
                current_points = result[0] + points
                current_level = result[1]
                
                # Update points
                self.conn.execute('''
                    UPDATE user_progress 
                    SET points = ?, updated_at = datetime('now')
                    WHERE user_id = ?
                ''', (current_points, user_id))
            else:
                # First time - create progress record
                current_points = points
                current_level = 1
                self.conn.execute('''
                    INSERT INTO user_progress 
                    (user_id, points, level, streak_days, updated_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                ''', (user_id, points, 1, 1))
            
            # Log point transaction
            self.conn.execute('''
                INSERT INTO point_transactions 
                (user_id, points, reason, created_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', (user_id, points, reason))
            
            print(f"✅ Awarded {points} points to user {user_id} for: {reason}")
            
        except Exception as e:
            print(f"Error awarding points: {e}")
    
    def _check_level_up(self, user_id):
        """Check if user should level up based on points"""
        try:
            cursor = self.conn.execute('''
                SELECT points, level FROM user_progress WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                return False
            
            current_points, current_level = result
            points_needed = current_level * 100  # 100 points per level
            
            if current_points >= points_needed:
                new_level = current_level + 1
                self.conn.execute('''
                    UPDATE user_progress 
                    SET level = ?, updated_at = datetime('now')
                    WHERE user_id = ?
                ''', (new_level, user_id))
                
                print(f"🎉 User {user_id} leveled up to level {new_level}!")
                return True
            
            return False
            
        except Exception as e:
            print(f"Error checking level up: {e}")
            return False
    
    def get_user_progress(self, user_id):
        """Get user's quest progress and statistics"""
        try:
            # Get basic progress
            cursor = self.conn.execute('''
                SELECT points, level, streak_days FROM user_progress 
                WHERE user_id = ?
            ''', (user_id,))
            
            progress = cursor.fetchone()
            if not progress:
                # Initialize progress if doesn't exist
                return {
                    'points': 0,
                    'level': 1,
                    'streak_days': 0,
                    'quests_completed_today': 0,
                    'total_quests_completed': 0,
                    'today_quests': []
                }
            
            points, level, streak_days = progress
            
            # Get today's quests
            cursor = self.conn.execute('''
                SELECT quest_id, title, description, quest_type, difficulty, points, emoji, completed
                FROM user_quests 
                WHERE user_id = ? AND date(created_at) = date('now')
                ORDER BY created_at
            ''', (user_id,))
            
            today_quests = []
            quests_completed_today = 0
            
            for row in cursor.fetchall():
                quest = {
                    'id': row[0],
                    'title': row[1],
                    'description': row[2],
                    'type': row[3],
                    'difficulty': row[4],
                    'points': row[5],
                    'emoji': row[6],
                    'completed': bool(row[7])
                }
                today_quests.append(quest)
                if quest['completed']:
                    quests_completed_today += 1
            
            # Get total quests completed
            cursor = self.conn.execute('''
                SELECT COUNT(*) FROM user_quests 
                WHERE user_id = ? AND completed = 1
            ''', (user_id,))
            
            total_quests_completed = cursor.fetchone()[0]
            
            # Calculate next level progress
            points_needed = level * 100
            progress_percent = min(100, (points / points_needed) * 100) if points_needed > 0 else 0
            
            return {
                'points': points,
                'level': level,
                'streak_days': streak_days,
                'quests_completed_today': quests_completed_today,
                'total_quests_completed': total_quests_completed,
                'today_quests': today_quests,
                'next_level_points': points_needed,
                'progress_percent': progress_percent,
                'points_to_next_level': max(0, points_needed - points)
            }
            
        except Exception as e:
            print(f"Error getting user progress: {e}")
            return {
                'points': 0,
                'level': 1,
                'streak_days': 0,
                'quests_completed_today': 0,
                'total_quests_completed': 0,
                'today_quests': [],
                'next_level_points': 100,
                'progress_percent': 0,
                'points_to_next_level': 100
            }
    
    def update_streak(self, user_id):
        """Update user's daily streak"""
        try:
            cursor = self.conn.execute('''
                SELECT streak_days, updated_at FROM user_progress 
                WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            if not result:
                return 1
            
            streak_days, last_updated = result
            
            # Check if last update was yesterday
            if last_updated:
                last_date = datetime.strptime(last_updated, '%Y-%m-%d %H:%M:%S').date()
                today = datetime.now().date()
                
                if (today - last_date).days == 1:
                    # Consecutive day - increment streak
                    new_streak = streak_days + 1
                elif (today - last_date).days == 0:
                    # Same day - keep streak
                    new_streak = streak_days
                else:
                    # Broken streak - reset to 1
                    new_streak = 1
            else:
                new_streak = 1
            
            # Update streak
            self.conn.execute('''
                UPDATE user_progress 
                SET streak_days = ?, updated_at = datetime('now')
                WHERE user_id = ?
            ''', (new_streak, user_id))
            
            self.conn.commit()
            return new_streak
            
        except Exception as e:
            print(f"Error updating streak: {e}")
            return 1
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()