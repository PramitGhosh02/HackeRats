"""
Description: Speech-to-text → Language Detection → AI Response → Text-to-Speech
"""

import os
import asyncio
import speech_recognition as sr
from pydub import AudioSegment
from langdetect import detect
import edge_tts


# AUDIO PREPROCESSING
def clean_audio(input_path: str, output_path: str = "clean.wav"):
    sound = AudioSegment.from_file(input_path)
    sound = sound.set_frame_rate(16000).set_channels(1)
    sound.export(output_path, format="wav")
    print("Audio cleaned successfully")
    return output_path

# SPEECH TO TEXT
def speech_to_text(audio_path: str):
    recognizer = sr.Recognizer()

    with sr.AudioFile(audio_path) as source:
        audio = recognizer.record(source)

    try:
        text = recognizer.recognize_google(audio)
        print("Recognized Text:", text)
        return text
    except Exception:
        print("Speech not clear")
        return None


# MULTILINGUAL AI RESPONSE
def multilingual_ai(text: str, language: str):
    text = text.lower()

    if "stress" in text or "तनाव" in text:
        if language == "hi":
            return "चिंता मत करो। सब ठीक हो जाएगा।"
        elif language == "bn":
            return "চিন্তা করবেন না। সব ঠিক হয়ে যাবে।"
        else:
            return "Don't worry. Everything will be okay."

    elif "happy" in text or "खुश" in text:
        if language == "hi":
            return "यह सुनकर अच्छा लगा!"
        elif language == "bn":
            return "এটা শুনে ভালো লাগলো!"
        else:
            return "That’s wonderful to hear!"

    return "I understand you. Tell me more."


# TEXT TO SPEECH
async def speak(text: str, language: str):
    if language == "hi":
        voice = "hi-IN-MadhurNeural"
    elif language == "bn":
        voice = "bn-IN-BashkarNeural"
    else:
        voice = "en-IN-PrabhatNeural"

    communicate = edge_tts.Communicate(text, voice)
    await communicate.save("response.mp3")
    print("Response saved as response.mp3")


# MAIN FUNCTION
def main():
    audio_file = input("Enter path of audio file: ")

    if not os.path.exists(audio_file):
        print("File not found!")
        return

    cleaned_audio = clean_audio(audio_file)
    text = speech_to_text(cleaned_audio)

    if not text:
        return

    language = detect(text)
    print("Detected Language:", language)

    response = multilingual_ai(text, language)
    print("AI Response:", response)

    asyncio.run(speak(response, language))


# ENTRY POINT
if __name__ == "__main__":
    main()