# therapeutic_engine.py - Main therapy recommendation system
from content_library import ContentLibrary
from database import get_db_connection, create_therapy_session
from datetime import datetime

class TherapeuticEngine:
    def __init__(self):
        self.content_lib = ContentLibrary()

    def generate_therapy_plan(self, user_id, current_emotion, mood_intensity='medium'):
        """Generate complete therapeutic intervention plan"""
        print(f"🎯 Generating therapy plan for {current_emotion} (intensity: {mood_intensity})")
        
        # Get personalized recommendations
        recommendations = self.content_lib.get_therapeutic_recommendations(current_emotion)
        
        # Create therapy session record
        conn = get_db_connection()
        create_therapy_session(conn, user_id, current_emotion)
        conn.close()

        # Structure the response
        therapy_plan = {
            'emotion_detected': current_emotion,
            'intensity_level': mood_intensity,
            'generated_at': datetime.now().isoformat(),
            'immediate_relief': self._get_immediate_relief(recommendations),
            'daily_practices': self._get_daily_practices(recommendations),
            'lifestyle_recommendations': recommendations.get('lifestyle', []),
            'therapeutic_insight': self._get_therapeutic_insight(current_emotion)
        }
        
        return therapy_plan

    def _get_immediate_relief(self, recommendations):
        """Get immediate relief interventions (5-15 min)"""
        immediate = []
        
        # Prioritize short, effective content
        for content_type in ['exercise', 'video', 'music']:
            if content_type in recommendations:
                for item in recommendations[content_type]:
                    if item.get('duration_minutes', 30) <= 15:  # Short interventions
                        if item.get('content_category') == 'immediate_relief':
                            immediate.append(item)
        
        # If no immediate relief found, use shortest available
        if not immediate and 'exercise' in recommendations:
            immediate = recommendations['exercise'][:1]
            
        return immediate[:2]  # Max 2 immediate interventions

    def _get_daily_practices(self, recommendations):
        """Get daily practice recommendations"""
        daily = []
        for content_type in ['music', 'exercise']:
            if content_type in recommendations:
                for item in recommendations[content_type]:
                    if item.get('content_category') == 'daily_practice':
                        daily.append(item)
        return daily[:3]  # Max 3 daily practices

    def _get_therapeutic_insight(self, emotion):
        """Provide psychological insight about the emotion"""
        insights = {
            'sadness': {
                'title': 'Understanding Sadness',
                'message': 'Sadness often signals that something matters to us deeply. It can be a catalyst for meaningful change and self-reflection.',
                'action': 'Allow yourself to feel this fully, then gently engage in comforting activities.'
            },
            'anxiety': {
                'title': 'Working with Anxiety',
                'message': 'Anxiety is your body\'s way of saying "I care about what happens next." It becomes problematic when it runs without brakes.',
                'action': 'Ground yourself in the present moment through breathing and sensory awareness.'
            },
            'anger': {
                'title': 'Transforming Anger',
                'message': 'Anger often points to violated boundaries or unmet needs. It carries tremendous energy for change.',
                'action': 'Channel this energy constructively through physical movement or clear communication.'
            },
            'joy': {
                'title': 'Amplifying Joy',
                'message': 'Joy connects us to what truly matters. These moments are precious resources for resilience.',
                'action': 'Savor this feeling and consider sharing it with others to multiply its impact.'
            },
            'neutral': {
                'title': 'Embracing Neutrality',
                'message': 'Neutral states provide the foundation from which all other emotions emerge. They offer valuable rest and integration time.',
                'action': 'Use this space for reflection and gentle exploration of what you truly need.'
            }
        }
        
        return insights.get(emotion.lower(), insights['neutral'])

    def close(self):
        """Close resources"""
        self.content_lib.close()