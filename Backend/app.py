from flask import Flask, request, jsonify, send_from_directory, redirect, session
from flask_cors import CORS
import os, librosa, numpy as np, joblib, tempfile, torch
from pydub import AudioSegment
import speech_recognition as sr
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from datetime import datetime, timedelta
import json
import random

from analytics_engine import AnalyticsEngine
from predictive_engine import PredictiveEngine
from digital_twin import DigitalTwin
from content_library import ContentLibrary
from therapeutic_engine import TherapeuticEngine
from audio_player import AudioPlayer
from soundscape_generator import SoundscapeGenerator
from quest_system import QuestSystem
from youtube_integration import YouTubeIntegration
from spotify_integration import SpotifyIntegration

from database import (
    get_db_connection,
    generate_unique_user_id, 
    create_user,
    get_user_by_id,
    get_user_by_email,
    create_mindmirror_entry,
    get_user_mindmirror_entries,
    create_user_baseline,
    get_user_baseline,
    create_user_pattern,
    get_user_patterns,
    create_burnout_risk,
    create_digital_twin_rule,
    create_user_prediction
)

app = Flask(__name__)
app.secret_key = 'mindmirror_secret_key_2025'  # Needed for sessions
CORS(app)

# ✅ FIX: Use local uploads directory instead of temp
UPLOAD_DIR = "uploads"

# ✅ FIX: Create uploads directory if it doesn't exist
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Debug route to check file existence
@app.route('/debug/files')
def debug_files():
    files = []
    for file in ['landing.html', 'dashboard.html', 'auth.css', 'auth.js', 'style.css', 'script.js']:
        exists = os.path.exists(file)
        files.append(f"{file}: {'✅ EXISTS' if exists else '❌ MISSING'}")
    return "<br>".join(files)

AUDIO_MODEL_PATH = "emotion_pipeline.pkl"
TEXT_MODEL_NAME = "cardiffnlp/twitter-roberta-base-emotion"
TEXT_EMOTION_LABELS = ['anger','joy','optimism','sadness','disgust','fear','love']
SAMPLE_RATE = 22050
CONF_THRESHOLD = 0.4

# Load models
audio_model = joblib.load(AUDIO_MODEL_PATH)
text_tokenizer = AutoTokenizer.from_pretrained(TEXT_MODEL_NAME)
text_model = AutoModelForSequenceClassification.from_pretrained(TEXT_MODEL_NAME)

EMOTION_KEYWORDS = {
    "joy":["happy","glad","excited","awesome","great","exhilarated","amazing","light","nice","content","cheerful","jovial","jolly","buoyant","elated"],
    "sadness":["sad","upset","cry","depressed","blue","low","disappointed"], 
    "anger":["angry","mad","furious","annoyed","agitated","pissed","red"],
    "fear":["scared","afraid","petrified","terror","fright","panic","horror","dreadful"],
    "anxiety":["nervous","anxious","unease","uneasiness","apprehensive","consternation","trepid"],
    "love":["love","affection","sweet"],
    "disgust":["disgust","hate","gross"],
    "optimism":["hopeful","positive","confident"]
}

def extract_audio_features(path):
    try:
        y, sr = librosa.load(path, sr=SAMPLE_RATE)
        if len(y)<sr: y=np.pad(y,(0,sr-len(y)),'constant')
        mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40).T, axis=0)
        return mfcc.reshape(1,-1)
    except: return None

def transcribe_audio(path):
    try:
        r = sr.Recognizer()
        with sr.AudioFile(path) as source:
            audio = r.record(source)
        return r.recognize_google(audio).lower()
    except: return ""

def predict_audio_emotion(path):
    features = extract_audio_features(path)
    pred, conf = "Uncertain", 0.0
    if features is not None:
        try:
            proba = audio_model.predict_proba(features)[0]
            pred = audio_model.classes_[np.argmax(proba)]
            conf = np.max(proba)
        except: pass
    if pred=="Uncertain" or conf<CONF_THRESHOLD:
        text = transcribe_audio(path)
        for emotion, keywords in EMOTION_KEYWORDS.items():
            if any(word in text for word in keywords):
                return emotion.capitalize(), 0.5
    return pred.capitalize(), float(conf)

def predict_text_emotion(text):
    try:
        inputs = text_tokenizer(text, return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = text_model(**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=1)[0]
        idx = torch.argmax(probs).item()
        conf = float(probs[idx])
        return (TEXT_EMOTION_LABELS[idx], conf) if conf>=CONF_THRESHOLD else ("Uncertain", conf)
    except: return "Uncertain", 0.0

# ✅ MOOD SCORE ALGORITHM
def calculate_mood_score(emotion, confidence):
    """
    Convert emotion and confidence into a numerical score (0-100).
    Higher scores represent more positive moods.
    """
    emotion = emotion.lower() if emotion else "uncertain"
    
    # Define base scores for each emotion (0-100 scale)
    emotion_base_scores = {
        "joy": 85, "love": 90, "optimism": 80,
        "neutral": 50, "uncertain": 50,
        "sadness": 30, "fear": 25, "anger": 20, "disgust": 15, "anxiety": 20
    }
    
    # Get base score for the emotion, default to 50 if not found
    base_score = emotion_base_scores.get(emotion, 50)
    
    # Adjust score based on confidence (higher confidence = stronger effect)
    # Confidence ranges from 0.0 to 1.0
    adjusted_score = base_score * confidence
    
    # Ensure score is between 0-100
    final_score = max(0, min(100, int(adjusted_score)))
    
    return final_score

# ===== Routes =====

@app.route("/uploads/<filename>")
def serve_audio(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ✅ ADD THESE MISSING STATIC FILE ROUTES
@app.route('/mic_test.html')
def serve_mic_test():
    return send_from_directory('.', 'mic_test.html')

# Serve all CSS files
@app.route('/<filename>.css')
def serve_css(filename):
    return send_from_directory('.', f'{filename}.css')

# Serve all JS files  
@app.route('/<filename>.js')
def serve_js(filename):
    return send_from_directory('.', f'{filename}.js')

# Serve favicon to prevent 404 errors
@app.route('/favicon.ico')
def favicon():
    return '', 204  # Return no content instead of 404

@app.route("/analyze_live_audio", methods=["POST"])
def analyze_live_audio():
    if not request.data:
        return jsonify({"error":"No audio"}),400
    raw_path = os.path.join(UPLOAD_DIR, "live_recording.webm")
    with open(raw_path,"wb") as f: f.write(request.data)
    # Convert to WAV
    wav_path = os.path.join(UPLOAD_DIR, "live_recording.wav")
    AudioSegment.from_file(raw_path, format="webm").set_frame_rate(SAMPLE_RATE).set_channels(1).export(wav_path, format="wav")
    audio_emotion, audio_conf = predict_audio_emotion(wav_path)
    return jsonify({
        "Audio_Emotion": audio_emotion,
        "Audio_Conf": round(audio_conf,2),
        "Final_Emotion": audio_emotion,
        "audio_url": f"/uploads/live_recording.wav"
    })

@app.route("/analyze", methods=["POST"])
def analyze():
    # Get user input
    text_input = request.form.get("text")
    audio_file = request.files.get("audio")

    # Get user_id from session to link this analysis to the user
    if 'user_id' not in session:
        return jsonify({"error": "User not logged in"}), 401
    user_id = session['user_id']

    # Initialize variables
    text_emotion, text_conf = ("Not provided", 0.0)
    audio_emotion, audio_conf = ("Not provided", 0.0)
    audio_filename = None  # This will store the filename for the database

    # Process text input
    if text_input: 
        text_emotion, text_conf = predict_text_emotion(text_input)
    
    # Process audio input
    if audio_file:
        file_extension = audio_file.filename.split('.')[-1].lower()
        # ✅ Create a unique filename using timestamp to avoid overwrites
        import time
        timestamp = int(time.time())
        base_filename = f"audio_{user_id}_{timestamp}"
        
        # Save the original file
        original_path = os.path.join(UPLOAD_DIR, f"{base_filename}.{file_extension}")
        audio_file.save(original_path)
        
        if file_extension == 'webm':
            # Convert WEBM to WAV for processing and storage
            wav_path = os.path.join(UPLOAD_DIR, f"{base_filename}.wav")
            AudioSegment.from_file(original_path, format="webm").set_frame_rate(SAMPLE_RATE).set_channels(1).export(wav_path, format="wav")
            audio_emotion, audio_conf = predict_audio_emotion(wav_path)
            audio_filename = f"{base_filename}.wav"  # Store the WAV filename
        else:
            # Use the original file for processing
            audio_emotion, audio_conf = predict_audio_emotion(original_path)
            audio_filename = f"{base_filename}.{file_extension}"  # Store the original filename

    # Determine final emotion
    final = audio_emotion if audio_conf >= text_conf else text_emotion
    
    print(f"🔊 Audio Result: {audio_emotion} (Conf: {audio_conf})")
    print(f"📝 Text Result: {text_emotion} (Conf: {text_conf})")
    print(f"🤔 Final Decision: {final}")

    # ✅ SAVE TO DATABASE
    conn = get_db_connection()
    save_success = False
    try:
        mood_score = calculate_mood_score(final, max(float(text_conf), float(audio_conf)))
        save_success = create_mindmirror_entry(
            conn=conn,
            user_id=user_id,
            journal_text=text_input if text_input else None,
            text_emotion=text_emotion if text_input != "Not provided" else None,
            text_confidence=float(text_conf) if text_input and text_conf != 0.0 else None,
            audio_emotion=audio_emotion if audio_file and audio_emotion != "Not provided" else None,
            audio_confidence=float(audio_conf) if audio_file and audio_conf != 0.0 else None,
            final_emotion=final,
            audio_file_path=audio_filename,  # ✅ Now storing just the filename, not full path
            mood_score=mood_score
        )
        if save_success:
            print("✅ Analysis saved to database successfully!")
        else:
            print("❌ Failed to save analysis to database.")
    except Exception as e:
        print(f"❌ Error saving to database: {e}")
    finally:
        conn.close()

    # Return results to frontend
    return jsonify({
        "Text_Emotion": text_emotion if text_input else "Not provided",
        "Text_Conf": round(text_conf, 2) if text_input else None,
        "Audio_Emotion": audio_emotion if audio_file else "Not provided",
        "Audio_Conf": round(audio_conf, 2) if audio_file else None,
        "Final_Emotion": final,
        "audio_url": f"/uploads/{audio_filename}" if audio_file else None,  # ✅ Updated to use the filename
        "saved_to_db": save_success
    })

# ✅ AUTHENTICATION ROUTES
@app.route('/')
def landing():
    """Serve the landing page - redirect to dashboard if already logged in"""
    if 'user_id' in session:
        return redirect('/dashboard')
    
    try:
        with open('landing.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Landing page not found. Error: {str(e)}", 404

@app.route('/dashboard')
def dashboard():
    """Serve the main dashboard - redirect to landing if not logged in"""
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        with open('dashboard.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Dashboard not found. Error: {str(e)}", 404

@app.route('/history')
def history():
    """Serve the history page - redirect to landing if not logged in"""
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        with open('history.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"History page not found. Error: {str(e)}", 404

@app.route('/logout')
def logout():
    """Logout user and clear session"""
    session.clear()
    return redirect('/')

@app.route('/profile')
def profile():
    """Serve the profile hub page - redirect to landing if not logged in"""
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        with open('profile.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Profile page not found. Error: {str(e)}", 404

# ✅ NEW: DEDICATED PAGES FOR FEATURES
@app.route('/insights')
def insights():
    """Serve the insights page"""
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        with open('insights.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Insights page not found. Error: {str(e)}", 404

@app.route('/burnout')
def burnout():
    """Serve the burnout assessment page"""
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        with open('burnout.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Burnout page not found. Error: {str(e)}", 404

@app.route('/simulator')
def simulator():
    """Serve the digital twin simulator page"""
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        with open('simulator.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Simulator page not found. Error: {str(e)}", 404

@app.route('/forecast')
def forecast():
    """Serve the mood forecast page"""
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        with open('forecast.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Forecast page not found. Error: {str(e)}", 404

@app.route('/therapy')
def therapy():
    """Serve the therapy hub page"""
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        with open('therapy.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Therapy page not found. Error: {str(e)}", 404

@app.route('/quests')
def quests():
    """Serve the quests page"""
    if 'user_id' not in session:
        return redirect('/')
    
    try:
        with open('quests.html', 'r', encoding='utf-8') as f:
            content = f.read()
        return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except Exception as e:
        return f"Quests page not found. Error: {str(e)}", 404

# ✅ STATIC FILE ROUTES
@app.route('/auth.css')
def serve_auth_css():
    return send_from_directory('.', 'auth.css')

@app.route('/auth.js')
def serve_auth_js():
    return send_from_directory('.', 'auth.js')

@app.route('/style.css')
def serve_style_css():
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def serve_script_js():
    return send_from_directory('.', 'script.js')

@app.route('/history.css')
def serve_history_css():
    return send_from_directory('.', 'history.css')

@app.route('/history.js')
def serve_history_js():
    return send_from_directory('.', 'history.js')

@app.route('/profile.js')
def serve_profile_js():
    return send_from_directory('.', 'profile.js')

@app.route('/therapy.js')
def serve_therapy_js():
    return send_from_directory('.', 'therapy.js')

@app.route('/quests.js')
def serve_quests_js():
    return send_from_directory('.', 'quests.js')

# ✅ API ROUTES
@app.route('/api/generate_user_id', methods=['GET'])
def api_generate_user_id():
    """Generate a unique user ID"""
    conn = get_db_connection()
    try:
        user_id = generate_unique_user_id(conn)
        return jsonify({'success': True, 'user_id': user_id})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/api/register', methods=['POST'])
def api_register():
    """Register a new user"""
    conn = get_db_connection()
    try:
        data = request.get_json()
        user_id = data['user_id']
        full_name = data['full_name']
        email = data['email']
        
        success = create_user(conn, user_id, full_name, email)
        
        if success:
            # Store user info in session
            session['user_id'] = user_id
            session['user_name'] = full_name
            session['user_email'] = email
            
            return jsonify({
                'success': True,
                'redirect': '/profile'  # ✅ Redirect to profile hub instead of dashboard
            })
        else:
            return jsonify({'success': False, 'message': 'User ID already exists'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def api_login():
    """Login existing user"""
    conn = get_db_connection()
    try:
        data = request.get_json()
        user_id = data['user_id']
        
        user = get_user_by_id(conn, user_id)
        
        if user:
            # Store user info in session
            session['user_id'] = user['user_id']
            session['user_name'] = user['full_name']
            session['user_email'] = user['email']
            
            return jsonify({
                'success': True,
                'user_id': user['user_id'],
                'full_name': user['full_name'],
                'email': user['email'],
                'redirect': '/profile'
            })
        else:
            return jsonify({'success': False, 'message': 'User ID not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

@app.route('/api/recover_id', methods=['POST'])
def api_recover_id():
    """Recover user ID by email"""
    conn = get_db_connection()
    try:
        data = request.get_json()
        email = data['email']
        
        user = get_user_by_email(conn, email)
        
        if user:
            return jsonify({
                'success': True,
                'user_id': user['user_id']
            })
        else:
            return jsonify({'success': False, 'message': 'Email not found'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})
    finally:
        conn.close()

# ✅ UPDATED API ENDPOINT: Get user's analysis history
@app.route('/api/get_entries', methods=['GET'])
def api_get_entries():
    """Get mindmirror entries for the logged-in user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401

    user_id = session['user_id']
    get_all = request.args.get('all', 'false').lower() == 'true'  # ✅ CHECK IF ALL RECORDS REQUESTED
    conn = get_db_connection()
    
    try:
        if get_all:
            # ✅ GET ALL RECORDS FOR CSV DOWNLOAD
            entries = get_user_mindmirror_entries(conn, user_id, limit=0)  # 0 = no limit
        else:
            # ✅ GET ONLY LATEST 5 FOR TABLE DISPLAY
            entries = get_user_mindmirror_entries(conn, user_id, limit=5)
        
        # Get total count for UI
        total_count = conn.execute(
            'SELECT COUNT(*) FROM mindmirror_entries WHERE user_id = ?', 
            (user_id,)
        ).fetchone()[0]
        
        # Convert to dictionaries
        entries_list = [dict(entry) for entry in entries]
        
        return jsonify({
            'success': True,
            'entries': entries_list,
            'total_count': total_count
        })
        
    except Exception as e:
        print(f"Error fetching entries: {e}")
        return jsonify({'success': False, 'message': 'Could not fetch entries'}), 500
    finally:
        conn.close()

# ✅ NEW API ENDPOINT: Update user profile
@app.route('/api/update_profile', methods=['POST'])
def api_update_profile():
    """Update user's name and email"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    user_id = session['user_id']
    conn = get_db_connection()
    
    try:
        data = request.get_json()
        full_name = data['full_name']
        email = data['email']
        
        # Update user in database
        conn.execute(
            'UPDATE users SET full_name = ?, email = ? WHERE user_id = ?',
            (full_name, email, user_id)
        )
        conn.commit()
        
        # Update session data
        session['user_name'] = full_name
        session['user_email'] = email
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        print(f"Error updating profile: {e}")
        return jsonify({'success': False, 'message': 'Could not update profile'}), 500
    finally:
        conn.close()

# ✅ NEW: Get user analytics and patterns
@app.route('/api/get_analytics', methods=['GET'])
def api_get_analytics():
    """Get user analytics, patterns, and insights"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    user_id = session['user_id']
    analytics_engine = AnalyticsEngine()
    
    try:
        # Calculate baseline
        baseline = analytics_engine.calculate_user_baseline(user_id)
        
        # Detect patterns
        patterns = analytics_engine.detect_temporal_patterns(user_id)
        
        # Save baseline to database if calculated
        if baseline:
            conn = get_db_connection()
            create_user_baseline(
                conn, user_id,
                voice_energy=baseline.get('voice_energy_baseline'),
                speech_rate=baseline.get('speech_rate_baseline'),
                avg_mood=baseline.get('avg_mood_score')
            )
            conn.close()
        
        # Save patterns to database if detected
        if patterns:
            conn = get_db_connection()
            if patterns.get('weekly'):
                create_user_pattern(
                    conn, user_id, 'weekly', 
                    json.dumps(patterns['weekly']), 0.8
                )
            if patterns.get('time_of_day'):
                create_user_pattern(
                    conn, user_id, 'time_of_day',
                    json.dumps(patterns['time_of_day']), 0.7
                )
            conn.close()
        
        return jsonify({
            'success': True,
            'baseline': baseline,
            'patterns': patterns,
            'insights': generate_insights(baseline, patterns)
        })
        
    except Exception as e:
        print(f"Error generating analytics: {e}")
        return jsonify({'success': False, 'message': 'Could not generate analytics'}), 500
    finally:
        analytics_engine.close()

# ✅ NEW: Burnout risk assessment
@app.route('/api/burnout_assessment', methods=['GET'])
def api_burnout_assessment():
    """Get burnout risk assessment for user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    user_id = session['user_id']
    predictive_engine = PredictiveEngine()
    
    try:
        assessment = predictive_engine.assess_burnout_risk(user_id)
        
        # Save to database
        conn = get_db_connection()
        create_burnout_risk(
            conn, user_id, 
            assessment['risk_level'],
            assessment['risk_score'],
            assessment['triggers']
        )
        conn.close()
        
        return jsonify({
            'success': True,
            'assessment': assessment
        })
        
    except Exception as e:
        print(f"Error in burnout assessment: {e}")
        return jsonify({'success': False, 'message': 'Could not assess burnout risk'}), 500
    finally:
        predictive_engine.close()

# ✅ NEW: Digital twin simulation
@app.route('/api/simulate_scenario', methods=['POST'])
def api_simulate_scenario():
    """Run digital twin simulation"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    scenario = data.get('scenario', '')
    
    if not scenario:
        return jsonify({'success': False, 'message': 'No scenario provided'}), 400
    
    digital_twin = DigitalTwin()
    
    try:
        simulation = digital_twin.simulate_scenario(user_id, scenario)
        
        return jsonify({
            'success': True,
            'simulation': simulation
        })
        
    except Exception as e:
        print(f"Error in simulation: {e}")
        return jsonify({'success': False, 'message': 'Could not run simulation'}), 500
    finally:
        digital_twin.close()

# ✅ NEW: Learn digital twin rules
@app.route('/api/learn_rules', methods=['POST'])
def api_learn_rules():
    """Learn personalized rules from user data"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    user_id = session['user_id']
    digital_twin = DigitalTwin()
    
    try:
        rules = digital_twin.learn_user_rules(user_id)
        
        return jsonify({
            'success': True,
            'rules': rules
        })
        
    except Exception as e:
        print(f"Error learning rules: {e}")
        return jsonify({'success': False, 'message': 'Could not learn rules'}), 500
    finally:
        digital_twin.close()

# ✅ NEW: Get mood forecast
@app.route('/api/mood_forecast', methods=['GET'])
def api_mood_forecast():
    """Get mood forecast for next few days"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    user_id = session['user_id']
    
    try:
        forecast = generate_mood_forecast(user_id)
        
        return jsonify({
            'success': True,
            'forecast': forecast
        })
        
    except Exception as e:
        print(f"Error generating forecast: {e}")
        return jsonify({'success': False, 'message': 'Could not generate forecast'}), 500

# ✅ PHASE 3A: CONTENT LIBRARY ENDPOINTS
@app.route('/api/init_content_library', methods=['POST'])
def api_init_content_library():
    """Initialize therapeutic content library (run once)"""
    try:
        content_lib = ContentLibrary()
        content_lib.initialize_default_content()
        content_lib.close()
        return jsonify({'success': True, 'message': 'Content library initialized successfully!'})
    except Exception as e:
        print(f"Error initializing content library: {e}")
        return jsonify({'success': False, 'message': 'Could not initialize content library'}), 500

@app.route('/api/get_therapy_recommendations', methods=['POST'])
def api_get_therapy_recommendations():
    """Get personalized therapeutic recommendations"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    current_emotion = data.get('emotion', '').lower()
    
    if not current_emotion:
        return jsonify({'success': False, 'message': 'No emotion provided'}), 400
    
    therapeutic_engine = TherapeuticEngine()
    try:
        therapy_plan = therapeutic_engine.generate_therapy_plan(user_id, current_emotion)
        return jsonify({
            'success': True,
            'therapy_plan': therapy_plan
        })
    except Exception as e:
        print(f"Error generating therapy plan: {e}")
        return jsonify({'success': False, 'message': 'Could not generate therapy plan'}), 500
    finally:
        therapeutic_engine.close()

@app.route('/api/get_immediate_relief', methods=['POST'])
def api_get_immediate_relief():
    """Get immediate relief recommendations only"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    current_emotion = data.get('emotion', '').lower()
    
    content_lib = ContentLibrary()
    try:
        recommendations = content_lib.get_therapeutic_recommendations(current_emotion, ['exercise', 'video'], 1)
        
        immediate_relief = []
        for content_type, items in recommendations.items():
            if items:
                # Filter for short interventions
                short_items = [item for item in items if item.get('duration_minutes', 30) <= 10]
                if short_items:
                    immediate_relief.extend(short_items[:2])  # Max 2 items
        
        return jsonify({
            'success': True,
            'immediate_relief': immediate_relief[:3]  # Max 3 total
        })
    except Exception as e:
        print(f"Error getting immediate relief: {e}")
        return jsonify({'success': False, 'message': 'Could not get immediate relief'}), 500
    finally:
        content_lib.close()

# ✅ PHASE 3B: SONIC THERAPY ENDPOINTS
@app.route('/api/generate_soundscape', methods=['POST'])
def api_generate_soundscape():
    """Generate personalized soundscape"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    emotion = data.get('emotion', '').lower()
    intensity = data.get('intensity', 'medium')
    duration = data.get('duration', 15)
    
    soundscape_gen = SoundscapeGenerator()
    try:
        soundscape = soundscape_gen.generate_soundscape(emotion, intensity, duration)
        return jsonify({
            'success': True,
            'soundscape': soundscape
        })
    except Exception as e:
        print(f"Soundscape generation error: {e}")
        return jsonify({'success': False, 'message': 'Could not generate soundscape'}), 500

@app.route('/api/start_playback', methods=['POST'])
def api_start_playback():
    """Start audio playback session"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    content_id = data.get('content_id')
    
    # Get content from database
    conn = get_db_connection()
    content = conn.execute(
        'SELECT * FROM therapeutic_content WHERE id = ?', 
        (content_id,)
    ).fetchone()
    conn.close()
    
    if not content:
        return jsonify({'success': False, 'message': 'Content not found'}), 404
    
    content_dict = dict(content)
    
    # Start playback (in a real app, this would interface with actual audio player)
    return jsonify({
        'success': True,
        'message': 'Playback started',
        'content': content_dict
    })

@app.route('/api/playback_progress', methods=['POST'])
def api_playback_progress():
    """Update playback progress"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    content_id = data.get('content_id')
    progress_seconds = data.get('progress_seconds', 0)
    completed = data.get('completed', False)
    
    # Log progress to database
    conn = get_db_connection()
    if completed:
        conn.execute('''
        UPDATE user_playback_sessions 
        SET completed = 1, progress_seconds = ?, ended_at = datetime('now')
        WHERE user_id = ? AND content_id = ? AND completed = 0
        ''', (progress_seconds, session['user_id'], content_id))
    else:
        conn.execute('''
        UPDATE user_playback_sessions 
        SET progress_seconds = ?
        WHERE user_id = ? AND content_id = ? AND completed = 0
        ''', (progress_seconds, session['user_id'], content_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'success': True})

# ✅ PHASE 3C: LIFESTYLE ENGINE ENDPOINTS
@app.route('/api/get_lifestyle_recommendations', methods=['POST'])
def api_get_lifestyle_recommendations():
    """Get personalized lifestyle recommendations"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    data = request.get_json()
    emotion = data.get('emotion', '').lower()
    time_of_day = data.get('time_of_day', '')
    
    content_lib = ContentLibrary()
    try:
        # If no specific time provided, determine based on current time
        if not time_of_day:
            current_hour = datetime.now().hour
            if 5 <= current_hour < 12:
                time_of_day = 'morning'
            elif 12 <= current_hour < 17:
                time_of_day = 'afternoon'
            else:
                time_of_day = 'evening'
        
        recommendations = content_lib.get_lifestyle_recommendations(emotion, time_of_day)
        return jsonify({
            'success': True,
            'recommendations': [dict(rec) for rec in recommendations],
            'time_of_day': time_of_day
        })
    except Exception as e:
        print(f"Lifestyle recommendations error: {e}")
        return jsonify({'success': False, 'message': 'Could not get lifestyle recommendations'}), 500
    finally:
        content_lib.close()

# ✅ PHASE 3D: QUEST SYSTEM ENDPOINTS
@app.route('/api/get_daily_quests', methods=['GET'])
def api_get_daily_quests():
    """Get daily therapeutic quests for user"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    user_id = session['user_id']
    quest_system = QuestSystem()
    
    try:
        quests = quest_system.generate_daily_quests(user_id)
        return jsonify({
            'success': True,
            'quests': quests
        })
    except Exception as e:
        print(f"Quest generation error: {e}")
        return jsonify({'success': False, 'message': 'Could not generate quests'}), 500
    finally:
        quest_system.close()

@app.route('/api/complete_quest', methods=['POST'])
def api_complete_quest():
    """Mark a quest as completed"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    quest_id = data.get('quest_id')
    
    quest_system = QuestSystem()
    
    try:
        result = quest_system.complete_quest(user_id, quest_id)
        return jsonify({
            'success': result['success'],
            'message': result['message'],
            'points_earned': result.get('points_earned', 0),
            'level_up': result.get('level_up', False)
        })
    except Exception as e:
        print(f"Quest completion error: {e}")
        return jsonify({'success': False, 'message': 'Could not complete quest'}), 500
    finally:
        quest_system.close()

@app.route('/api/get_user_progress', methods=['GET'])
def api_get_user_progress():
    """Get user's quest progress and stats"""
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'User not logged in'}), 401
    
    user_id = session['user_id']
    quest_system = QuestSystem()
    
    try:
        progress = quest_system.get_user_progress(user_id)
        return jsonify({
            'success': True,
            'progress': progress
        })
    except Exception as e:
        print(f"Progress fetch error: {e}")
        return jsonify({'success': False, 'message': 'Could not fetch progress'}), 500
    finally:
        quest_system.close()

# ✅ NEW: Helper function for insights
def generate_insights(baseline, patterns):
    """Generate human-readable insights from data"""
    insights = []
    
    if not baseline or not patterns:
        return ["🔍 Keep using MindMirror to unlock personalized insights!"]
    
    # Weekly pattern insights
    if patterns.get('weekly'):
        weekly = patterns['weekly']
        if weekly:
            best_day = max(weekly, key=weekly.get)
            worst_day = min(weekly, key=weekly.get)
            day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            insights.append(f"🌟 Your best mood days are {day_names[best_day]}s")
            insights.append(f"💡 You tend to feel lower on {day_names[worst_day]}s")
    
    # Time of day insights
    if patterns.get('time_of_day'):
        time_patterns = patterns['time_of_day']
        if time_patterns:
            best_time = max(time_patterns, key=time_patterns.get)
            insights.append(f"🕒 You're most positive during the {best_time}")
    
    # Baseline insights
    if baseline and baseline.get('avg_mood_score'):
        avg_mood = baseline['avg_mood_score']
        if avg_mood > 70:
            insights.append("😊 You maintain a generally positive outlook!")
        elif avg_mood < 40:
            insights.append("🤗 Remember to be gentle with yourself during tough periods")
        else:
            insights.append("⚖️ You have a balanced emotional range")
    
    return insights if insights else ["📈 Continue tracking to discover more patterns!"]

# ✅ NEW: Helper function for mood forecasting
def generate_mood_forecast(user_id):
    """Generate simple mood forecast based on patterns"""
    from analytics_engine import AnalyticsEngine
    analytics = AnalyticsEngine()
    
    baseline = analytics.calculate_user_baseline(user_id)
    patterns = analytics.detect_temporal_patterns(user_id)
    analytics.close()
    
    if not baseline or not patterns:
        return {"message": "Need more data for forecasting"}
    
    base_mood = baseline.get('avg_mood_score', 50)
    
    # Simple forecasting based on weekly patterns
    forecast = []
    today_weekday = datetime.now().weekday()
    
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    
    if patterns.get('weekly'):
        weekly_patterns = patterns['weekly']
        
        for i in range(3):  # Next 3 days forecast
            forecast_day = (today_weekday + i + 1) % 7
            day_name = day_names[forecast_day]
            
            # Get historical average for this weekday
            historical_mood = weekly_patterns.get(forecast_day, base_mood)
            
            # Add some randomness for realism
            variation = random.randint(-5, 5)
            predicted_mood = max(0, min(100, historical_mood + variation))
            
            confidence = 0.6 + (random.random() * 0.2)  # 60-80% confidence
            
            forecast.append({
                'day': day_name,
                'predicted_mood': int(predicted_mood),
                'confidence': round(confidence, 2),
                'trend': 'stable' if abs(predicted_mood - base_mood) < 10 else 
                        'improving' if predicted_mood > base_mood else 'declining'
            })
    else:
        # Fallback forecast
        for i in range(3):
            forecast_day = (today_weekday + i + 1) % 7
            day_name = day_names[forecast_day]
            
            forecast.append({
                'day': day_name,
                'predicted_mood': base_mood,
                'confidence': 0.5,
                'trend': 'stable'
            })
    
    return {
        'base_mood': base_mood,
        'forecast_days': forecast,
        'generated_at': datetime.now().isoformat()
    }

if __name__=="__main__":
    print("✅ Starting MindMirror server on port 5000...")
    print("📁 Current directory:", os.getcwd())
    print("📁 Files found:", [f for f in os.listdir('.') if f.endswith(('.html', '.css', '.js'))])
    app.run(host="0.0.0.0", port=5000, debug=True)