from google.cloud import speech
import io
from pydub import AudioSegment

def convert_to_mono(input_path, output_path):
    audio = AudioSegment.from_file(input_path)
    mono_audio = audio.set_channels(1)
    mono_audio.export(output_path, format="wav")

def transcribe_audio(file_path):
    client = speech.SpeechClient()

    with io.open(file_path, "rb") as audio_file:
        content = audio_file.read()

    audio = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=44100,  # Ensure this matches your audio file's sample rate
        language_code="en-US",
    )

    response = client.recognize(config=config, audio=audio)

    for result in response.results:
        print("Transcript: {}".format(result.alternatives[0].transcript))

if __name__ == "__main__":
    original_audio_path = "C:\\Users\\naman\\OneDrive\\Desktop\\GCP\\harvard.wav"
    mono_audio_path = "C:\\Users\\naman\\OneDrive\\Desktop\\GCP\\harvard_mono.wav"
    
    # Convert to mono
    convert_to_mono(original_audio_path, mono_audio_path)
    
    # Transcribe the mono audio
    transcribe_audio(mono_audio_path)
