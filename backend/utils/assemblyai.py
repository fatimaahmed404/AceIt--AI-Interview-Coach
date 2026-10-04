import assemblyai as aai

try:
    from config import ASSEMBLYAI_API_KEY
except Exception:  # noqa: BLE001 - allow running the module standalone
    import os
    ASSEMBLYAI_API_KEY = os.environ.get("ASSEMBLYAI_API_KEY", "")

aai.settings.api_key = ASSEMBLYAI_API_KEY

def transcribe_audio(file_path):
    config = aai.TranscriptionConfig(
        speech_models=[aai.SpeechModel.universal]
    )
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(file_path)

    if transcript.error:
        print(f"Transcription error: {transcript.error}")
        return "Could not transcribe audio."

    return transcript.text