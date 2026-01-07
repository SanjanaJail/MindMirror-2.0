import librosa
import numpy as np
import joblib

model = joblib.load("emotion_pipeline.pkl")

def extract_features(file_path):
    y, sr = librosa.load(file_path, duration=3, offset=0.5)
    mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40).T, axis=0)
    return mfcc.reshape(1, -1)

def predict_emotion(file_path):
    features = extract_features(file_path)
    prediction = model.predict(features)[0]
    probs = model.predict_proba(features)[0]
    confidence = np.max(probs)
    print(f"🎙️ File: {file_path}")
    print(f"🧠 Predicted Emotion: {prediction} ({confidence*100:.2f}%)")

if __name__ == "__main__":
    test_file = r"C:\Users\sanja\mindmirror\audio_model\CREMA-D\AudioWAV\1001_DFA_SAD_XX.wav"  
    predict_emotion(test_file)