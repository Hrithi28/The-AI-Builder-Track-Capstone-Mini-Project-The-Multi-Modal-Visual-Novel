# The Multi-Modal Visual Novel

MirAI School of Technology — Virtual Summer Internship 2026, AI Builder Track
Capstone Mini-Project

## How to run

1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and add your real Gemini API key.
3. `streamlit run app.py`
4. Pick a Genre and Art Style in the sidebar, click **Begin the Adventure**, and
   play through by clicking the dynamically-generated option buttons.

## Architecture notes, mapped to the assignment phases

**Phase 1 — Director's Cut**
`get_gemini_client()` is wrapped in `@st.cache_resource` so the client is
configured once and reused across reruns. The sidebar ("Story Settings") holds
the Genre and Art Style dropdowns. `st.session_state` stores the live
`gemini_chat` object, the current scene, and a running `story_log`.

**Phase 2 — Structured JSON Engine**
The system instruction (sent as the first turn of the chat) forces Gemini to
reply with only a JSON object containing `story_text`, `image_prompt`, and
`options`. `parse_story_json()` strips any stray markdown fences the model
might add and uses `json.loads()` to turn the string into a Python dict.
Malformed responses raise `json.JSONDecodeError`, which is caught and
surfaced as a toast rather than crashing the app.

**Phase 3 — Dynamic UI Generation**
Because choices come from the model, not a fixed set, `st.chat_input()` isn't
usable. Instead, a `for` loop walks `scene["options"]` and creates one
`st.button()` per choice inside dynamically sized `st.columns()`. Clicking a
button sends that option's exact text back to Gemini as the player's next
move.

**Phase 4 — Multi-Media Rendering & TTS**
`generate_scene_image()` sends the model's `image_prompt` to Pollinations and
returns raw image bytes. `generate_narration()` runs the `story_text` through
`gTTS`, writes the MP3 to an in-memory buffer, and returns those bytes.
Both the image and the audio player are rendered from `st.session_state`, so
they persist across reruns instead of disappearing when a button is clicked.

**Phase 5 — Graceful Failures**
Both `generate_scene_image()` and `generate_narration()` are wrapped in
`try...except`. On failure they call `st.toast(...)` with a friendly message
("Image server is busy, skipping visual...") and return `None` — the story
continues with just text (and no image or audio) instead of crashing with a
traceback. The Gemini call itself is similarly wrapped so a malformed JSON
response doesn't kill the app either.

## Pre-submission checklist

- [x] JSON parsing: `story_text`, `image_prompt`, `options` extracted via `json.loads`



Streamlit Deployed link - https://lnkd.in/dWMMt-FD
- [x] Dynamic buttons generated per `options` returned by the model
- [x] Image + narration audio rendered and persisted via `session_state`
- [x] `try/except` + `st.toast` around both the image and audio calls
- [ ] **60-second screen recording** — must be captured live, showing the
      dynamic buttons changing between scenes and audio narration playing
      (record with system audio on)
