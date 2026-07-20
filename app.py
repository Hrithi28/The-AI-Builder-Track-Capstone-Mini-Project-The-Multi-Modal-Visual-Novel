import io
import json
import os
import re

import requests
import streamlit as st
from dotenv import load_dotenv
from gtts import gTTS
import google.generativeai as genai

load_dotenv()

GENRES = ["Fantasy", "Sci-Fi", "Horror", "Noir Mystery", "Fairy Tale"]
ART_STYLES = ["Anime", "Realistic", "Watercolor", "Cyberpunk", "Storybook Illustration"]

# ---------------------------------------------------------------
# Phase 1: The Director's Cut (UI & Configuration)
# ---------------------------------------------------------------

@st.cache_resource
def get_gemini_client():
    """Securely cache the configured Gemini client across reruns."""
    api_key = os.getenv("API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        st.error("`API_KEY` (or `GEMINI_API_KEY`) environment variable not set.")
        st.stop()
    genai.configure(api_key=api_key)
    return genai.GenerativeModel("gemini-2.5-flash")


def build_system_instruction(genre: str, art_style: str) -> str:
    return (
        "You are the narrative engine for an interactive choose-your-own-adventure "
        f"visual novel. Genre: {genre}. All scenes should feel consistent with this genre.\n\n"
        "You MUST respond with ONLY a single valid JSON object and nothing else — "
        "no markdown code fences, no commentary before or after it. The JSON object "
        "must contain exactly these three keys:\n"
        '  "story_text": a vivid narrative paragraph (3-5 sentences) continuing the '
        "story based on the reader's chosen action.\n"
        '  "image_prompt": a heavily descriptive, visual prompt suitable for an AI '
        f'image generator, depicting the current scene rendered in "{art_style}" style.\n'
        '  "options": a JSON array of 2 to 3 short strings, each a distinct action '
        "the reader could take next.\n\n"
        "Keep the story moving forward and never break character or mention that you "
        "are an AI."
    )


st.set_page_config(page_title="Visual Novel Engine", page_icon="📖")
st.title("📖 The Multi-Modal Visual Novel")
st.caption("A choose-your-own-adventure engine powered by Gemini, Pollinations, and TTS narration.")

with st.sidebar:
    st.title("Story Settings")
    st.divider()
    genre = st.selectbox("Story Genre", GENRES)
    art_style = st.selectbox("Art Style", ART_STYLES)
    st.divider()
    restart = st.button("🔄 Restart Story", use_container_width=True)
    st.caption("Images: Pollinations.ai · Narration: gTTS · Story: Gemini")

# Session state: chat history + the live Gemini chat object + current rendered scene
if "gemini_chat" not in st.session_state or restart:
    client = get_gemini_client()
    st.session_state.gemini_chat = client.start_chat(history=[])
    st.session_state.story_log = []       # list of past {story_text, image_prompt, options} scenes
    st.session_state.current_scene = None  # the scene currently rendered on screen
    st.session_state.current_image_bytes = None
    st.session_state.current_audio_bytes = None
    st.session_state.genre = genre
    st.session_state.art_style = art_style
    st.session_state.started = False

# If the user changes genre/art style mid-story, keep it locked to avoid tonal whiplash
genre = st.session_state.genre
art_style = st.session_state.art_style


# ---------------------------------------------------------------
# Phase 2: The Structured JSON Engine
# ---------------------------------------------------------------

def parse_story_json(raw_text: str) -> dict:
    """Parse Gemini's response into a dict with story_text, image_prompt, options."""
    cleaned = raw_text.strip()
    # Strip markdown code fences if the model added them despite instructions
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    data = json.loads(cleaned)

    if not all(k in data for k in ("story_text", "image_prompt", "options")):
        raise ValueError("Missing required keys in Gemini's JSON response.")
    return data


def request_next_scene(action_text: str):
    """Send the player's action to Gemini and parse the structured JSON scene."""
    try:
        with st.spinner("The story unfolds..."):
            response = st.session_state.gemini_chat.send_message(action_text)
            scene = parse_story_json(response.text)
    except json.JSONDecodeError:
        st.toast("The narrator stumbled over their words — please try that choice again.")
        return
    except Exception as e:
        st.toast(f"Story engine error: {e}")
        return

    # Save the previous scene to the log before overwriting
    if st.session_state.current_scene is not None:
        st.session_state.story_log.append(st.session_state.current_scene)

    st.session_state.current_scene = scene
    st.session_state.current_image_bytes = generate_scene_image(scene["image_prompt"])
    st.session_state.current_audio_bytes = generate_narration(scene["story_text"])
    st.session_state.started = True


# ---------------------------------------------------------------
# Phase 4: Multi-Media Rendering & TTS
# ---------------------------------------------------------------

def generate_scene_image(image_prompt: str):
    """Fetch a scene image from Pollinations. Returns None (and toasts) on failure."""
    try:
        encoded = requests.utils.quote(image_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded}?width=768&height=512"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            return resp.content
        st.toast("Image server is busy, skipping visual...")
        return None
    except Exception:
        st.toast("Image server is busy, skipping visual...")
        return None


def generate_narration(story_text: str):
    """Convert story_text to speech via gTTS. Returns None (and toasts) on failure."""
    try:
        tts = gTTS(text=story_text, lang="en")
        buffer = io.BytesIO()
        tts.write_to_fp(buffer)
        buffer.seek(0)
        return buffer.read()
    except Exception:
        st.toast("Narration engine is busy, continuing without audio...")
        return None


# ---------------------------------------------------------------
# Phase 3: Dynamic UI Generation
# ---------------------------------------------------------------

if not st.session_state.started:
    st.info(f"Genre: **{genre}** · Art style: **{art_style}**. Ready when you are.")
    if st.button("▶️ Begin the Adventure", type="primary", use_container_width=True):
        client = get_gemini_client()
        # Seed the chat with the system instruction as the very first turn
        system_instruction = build_system_instruction(genre, art_style)
        st.session_state.gemini_chat = client.start_chat(history=[
            {"role": "user", "parts": [system_instruction]},
            {"role": "model", "parts": ["Understood. I will respond only in the required JSON format."]},
        ])
        request_next_scene("Begin the story with an opening scene.")
        st.rerun()
else:
    scene = st.session_state.current_scene

    if st.session_state.current_image_bytes:
        st.image(st.session_state.current_image_bytes, use_container_width=True)

    st.markdown(f"### {scene['story_text']}")

    if st.session_state.current_audio_bytes:
        st.audio(st.session_state.current_audio_bytes, format="audio/mp3")

    st.divider()
    st.markdown("**What do you do?**")

    # Dynamically generate one button per option returned by Gemini
    cols = st.columns(len(scene["options"]))
    for i, option_text in enumerate(scene["options"]):
        with cols[i]:
            if st.button(option_text, key=f"option_{len(st.session_state.story_log)}_{i}",
                         use_container_width=True):
                request_next_scene(option_text)
                st.rerun()

    with st.expander("📜 Story so far"):
        for past_scene in st.session_state.story_log:
            st.write(past_scene["story_text"])
            st.divider()
