import pandas as pd
import re
import pickle
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline

def parse_sst2(filepath):
    sentences, labels = [], []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            label = int(line[1])  # 0,1=negative, 3,4=positive, 2=neutral
            # extract all words — remove brackets and numbers
            words = re.sub(r'\([0-9]', '', line)
            words = re.sub(r'[()]', ' ', words).strip()
            if label != 2:  # skip neutral
                sentences.append(words)
                labels.append(1 if label >= 3 else 0) 
    return sentences, labels

def train():
    sentences, labels = parse_sst2('datasets/sst2/train.txt')
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1,2))),
        ('clf', LogisticRegression(max_iter=1000))
    ])
    pipeline.fit(sentences, labels)
    pickle.dump(pipeline, open('models/confidence_model.pkl', 'wb'))
    print(f"Trained on {len(sentences)} samples")

def predict_confidence(text):
    model = pickle.load(open('models/confidence_model.pkl', 'rb'))
    prob = model.predict_proba([text])[0][1]
    return round(prob * 10, 2)