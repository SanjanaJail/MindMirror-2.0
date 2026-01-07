# predictive_engine.py - Burnout detection and predictions

import json
from datetime import datetime, timedelta
import numpy as np
from database import get_db_connection

class PredictiveEngine:
    def __init__(self):
        self.conn = get_db_connection()
    
    def assess_burnout_risk(self, user_id):
        """Comprehensive burnout risk assessment"""
        try:
            print(f"🔍 Assessing burnout risk for user {user_id}")
            
            # Get recent entries (last 30 days)
            entries = self.conn.execute('''
                SELECT * FROM mindmirror_entries 
                WHERE user_id = ? AND timestamp >= date('now', '-30 days')
                ORDER BY timestamp DESC
            ''', (user_id,)).fetchall()
            
            if len(entries) < 5:
                return self._create_low_risk_assessment("Not enough data")
            
            risk_score = 0
            triggers = []
            
            # 1. Mood Decline Analysis
            mood_trend = self._analyze_mood_trend(entries)
            if mood_trend.get('trend') == 'declining' and mood_trend.get('strength', 0) > 0.3:
                risk_score += 25
                triggers.append(f"Mood declining ({mood_trend['strength']*100:.0f}% trend)")
            
            # 2. Negative Emotion Frequency
            neg_emotion_ratio = self._analyze_negative_emotions(entries)
            if neg_emotion_ratio > 0.6:  # 60% negative emotions
                risk_score += 20
                triggers.append(f"High negative emotions ({neg_emotion_ratio*100:.0f}%)")
            
            # 3. Journal Sentiment Analysis
            sentiment_trend = self._analyze_journal_sentiment(entries)
            if sentiment_trend < -0.2:
                risk_score += 15
                triggers.append("Increasing negative language")
            
            # 4. Engagement Patterns
            engagement_risk = self._analyze_engagement(entries)
            if engagement_risk:
                risk_score += engagement_risk['score']
                triggers.append(engagement_risk['reason'])
            
            # 5. Consistency Analysis
            consistency_risk = self._analyze_consistency(entries)
            if consistency_risk:
                risk_score += consistency_risk['score']
                triggers.append(consistency_risk['reason'])
            
            # Determine risk level
            risk_level = "low"
            if risk_score >= 50:
                risk_level = "high"
            elif risk_score >= 30:
                risk_level = "medium"
            
            assessment = {
                'risk_level': risk_level,
                'risk_score': risk_score,
                'triggers': triggers,
                'assessment_date': datetime.now().isoformat(),
                'entries_analyzed': len(entries),
                'recommendations': self._generate_recommendations(risk_level, triggers)
            }
            
            print(f"✅ Burnout assessment: {risk_level} (score: {risk_score})")
            return assessment
            
        except Exception as e:
            print(f"❌ Error in burnout assessment: {e}")
            return self._create_low_risk_assessment(f"Assessment error: {e}")
    
    def _analyze_mood_trend(self, entries):
        """Analyze mood trend over time"""
        if len(entries) < 3:
            return {'trend': 'stable', 'strength': 0}
        
        # Get mood scores in chronological order
        mood_data = []
        for entry in reversed(entries):  # Oldest first
            if entry['mood_score']:
                mood_data.append(entry['mood_score'])
        
        if len(mood_data) < 3:
            return {'trend': 'stable', 'strength': 0}
        
        # Simple linear trend calculation
        x = np.arange(len(mood_data))
        y = np.array(mood_data)
        slope = np.polyfit(x, y, 1)[0]
        
        trend = 'declining' if slope < -2 else 'improving' if slope > 2 else 'stable'
        
        return {
            'trend': trend,
            'strength': abs(slope) / 10,  # Normalize
            'slope': slope
        }
    
    def _analyze_negative_emotions(self, entries):
        """Calculate ratio of negative emotions"""
        negative_emotions = ['sadness', 'anger', 'fear', 'anxiety', 'disgust']
        
        negative_count = 0
        total_emotions = 0
        
        for entry in entries:
            if entry['final_emotion'] and entry['final_emotion'].lower() in [e.lower() for e in negative_emotions]:
                negative_count += 1
            total_emotions += 1
        
        return negative_count / total_emotions if total_emotions > 0 else 0
    
    def _analyze_journal_sentiment(self, entries):
        """Simple journal sentiment analysis"""
        negative_words = ['tired', 'exhausted', 'overwhelmed', 'stress', 'burnout', 'cant', 'wont', 
                         'hard', 'difficult', 'struggle', 'anxious', 'worried', 'sad', 'angry']
        
        sentiment_score = 0
        analyzed_entries = 0
        
        for entry in entries:
            if entry['journal_text']:
                text = entry['journal_text'].lower()
                negative_count = sum(1 for word in negative_words if word in text)
                word_count = len(text.split())
                
                if word_count > 0:
                    entry_sentiment = - (negative_count / min(word_count, 10))  # Normalize
                    sentiment_score += entry_sentiment
                    analyzed_entries += 1
        
        return sentiment_score / analyzed_entries if analyzed_entries > 0 else 0
    
    def _analyze_engagement(self, entries):
        """Analyze user engagement patterns"""
        if len(entries) < 7:
            return None
        
        # Check for declining frequency
        recent_count = len([e for e in entries[:7]])  # Last 7 entries
        older_count = len([e for e in entries[7:14]]) if len(entries) >= 14 else recent_count
        
        if older_count > 0 and recent_count / older_count < 0.5:
            return {
                'score': 15,
                'reason': f"Engagement dropped {((1 - recent_count/older_count)*100):.0f}%"
            }
        
        return None
    
    def _analyze_consistency(self, entries):
        """Analyze consistency patterns"""
        if len(entries) < 10:
            return None
        
        # Check for erratic posting times (sign of stress)
        times = []
        for entry in entries[:10]:  # Last 10 entries
            try:
                if 'T' in entry['timestamp']:
                    hour = datetime.fromisoformat(entry['timestamp']).hour
                else:
                    hour = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S').hour
                times.append(hour)
            except:
                continue
        
        if len(times) >= 5:
            hour_std = np.std(times)
            if hour_std > 6:  # Very erratic posting times
                return {
                    'score': 10,
                    'reason': "Irregular activity patterns"
                }
        
        return None
    
    def _generate_recommendations(self, risk_level, triggers):
        """Generate personalized recommendations"""
        recommendations = []
        
        if risk_level == "high":
            recommendations.extend([
                "🛑 Consider taking a mental health day",
                "💬 Reach out to friends or family for support",
                "🌿 Practice mindfulness or meditation",
                "📵 Consider a digital detox this weekend"
            ])
        elif risk_level == "medium":
            recommendations.extend([
                "⚖️ Balance your workload this week",
                "🎯 Set clear boundaries for work/life",
                "🏃 Make time for physical activity",
                "😴 Ensure 7-8 hours of sleep nightly"
            ])
        else:
            recommendations.extend([
                "🌟 Great job maintaining balance!",
                "📊 Continue tracking for early detection",
                "🎉 Celebrate your emotional awareness"
            ])
        
        # Add trigger-specific recommendations
        if any('negative emotions' in trigger for trigger in triggers):
            recommendations.append("🎨 Try creative expression to process emotions")
        
        if any('declining' in trigger for trigger in triggers):
            recommendations.append("📈 Schedule enjoyable activities to boost mood")
        
        return recommendations
    
    def _create_low_risk_assessment(self, reason):
        """Create a default low-risk assessment"""
        return {
            'risk_level': 'low',
            'risk_score': 10,
            'triggers': [f"Insufficient data: {reason}"],
            'recommendations': ["📊 Continue using MindMirror to unlock insights"],
            'assessment_date': datetime.now().isoformat(),
            'entries_analyzed': 0
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()