# digital_twin.py - Digital twin simulation engine

import json
from datetime import datetime, timedelta
from database import get_db_connection

class DigitalTwin:
    def __init__(self):
        self.conn = get_db_connection()
    
    def simulate_scenario(self, user_id, scenario):
        """Simulate what-if scenarios for user"""
        print(f"🤖 Digital Twin simulating: {scenario} for user {user_id}")
        
        # Get user baseline and patterns
        from analytics_engine import AnalyticsEngine
        analytics = AnalyticsEngine()
        baseline = analytics.calculate_user_baseline(user_id)
        patterns = analytics.detect_temporal_patterns(user_id)
        analytics.close()
        
        if not baseline:
            return self._create_default_response("Need more data to simulate")
        
        base_mood = baseline.get('avg_mood_score', 50)
        simulation_results = {
            'scenario': scenario,
            'base_mood': base_mood,
            'predicted_mood': base_mood,
            'confidence': 0.7,
            'factors': [],
            'recommendations': []
        }
        
        # Scenario-based simulations
        scenario_lower = scenario.lower()
        
        if 'exercise' in scenario_lower or 'workout' in scenario_lower:
            simulation_results['predicted_mood'] = min(100, base_mood + 15)
            simulation_results['factors'].append("Exercise typically boosts mood by 15 points")
            simulation_results['recommendations'].append("🏃 Even 20 minutes of exercise can significantly improve mood")
        
        elif 'sleep' in scenario_lower and ('less' in scenario_lower or 'reduce' in scenario_lower):
            simulation_results['predicted_mood'] = max(0, base_mood - 20)
            simulation_results['factors'].append("Sleep deprivation reduces mood by 20+ points")
            simulation_results['recommendations'].append("😴 Prioritize 7+ hours of sleep for optimal mental health")
        
        elif 'social' in scenario_lower or 'friends' in scenario_lower:
            simulation_results['predicted_mood'] = min(100, base_mood + 12)
            simulation_results['factors'].append("Social connection boosts mood by 12 points")
            simulation_results['recommendations'].append("👥 Regular social activities maintain emotional well-being")
        
        elif 'work' in scenario_lower and ('more' in scenario_lower or 'extra' in scenario_lower):
            simulation_results['predicted_mood'] = max(0, base_mood - 18)
            simulation_results['factors'].append("Overtime work often decreases mood by 18 points")
            simulation_results['recommendations'].append("⚖️ Balance work with restorative activities")
        
        elif 'meditate' in scenario_lower or 'mindfulness' in scenario_lower:
            simulation_results['predicted_mood'] = min(100, base_mood + 10)
            simulation_results['factors'].append("Mindfulness practice increases mood by 10 points")
            simulation_results['recommendations'].append("🧘 Regular practice builds emotional resilience")
        
        else:
            simulation_results['predicted_mood'] = base_mood
            simulation_results['factors'].append("No specific pattern detected for this scenario")
            simulation_results['recommendations'].append("📝 Try scenarios like 'exercise more' or 'sleep less'")
        
        # Calculate confidence based on data quality
        data_points = baseline.get('data_points_used', 0)
        simulation_results['confidence'] = min(0.9, 0.5 + (data_points / 20))
        
        print(f"✅ Simulation complete: {base_mood} → {simulation_results['predicted_mood']}")
        return simulation_results
    
    def learn_user_rules(self, user_id):
        """Learn personalized rules from user data"""
        print(f"🧠 Learning rules for user {user_id}")
        
        entries = self.conn.execute('''
            SELECT * FROM mindmirror_entries 
            WHERE user_id = ? 
            ORDER BY timestamp DESC LIMIT 50
        ''', (user_id,)).fetchall()
        
        if len(entries) < 10:
            return {"message": "Need more data to learn patterns"}
        
        rules = []
        
        # Example rule learning (simplified)
        # In a real system, this would use ML to detect correlations
        
        rules.append({
            'type': 'consistency_boost',
            'condition': 'Regular daily entries',
            'outcome': 'Mood stability +10 points',
            'confidence': 0.75
        })
        
        rules.append({
            'type': 'weekend_effect',
            'condition': 'Friday to Monday transition',
            'outcome': 'Typical mood variation detected',
            'confidence': 0.65
        })
        
        # Store learned rules
        for rule in rules:
            self.conn.execute('''
                INSERT OR REPLACE INTO digital_twin_rules 
                (user_id, rule_type, condition, outcome, confidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (user_id, rule['type'], rule['condition'], rule['outcome'], rule['confidence']))
        
        self.conn.commit()
        
        return {
            'rules_learned': len(rules),
            'rules': rules,
            'message': f"Learned {len(rules)} personalized patterns"
        }
    
    def _create_default_response(self, message):
        """Create default response when data is insufficient"""
        return {
            'scenario': 'unknown',
            'base_mood': 50,
            'predicted_mood': 50,
            'confidence': 0.3,
            'factors': [message],
            'recommendations': ["📊 Continue using MindMirror to improve predictions"]
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()