# Podcast Generator

This application is a podcast generator that works %100 locally on your computer. It uses Phidata assistant client to generate dialogues for a podcast based on user inputs. It is built with Python and uses the Streamlit library for the web interface, llama3-8b-instruct model for AI dialog generation, and the TTS (Text-to-Speech) library for generating audio from the generated dialogues.

![Podcast Generator](https://i.ibb.co/gZJJYXT/Ekran-g-r-nt-s-2024-05-21-201959.png)

## Features

- User can select a host character and guest characters for the podcast.
- User can define the persona for each character.
- User can specify the topic of the podcast.
- User can specify the number of dialogues in the podcast.
- The application generates a transcript of the podcast.
- The application generates an audio file of the podcast.

## Prerequisites

Before running the application, ensure that you meet the following prerequisites:

- Download and install Ollama from https://ollama.com/
- You need to have `ffmpeg` installed on your system. `ffmpeg` is a free and open-source software project consisting of a large suite of libraries and programs for handling video, audio, and other multimedia files and streams.
- Your system should have at least 4GB of VRAM as the application uses a local TTS model which is resource-intensive.

### Installing ffmpeg

#### On Windows

1.  Download the latest version of ffmpeg from the  official website.
2.  Extract the downloaded file.
3.  Add the bin folder from the extracted file to your system's PATH.
   
Or with chocolatey

```bash
choco install ffmpeg
```

#### On macOS

You can install ffmpeg using Homebrew:
```bash
brew  install  ffmpeg
```
#### On Linux

You can install ffmpeg using apt:

```bash
sudo apt update
sudo apt install ffmpeg
```

After installing ffmpeg, you can run the application as described in the "How to Run" section.
## How to Run

1. Clone the repository.
2. Install the required Python libraries using pip:

```bash
pip install -r requirements.txt
```

3. Run the Streamlit application:

```bash
streamlit run app.py
```

4. Open the application in your web browser at `http://localhost:8501`.

## Usage

1. Select your host character and the guests you would like to have on the show.
2. Enter your podcast topic.
3. Set the number of dialogues you want in the podcast.
4. Define the persona for each character.
5. Click the "Submit" button to generate the podcast.
6. The application will generate a transcript and an audio file of the podcast.


