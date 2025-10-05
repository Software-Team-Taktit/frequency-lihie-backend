from deps.heb_freq_phrase import _digits_to_hebrew, freq_to_phrase_he
import os, json, sys, pika, soundfile as sf, torch
from transformers import AutoProcessor, VitsModel

QUEUE = os.getenv("TTS_QUEUE", "tts_he_mms")
RMQ_HOST = os.getenv("RABBIT_HOST", "localhost")
MODEL_ID = "facebook/mms-tts-heb"
STATIC_DIR = os.getenv("STATIC_DIR","static")

