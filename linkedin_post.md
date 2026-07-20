🎮📖 Just shipped my Capstone Project for the MirAI School of Technology "AI Builder" Track: a Multi-Modal Visual Novel Engine built entirely in Streamlit!

This one pushed me past the live-session material — I had to independently research and implement three new engineering concepts:

🧩 Structured JSON parsing — instructing Gemini to return strict JSON (story text, image prompt, and branching options) and safely parsing it with Python's json library
🔘 Dynamic UI generation — rendering a different set of st.button() choices every turn, generated on the fly from the AI's own output
🔊 Text-to-speech narration — converting each story beat into audio with gTTS and playing it back with st.audio()

Under the hood: Gemini drives the narrative and branching logic, Pollinations.ai renders the scene art, and the whole thing runs on a stateful Streamlit architecture that survives reruns without losing the story. I also wrapped every external API call in try/except with st.toast() fallbacks, so a slow image or audio server degrades gracefully instead of crashing the app.

Huge thanks to MirAI School of Technology for a track that keeps raising the bar every week. On to the next build!

#AIBuilder #Streamlit #GenerativeAI #Python #MirAISchoolOfTechnology
