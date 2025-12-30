# -------------------------
# IMPORTS
# -------------------------

import json
import simpleaudio as sa
import speech_recognition as sr
import webbrowser
import winsound
import time
from gtts import gTTS
from playsound import playsound
import os
import requests
import wikipedia
import musicLibrary
import re
from dotenv import load_dotenv

load_dotenv()

# Read News API key
newsapi = os.getenv("NEWSAPI_KEY")


# -------------------------
# SETTINGS
# -------------------------

recognizer = sr.Recognizer()

with sr.Microphone() as source:
    print("Calibrating microphone...")
    recognizer.adjust_for_ambient_noise(source, duration=1)
    print("Calibration complete")

recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = False


# -------------------------
# VOICE OUTPUT (gTTS ONLY)
# -------------------------

def speak(text):
    temp_file = "temp_audio.mp3"
    tts = gTTS(text=text, lang="en")
    tts.save(temp_file)
    playsound(temp_file)
    os.remove(temp_file)


def speak_yes():
    winsound.PlaySound("yes.wav", winsound.SND_FILENAME)




def ask_openrouter(prompt: str) -> str:
    """
    Send a question to OpenRouter using MiMo-V2-Flash (free).
    """
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
# COMMAND PROCESSOR
# -------------------------

def processCommand(command):
    command = command.lower()

    if "open google" in command:
        webbrowser.open("https://www.google.com")

    elif "open youtube" in command:
        webbrowser.open("https://www.youtube.com")

    elif "open facebook" in command:
        webbrowser.open("https://www.facebook.com")

    elif "open linkedin" in command:
        webbrowser.open("https://www.linkedin.com")

    elif "play" in command:
        song_name = command.replace("play", "").strip().lower()

        if song_name in musicLibrary.music:
            url = musicLibrary.music[song_name]
            if "youtube.com/watch" in url:
                url += "&autoplay=1"
            speak(f"Playing {song_name}")
            webbrowser.open(url)

        else:
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

    # --- MODE 3: EVERYTHING ELSE GOES TO AI ---
    else:
        print("\nAsking AI about:", command)
        speak("Let me check that for you.")

        answer = ask_openrouter(
            f"Answer this clearly and briefly for a voice assistant user: {command}"
)

        print("\nAI Result:")
        print(answer)
        speak(answer)

# -------------------------
# MAIN LOOP
# -------------------------

is_listening = True
time.sleep(1.5)

if __name__ == "__main__":
    speak("Initializing Jarvis")
    print("Jarvis is ready...")
    print("Listening for wake word...")

    while True:
        with sr.Microphone() as source:

            # WAKE WORD MODE
            if is_listening:
                try:
                    audio = recognizer.listen(source, phrase_time_limit=4)
                    word = recognizer.recognize_google(audio)

                    if "jarvis" in word.lower():
                        print("Yes!! My Master...")
                        print("Jarvis Active")
                        speak_yes()
                        is_listening = False

                except sr.UnknownValueError:
                    pass

            # COMMAND MODE
            else:
                print("Listening for command...")

                try:
                    audio = recognizer.listen(source, phrase_time_limit=12)
                    command = recognizer.recognize_google(audio)
                    print("Command heard:", command)
                    processCommand(command)

                except sr.UnknownValueError:
                    speak("I didn't catch that. Please say it again.")

                is_listening = True
