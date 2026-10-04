import json
import numpy as np
import pickle
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# load all Q&A pairs from jsonl
def load_technical_qa(filepath):
    pairs = []
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    obj = json.loads(line)
                    pairs.append((obj['question'], obj['answer']))
                except:
                    continue
    return pairs

def train():
    pairs = load_technical_qa('datasets/technical_qa/train.jsonl')
    
    # build a vectorizer trained on all Q&A text
    all_text = [q + " " + a for q, a in pairs]
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
    vectorizer.fit(all_text)
    
    pickle.dump(vectorizer, open('models/relevance_vectorizer.pkl', 'wb'))
    print(f"Vectorizer trained on {len(pairs)} Q&A pairs")

def predict_relevance(question, answer):
    vectorizer = pickle.load(open('models/relevance_vectorizer.pkl', 'rb'))
    
    vectors = vectorizer.transform([question, answer])
    similarity = cosine_similarity(vectors[0], vectors[1])[0][0]

    scaled = min(10.0, (float(similarity) * 50) + 3.0)
    return round(scaled, 2)