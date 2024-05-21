import streamlit as st
from groq import Groq
import time
import json
import os
from TTS.api import TTS
import torch
import subprocess


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
Character Personas:\n {character_personas}\n
The podcast will have {number_of_dialogs} dialogs.\n"""
    instructions = """Instructions:\n
Don't use non-verbal cues like *laughs* or *ahem* or parentheticals in the podcast. Use Hehe or Haha instead of *laughs*.\n
Also don't use a speaker label on the add_dialog tool's content parameter but you should always set speaker parameter for the correct speaker."""

    st.write(podcast_template)
    transcript_file_name = f"podcasts/podcast{timestamp}.txt"
    transcript_file = open(transcript_file_name, "w")

    dialogs = []
    messages = [
        {
            "role": "system",
            "content": "You are a podcast generator. Generate the dialog for a podcast based on the description given by the user. Always use only one tool at a time."
        },
        {
            "role": "user",
            "content": podcast_template + instructions
        }
    ]
    groqclient = Groq()
    for _ in range(0, number_of_dialogs):
        response = groqclient.chat.completions.create(
        model="llama3-70b-8192",
        messages=messages,
        tools=[
                { 
                    "type": "function",
                    "function": {
                        "name": "add_dialog",
                        "description": "Add dialog to the podcast",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "speaker": {
                                    "type": "string",
                                    "description": "The name of the speaker"
                                },
                                "content": {
                                    "type": "string",
                                    "description": "The content of the speech"
                                },
                                "dialog_counter": {
                                    "type": "string",
                                    "description": "The number of the dialog. Should be incremented by 1 for each dialog"
                                }
                            },
                            "required": ["speaker","content","dialog_counter"],
                        },
                    },
                }
            ],
        tool_choice={"type": "function", "function": { "name": "add_dialog" } },
        max_tokens=4096,
        temperature=0.7
    )

        message = response.choices[0].message # type: ignore

        if len(message.tool_calls) > 1:
            print("More than one tool call. Exiting.")
            raise Exception("More than one tool call. Exiting.")

        tool_call= message.tool_calls[0]

        
        arguments = json.loads(tool_call.function.arguments)

        if debug:
            print(str(arguments))
        
        transcript_line = arguments['speaker'] + " says: " + arguments['content']  + "\n"
        transcript_file.write(transcript_line)
        messages.append(message)
        dialogs.append(arguments)

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

    if not os.path.exists('podcasts'):
        os.makedirs('podcasts')
        
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
    st.write("✨Podcast generated successfully✨")