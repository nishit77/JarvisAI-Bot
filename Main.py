# -------------------------
# IMPORTS
# -------------------------

import json
import simpleaudio as sa
import speech_recognition as sr
import webbrowser
import winsound
import time
import os
import requests
import wikipedia
import musicLibrary
import re
from dotenv import load_dotenv
import asyncio
import edge_tts
from pydub import AudioSegment
import io
import threading
import wave
import pvporcupine
import pyaudio
import struct
import numpy as np
from difflib import get_close_matches

# -------------------------
# MODELS / KEYS
# -------------------------

load_dotenv()
PICOVOICE_KEY = os.getenv("PICOVOICE_ACCESS_KEY")
newsapi = os.getenv("NEWSAPI_KEY")

porcupine = pvporcupine.create(
    access_key=PICOVOICE_KEY,
    keywords=["jarvis"]
)

# -------------------------
# SETTINGS
# -------------------------

recognizer = sr.Recognizer()
recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = False

# -------------------------
# EVENTS (WAKE-WORD <-> STT CONTROL)
# -------------------------

wake_event = threading.Event()
stt_event = threading.Event()

wake_event.set()   # wake-word engine starts active

# -------------------------
# TTS (edge-tts + simpleaudio)  <-- UNCHANGED
# -------------------------

async def speak_async(text):
    communicate = edge_tts.Communicate(text, "en-US-AriaNeural")

    mp3_bytes = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            mp3_bytes += chunk["data"]

    audio = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")

    raw = audio.raw_data
    channels = audio.channels
    sample_width = audio.sample_width
    frame_rate = audio.frame_rate

    play_obj = sa.play_buffer(raw, channels, sample_width, frame_rate)
    play_obj.wait_done()

def speak(text):
    # Run TTS in separate thread so it never blocks wake/STT
    def _run():
        asyncio.run(speak_async(text))
    threading.Thread(target=_run, daemon=True).start()

def speak_yes():
    winsound.PlaySound("yes.wav", winsound.SND_FILENAME)

# -------------------------
# GOOGLE STT (PURE GSTT)
# -------------------------

def transcribe_google(audio_data):
    """
    Uses Google Speech Recognition via speech_recognition.
    Optimized for Indian English (en-IN).
    """
    try:
        text = recognizer.recognize_google(audio_data, language="en-IN")
        text = text.strip().lower()
        print("Google STT heard:", repr(text))
        return text
    except sr.UnknownValueError:
        print("Google STT: UnknownValueError")
        return ""
    except sr.RequestError as e:
        print("Google STT: API RequestError:", e)
        return ""
    except Exception as e:
        print("Google STT: General error:", e)
        return ""

# -------------------------
# OPENROUTER AI
# -------------------------

def ask_openrouter(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "xiaomi/mimo-v2-flash:free",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        return data["choices"][0]["message"]["content"].strip()

    except Exception as e:
        print("OpenRouter API error:", e)
        return "Sorry, I had an issue contacting the AI service."

# -------------------------
# FUZZY HELPERS
# -------------------------

def fuzzy_best_match(text: str, candidates, cutoff: float = 0.55):
    """
    Return the best fuzzy match from candidates or None.
    """
    if not text or not candidates:
        return None
    matches = get_close_matches(text, candidates, n=1, cutoff=cutoff)
    return matches[0] if matches else None

def fuzzy_contains(command: str, patterns, cutoff: float = 0.7) -> bool:
    """
    Returns True if any pattern is clearly present in command,
    either literally or as a fuzzy match.
    """
    command = command.lower()
    for pattern in patterns:
        pattern = pattern.lower()
        if pattern in command:
            return True
        # fuzzy match small phrases
        if fuzzy_best_match(pattern, [command], cutoff=cutoff):
            return True
    return False

# -------------------------
# COMMAND PROCESSOR
# -------------------------

def processCommand(command):
    command = command.lower()
    print("Processing command:", repr(command))

    # ----- basic site/app commands with fuzzy matching -----

    if fuzzy_contains(command, ["open google", "google"]):
        webbrowser.open("https://www.google.com")
        return

    elif fuzzy_contains(command, ["open youtube", "you tube", "utube", "youtube"]):
        webbrowser.open("https://www.youtube.com")
        return

    elif fuzzy_contains(command, ["open facebook", "facebook", "fb"]):
        webbrowser.open("https://www.facebook.com")
        return

    elif fuzzy_contains(command, ["open linkedin", "link din", "linkedin"]):
        webbrowser.open("https://www.linkedin.com")
        return

    # ----- play music with fuzzy matching for Indian names/songs -----

    elif "play" in command:
        # Remove "play" and punctuation that often appears in STT
        song_name = command.replace("play", "")
        song_name = song_name.replace(",", " ").replace(".", " ").strip().lower()

        # 1) Try direct match first
        if song_name in musicLibrary.music:
            matched = song_name
        else:
            # 2) Try fuzzy match against known songs
            all_songs = list(musicLibrary.music.keys())
            matched = fuzzy_best_match(song_name, all_songs, cutoff=0.75)

        if matched:
            url = musicLibrary.music[matched]
            if "youtube.com/watch" in url:
                url += "&autoplay=1"
            speak(f"Playing {matched}")
            webbrowser.open(url)
            return

        # 3) Fallback to YouTube search if not in local library
        speak("Searching on YouTube.")
        search_query = f'"{song_name}"'
        search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/119.0.0.0 Safari/537.36"
            )
        }

        try:
            r = requests.get(search_url, headers=headers)
            video_ids = re.findall(r"watch\?v=(\S{11})", r.text)

            if video_ids:
                best_url = f"https://www.youtube.com/watch?v={video_ids[0]}&autoplay=1"
                speak(f"Playing {song_name}")
                webbrowser.open(best_url)
            else:
                speak("Opening YouTube search results.")
                webbrowser.open(search_url)

        except Exception as e:
            print("Error:", e)
            speak("I ran into an issue playing the song.")
        return

    # ----- news -----

    elif "news" in command:
        r = requests.get(
            f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi.strip()}"
        )

        if r.status_code == 200:
            articles = r.json().get("articles", [])
            for article in articles[:5]:
                title = article.get("title")
                if title:
                    print("•", title)
                    speak(title)
                    time.sleep(0.5)
        else:
            speak("I could not fetch the news.")
        return

    # ----- default: ask AI -----

    else:
        print("\nAsking AI about:", command)
        speak("Let me check that for you.")

        def run_ai():
            answer = ask_openrouter(
                f"Answer this clearly and briefly for a voice assistant user: {command}"
            )
            print("\nAI Result:")
            print(answer)
            speak(answer)

        threading.Thread(target=run_ai, daemon=True).start()
        return

# -------------------------
# WAKE-WORD LISTENER (PORCUPINE)
# -------------------------

def wake_word_listener():
    pa = pyaudio.PyAudio()
    stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length
    )

    print("Wake-word engine running...")

    while True:
        # Only run when wake_event is set
        wake_event.wait()

        pcm = stream.read(porcupine.frame_length, exception_on_overflow=False)
        pcm_frame = struct.unpack_from("h" * porcupine.frame_length, pcm)

        if porcupine.process(pcm_frame) >= 0:
            print("Wake word detected!")
            speak_yes()

            # Pause wake-word engine
            wake_event.clear()
            stream.stop_stream()

            # Trigger STT
            stt_event.set()

            # Wait for STT to finish (stt_listener will set wake_event again)
            wake_event.wait()

            # Resume wake-word engine
            stream.start_stream()

# -------------------------
# STT LISTENER (PURE GOOGLE STT)
# -------------------------

def stt_listener():
    while True:
        # Wait until wake-word tells us to start
        stt_event.wait()

        print("Listening for command...")

        with sr.Microphone() as source:
            # brief ambient noise adjustment
            recognizer.adjust_for_ambient_noise(source, duration=0.3)

            try:
                # phrase_time_limit to keep it snappy
                audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
                text = transcribe_google(audio)

                if not text:
                    speak("I didn't catch that. Please say it again.")
                else:
                    print("Final command text:", repr(text))
                    processCommand(text)

            except sr.WaitTimeoutError:
                print("STT: WaitTimeoutError")
                speak("I didn't hear anything.")

            except Exception as e:
                print("STT error:", e)
                speak("I ran into an issue understanding you.")

        # STT finished → allow wake-word to resume
        stt_event.clear()
        wake_event.set()

# -------------------------
# MAIN ENTRY
# -------------------------

if __name__ == "__main__":
    # Start background threads
    threading.Thread(target=wake_word_listener, daemon=True).start()
    threading.Thread(target=stt_listener, daemon=True).start()

    speak("Initializing Jarvis")
    print("Jarvis is ready...")
    print("Say 'Jarvis' to wake me up.")

    # Keep main thread alive
    while True:
        time.sleep(1)