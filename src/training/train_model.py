# train_model.py - Final Working Version
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report, accuracy_score, f1_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
import joblib
import librosa
import os
import warnings

# Suppress warnings
warnings.filterwarnings("ignore")

# 1. Enhanced Feature Extraction
def extract_robust_features(file_path, target_sr=22050, min_duration=1.0):
    try:
        y, sr = librosa.load(file_path, sr=target_sr, mono=True)
        
        if len(y)/sr < min_duration:
            return None
            
        n_fft = min(2048, len(y))
        if n_fft % 2 != 0:
            n_fft -= 1
            
        if len(y) < n_fft:
            y = np.pad(y, (0, n_fft - len(y)), mode='constant')
        
        features = []
        
        # MFCCs
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40, n_fft=n_fft)
        features.extend(np.mean(mfcc, axis=1))
        features.extend(np.std(mfcc, axis=1))
        
        # Chroma
        chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_fft=n_fft)
        features.extend(np.mean(chroma, axis=1))
        
        return np.array(features)
    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        return None

# 2. Dataset Loading
def load_balanced_dataset(data_path, samples_per_class=100):
    emotions_map = {
        "ANG": "Angry", "DIS": "Disgust", "FEA": "Fear",
        "HAP": "Happy", "NEU": "Neutral", "SAD": "Sad"
    }
    
    features = []
    labels = []
    class_counts = {e: 0 for e in emotions_map.values()}
    
    for file in os.listdir(data_path):
        if file.endswith(".wav"):
            try:
                emotion = emotions_map[file.split("_")[2]]
                if class_counts[emotion] < samples_per_class:
                    path = os.path.join(data_path, file)
                    feat = extract_robust_features(path)
                    if feat is not None:
                        features.append(feat)
                        labels.append(emotion)
                        class_counts[emotion] += 1
            except:
                continue
    
    return np.array(features), np.array(labels)

# 3. Model Training
def train_emotion_model(X, y):
    # Encode labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )
    
    # Models to evaluate
    models = {
        "RandomForest": RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            random_state=42
        ),
        "SVM": SVC(
            C=1.0,
            kernel='rbf',
            probability=True,
            random_state=42
        ),
        "MLP": MLPClassifier(
            hidden_layer_sizes=(100,),
            max_iter=500,
            early_stopping=True,
            random_state=42
        )
    }
    
    best_model = None
    best_f1 = 0
    
    for name, model in models.items():
        print(f"\n🚀 Training {name}...")
        
        # Create pipeline for each model
        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('smote', SMOTE(random_state=42)),
            ('model', model)
        ])
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        acc = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')
        
        print(f"✅ {name} Results:")
        print(f"Accuracy: {acc:.4f}")
        print(f"F1-Score: {f1:.4f}")
        print(classification_report(y_test, y_pred, target_names=le.classes_))
        
        if f1 > best_f1:
            best_f1 = f1
            best_model = pipeline
            print("🌟 New best model!")
    
    # Train final model on all data
    final_pipeline = Pipeline([
        ('scaler', StandardScaler()),
        ('model', best_model.named_steps['model'])
    ])
    
    final_pipeline.fit(X, y_encoded)
    
    # Save artifacts
    joblib.dump(final_pipeline, "emotion_pipeline.pkl")
    joblib.dump(le, "label_encoder.pkl")
    
    print(f"\n🎉 Best model: {type(best_model.named_steps['model']).__name__}")
    return final_pipeline

if __name__ == "__main__":
    DATA_PATH = r"C:\Users\sanja\mindmirror\audio_model\CREMA-D\AudioWAV"
    
    print("🔍 Loading dataset...")
    X, y = load_balanced_dataset(DATA_PATH, samples_per_class=100)
    
    print("\n📊 Class Distribution:")
    print(pd.Series(y).value_counts())
    
    print("\n🧠 Starting model training...")
    pipeline = train_emotion_model(X, y)
    
    print("\n💾 Saved files:")
    print("- emotion_pipeline.pkl")
    print("- label_encoder.pkl")