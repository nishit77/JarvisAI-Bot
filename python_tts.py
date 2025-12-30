from TTS.api import TTS

tts = TTS("tts_models/en/ljspeech/tacotron2-DDC", gpu=False)

tts.tts_to_file(
    text="Jarvis voice system is now online.",
    file_path="jarvis_test.wav"
)

print("Done")
