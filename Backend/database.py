import sqlite3
import os
import uuid
from datetime import datetime
import json
import timedelta

# Database file path (in the same directory as your app)
DATABASE_PATH = "mindmirror.db"

def get_db_connection():
    """Create and return a database connection"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This enables name-based access to columns
    return conn

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    try:
        # Create users table (EXACTLY like your diabetes project)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create mindmirror_entries table (this is new for mental health)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS mindmirror_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                journal_text TEXT,
                text_emotion TEXT,
                text_confidence REAL,
                audio_emotion TEXT,
                audio_confidence REAL,
                final_emotion TEXT,
                mood_score INTEGER,
                audio_file_path TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')
        conn.execute('''
        CREATE TABLE IF NOT EXISTS user_baselines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            voice_energy_baseline REAL,
            speech_rate_baseline REAL,
            avg_mood_score REAL,
            typical_sleep_hours INTEGER,
            created_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # NEW: User patterns table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS user_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            pattern_type TEXT NOT NULL,  -- 'weekly', 'time_of_day', 'seasonal'
            pattern_data TEXT NOT NULL,  -- JSON string of the pattern
            confidence_score REAL,
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    # NEW: Life integrations table
        conn.execute('''
        CREATE TABLE IF NOT EXISTS life_integrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            integration_type TEXT NOT NULL,  -- 'sleep', 'weather', 'calendar'
            data_point TEXT NOT NULL,
            mood_correlation REAL,
            recorded_date DATE DEFAULT CURRENT_DATE,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
        conn.execute('''
    CREATE TABLE IF NOT EXISTS burnout_risks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        risk_level TEXT NOT NULL,  -- 'low', 'medium', 'high'
        risk_score INTEGER,        -- 0-100
        triggers TEXT,             -- JSON of contributing factors
        detected_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
''')

# NEW: Digital twin rules and predictions
        conn.execute('''
    CREATE TABLE IF NOT EXISTS digital_twin_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        rule_type TEXT NOT NULL,    -- 'sleep_mood', 'social_energy', 'work_stress'
        condition TEXT NOT NULL,    -- 'if sleep < 6 hours'
        outcome TEXT NOT NULL,      -- 'then mood drops 25 points'
        confidence REAL,            -- How accurate this rule is (0-1)
        last_triggered DATETIME,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
''')

# NEW: User predictions and forecasts
        conn.execute('''
    CREATE TABLE IF NOT EXISTS user_predictions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        prediction_type TEXT NOT NULL,  -- 'burnout', 'mood_trend', 'weekly_forecast'
        prediction_data TEXT NOT NULL,  -- JSON with prediction details
        confidence REAL,
        prediction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
        valid_until DATETIME,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
''')
        conn.execute('''
    CREATE TABLE IF NOT EXISTS therapeutic_content (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content_type TEXT NOT NULL,      -- 'music', 'video', 'exercise', 'meditation'
        emotion_target TEXT NOT NULL,    -- 'sadness', 'anxiety', 'anger', 'joy', 'neutral'
        title TEXT NOT NULL,
        description TEXT,
        content_url TEXT NOT NULL,
        duration_minutes INTEGER,
        intensity_level TEXT,            -- 'gentle', 'moderate', 'intense'
        content_category TEXT,           -- 'immediate_relief', 'daily_practice', 'deep_work'
        scientific_basis TEXT,
        created_date DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')

# User therapy interactions
        conn.execute('''
    CREATE TABLE IF NOT EXISTS user_therapy_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        emotion_detected TEXT NOT NULL,
        content_id INTEGER,
        session_type TEXT,               -- 'immediate_relief', 'daily_boost'
        started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed BOOLEAN DEFAULT FALSE,
        mood_before INTEGER,
        mood_after INTEGER,
        feedback_rating INTEGER,
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        FOREIGN KEY (content_id) REFERENCES therapeutic_content (id)
    )
''')

# Lifestyle recommendations
        conn.execute('''
    CREATE TABLE IF NOT EXISTS lifestyle_recommendations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        emotion_target TEXT NOT NULL,
        time_of_day TEXT,                -- 'morning', 'afternoon', 'evening'
        category TEXT NOT NULL,          -- 'diet', 'exercise', 'social', 'mindfulness'
        recommendation TEXT NOT NULL,
        duration TEXT,                   -- '5min', '15min', '30min', '1h+'
        difficulty TEXT,                 -- 'easy', 'medium', 'hard'
        scientific_basis TEXT,
        created_date DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
        # Quest system tables
        conn.execute('''
CREATE TABLE IF NOT EXISTS user_quests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    quest_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    quest_type TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    points INTEGER NOT NULL,
    emoji TEXT,
    action_type TEXT,
    completed BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at DATETIME,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
''')

        conn.execute('''
CREATE TABLE IF NOT EXISTS user_progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT UNIQUE NOT NULL,
    points INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1,
    streak_days INTEGER DEFAULT 0,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
''')

        conn.execute('''
CREATE TABLE IF NOT EXISTS point_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    points INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
''')


        
        conn.commit()
        print("✅ Database initialized successfully!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
    finally:
        conn.close()

def generate_unique_user_id(conn):
    """Generate a unique user ID (EXACTLY like your diabetes project)"""
    while True:
        new_id = str(uuid.uuid4())[:8].upper()  # First 8 chars of UUID
        # Check if ID already exists
        existing = conn.execute(
            'SELECT 1 FROM users WHERE user_id = ?', (new_id,)
        ).fetchone()
        if not existing:
            return new_id

def create_user(conn, user_id, full_name, email):
    """Create a new user (EXACTLY like your diabetes project)"""
    try:
        conn.execute(
            'INSERT INTO users (user_id, full_name, email) VALUES (?, ?, ?)',
            (user_id, full_name, email)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user_by_id(conn, user_id):
    """Get user by ID (EXACTLY like your diabetes project)"""
    return conn.execute(
        'SELECT * FROM users WHERE user_id = ?', (user_id,)
    ).fetchone()

def get_user_by_email(conn, email):
    """Get user by email (EXACTLY like your diabetes project)"""
    return conn.execute(
        'SELECT * FROM users WHERE email = ?', (email,)
    ).fetchone()

# NEW: MindMirror-specific functions
def create_mindmirror_entry(conn, user_id, journal_text, text_emotion, text_confidence, 
                          audio_emotion, audio_confidence, final_emotion, audio_file_path=None, mood_score=None):
    """Create a new mental health analysis entry"""
    try:
        conn.execute('''
            INSERT INTO mindmirror_entries 
            (user_id, journal_text, text_emotion, text_confidence, 
             audio_emotion, audio_confidence, final_emotion, audio_file_path, mood_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, journal_text, text_emotion, text_confidence,
              audio_emotion, audio_confidence, final_emotion, audio_file_path, mood_score))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating mindmirror entry: {e}")
        return False

def get_user_mindmirror_entries(conn, user_id, limit=5):
    """Get mental health entries for a user (latest first)"""
    if limit == 0:
        # ✅ NO LIMIT - GET ALL RECORDS
        return conn.execute('''
            SELECT * FROM mindmirror_entries 
            WHERE user_id = ? 
            ORDER BY timestamp DESC
        ''', (user_id,)).fetchall()
    else:
        # ✅ WITH LIMIT - GET LATEST N RECORDS
        return conn.execute('''
            SELECT * FROM mindmirror_entries 
            WHERE user_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (user_id, limit)).fetchall()
def get_entries_by_date_range(conn, user_id, start_date, end_date):
    """Get entries for a specific date range"""
    return conn.execute('''
        SELECT * FROM mindmirror_entries 
        WHERE user_id = ? AND date(timestamp) BETWEEN ? AND ?
        ORDER BY timestamp DESC
    ''', (user_id, start_date, end_date)).fetchall()



def create_user_baseline(conn, user_id, voice_energy=None, speech_rate=None, avg_mood=None, sleep_hours=None):
    """Create or update user baseline data"""
    try:
        conn.execute('''
            INSERT OR REPLACE INTO user_baselines 
            (user_id, voice_energy_baseline, speech_rate_baseline, avg_mood_score, typical_sleep_hours)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, voice_energy, speech_rate, avg_mood, sleep_hours))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating user baseline: {e}")
        return False

def get_user_baseline(conn, user_id):
    """Get user's baseline data"""
    return conn.execute(
        'SELECT * FROM user_baselines WHERE user_id = ? ORDER BY created_date DESC LIMIT 1',
        (user_id,)
    ).fetchone()

def create_user_pattern(conn, user_id, pattern_type, pattern_data, confidence):
    """Store detected user patterns"""
    try:
        conn.execute('''
            INSERT INTO user_patterns (user_id, pattern_type, pattern_data, confidence_score)
            VALUES (?, ?, ?, ?)
        ''', (user_id, pattern_type, pattern_data, confidence))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating user pattern: {e}")
        return False

def get_user_patterns(conn, user_id, pattern_type=None):
    """Get user patterns, optionally filtered by type"""
    if pattern_type:
        return conn.execute(
            'SELECT * FROM user_patterns WHERE user_id = ? AND pattern_type = ? ORDER BY last_updated DESC',
            (user_id, pattern_type)
        ).fetchall()
    else:
        return conn.execute(
            'SELECT * FROM user_patterns WHERE user_id = ? ORDER BY last_updated DESC',
            (user_id,)
        ).fetchall()
    

# Add to your existing database functions:

def create_burnout_risk(conn, user_id, risk_level, risk_score, triggers):
    """Store burnout risk assessment"""
    try:
        conn.execute('''
            INSERT INTO burnout_risks (user_id, risk_level, risk_score, triggers)
            VALUES (?, ?, ?, ?)
        ''', (user_id, risk_level, risk_score, json.dumps(triggers)))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating burnout risk: {e}")
        return False

def get_recent_burnout_risks(conn, user_id, days=30):
    """Get recent burnout risks for a user"""
    return conn.execute('''
        SELECT * FROM burnout_risks 
        WHERE user_id = ? AND detected_date >= date('now', '-' || ? || ' days')
        ORDER BY detected_date DESC
    ''', (user_id, days)).fetchall()

def create_digital_twin_rule(conn, user_id, rule_type, condition, outcome, confidence):
    """Store a digital twin rule"""
    try:
        conn.execute('''
            INSERT INTO digital_twin_rules (user_id, rule_type, condition, outcome, confidence)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, rule_type, condition, outcome, confidence))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating digital twin rule: {e}")
        return False

def get_digital_twin_rules(conn, user_id, rule_type=None):
    """Get digital twin rules for a user"""
    if rule_type:
        return conn.execute('''
            SELECT * FROM digital_twin_rules 
            WHERE user_id = ? AND rule_type = ?
            ORDER BY confidence DESC
        ''', (user_id, rule_type)).fetchall()
    else:
        return conn.execute('''
            SELECT * FROM digital_twin_rules 
            WHERE user_id = ?
            ORDER BY confidence DESC
        ''', (user_id,)).fetchall()

def create_user_prediction(conn, user_id, prediction_type, prediction_data, confidence, valid_hours=24):
    """Store user prediction"""
    try:
        valid_until = datetime.now() + timedelta(hours=valid_hours)
        conn.execute('''
            INSERT INTO user_predictions (user_id, prediction_type, prediction_data, confidence, valid_until)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, prediction_type, json.dumps(prediction_data), confidence, valid_until))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating user prediction: {e}")
        return False

def get_active_predictions(conn, user_id, prediction_type=None):
    """Get active predictions (not expired)"""
    if prediction_type:
        return conn.execute('''
            SELECT * FROM user_predictions 
            WHERE user_id = ? AND prediction_type = ? AND valid_until > datetime('now')
            ORDER BY prediction_date DESC
        ''', (user_id, prediction_type)).fetchall()
    else:
        return conn.execute('''
            SELECT * FROM user_predictions 
            WHERE user_id = ? AND valid_until > datetime('now')
            ORDER BY prediction_date DESC
        ''', (user_id,)).fetchall()
# Add to your existing database functions:

def create_therapeutic_content(conn, content_type, emotion_target, title, description, 
                             content_url, duration_minutes, intensity_level, content_category, scientific_basis):
    """Add therapeutic content to library"""
    try:
        conn.execute('''
            INSERT INTO therapeutic_content 
            (content_type, emotion_target, title, description, content_url, 
             duration_minutes, intensity_level, content_category, scientific_basis)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (content_type, emotion_target, title, description, content_url,
              duration_minutes, intensity_level, content_category, scientific_basis))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating therapeutic content: {e}")
        return False

def get_content_by_emotion(conn, emotion_target, content_type=None, limit=5):
    """Get therapeutic content for specific emotion"""
    if content_type:
        return conn.execute('''
            SELECT * FROM therapeutic_content 
            WHERE emotion_target = ? AND content_type = ?
            ORDER BY RANDOM() LIMIT ?
        ''', (emotion_target, content_type, limit)).fetchall()
    else:
        return conn.execute('''
            SELECT * FROM therapeutic_content 
            WHERE emotion_target = ?
            ORDER BY RANDOM() LIMIT ?
        ''', (emotion_target, limit)).fetchall()

def create_therapy_session(conn, user_id, emotion_detected, content_id=None, session_type='immediate_relief'):
    """Record therapy session"""
    try:
        conn.execute('''
            INSERT INTO user_therapy_sessions 
            (user_id, emotion_detected, content_id, session_type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, emotion_detected, content_id, session_type))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating therapy session: {e}")
        return False

def get_lifestyle_recommendations(conn, emotion_target, time_of_day=None, category=None):
    """Get lifestyle recommendations"""
    query = 'SELECT * FROM lifestyle_recommendations WHERE emotion_target = ?'
    params = [emotion_target]
    
    if time_of_day:
        query += ' AND time_of_day = ?'
        params.append(time_of_day)
    
    if category:
        query += ' AND category = ?'
        params.append(category)
    
    query += ' ORDER BY RANDOM() LIMIT 3'
    
    return conn.execute(query, params).fetchall()

# Initialize the database when this module is imported
init_db()