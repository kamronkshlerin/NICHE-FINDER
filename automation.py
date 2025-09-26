import streamlit as st
import requests
from datetime import datetime, timedelta
import pandas as pd

# ----------------- Configuration -----------------
API_KEY = "AIzaSyAWl_7gJfUy_HEWp-zHDyUsPq68Wr5yyM4"
YOUTUBE_SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
YOUTUBE_VIDEO_URL = "https://www.googleapis.com/youtube/v3/videos"
YOUTUBE_CHANNEL_URL = "https://www.googleapis.com/youtube/v3/channels"

# ----------------- Streamlit UI -----------------
st.title("🚀 YouTube Viral Topics Finder")

days = st.number_input("Enter Days to Search (1-30):", min_value=1, max_value=30, value=5)
subscriber_limit = st.number_input("Max Subscribers Filter:", min_value=0, value=3000)
max_videos = st.number_input("Max Videos per Keyword:", min_value=1, max_value=50, value=10)

keywords = [
    "ASMR Relaxation", "Sleep ASMR", "Whisper ASMR",
    "Tapping ASMR", "Personal Attention ASMR", "ASMR Roleplay",
    "ASMR Sounds", "ASMR Triggers", "ASMR Eating Sounds",
    "ASMR Mouth Sounds", "ASMR Haircut Roleplay", "ASMR Sleep Aid"
]

# ----------------- Caching API Calls -----------------
@st.cache_data(ttl=3600)
def fetch_youtube_data(url, params):
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        st.warning(f"Failed API call: {url} with params {params}")
        return None

# ----------------- Fetch Data -----------------
if st.button("Fetch Viral Videos"):
    start_date = (datetime.utcnow() - timedelta(days=int(days))).isoformat("T") + "Z"
    all_results = []

    progress = st.progress(0)
    for idx, keyword in enumerate(keywords, 1):
        st.info(f"Searching for keyword: {keyword}")
        
        search_params = {
            "part": "snippet",
            "q": keyword,
            "type": "video",
            "order": "viewCount",
            "publishedAfter": start_date,
            "maxResults": max_videos,
            "key": API_KEY
        }
        search_data = fetch_youtube_data(YOUTUBE_SEARCH_URL, search_params)
        if not search_data or "items" not in search_data:
            st.warning(f"No results for: {keyword}")
            continue

        videos = search_data["items"]
        video_ids = [v["id"]["videoId"] for v in videos if "id" in v and "videoId" in v["id"]]
        channel_ids = [v["snippet"]["channelId"] for v in videos]

        # Fetch video stats
        stats_data = fetch_youtube_data(YOUTUBE_VIDEO_URL, {
            "part": "statistics",
            "id": ",".join(video_ids),
            "key": API_KEY
        })
        # Fetch channel stats
        channel_data = fetch_youtube_data(YOUTUBE_CHANNEL_URL, {
            "part": "statistics",
            "id": ",".join(channel_ids),
            "key": API_KEY
        })

        if not stats_data or not channel_data:
            st.warning(f"Stats not found for: {keyword}")
            continue

        for video, stat, channel in zip(videos, stats_data["items"], channel_data["items"]):
            views = int(stat["statistics"].get("viewCount", 0))
            subs = int(channel["statistics"].get("subscriberCount", 0))
            if subs <= subscriber_limit:
                all_results.append({
                    "Keyword": keyword,
                    "Title": video["snippet"].get("title", "N/A"),
                    "Description": video["snippet"].get("description", "")[:200],
                    "URL": f"https://www.youtube.com/watch?v={video['id']['videoId']}",
                    "Views": views,
                    "Subscribers": subs
                })
        
        progress.progress(idx / len(keywords))

    # ----------------- Display Results -----------------
    if all_results:
        df = pd.DataFrame(all_results)
        st.success(f"Found {len(all_results)} videos under {subscriber_limit} subscribers!")
        st.dataframe(df.sort_values(by="Views", ascending=False).reset_index(drop=True))

        # Option to download CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name="youtube_viral_videos.csv",
            mime="text/csv"
        )
    else:
        st.warning("No results found for the given filters.")
