from classifiers.confidence import train as train_confidence
from classifiers.toxicity import train as train_toxicity
from classifiers.relevance import train as train_relevance
from classifiers.audio_model import train as train_audio

print("1/4 Training confidence classifier (SST2)...")
train_confidence()

print("2/4 Training toxicity classifier (Jigsaw)...")
train_toxicity()

print("3/4 Training relevance vectorizer (Technical Q&A)...")
train_relevance()

print("4/4 Training audio model (Speech Accent Archive)...")
train_audio()

print("\nAll done! Check your /models folder.")