import numpy as np
import pandas as pd
import librosa
import tensorflow as tf
import os
import pickle

def extract_features(audio_path):
    try:
        y, sr = librosa.load(audio_path, duration=30, sr=22050)
        
        if len(y) < sr * 0.5:  # less than 0.5 seconds
            return None
            
        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40)
        
        # consistent shape 
        if mfcc.shape[1] == 0:
            return None
            
        mfcc_mean = np.mean(mfcc, axis=1)  
        
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        zcr = float(np.mean(librosa.feature.zero_crossing_rate(y)))
        energy = float(np.mean(librosa.feature.rms(y=y)))
        
        # force everything to scalar before appending
        tempo = float(tempo) if np.isscalar(tempo) else float(tempo[0])
        
        features = np.append(mfcc_mean, [tempo, zcr, energy])
        
        if features.shape != (43,):
            return None
            
        return features
    except Exception as e:
        print(f"Skipping {audio_path}: {e}")
        return None

def train():
    csv_path = 'datasets/speech_accent/speakers_all.csv'
    audio_folder = 'datasets/speech_accent/recordings/recordings/'

    df = pd.read_csv(csv_path)
    df = df[df['file_missing?'] == False].reset_index(drop=True)
    print(f"Processing {len(df)} entries")
    
    lang_counter = {}
    filenames = []
    for _, row in df.iterrows():
        lang = str(row['native_language']).strip().lower()
        lang_counter[lang] = lang_counter.get(lang, 0) + 1
        filenames.append(f"{lang}{lang_counter[lang]}.mp3")
    df['constructed_filename'] = filenames

    X, y = [], []
    skipped = 0

    for _, row in df.iterrows():
        path = os.path.join(audio_folder, row['constructed_filename'])
        if not os.path.exists(path):
            skipped += 1
            continue

        features = extract_features(path)
        if features is None or len(features) != 43:
            skipped += 1
            continue

        label = 1 if str(row['native_language']).strip().lower() == 'english' else 0
        X.append(features)
        y.append(label)

    print(f"Loaded {len(X)} samples, skipped {skipped}")

    if len(X) < 10:
        print("ERROR: Too few loaded.")
        return

    X = np.array(X)
    y = np.array(y)

    model = tf.keras.Sequential([
        tf.keras.layers.Dense(128, activation='relu', input_shape=(43,)),
        tf.keras.layers.Dropout(0.3),
        tf.keras.layers.Dense(64, activation='relu'),
        tf.keras.layers.Dropout(0.2),
        tf.keras.layers.Dense(1, activation='sigmoid')
    ])
    model.compile(optimizer='adam', loss='binary_crossentropy',
                  metrics=['accuracy'])
    model.fit(X, y, epochs=20, batch_size=32,
              validation_split=0.2, verbose=1)

    os.makedirs('models', exist_ok=True)
    model.save('models/audio_model.h5')
    print("audio_model.h5 saved!")

def predict_audio(audio_path):
    model = tf.keras.models.load_model('models/audio_model.h5')
    features = extract_features(audio_path)
    if features is None:
        return 5.0  
    score = model.predict(features.reshape(1, -1), verbose=0)[0][0]
    return round(float(score) * 10, 2)