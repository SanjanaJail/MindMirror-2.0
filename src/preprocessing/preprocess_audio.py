import os
import librosa
import numpy as np
import pandas as pd

DATA_PATH = r"C:\Users\sanja\mindmirror\audio_model\CREMA-D\AudioWAV"
emotions_map = {
    "ANG": "Angry",
    "DIS": "Disgust",
    "FEA": "Fear",
    "HAP": "Happy",
    "NEU": "Neutral",
    "SAD": "Sad"
}

def extract_features(file_path):
    try:
        y, sr = librosa.load(file_path, duration=3, offset=0.5)
        mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40).T, axis=0)
        return mfcc
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return None

data = []
for file in os.listdir(DATA_PATH):
    if file.endswith(".wav"):
        emotion_code = file.split("_")[2]
        if emotion_code in emotions_map:
            path = os.path.join(DATA_PATH, file)
            features = extract_features(path)
            if features is not None:
                data.append([*features, emotions_map[emotion_code]])
                print(f"✅ Processed: {file}")


if data:
    columns = [f"mfcc_{i}" for i in range(40)] + ["emotion"]
    df = pd.DataFrame(data, columns=columns)
    df.to_csv("audio_features.csv", index=False)
    print("🎉 Features extracted successfully!")
else:
    print("⚠️ No data extracted. Check file paths!")
