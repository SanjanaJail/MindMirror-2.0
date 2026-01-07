# backfill_scores.py - One-time script to add mood scores to existing entries
import sqlite3
from app import calculate_mood_score  # Import your function

def backfill_mood_scores():
    conn = sqlite3.connect('mindmirror.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all entries without mood scores
    cursor.execute("SELECT * FROM mindmirror_entries WHERE mood_score IS NULL")
    entries = cursor.fetchall()
    
    print(f"Found {len(entries)} entries to update...")
    
    for entry in entries:
        emotion = entry['final_emotion']
        # Use text confidence if available, otherwise audio, otherwise 0.5
        confidence = entry['text_confidence'] or entry['audio_confidence'] or 0.5
        
        if emotion:  # Only calculate if we have an emotion
            score = calculate_mood_score(emotion, confidence)
            
            # Update the entry with the calculated score
            cursor.execute(
                "UPDATE mindmirror_entries SET mood_score = ? WHERE id = ?",
                (score, entry['id'])
            )
            print(f"Updated entry {entry['id']}: {emotion} -> {score}")
    
    conn.commit()
    conn.close()
    print("✅ Backfilling complete!")

if __name__ == "__main__":
    backfill_mood_scores()