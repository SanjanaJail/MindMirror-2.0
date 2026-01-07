# soundscape_generator.py - Generate personalized soundscapes
import random
import math
from datetime import datetime

class SoundscapeGenerator:
    def __init__(self):
        self.sound_elements = {
            'nature': {
                'rain': {'intensity': 0.3, 'mood': ['sadness', 'anxiety']},
                'ocean': {'intensity': 0.4, 'mood': ['anxiety', 'neutral']},
                'forest': {'intensity': 0.5, 'mood': ['sadness', 'neutral']},
                'birds': {'intensity': 0.6, 'mood': ['joy', 'neutral']},
                'stream': {'intensity': 0.3, 'mood': ['anxiety', 'sadness']}
            },
            'ambient': {
                'white_noise': {'intensity': 0.2, 'mood': ['anxiety']},
                'pink_noise': {'intensity': 0.3, 'mood': ['anxiety', 'neutral']},
                'brown_noise': {'intensity': 0.4, 'mood': ['anxiety']},
                'crystal': {'intensity': 0.5, 'mood': ['joy', 'neutral']},
                'space': {'intensity': 0.6, 'mood': ['neutral']}
            },
            'melodic': {
                'piano': {'intensity': 0.4, 'mood': ['sadness', 'neutral']},
                'strings': {'intensity': 0.5, 'mood': ['sadness', 'joy']},
                'flute': {'intensity': 0.3, 'mood': ['anxiety', 'neutral']},
                'harp': {'intensity': 0.4, 'mood': ['joy', 'neutral']},
                'singing_bowl': {'intensity': 0.6, 'mood': ['anxiety', 'neutral']}
            }
        }
    
    def generate_soundscape(self, target_emotion, intensity='medium', duration_minutes=15):
        """Generate personalized soundscape based on emotion and intensity"""
        intensity_weights = {
            'gentle': 0.3,
            'medium': 0.5, 
            'intense': 0.7
        }
        
        target_intensity = intensity_weights.get(intensity, 0.5)
        
        # Select sound elements that match the target emotion and intensity
        selected_elements = []
        
        for category, elements in self.sound_elements.items():
            for element_name, element_data in elements.items():
                if target_emotion in element_data['mood']:
                    intensity_diff = abs(element_data['intensity'] - target_intensity)
                    if intensity_diff <= 0.2:  # Within acceptable intensity range
                        selected_elements.append({
                            'category': category,
                            'name': element_name,
                            'intensity': element_data['intensity'],
                            'weight': random.uniform(0.3, 0.8)  # Random weight for variety
                        })
        
        # Sort by best match and take top elements
        selected_elements.sort(key=lambda x: abs(x['intensity'] - target_intensity))
        final_elements = selected_elements[:min(4, len(selected_elements))]
        
        # Generate soundscape structure
        soundscape = {
            'emotion_target': target_emotion,
            'intensity': intensity,
            'duration_minutes': duration_minutes,
            'elements': final_elements,
            'layers': self._generate_layers(final_elements, duration_minutes),
            'transition_points': self._generate_transitions(duration_minutes),
            'generated_at': datetime.now().isoformat()
        }
        
        return soundscape
    
    def _generate_layers(self, elements, duration_minutes):
        """Generate layered sound structure"""
        layers = []
        total_duration = duration_minutes * 60  # Convert to seconds
        
        for i, element in enumerate(elements):
            layer = {
                'element': element['name'],
                'category': element['category'],
                'start_time': 0 if i == 0 else random.randint(30, 120),  # Staggered start
                'duration': total_duration,
                'volume': element['weight'],
                'fade_in': random.randint(5, 15),
                'fade_out': random.randint(10, 20)
            }
            layers.append(layer)
        
        return layers
    
    def _generate_transitions(self, duration_minutes):
        """Generate transition points for dynamic soundscape"""
        transitions = []
        total_seconds = duration_minutes * 60
        
        # Add 2-4 transition points
        num_transitions = random.randint(2, 4)
        for i in range(num_transitions):
            transition_time = random.randint(60, total_seconds - 60)
            transition_type = random.choice(['fade', 'crossfade', 'intensity_change'])
            
            transitions.append({
                'time_seconds': transition_time,
                'type': transition_type,
                'duration': random.randint(10, 30)
            })
        
        return sorted(transitions, key=lambda x: x['time_seconds'])
    
    def get_soundscape_description(self, soundscape):
        """Generate human-readable soundscape description"""
        elements_str = ", ".join([elem['name'] for elem in soundscape['elements']])
        
        descriptions = {
            'sadness': f"A gentle soundscape featuring {elements_str} to comfort and soothe",
            'anxiety': f"A calming blend of {elements_str} to ease tension and promote relaxation", 
            'anger': f"An immersive {elements_str} experience to channel and transform energy",
            'joy': f"An uplifting combination of {elements_str} to amplify positive feelings",
            'neutral': f"A balanced mix of {elements_str} to maintain emotional equilibrium"
        }
        
        return descriptions.get(soundscape['emotion_target'], 
                              f"A therapeutic soundscape featuring {elements_str}")