from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import numpy as np

model_name = "cardiffnlp/twitter-roberta-base-emotion"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)

labels = ['anger', 'joy', 'optimism', 'sadness', 'disgust', 'fear', 'love']

def predict_text_emotion(text):
    inputs = tokenizer(text, return_tensors="pt", truncation=True)
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.nn.functional.softmax(logits, dim=1)[0]
    pred_idx = torch.argmax(probs).item()
    return labels[pred_idx], float(probs[pred_idx])

if __name__ == "__main__":
    journal = "I feel anxious and tired today. Nothing excites me anymore."
    label, confidence = predict_text_emotion(journal)
    print(f"📝 Journal: {journal}")
    print(f"🧠 Predicted Emotion: {label} ({confidence*100:.2f}%)")