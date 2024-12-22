import streamlit as st
from anime_scraper import scrape_anime_season
from datetime import datetime
import json
import logging
import sys
import requests
from streamlit_ace import st_ace
from urllib.parse import quote_plus
import asyncio
import aiohttp
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

async def validate_rss_feed_async(session, url, timeout=5):
    """Asynchronously validate a single RSS feed."""
    try:
        async with session.get(url, timeout=timeout) as response:
            return url, response.status == 200 and 'xml' in response.headers.get('content-type', '')
    except Exception as e:
        logger.error(f"Error validating RSS feed {url}: {str(e)}")
        return url, False

def validate_rss_feed(url):
    """Synchronously validate a single RSS feed."""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200 and 'xml' in response.headers.get('content-type', '')
    except:
        return False

def format_rss_url(title):
    """Format the RSS URL for a given anime title."""
    return f"https://nyaa.si/?page=rss&q=-batch+ember+{quote_plus(title)}&c=0_0&f=0"

async def validate_all_rss_feeds_async(urls):
    """Validate multiple RSS feeds concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [validate_rss_feed_async(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return dict(results)

def run_async_validation(urls):
    """Run async validation in a synchronous context."""
    return asyncio.run(validate_all_rss_feeds_async(urls))

def get_current_season():
    """Get the current anime season based on the current date."""
    current_date = datetime.now()
    month = current_date.month
    year = current_date.year
    
    if month in [1, 2, 3]:
        return "winter", year
    elif month in [4, 5, 6]:
        return "spring", year
    elif month in [7, 8, 9]:
        return "summer", year
    else:  # month in [10, 11, 12]
        return "fall", year

# Initialize session state
if 'season' not in st.session_state:
    current_season, current_year = get_current_season()
    st.session_state.season = current_season
    st.session_state.year = current_year
if 'anime_list' not in st.session_state:
    st.session_state.anime_list = None
if 'edited_json' not in st.session_state:
    st.session_state.edited_json = None
if 'edited_values' not in st.session_state:
    st.session_state.edited_values = {}
if 'rss_validation_results' not in st.session_state:
    st.session_state.rss_validation_results = {}

st.title("Anime Scraper")
st.write("Fetch seasonal anime details with advanced features for editing and validation.")

def reset_to_current():
    """Reset all session state values to current season."""
    current_season, current_year = get_current_season()
    st.session_state.season = current_season
    st.session_state.year = current_year
    st.session_state.anime_list = None
    st.session_state.edited_json = None
    st.session_state.edited_values = {}
    st.session_state.rss_validation_results = {}

# Sidebar configuration
st.sidebar.header("Options")

season = st.sidebar.selectbox(
    "Select Season",
    ["winter", "spring", "summer", "fall"],
    index=["winter", "spring", "summer", "fall"].index(st.session_state.season),
    key='season_select'
)
year = st.sidebar.number_input(
    "Select Year",
    min_value=1950,
    max_value=2050,
    value=st.session_state.year,
    key='year_input'
)

# Reset button
if st.sidebar.button("Reset to Current Date"):
    reset_to_current()
    current_season, current_year = get_current_season()
    st.sidebar.success(f"Reset to: {current_season.capitalize()} {current_year}")
    st.rerun()

# Main content
show_json = st.checkbox("Show JSON Editor")
fetch_clicked = st.button("Fetch Anime")

if fetch_clicked:
    logger.info(f"Fetching anime for Season: {season} | Year: {year}")
    st.session_state.anime_list = scrape_anime_season(season, year)
    st.session_state.edited_json = None
    st.session_state.edited_values = {}
    st.session_state.rss_validation_results = {}

if st.session_state.anime_list:
    anime_list = st.session_state.anime_list
    logger.info(f"Found {len(anime_list)} anime entries.")
    st.success(f"### {season.capitalize()} {year} Anime")
    st.write(f"Found {len(anime_list)} anime.")

    # Validate All RSS Feeds button
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Validate All RSS Feeds"):
            with st.spinner("Validating all RSS feeds..."):
                start_time = time.time()
                rss_urls = [anime['rssUrl'] for anime in anime_list]
                results = run_async_validation(rss_urls)
                st.session_state.rss_validation_results = results
                end_time = time.time()
                valid_count = sum(1 for valid in results.values() if valid)
                
                with col2:
                    st.success(f"Validation complete in {end_time - start_time:.2f} seconds")
                    st.write(f"Valid feeds: {valid_count}/{len(rss_urls)}")

    if show_json:
        st.write("### JSON Editor")
        initial_json = st.session_state.edited_json or json.dumps(anime_list, indent=2)
        min_lines = len(initial_json.splitlines())
        editor_height = max(800, min_lines * 20)
        
        edited_json = st_ace(
            value=initial_json,
            language="json",
            theme="monokai",
            height=editor_height,
            keybinding="vscode",
            show_gutter=True,
            wrap=True,
            font_size=14,
            tab_size=2,
            show_print_margin=True,
            key="json_editor"
        )
        
        st.session_state.edited_json = edited_json

        try:
            updated_anime_list = json.loads(edited_json)
            st.success("✅ Valid JSON format")
            st.write("### Formatted View")
            st.json(updated_anime_list)
        except json.JSONDecodeError as e:
            st.error(f"Invalid JSON format: {str(e)}")
            logger.error(f"JSON validation error: {str(e)}")

    else:
        for idx, anime in enumerate(anime_list):
            title_key = f"title_{idx}"
            rss_key = f"rss_{idx}"
            
            if title_key not in st.session_state.edited_values:
                st.session_state.edited_values[title_key] = anime['title']
                st.session_state.edited_values[rss_key] = anime['rssUrl']

            with st.expander(anime['title'], expanded=True):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("##### Title")
                    new_title = st.text_input(
                        "Edit title",
                        value=st.session_state.edited_values[title_key],
                        key=f"title_input_{idx}",
                        label_visibility="collapsed"
                    )
                    st.session_state.edited_values[title_key] = new_title

                    st.markdown("##### Date")
                    st.info(anime['date'])

                    st.markdown("##### Genres")
                    st.write(", ".join(anime['genres']))

                with col2:
                    st.markdown("##### RSS Feed")
                    new_rss = st.text_input(
                        "Edit RSS feed",
                        value=st.session_state.edited_values[rss_key],
                        key=f"rss_input_{idx}",
                        label_visibility="collapsed"
                    )
                    st.session_state.edited_values[rss_key] = new_rss

                    col2_1, col2_2, col2_3 = st.columns([1, 1, 1])
                    with col2_1:
                        if st.button("Validate RSS", key=f"validate_{idx}"):
                            with st.spinner("Validating RSS feed..."):
                                is_valid = validate_rss_feed(new_rss)
                                if is_valid:
                                    st.success("✅ RSS feed is valid")
                                else:
                                    st.error("❌ RSS feed is invalid or inaccessible")
                    
                    with col2_2:
                        if st.button("Regenerate RSS", key=f"regenerate_{idx}"):
                            new_rss = format_rss_url(new_title)
                            st.session_state.edited_values[rss_key] = new_rss
                            st.rerun()
                    
                    with col2_3:
                        if st.session_state.rss_validation_results:
                            if new_rss in st.session_state.rss_validation_results:
                                is_valid = st.session_state.rss_validation_results[new_rss]
                                if is_valid:
                                    st.success("✅ Valid")
                                else:
                                    st.error("❌ Invalid")

                st.markdown("##### Synopsis")
                st.info(anime['synopsis'])

        if st.button("Save All Changes"):
            updated_anime = []
            for idx, anime in enumerate(anime_list):
                title_key = f"title_{idx}"
                rss_key = f"rss_{idx}"
                updated_anime.append({
                    **anime,
                    'title': st.session_state.edited_values[title_key],
                    'rssUrl': st.session_state.edited_values[rss_key]
                })
            
            st.session_state.anime_list = updated_anime
            st.session_state.edited_json = json.dumps(updated_anime, indent=2)
            
            st.success("Changes saved successfully!")
            if st.checkbox("Show updated data"):
                st.json(updated_anime)

else:
    if fetch_clicked:
        st.warning("No anime found for the selected season.")
        logger.warning(f"No anime found for {season} {year}")
