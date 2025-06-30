import streamlit as st
import asyncio
import nest_asyncio
import json
import os
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, RunConfig

nest_asyncio.apply()  # Fix event loop issue in Streamlit
load_dotenv()

# Load API key
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file.")

# Setup Gemini Client
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(model=model, model_provider=external_client)

# Define agents
title_agent = Agent(
    name="Title Agent",
    instructions="Generate a short, catchy post title from the topic and tone. Just one line."
)

caption_agent = Agent(
    name="Caption Agent",
    instructions="Write 2–3 engaging social media captions based on topic and tone."
)

hashtag_agent = Agent(
    name="Hashtag Agent",
    instructions="Generate 10 trending hashtags for the given topic and niche. No '#' symbols."
)

# History file
HISTORY_FILE = "history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as f:
            return json.load(f)
    return []

def save_history(entry):
    history = load_history()
    history.insert(0, entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[:20], f)

# Streamlit UI
st.set_page_config(page_title="Gemini Caption + Hashtag Generator", layout="centered")
st.title("📣 Gemini Caption + Hashtag Generator")

tab1, tab2 = st.tabs(["🚀 Generate", "📜 History"])

with tab1:
    topic = st.text_input("Enter Post Topic")
    tone = st.selectbox("Choose a Tone", ["Casual", "Funny", "Emotional"])
    niche = st.selectbox("Select a Niche", ["Food", "Travel", "Tech", "Lifestyle", "Other"])
    platform = st.selectbox("Platform", ["Instagram", "YouTube", "TikTok", "LinkedIn", "Other"])

    async def generate_all():
        title = (await Runner.run(title_agent, input=f"Topic: {topic}\nTone: {tone}", run_config=config)).final_output.strip()
        captions = (await Runner.run(caption_agent, input=f"Topic: {topic}\nTone: {tone}", run_config=config)).final_output.strip().split("\n")
        hashtags = (await Runner.run(hashtag_agent, input=f"Topic: {topic}\nNiche: {niche}", run_config=config)).final_output.strip().replace("#", "").split()

        st.subheader("📝 Generated Content")
        st.markdown(f"**Post Title:** {title}")
        st.markdown("**Caption Variations:**")
        for cap in captions:
            st.markdown(f"- {cap}")
        st.markdown("**Trending Hashtags:**")
        st.code(" ".join(f"#{h}" for h in hashtags))

        save_history({
            "platform": platform,
            "topic": topic,
            "tone": tone,
            "niche": niche,
            "title": title,
            "captions": captions,
            "hashtags": hashtags
        })

    if st.button("Generate") and topic:
        with st.spinner("Generating with Gemini..."):
            asyncio.run(generate_all())
    elif not topic:
        st.info("Please enter a topic first.")

with tab2:
    st.subheader("📜 Previous Captions & Hashtags")
    history = load_history()
    if not history:
        st.info("No history yet.")
    else:
        for entry in history:
            st.markdown(f"**🗂 Platform:** {entry.get('platform', 'N/A')} | **Topic:** {entry['topic']} | 🎭 Tone: {entry['tone']} | 🎯 Niche: {entry['niche']}")
            st.markdown(f"**📌 Title:** {entry.get('title', '')}")
            st.markdown("**📝 Captions:**")
            for cap in entry["captions"]:
                st.markdown(f"- {cap}")
            st.markdown("**🔖 Hashtags:**")
            st.code(" ".join(f"#{h}" for h in entry["hashtags"]))
            st.markdown("---")
