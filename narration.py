from openai import OpenAI
from pathlib import Path
import time
import os
import base64
import shutil
import requests
from pydub import AudioSegment, silence
from playsound import playsound
from datetime import datetime
from elevenlabs import generate, play, set_api_key, voices
from moviepy.editor import VideoFileClip, AudioFileClip
from extract_frames import *

def encode_image(image_path):
  with open(image_path, "rb") as image_file:
    return base64.b64encode(image_file.read()).decode('utf-8')

def generate_new_line(base64_image):
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "Describe this image"},
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                },
            ],
        },
    ]

def prompt_gptv(script, frame):
    client = OpenAI()
    openapi_key = os.getenv('OPENAI_API_KEY')

    # Getting the base64 string
    base64_image = encode_image(frame)

    response = client.chat.completions.create(
        model="gpt-4-vision-preview",
        messages=[
            {
                "role": "system",
                "content": """
                You are Sir David Attenborough. Narrate the picture of the human as if it is a nature documentary.
                Make it snarky and funny. Don't repeat yourself. Make it short, 30 words or less. 
                If a scene is blurry or unclear, admit that you're not sure what's going on. Do not EVER refuse to provide image descriptions.
                If I do anything remotely interesting, make a big deal about it!
                """,
            },
        ]
        + script
        + generate_new_line(base64_image),
        max_tokens=500,
    )
    response_text = response.choices[0].message.content
    return response_text


def play_audio(text, audio_files):

    audio = generate(text, voice=os.environ.get("ELEVENLABS_VOICE_ID"))

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    dir_path = "narration"
    os.makedirs(dir_path, exist_ok=True)
    file_name = "audio" + current_time + ".wav"
    file_path = os.path.join(dir_path, file_name)
    audio_files.append(file_path)

    with open(file_path, "wb") as f:
        f.write(audio)
    
    play(audio)
    timed_audio = AudioSegment.from_file(file_path)
    audio_len = len(timed_audio) / 1000.0
    return audio_len, audio_files

def concatenate_with_silence(file_paths, silence_durations):
    # Create an empty AudioSegment object
    combined = AudioSegment.silent(duration=0)

    for file_path, silence_duration in zip(file_paths, silence_durations):
        # Load the audio file
        print(f'file path: {file_path}')
        audio = AudioSegment.from_wav(file_path)

        # Add the audio and then the silence to the combined audio
        combined += audio
        combined += AudioSegment.silent(duration=silence_duration * 1000)  # duration in milliseconds

    return combined

def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        # Check if it's a file or a directory
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)  # Remove the file or link
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)  # Remove the directory and all its contents

def add_audio_to_video(video_path, audio_path, output_path):
    # Load the video clip
    video_clip = VideoFileClip(video_path)

    # Load the audio file
    audio_clip = AudioFileClip(audio_path)

    # Set the audio of the video clip as the audio file
    final_clip = video_clip.set_audio(audio_clip)

    # Write the result to a file
    final_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

def main():
    set_api_key(os.environ.get("ELEVENLABS_API_KEY"))

    video_path = 'movie.mov'
    output_folder = 'frame_screenshots'
    timestamps = [3, 28, 46]

    clear_folder(output_folder)
    get_frames(video_path, timestamps, output_folder)

    script = []
    for filename in os.listdir(output_folder):
        if filename.endswith('.jpg'):
            frame = os.path.join(output_folder, filename)

            description = prompt_gptv(script, frame)
            script.append({"role": "assistant", "content": description})

            # Selena's TODOs
            # TODO line up audio with visual
            # TODO watch end of films
    
    timestamps.insert(0, 0)
    i = 0
    audio_len = 0
    silence = [timestamps[1]] # first audio
    audio_files = []
    print("START")
    for text in script:
    
        sleep_in_s = timestamps[i+1] - timestamps[i] - audio_len
        silence.append(sleep_in_s)
        print(f'sleep len: {sleep_in_s}')
        print(f'text: {text}')

        if sleep_in_s > 0:
            time.sleep(timestamps[i+1] - timestamps[i] - audio_len) # align audio with video
        else:
            time.sleep(50)
            print("\nError: audio overlap\n")
        audio_len, audio_files = play_audio(text['content'], audio_files)
        i += 1

    # combine audio files
    final_audio = concatenate_with_silence(audio_files, silence)
    final_audio.export("final_audio.wav", format="wav")

    # add audio to video
    video_path = 'movie.mov'
    audio_path = 'final_audio.wav'
    movie_with_narration = 'narrated_movie.mp4'
    add_audio_to_video(video_path, audio_path, movie_with_narration)

if __name__ == "__main__":
    main()
