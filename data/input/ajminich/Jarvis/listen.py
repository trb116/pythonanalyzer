#!/usr/bin/env python

from jarvis import Jarvis

import logging
import speech_recognition as sr

logger = logging.getLogger(__name__)

# for testing purposes, we're just using the default API key
GOOGLE_SPEECH_RECOGNITION_API_KEY = None

def run_transcription_loop():
    # Most of this code taken from https://github.com/Uberi/speech_recognition/blob/master/examples/microphone_recognition.py.
    r = sr.Recognizer()
    with sr.Microphone() as source:

        while True:
            logger.debug("Awaiting user input.")
            audio = r.listen(source)

            logger.debug("Attempting to transcribe user input.")

            try:
                result = r.recognize_google(audio,
                                            key=GOOGLE_SPEECH_RECOGNITION_API_KEY)
                Jarvis.handle_action(result)
            except sr.UnknownValueError:
                logger.debug("Google Speech Recognition could not understand audio")
            except sr.RequestError as e:
                logger.warn("Could not request results from Google Speech Recognition service: %s", e)
            except Exception as e:
                logger.error("Could not process text: %s", e)

def main():
    # Set up logger.
    FORMAT = '%(asctime)s %(filename)s:%(lineno)s [%(levelname)s] %(message)s'
    logging.basicConfig(format=FORMAT, level=logging.DEBUG)

    run_transcription_loop()

if __name__ == '__main__':
    main()