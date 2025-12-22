# -------------------------
# IMPORTS
# -------------------------

# Speech recognition library to convert microphone audio into text
import speech_recognition as sr

# Used to open websites (YouTube, Google, etc.) in the browser
import webbrowser

# Windows-only library to play short system sounds (yes.wav)
import winsound

# Used for delays (sleep)
import time

# Google Text-to-Speech: converts text into spoken audio (MP3)
from gtts import gTTS

# Plays audio files (used to play the generated MP3)
from playsound import playsound

# Used for file handling (delete temp audio file)
import os

# Used to make HTTP requests (News API, YouTube search)
import requests

# Wikipedia library to fetch summaries
import wikipedia

# Your custom music library file (dictionary of song → YouTube links)
import musicLibrary

# Regular expressions: used to extract YouTube video IDs from HTML
import re

from dotenv import load_dotenv
load_dotenv()

import os
newsapi = os.getenv("NEWSAPI_KEY")


# -------------------------
# SETTINGS
# -------------------------


# Create a recognizer object (this does the speech recognition)
recognizer = sr.Recognizer()

# -------------------------
# MICROPHONE TUNING
# -------------------------

# Fixed energy threshold:
# If sound is quieter than this, it will be ignored as noise
recognizer.energy_threshold = 300

# Disable auto-adjustment so recognition is consistent
recognizer.dynamic_energy_threshold = False


# -------------------------
# VOICE OUTPUT FUNCTIONS
# -------------------------

def speak(text):
    """
    Converts text to speech using Google TTS.
    Saves audio as a temporary MP3, plays it, then deletes it.
    """
    tts = gTTS(text=text, lang='en')
    filename = "temp_audio.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)
    time.sleep(0.1)  # tiny pause so audio doesn't overlap


def speak_yes():
    """
    Plays a short confirmation sound when wake word is detected.
    """
    winsound.PlaySound("yes.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)


# -------------------------
# COMMAND PROCESSOR
# -------------------------

def processCommand(command):
    """
    Takes the recognized voice command and decides what action to perform.
    """
    command = command.lower()

    # -------------------------
    # WEBSITE COMMANDS
    # -------------------------
    if "open google" in command:
        webbrowser.open("http://www.google.com")

    elif "open youtube" in command:
        webbrowser.open("http://www.youtube.com")

    elif "open facebook" in command:
        webbrowser.open("http://www.facebook.com")

    elif "open linkedin" in command:
        webbrowser.open("http://www.linkedin.com")  


    # -------------------------
    # MUSIC COMMAND
    # -------------------------
    elif "play" in command:
        # Extract song name from command
        # Example: "play skyfall" → "skyfall"
        song_name = command.replace("play", "").strip().lower()

        # CASE 1: Song exists in your musicLibrary.py
        if song_name in musicLibrary.music:
            url = musicLibrary.music[song_name]

            # Add autoplay=1 to YouTube URLs
            if "youtube.com/watch" in url:
                if "?" in url:
                    url += "&autoplay=1"
                else:
                    url += "?autoplay=1"

            speak(f"Playing {song_name}")
            webbrowser.open(url)

        # CASE 2: Song NOT in library → Search YouTube automatically
        else:
            # Use quotes for more accurate search results
            search_query = f'"{song_name}"'
            search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"

            # Fake browser headers (prevents YouTube blocking the request)
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 Safari/537.36"
                )
            }

            try:
                # Fetch YouTube search page HTML
                r = requests.get(search_url, headers=headers)

                # REGEX:
                # Finds all video IDs in the page (each ID is exactly 11 chars)
                video_ids = re.findall(r"watch\?v=(\S{11})", r.text)

                if video_ids:
                    # Remove duplicates and keep top few results
                    unique_ids = []
                    for vid in video_ids:
                        if vid not in unique_ids:
                            unique_ids.append(vid)
                        if len(unique_ids) >= 3:
                            break

                    # Pick the first (best-ranked) video
                    best_url = f"https://www.youtube.com/watch?v={unique_ids[0]}&autoplay=1"

                    speak(f"Playing {song_name}")
                    webbrowser.open(best_url)

                else:
                    # If no video found, open search results page
                    speak("I couldn't find a link. Opening search results.")
                    webbrowser.open(search_url)

            except Exception as e:
                print(f"Error: {e}")
                speak("I ran into an issue searching YouTube.")


    # -------------------------
    # NEWS COMMAND
    # -------------------------
    elif "news" in command:
        r = requests.get(
            f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi.strip()}"
        )

        if r.status_code == 200:
            data = r.json()
            articles = data.get('articles', [])

            for article in articles[:5]:
                title = article.get("title")
                if title:
                    speak(title)
                    time.sleep(0.5)
        else:
            speak("Sorry, I could not fetch the news")


    # -------------------------
    # WIKIPEDIA COMMAND
    # -------------------------
    elif (
        "who" in command or "who's" in command or
        "what" in command or "what's" in command or
        "where" in command or "where's" in command or
        "how" in command or "how's" in command or
        "whom" in command or "to whom" in command or
        "wikipedia" in command
    ):
        # Clean the question to extract only the topic
        topic = (
            command.replace("wikipedia", "")
                   .replace("who is", "")
                   .replace("who's", "")
                   .replace("what is", "")
                   .replace("what's", "")
                   .replace("where is", "")
                   .replace("where's", "")
                   .replace("how is", "")
                   .replace("how's", "")
                   .replace("whom", "")
                   .replace("to whom", "")
                   .strip()
        )

        try:
            summary = wikipedia.summary(topic, sentences=2)
            speak(summary)
        except Exception:
            speak("Sorry, I could not find information on that topic.")

    else:
        speak("Sorry, I did not understand that command.")


# -------------------------
# MAIN LOOP (JARVIS BRAIN)
# -------------------------
if __name__ == "__main__":
    speak("Initializing Jarvis")
    print("Jarvis is ready...")

    while True:
        try:
            # -------------------------
            # WAKE WORD LISTENING
            # -------------------------
            with sr.Microphone() as source:
                print("Listening for wake word...")
                recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = recognizer.listen(source)

            try:
                # Convert wake word audio to text
                word = recognizer.recognize_google(audio, language='en-US')
                print("Heard:", word)

                if "jarvis" in word.lower():
                    print("Yes!! My Master...\nJarvis Active")
                    speak_yes()
                    time.sleep(1)

                    # -------------------------
                    # COMMAND LISTENING
                    # -------------------------
                    with sr.Microphone() as source:
                        print("Listening for command...")
                        recognizer.adjust_for_ambient_noise(source, duration=0.7)
                        audio = recognizer.listen(
                            source,
                            timeout=None,
                            phrase_time_limit=10
                        )

                    try:
                        c = recognizer.recognize_google(audio, language='en-US')
                        print("Command heard:", c)
                        processCommand(c)

                    except sr.UnknownValueError:
                        # Silent ignore if speech not understood
                        pass

            except sr.RequestError:
                print("Speech service error")
                speak("Speech service is unavailable.")

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
