# -------------------------
# IMPORTS
# -------------------------

# Converts microphone audio into text using Google Speech Recognition
import speech_recognition as sr

# Opens URLs in the default web browser
import webbrowser

# Windows-only library to play short system sounds (used for yes.wav)
import winsound

# Used for pauses / delays between actions
import time

# Google Text-to-Speech: converts text into spoken MP3 audio
from gtts import gTTS

# Plays audio files (used for playing generated speech)
from playsound import playsound

# Used for file handling (creating & deleting temporary audio files)
import os

# Used to make HTTP requests (News API, YouTube search page)
import requests

# Used to fetch summaries from Wikipedia
import wikipedia

# Custom module containing predefined song → YouTube URL mappings
import musicLibrary

# Regular expressions: used to extract video IDs from raw HTML
import re

# Used to load environment variables securely
from dotenv import load_dotenv
load_dotenv()

# Read News API key from .env file
import os
newsapi = os.getenv("NEWSAPI_KEY")


# -------------------------
# SETTINGS
# -------------------------


# Create a speech recognizer object
# This object handles converting speech to text
recognizer = sr.Recognizer()


# -------------------------
# MICROPHONE TUNING
# -------------------------

# Fixed energy threshold
# Sounds below this volume are treated as background noise
recognizer.energy_threshold = 300

# Disable automatic energy adjustment
# Keeps recognition behavior consistent
recognizer.dynamic_energy_threshold = False


# -------------------------
# VOICE OUTPUT FUNCTIONS
# -------------------------

def speak(text):
    """
    Converts text into speech using Google Text-to-Speech.
    
    Flow:
    1. Convert text → speech
    2. Save as temporary MP3 file
    3. Play the audio
    4. Delete the file after playing

    """
    tts = gTTS(text=text, lang='en')
    filename = "temp_audio.mp3"
    tts.save(filename)
    playsound(filename)
    os.remove(filename)

    # Small pause to prevent audio overlap
    time.sleep(0.1)


def speak_yes():
    """
    Plays a short confirmation sound
    Used when wake word 'Jarvis' is detected

    """
    winsound.PlaySound("yes.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)


# -------------------------
# COMMAND PROCESSOR
# -------------------------

def processCommand(command):
    """
    Takes the recognized speech text
    and decides what action Jarvis should perform.

    """
    command = command.lower()  # normalize command


    # -------------------------
    # WEBSITE COMMANDS
    # -------------------------

    # Opens Google
    if "open google" in command:
        webbrowser.open("http://www.google.com")

    # Opens YouTube
    elif "open youtube" in command:
        webbrowser.open("http://www.youtube.com")

    # Opens Facebook
    elif "open facebook" in command:
        webbrowser.open("http://www.facebook.com")

    # Opens LinkedIn
    elif "open linkedin" in command:
        webbrowser.open("http://www.linkedin.com")  


    # -------------------------
    # MUSIC COMMAND
    # -------------------------

    elif "play" in command:
        # Extract song name from command
        # Example: "play skyfall" → "skyfall"
        song_name = command.replace("play", "").strip().lower()

        # CASE 1:
        # Song exists in musicLibrary.py
        if song_name in musicLibrary.music:
            url = musicLibrary.music[song_name]

            # If YouTube link exists, force autoplay
            if "youtube.com/watch" in url:
                if "?" in url:
                    url += "&autoplay=1"
                else:
                    url += "?autoplay=1"

            speak(f"Playing {song_name}")
            webbrowser.open(url)

        # CASE 2:
        # Song NOT found in music library
        # → Perform YouTube search automatically
        else:
            # Use quotes to improve search accuracy
            search_query = f'"{song_name}"'
            search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"

            # Fake browser headers
            # Prevents YouTube from blocking the request
            headers = {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 Safari/537.36"
                )
            }

            try:
                # Fetch the YouTube search results page
                r = requests.get(search_url, headers=headers)

                # REGEX explanation:
                # Finds all video IDs in the page
                # Each YouTube video ID is exactly 11 characters
                video_ids = re.findall(r"watch\?v=(\S{11})", r.text)

                if video_ids:
                    # Remove duplicate video IDs
                    # Keep only the top few search results
                    unique_ids = []
                    for vid in video_ids:
                        if vid not in unique_ids:
                            unique_ids.append(vid)
                        if len(unique_ids) >= 3:
                            break

                    # Choose the first (top-ranked) video
                    best_url = f"https://www.youtube.com/watch?v={unique_ids[0]}&autoplay=1"

                    speak(f"Playing {song_name}")
                    webbrowser.open(best_url)

                else:
                    # Fallback: open YouTube search page
                    speak("I couldn't find a link. Opening search results.")
                    webbrowser.open(search_url)

            except Exception as e:
                # Handles network / parsing errors
                print(f"Error: {e}")
                speak("I ran into an issue searching YouTube.")


    # -------------------------
    # NEWS COMMAND
    # -------------------------

    elif "news" in command:
        # Fetch top US headlines from NewsAPI
        r = requests.get(
            f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi.strip()}"
        )

        if r.status_code == 200:
            data = r.json()
            articles = data.get('articles', [])

            # Read out the top 5 headlines
            for article in articles[:5]:
                title = article.get("title")
                if title:
                    print("•", title)
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
        # Clean the question
        # Remove filler words to extract the topic only
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
            # Fetch a short Wikipedia summary
            summary = wikipedia.summary(topic, sentences=2)

            # Print first, then speak
            print("\nWikipedia Result:")
            print(summary)

            speak(summary)

        except Exception:
            speak("Sorry, I could not find information on that topic.")

    else:
        # Fallback for unknown commands
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
                        # Ignore unintelligible speech silently
                        pass

            except sr.RequestError:
                # This error occurs when the speech recognition service (Google API)
                # cannot be reached due to internet issues or service downtime.
                print("Speech service error")
                speak("Speech service is unavailable.")

        except Exception as e:
            # It catches ANY unexpected error that was not handled above.
            print("Error:", e)
            speak("Something went wrong.")
