import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from PIL import Image, ImageColor
import re
import time

# -----------------------------------
# Setup
# -----------------------------------
st.set_page_config(
    page_title="Crochet Finder", 
    layout="wide", 
    page_icon="🧶",
    initial_sidebar_state="expanded"
)

DATA_FILE = Path("/Users/tanyajustin/Documents/crochet_videos_with_colors.xlsx")

# -----------------------------------
# Helper Functions
# -----------------------------------
@st.cache_data
def load_data(path):
    try:
        df = pd.read_excel(path)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        
        # Data validation
        required_columns = ['title', 'thumbnail_url', 'url', 'channel', 'duration']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"Missing required columns: {missing_columns}")
            return pd.DataFrame()

        # --- Extract Difficulty from text ---
        def extract_difficulty(text):
            text = str(text).lower()
            if any(k in text for k in ["beginner", "easy", "no-sew", "simple", "basic"]):
                return "Easy"
            elif any(k in text for k in ["intermediate", "medium", "project", "practice"]):
                return "Medium"
            elif any(k in text for k in ["advanced", "complex", "expert", "intricate"]):
                return "Hard"
            else:
                return "Unspecified"

        df["difficulty"] = df.apply(
            lambda r: extract_difficulty(
                f"{r.get('title', '')} {r.get('transcript', '')}"
            ),
            axis=1,
        )

        # --- Parse RGB fallback ---
        def parse_rgb(x):
            if isinstance(x, list) and len(x) == 3:
                return x
            if isinstance(x, str):
                if x.startswith("#") and len(x) >= 7:
                    try:
                        return [int(x[1:3], 16), int(x[3:5], 16), int(x[5:7], 16)]
                    except:
                        pass
                elif x.startswith("rgb"):
                    try:
                        return [int(i) for i in re.findall(r'\d+', x)[:3]]
                    except:
                        pass
            return [204, 204, 204]  # Default gray

        if "dominant_rgb" not in df.columns:
            df["dominant_rgb"] = df.get("dominant_color_hex", "#cccccc").apply(parse_rgb)
            
        # Ensure duration is numeric
        df["duration"] = pd.to_numeric(df["duration"], errors="coerce").fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return pd.DataFrame()

def rgb_distance(a, b):
    return np.sqrt(sum((a[i] - b[i]) ** 2 for i in range(3)))

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(*rgb)

# -----------------------------------
# FIXED CSS Styling - Better Contrast
# -----------------------------------
st.markdown("""
<style>
    /* Base Theme */
    .main {
        background: linear-gradient(135deg, #fdf6f0 0%, #fffaf7 50%, #f8f0e9 100%);
        color: #3A2C1F !important; /* Dark Brown Text */
        font-family: 'Poppins', sans-serif;
    }

    /* Headings */
    .main-header {
        background: linear-gradient(135deg, #ffd6ba 0%, #ffe0e9 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(255, 183, 197, 0.3);
        border: 2px solid #ffffff;
    }

    .main-header h1 {
        color: #3A2C1F !important;
        font-weight: 800;
        font-size: 2.6rem;
        margin-bottom: 0.3rem;
        letter-spacing: -0.5px;
    }

    .main-header p {
        color: #5A3924 !important;
        font-weight: 500;
        font-size: 1.1rem;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fff7f3 0%, #fff0eb 100%);
        border-right: 2px solid #ffd6ba;
        color: #3A2C1F !important;
    }

    .sidebar-header {
        background: linear-gradient(135deg, #ffb7c5, #ffd6ba);
        padding: 1rem;
        border-radius: 15px;
        color: #3A2C1F !important;
        text-align: center;
        margin-bottom: 1.5rem;
        border: 2px solid #ffffff;
        font-weight: 700;
    }

    /* Filter Sections */
    .filter-section {
        background: white;
        padding: 1.2rem;
        border-radius: 15px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #ffe8dc;
        color: #3A2C1F !important;
    }

    .filter-section label {
        color: #3A2C1F !important;
        font-weight: 600;
    }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #ffb7c5 0%, #ffd6ba 100%);
        border: none;
        border-radius: 12px;
        color: #3A2C1F !important;
        font-weight: 600;
        padding: 0.5rem 1rem;
        box-shadow: 0 3px 8px rgba(255, 183, 197, 0.3);
        transition: 0.3s;
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        background: linear-gradient(135deg, #ff91a4 0%, #ffc4a3 100%);
        box-shadow: 0 6px 16px rgba(255, 183, 197, 0.4);
    }

    /* Category buttons */
    .category-btn {
        background: white !important;
        color: #3A2C1F !important;
        border: 1.5px solid #ffd6ba !important;
        font-weight: 600;
    }

    .category-btn:hover {
        background: #fff4f0 !important;
        border-color: #ffb7c5 !important;
    }

    /* Result Cards */
    .result-card {
        background: #ffffff;
        border-radius: 20px;
        padding: 1.2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 32px rgba(0,0,0,0.08);
        border: 1px solid #f3e4dd;
        color: #3A2C1F !important;
    }

    .result-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 36px rgba(0,0,0,0.1);
    }

    .result-card img {
        border-radius: 12px;
        transition: all 0.3s ease;
    }

    .result-card:hover img {
        transform: scale(1.02);
    }

    .result-title {
        font-weight: 700;
        color: #2E1E0F !important;
        font-size: 1.1rem;
        line-height: 1.4;
        margin-top: 0.8rem;
    }

    .result-meta {
        color: #5A3924 !important;
        font-size: 0.85rem;
        margin-top: 0.2rem;
    }

    /* Watch button */
    .save-button {
        display: inline-block;
        background: linear-gradient(135deg, #ffb7c5 0%, #ff91a4 100%);
        border-radius: 10px;
        padding: 0.5rem 1rem;
        color: white !important;
        font-weight: 600;
        margin-top: 0.8rem;
        text-align: center;
        transition: all 0.3s ease;
        text-decoration: none;
    }

    .save-button:hover {
        background: linear-gradient(135deg, #ff91a4 0%, #ffb7c5 100%);
        transform: translateY(-2px);
    }

    /* Stats Boxes */
    .stats-container {
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        color: #3A2C1F !important;
        text-align: center;
        padding: 1rem;
        font-weight: 600;
    }

    .stats-container strong {
        color: #D46A6A !important;
        font-size: 1.2rem;
    }

    /* Global Text Adjustments */
    .stApp, .stMarkdown, .stText, label, p, span, div {
        color: #3A2C1F !important;
    }

    /* Footer */
    .footer {
        text-align: center;
        color: #5A3924 !important;
        margin-top: 2rem;
        padding-bottom: 2rem;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------
# Load Data with Progress
# -----------------------------------
with st.spinner('🧶 Loading crochet data...'):
    df = load_data(DATA_FILE)

if df.empty:
    st.error("❌ No data loaded. Please check the data file.")
    st.stop()

# -----------------------------------
# Sidebar Filters
# -----------------------------------
with st.sidebar:
    st.markdown('<div class="sidebar-header"><h2>🎀 Crochet Finder</h2><p>Find your perfect pattern</p></div>', unsafe_allow_html=True)
    
    # Search
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    search_term = st.text_input("🔍 **Search videos**", placeholder="Search titles and descriptions...")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Difficulty
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.markdown("**🧶 Difficulty Level**")
    difficulty = st.radio(
        "Select difficulty:",
        ["All", "Easy", "Medium", "Hard"],
        horizontal=False,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Duration
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.markdown("**🕒 Duration**")
    duration_class = st.radio(
        "Select duration range:",
        ["All", "Quick (<15 min)", "Medium (15–45 min)", "Long (>45 min)"],
        horizontal=False,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Categories
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.markdown("**🧩 Categories**")
    
    categories = {
        "plushie": ("🧸 Plushies", "#ffb7c5"),
        "flowers": ("🌸 Flowers", "#ff9aa2"),
        "grannysquare": ("🧶 Granny Squares", "#ffd6ba"),
        "tapestry": ("🧵 Tapestry", "#b5ead7"),
        "wearable": ("👕 Wearables", "#c7ceea"),
        "unique": ("✨ Unique", "#e2f0cb")
    }
    
    if "selected_cat" not in st.session_state:
        st.session_state["selected_cat"] = None
    
    for cat_key, (cat_name, color) in categories.items():
        col1, col2 = st.columns([1, 8])
        with col1:
            st.markdown(f'<div class="color-preview" style="background-color: {color};"></div>', unsafe_allow_html=True)
        with col2:
            if st.button(cat_name, key=f"cat_{cat_key}", use_container_width=True):
                st.session_state["selected_cat"] = cat_key
    
    if st.session_state["selected_cat"] and st.button("🔄 Clear Category", use_container_width=True):
        st.session_state["selected_cat"] = None
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Color Matching
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    st.markdown("**🎨 Color Match**")
    
    uploaded_file = st.file_uploader("Upload yarn image", type=["png", "jpg", "jpeg"], help="Upload an image of your yarn to find matching patterns")
    selected_color = None
    
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")
        st.image(image, caption="Your Yarn 🧶", use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            picked = st.color_picker("Pick color", "#ffb7c5")
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)
            st.color_picker("", picked, disabled=True, label_visibility="collapsed")
        
        selected_color = tuple(int(picked.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    
    tolerance = st.slider("**🎯 Color match sensitivity**", 50, 400, 120, 
                         help="Lower = exact match, Higher = broader range")
    st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------------
# Filtering Logic
# -----------------------------------
filtered = df.copy()

# Apply filters
if search_term:
    mask_title = filtered["title"].str.contains(search_term, case=False, na=False)
    mask_trans = filtered.get("transcript", pd.Series([""] * len(filtered))).astype(str).str.contains(search_term, case=False, na=False)
    filtered = filtered[mask_title | mask_trans]

if difficulty != "All":
    filtered = filtered[filtered["difficulty"] == difficulty]

selected_cat = st.session_state["selected_cat"]
if selected_cat:
    filtered = filtered[filtered["category"].str.contains(selected_cat, case=False, na=False)]

if duration_class == "Quick (<15 min)":
    filtered = filtered[filtered["duration"] <= 15]
elif duration_class == "Medium (15–45 min)":
    filtered = filtered[(filtered["duration"] > 15) & (filtered["duration"] <= 45)]
elif duration_class == "Long (>45 min)":
    filtered = filtered[filtered["duration"] > 45]

if selected_color:
    filtered["color_distance"] = filtered["dominant_rgb"].apply(lambda x: rgb_distance(x, selected_color))
    filtered = filtered[filtered["color_distance"] < tolerance]
    # Sort by color similarity if color matching is active
    filtered = filtered.sort_values("color_distance")

# -----------------------------------
# Main Content
# -----------------------------------
st.markdown("""
<div class="main-header">
    <h1>🧵 Crochet Video Finder</h1>
    <p>Discover the perfect tutorial for your next project • {total_count} patterns available</p>
</div>
""".format(total_count=len(df)), unsafe_allow_html=True)

# Stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="stats-container">📊 <strong>{len(filtered)}</strong><br>Results</div>', unsafe_allow_html=True)
with col2:
    easy_count = len(filtered[filtered["difficulty"] == "Easy"])
    st.markdown(f'<div class="stats-container">🟢 <strong>{easy_count}</strong><br>Easy</div>', unsafe_allow_html=True)
with col3:
    medium_count = len(filtered[filtered["difficulty"] == "Medium"])
    st.markdown(f'<div class="stats-container">🟡 <strong>{medium_count}</strong><br>Medium</div>', unsafe_allow_html=True)
with col4:
    hard_count = len(filtered[filtered["difficulty"] == "Hard"])
    st.markdown(f'<div class="stats-container">🔴 <strong>{hard_count}</strong><br>Hard</div>', unsafe_allow_html=True)

# Results
if len(filtered) == 0:
    st.markdown("""
    <div style="text-align: center; padding: 4rem; background: white; border-radius: 20px; margin: 2rem 0;">
        <h3 style="color: #ff6b95; margin-bottom: 1rem;">🎯 No patterns found</h3>
        <p style="color: #6b5f58;">Try adjusting your filters or search terms to find more patterns!</p>
    </div>
    """, unsafe_allow_html=True)
else:
    # Sort options
    col1, col2 = st.columns([3, 1])
    with col2:
        sort_by = st.selectbox("Sort by:", ["Relevance", "Duration (Short first)", "Duration (Long first)"])
    
    if sort_by == "Duration (Short first)":
        filtered = filtered.sort_values("duration")
    elif sort_by == "Duration (Long first)":
        filtered = filtered.sort_values("duration", ascending=False)
    
    # Display results in grid
    cols = st.columns(3)
    for i, (_, row) in enumerate(filtered.iterrows()):
        with cols[i % 3]:
            # Get color indicator
            color_hex = rgb_to_hex(row['dominant_rgb']) if 'dominant_rgb' in row else "#cccccc"
            
            # Difficulty badge color
            diff_color = {
                "Easy": "#4CAF50",
                "Medium": "#FF9800", 
                "Hard": "#F44336",
                "Unspecified": "#9E9E9E"
            }.get(row.get('difficulty', 'Unspecified'), "#9E9E9E")
            
            st.markdown(f"""
            <div class="result-card">
                <img src="{row['thumbnail_url']}" width="100%">
                <div class="result-title">{row['title'][:80]}{'...' if len(row['title']) > 80 else ''}</div>
                <div class="result-meta">
                    <span>👩‍🎨 {row['channel']}</span>
                </div>
                <div class="result-meta">
                    <span>⏱ {row['duration']} min</span> • 
                    <span style="color: {diff_color}; font-weight: 600;">🎚 {row.get('difficulty', 'Unspecified')}</span>
                </div>
                <div class="result-meta">
                    <span>🧩 {row.get('category', 'Unspecified')}</span>
                </div>
                <a href="{row['url']}" target="_blank" class="save-button">💖 Watch Tutorial</a>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="footer">
    <hr style="border: none; height: 1px; background: linear-gradient(90deg, transparent, #ffd6ba, transparent); margin: 2rem 0;">
    <p>✨ Made with 💖 by Tanya Michelle Justin ✨</p>
</div>
""", unsafe_allow_html=True)