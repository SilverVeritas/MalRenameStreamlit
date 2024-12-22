### File: home.py

import streamlit as st
from anime_scraper import scrape_anime_season
from qbittorrent_integration import add_anime_to_qbittorrent

st.title("Welcome to the Seasonal Anime Downloader")
st.write("Navigate to the pages on the sidebar to get started.")