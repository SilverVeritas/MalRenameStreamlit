### File: pages/2_Add_to_qBittorrent.py
import streamlit as st
from qbittorrent_integration import add_anime_to_qbittorrent
from anime_scraper import scrape_anime_season

st.title("Add Anime to qBittorrent")

season = st.selectbox("Select Season", ["fall", "winter", "spring", "summer"], index=0)
year = st.number_input("Select Year", min_value=2000, max_value=2050, value=2024)

if st.button("Add to qBittorrent"):
    anime_list = scrape_anime_season(season, year)
    if anime_list:
        add_anime_to_qbittorrent(anime_list, season, year)
        st.success("Anime added to qBittorrent.")
    else:
        st.warning("No anime to add.")
