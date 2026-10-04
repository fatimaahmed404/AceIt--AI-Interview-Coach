import pandas as pd
import pickle
import json
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

def train():
    df = pd.read_csv('datasets/jigsaw/train.csv')
    df = df.dropna(subset=['comment_text'])
    df['label'] = df[['toxic','severe_toxic','obscene',
                       'threat','insult','identity_hate']].max(axis=1)

    toxic = df[df['label'] == 1]
    clean = df[df['label'] == 0].sample(len(toxic) * 2, random_state=42)
    df_balanced = pd.concat([toxic, clean]).sample(frac=1, random_state=42)

    X = df_balanced['comment_text']
    y = df_balanced['label']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    classifiers = {
        'Naive Bayes': MultinomialNB(),
        'Logistic Regression': LogisticRegression(max_iter=1000),
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1),
        'Gradient Boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
    }

    tfidf = TfidfVectorizer(max_features=5000, strip_accents='unicode')
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)

    results = {}
    best_model = None
    best_f1 = 0

    for name, clf in classifiers.items():
        print(f"Training {name}...")
        clf.fit(X_train_tfidf, y_train)
        y_pred = clf.predict(X_test_tfidf)

        metrics = {
            'accuracy':  round(accuracy_score(y_test, y_pred) * 100, 2),
            'precision': round(precision_score(y_test, y_pred) * 100, 2),
            'recall':    round(recall_score(y_test, y_pred) * 100, 2),
            'f1':        round(f1_score(y_test, y_pred) * 100, 2),
        }
        results[name] = metrics
        print(f"  Accuracy: {metrics['accuracy']}%  F1: {metrics['f1']}%")

        if metrics['f1'] > best_f1:
            best_f1 = metrics['f1']
            best_model = (name, clf)

    print(f"\nBest model: {best_model[0]} with F1 {best_f1}%")

    # save best model pipeline
    best_pipeline = Pipeline([
        ('tfidf', tfidf),
        ('clf', best_model[1])
    ])
    pickle.dump(best_pipeline, open('models/toxicity_model.pkl', 'wb'))

    # save tfidf separately so all models can use it
    pickle.dump(tfidf, open('models/toxicity_tfidf.pkl', 'wb'))

    # save all classifiers individually for the comparison endpoint
    all_models = {}
    for name, clf in classifiers.items():
        all_models[name] = clf
    pickle.dump(all_models, open('models/toxicity_all_models.pkl', 'wb'))

    # save results to json for frontend
    results['best'] = best_model[0]
    with open('models/toxicity_comparison.json', 'w') as f:
        json.dump(results, f)
    print("Comparison saved to models/toxicity_comparison.json")

def predict_toxicity(text):
    model = pickle.load(open('models/toxicity_model.pkl', 'rb'))
    prob = model.predict_proba([text])[0][1]
    return round((1 - prob) * 10, 2)