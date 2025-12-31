import pyttsx3

engine = pyttsx3.init()

voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id)
engine.setProperty('rate', 170)
engine.setProperty('volume', 1.0)

engine.say("Hello Nishit, this is a test.")
engine.runAndWait()
