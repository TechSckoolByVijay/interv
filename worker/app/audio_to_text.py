import logging
from pydub import AudioSegment
import speech_recognition as sr
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_text_from_audio(audio_path: str) -> str:
    """
    Converts a .webm audio file to .wav and transcribes it to text.
    Args:
        audio_path (str): Path to the input .webm audio file.
    Returns:
        str: Transcribed text from the audio.
    """
    try:
        logger.info(f"Loading audio file: {audio_path}")
        audio = AudioSegment.from_file(audio_path, format="webm")
        audio = audio.set_channels(1).set_frame_rate(16000)
        wav_path = "converted.wav"
        audio.export(wav_path, format="wav")
        logger.info(f"Exported WAV file: {wav_path}")

        r = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = r.record(source)
        logger.info("Audio data loaded for transcription.")

        text = r.recognize_google(audio_data)
        logger.info("Transcription successful.")
        return text
    except sr.UnknownValueError:
        logger.warning("Speech Recognition could not understand the audio.")
        return ""
    except sr.RequestError as e:
        logger.error(f"API error: {e}")
        return ""
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return ""
    finally:
        # Clean up the temporary wav file if it exists
        if os.path.exists("converted.wav"):
            os.remove("converted.wav")
            logger.info("Temporary WAV file removed.")

# Example usage:
# text = extract_text_from_audio("audio.webm")
# print(text)


