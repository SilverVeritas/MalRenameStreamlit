import streamlit as st
from anime_scraper import scrape_anime_season
from datetime import datetime
import json
import logging
import sys
from streamlit_ace import st_ace
import streamlit.components.v1 as components

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Custom CSS for styling
st.markdown("""
<style>
    .json-key { color: #2196F3 !important; }  /* Blue */
    .json-date { color: #4CAF50 !important; }  /* Green */
    .json-genres { color: #9C27B0 !important; }  /* Purple */
    .json-synopsis { color: #FF9800 !important; }  /* Orange */
    .json-rss { color: #009688 !important; }  /* Teal */
    
    .success-message {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        transition: transform 0.2s;
    }
</style>
""", unsafe_allow_html=True)

st.title("Anime Scraper")
st.write("Fetch seasonal anime details with advanced JSON editing and visualization.")

# Session state for preserving values across reruns
if 'current_season' not in st.session_state:
    st.session_state.current_season = None
if 'current_year' not in st.session_state:
    st.session_state.current_year = None

# Helper function to get season
def get_season_from_month(month):
    seasons = {
        (12, 1, 2): "winter",
        (3, 4, 5): "spring",
        (6, 7, 8): "summer",
        (9, 10, 11): "fall"
    }
    return next(season for months, season in seasons.items() if month in months)

# Sidebar configuration
st.sidebar.header("Options")
current_year = datetime.now().year
current_month = datetime.now().month

# Create placeholders for dynamic updating
season_container = st.sidebar.empty()
year_container = st.sidebar.empty()
reset_container = st.sidebar.empty()

# Initialize or get values from session state
if st.session_state.current_season is None:
    st.session_state.current_season = get_season_from_month(current_month)
if st.session_state.current_year is None:
    st.session_state.current_year = current_year

# Season and year selection
season = season_container.selectbox(
    "Select Season",
    ["winter", "spring", "summer", "fall"],
    index=["winter", "spring", "summer", "fall"].index(st.session_state.current_season)
)
year = year_container.number_input(
    "Select Year",
    min_value=1950,
    max_value=2050,
    value=st.session_state.current_year
)

# Reset functionality
def reset_to_current():
    st.session_state.current_season = get_season_from_month(current_month)
    st.session_state.current_year = current_year
    st.sidebar.success(f"Reset to: {st.session_state.current_season.capitalize()} {st.session_state.current_year}")
    logger.info(f"Reset to current date: {st.session_state.current_season} {st.session_state.current_year}")

if reset_container.button("Reset to Current Date"):
    reset_to_current()

# Main content area
show_json = st.checkbox("Show Advanced JSON Editor")
fetch_clicked = st.button("Fetch Anime")

def format_json_with_colors(json_obj):
    """Custom JSON formatter with color coding for specific fields"""
    if isinstance(json_obj, dict):
        items = []
        for key, value in json_obj.items():
            color_class = {
                'title': 'json-key',
                'date': 'json-date',
                'genres': 'json-genres',
                'synopsis': 'json-synopsis',
                'rssUrl': 'json-rss'
            }.get(key, '')
            
            formatted_value = format_json_with_colors(value)
            items.append(f'<span class="{color_class}">"{key}"</span>: {formatted_value}')
        return '{' + ', '.join(items) + '}'
    elif isinstance(json_obj, list):
        return '[' + ', '.join(format_json_with_colors(item) for item in json_obj) + ']'
    elif isinstance(json_obj, str):
        return f'"{json_obj}"'
    else:
        return str(json_obj)

if fetch_clicked:
    logger.info(f"Fetching anime for Season: {season} | Year: {year}")
    anime_list = scrape_anime_season(season, year)

    if anime_list:
        logger.info(f"Found {len(anime_list)} anime entries.")
        st.success(f"### {season.capitalize()} {year} Anime")
        st.write(f"Found {len(anime_list)} anime.")

        if show_json:
            st.write("### JSON Editor")
            # Use streamlit-ace for advanced editing capabilities
            edited_json = st_ace(
                value=json.dumps(anime_list, indent=4),
                language="json",
                theme="monokai",
                key_bindings="vscode",
                min_lines=20,
                max_lines=40,
                font_size=14,
                tab_size=4,
                show_gutter=True,
                wrap=True,
                auto_update=True,
                readonly=False
            )

            try:
                updated_anime_list = json.loads(edited_json)
                st.success("✅ JSON is valid")
                
                # Display colored JSON
                st.write("### Formatted JSON Preview")
                colored_json = format_json_with_colors(updated_anime_list)
                st.markdown(f'<pre>{colored_json}</pre>', unsafe_allow_html=True)
                
                logger.info("JSON updated and validated successfully")
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON format: {str(e)}")
                logger.error(f"JSON validation error: {str(e)}")
        else:
            # Display anime details in expandable sections
            for anime in anime_list:
                with st.expander(anime['title']):
                    cols = st.columns([2, 3])
                    with cols[0]:
                        st.write("📅 **Date**", anime['date'])
                        st.write("🏷️ **Genres**", ", ".join(anime['genres']))
                    with cols[1]:
                        st.write("📝 **Synopsis**", anime['synopsis'])
                        st.markdown(f"🔗 [RSS Feed]({anime['rssUrl']})")
    else:
        st.warning("No anime found for the selected season.")
        logger.warning(f"No anime found for {season} {year}")