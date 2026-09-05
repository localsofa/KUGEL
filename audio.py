import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel
import scipy.io.wavfile as wavfile


MODEL_SIZE = "base"

model = WhisperModel(
    MODEL_SIZE,
    compute_type="int8"
)


def listen():

    print("Listening...")

    sample_rate = 16000
    duration = 5

    audio = sd.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype=np.float32
    )

    sd.wait()

    wavfile.write(
        "temp_audio.wav",
        sample_rate,
        audio
    )

    segments, info = model.transcribe(
        "temp_audio.wav",
        language="en"
    )

    text = ""

    for segment in segments:
        text += segment.text

    return text.strip()