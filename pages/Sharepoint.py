import json
import os

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from src.frontend.SharepointLogic import (
    create_sharepoint_indexer,
    get_sharepoint_list,
    delete_sharepoint_indexer, list_indexer
)
from src.frontend.common import dataframe_with_selections, clear_cache_reload

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL")
BOT_URL = os.getenv("TEAMS_BOT_URL")


col1, col2, col3, col4 = st.columns(spec=4)
with col1:
    create_indexer_btn = st.button(label="Create Indexer")
with col2:
    delete_btn = st.button('Delete')
with col3:
    refresh_btn = st.button("Refresh")
with col4:
    bot_btn = st.link_button("Open Bot", url=BOT_URL)

sites = get_sharepoint_list(backend_url=BACKEND_URL)
df = pd.DataFrame(sites)
selection = dataframe_with_selections(df)
st.write("Your selection:")
st.write(selection)
selection_parsed = json.loads(selection.to_json(orient="records"))
st.write("Current Indexers:")
indexers = list_indexer(backend_url=BACKEND_URL)
indexers_df = pd.DataFrame(indexers)
st.dataframe(data=indexers_df)
btn = create_indexer_btn
if btn:
    if create_sharepoint_indexer(backend_url=BACKEND_URL, site_list=selection_parsed):
        clear_cache_reload()
if delete_btn:
    if delete_sharepoint_indexer(backend_url=BACKEND_URL, site_list=selection_parsed):
        clear_cache_reload()
if refresh_btn:
    clear_cache_reload()
