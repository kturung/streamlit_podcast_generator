import streamlit as st
import time
import os
from TTS.api import TTS
import torch
import subprocess
from typing import List
from pydantic import BaseModel, Field
from phi.assistant import Assistant
from phi.llm.ollama import Ollama


st.title("🎙️Podcast Generator🎙️")

if "characters_and_topics_submitted" not in st.session_state or st.sidebar.button("Restart the podcast"):
   st.session_state["messages"] = []
   st.session_state["characters_and_topics_submitted"] = False
   st.session_state["character_persona_submitted"] = False
   st.rerun()

def generate_dialog(number_of_dialogs, timestamp, debug=True):

    character_personas = ""
    for guest in st.session_state["guests"]:
        character_personas += f"- {guest} Persona: {st.session_state[f'{guest}_persona']}\n"
    
    guest_introductions = ""
    for guest in st.session_state["guests"]:
        guest_introductions += f", {guest}"

    podcast_template = f"""## Podcast Outline\nThis is a podcast between {st.session_state["host_character"]}{guest_introductions}.\n 
{st.session_state["host_character"]} is the host of the show.\n
{st.session_state['podcast_topic']}\n
Character Personas:\n {character_personas}\n"""
    instructions = f"""Instructions:\n
- The podcast should more or less have {number_of_dialogs} dialogs. Always include a closure dialog to the podcast.\n
- Don't use non-verbal cues like *laughs* or *ahem* or parentheticals in the podcast. Use Hehe or Haha instead of *laughs*.\n
- Also don't use a speaker label on the content parameter but you should always set speaker key for the correct speaker."""

    st.write(podcast_template)
    if not os.path.exists('podcasts'):
        os.makedirs('podcasts')
    transcript_file_name = f"podcasts/podcast{timestamp}.txt"
    transcript_file = open(transcript_file_name, "w")

    

    class PodcastScript(BaseModel):
        dialogs: List[dict] = Field(..., description="Contains dictionaries with these key values: speaker, content and the dialog_counter. speaker: name of the speaker, content: content of the speech, dialog_counter: The number of the dialog. Should be incremented by 1 for each dialog")
    

    podcast_assistant = Assistant(
        llm=Ollama(model="llama3:8b-instruct-q4_K_M"),
        description="You are a podcast transcript writer",
        output_model=PodcastScript
    )
    
    result = podcast_assistant.run(f"Generate a podcast transcript for this Podcast Outline: {podcast_template} {instructions}")
        
    print(result.dialogs)

    dialogs = result.dialogs

    for dialog in dialogs:
        transcript_line = dialog['speaker'] + " says: " + dialog['content']  + "\n"
        transcript_file.write(transcript_line)

    transcript_file.close()
    return dialogs

def generate_audio(dialogs, timestamp):
    device = "cuda" if torch.cuda.is_available() else "cpu"
    voice_names = {
        "Mia"    : r"voices\Mia.wav",
        "Denzel" : r"voices\Denzel_Wash.wav",
        "Alex"   : r"voices\Alex_Danivero.wav",
        "Nimbus" : r"voices\Nimbus.wav",
        "Tony"   : r"voices\Tony_King.wav",
        "Roland" : r"voices\Roland.wav",
    }
    dialog_files = []

    if not os.path.exists('dialogs'):
        os.makedirs('dialogs')
        
    concat_file = open("concat.txt", "w")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
    try:
        for i, dialog in enumerate(dialogs):
            filename = f"dialogs/dialog{i}.wav"

            if len(dialog["content"]) > 250:
                split_sentences = True
            else:
                split_sentences = False

            tts.tts_to_file(text=dialog["content"], speaker_wav=voice_names[dialog["speaker"]], language="en", split_sentences=split_sentences ,file_path=filename)
            concat_file.write("file " + filename + "\n")
            dialog_files.append(filename)
    except Exception as e:
        print(f"ERROR: {e}")

    concat_file.close()

    podcast_file = f"podcasts/podcast{timestamp}.wav"

    print("Concatenating audio")
    subprocess.run(f"ffmpeg -f concat -safe 0 -i concat.txt -c copy {podcast_file}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    os.unlink("concat.txt")

    for file in dialog_files:
        os.unlink(file)
    
    st.audio(podcast_file, format='audio/wav')

def generate_podcast():
    current_time = time.time()
    with st.spinner("📜 Generating the transcript..."):
        dialogs = generate_dialog(st.session_state["dialog_count"], current_time, st.session_state["podcast_topic"])
    st.write("Transcript generated successfully")
    with st.spinner("🎤 Generating the audio..."):
        generate_audio(dialogs, current_time)
    
if not st.session_state["characters_and_topics_submitted"]:
    with st.form("characters_and_topics"):
        st.selectbox(
        "Select your host character",
        ("Tony", "Mia"), key="host_character")
        st.multiselect(
        "Select the guests you would like to have on the show",
        ["Denzel", "Alex", "Nimbus", "Tony", "Roland"],key="guests")
        st.text_area("Enter your podcast topic here", key="podcast_topic")
        st.slider("Number of dialogs", 7, 15, 12, key="dialog_count")
        st.session_state["characters_and_topics_submitted"] = st.form_submit_button("Submit")

if st.session_state["characters_and_topics_submitted"]:
    with st.form("character_persona"):
        for guest in st.session_state["guests"]:
            st.text_area(f"Enter persona for {guest}", key=f"{guest}_persona")
        st.session_state["character_persona_submitted"] = st.form_submit_button("Submit")

if st.session_state["character_persona_submitted"]:
    generate_podcast()
    st.write("Podcast generated successfully")