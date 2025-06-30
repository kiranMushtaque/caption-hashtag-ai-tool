import streamlit as st
from agents import Agent, Runner, RunConfig, AsyncOpenAI, OpenAIChatCompletionsModel
from dotenv import load_dotenv
import os, json
import asyncio

# Load API Key
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file.")

# Gemini via OpenAI-compatible client
external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

model = OpenAIChatCompletionsModel(
    model="gemini-1.5-flash",
    openai_client=external_client
)

config = RunConfig(model=model, model_provider=external_client)

# Agents
title_agent = Agent(
    name="Title Agent",
    instructions="Generate an engaging, short social media post title based on the topic and tone. Output only the title."
)

caption_agent = Agent(
    name="Caption Agent",
    instructions="Generate 2–3 casual and engaging social media captions for the given topic and tone."
)

hashtag_agent = Agent(
    name="Hashtag Agent",
    instructions="Generate 10 relevant and trending hashtags for the given topic and niche. Do not include # symbols."
)

# History File
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

# UI
st.set_page_config(page_title="Gemini Caption & Hashtag Generator", layout="centered")
st.title("📣 Gemini Caption + Hashtag Generator")

tab1, tab2 = st.tabs(["🚀 Generate", "📜 History"])

with tab1:
    topic = st.text_input("Enter Post Topic")
    tone = st.selectbox("Choose a Tone", ["Casual", "Funny", "Emotional", "Inspiring"])
    niche = st.selectbox("Select a Niche", ["Food", "Travel", "Fitness", "Education", "Other"])
    platform = st.selectbox("Platform", ["Instagram", "Twitter", "LinkedIn", "YouTube", "Facebook", "Other"])

    if st.button("Generate Content") and topic:
        with st.spinner("Generating Title, Captions & Hashtags..."):
            title = Runner.run_sync(
                title_agent,
                input=f"Topic: {topic}\nTone: {tone}",
                run_config=config
            ).final_output.strip()

            captions = Runner.run_sync(
                caption_agent,
                input=f"Topic: {topic}\nTone: {tone}",
                run_config=config
            ).final_output.strip().split("\n")

            hashtags = Runner.run_sync(
                hashtag_agent,
                input=f"Topic: {topic}\nNiche: {niche}",
                run_config=config
            ).final_output.strip().replace("#", "").split()

        st.subheader("📝 Generated Content")
        st.markdown(f"**Post Title:** {title}")

        st.markdown("**Caption Variations:**")
        for cap in captions:
            st.markdown(f"- {cap.strip()}")

        st.markdown("**Trending Hashtags:**")
        st.code(" ".join(f"#{tag.strip()}" for tag in hashtags))

        # Save to history
        save_history({
            "platform": platform,
            "topic": topic,
            "tone": tone,
            "niche": niche,
            "title": title,
            "captions": captions,
            "hashtags": hashtags
        })

    elif not topic:
        st.info("Please enter a topic to generate content.")

with tab2:
    st.subheader("📜 History")
    history = load_history()
    if not history:
        st.info("No history yet.")
    else:
        for entry in history:
            st.markdown(f"**🗂 Platform:** {entry.get('platform', 'N/A')} | **Topic:** {entry.get('topic', 'N/A')} | 🎭 Tone: {entry.get('tone', 'N/A')} | 🎯 Niche: {entry.get('niche', 'N/A')}")
            st.markdown(f"**🔤 Title:** {entry.get('title', 'N/A')}")
            st.markdown("**Captions:**")
            for cap in entry.get("captions", []):
                st.markdown(f"- {cap}")
            st.markdown("**Hashtags:**")
            st.code(" ".join(f"#{tag}" for tag in entry.get("hashtags", [])))
            st.markdown("---")
