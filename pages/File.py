import os
import json

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.FrontendUtils.FileLogic import (
    click_uploadbtn,
    upload_files,
    list_files,
    delete_files,
    configure_search
)
from src.FrontendUtils.common import (
    dataframe_with_selections,
    clear_cache_reload,
)

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL")
ALLOWED_FILES = ["pdf", "docx", "doc", "xlsx", "xls"]
BOT_URL = os.getenv("TEAMS_BOT_URL")


if 'uploadbtn_state' not in st.session_state:
    st.session_state.uploadbtn_state = False
col1, col2, col3, col4, col5 = st.columns(spec=5)
with col1:
    upload_btn = st.button(label="Upload", key="upload_btn", on_click=click_uploadbtn)
    if st.session_state.uploadbtn_state:
        with st.sidebar:
            file_list = st.sidebar.file_uploader(label='Upload file', accept_multiple_files=True, type=ALLOWED_FILES)
            if len(file_list) > 0:
                upload_submit = st.button(label="Upload")
                if upload_submit:
                    res = upload_files(backend_url=BACKEND_URL, file_list=file_list)
                    if res:
                        st.sidebar.success("File uploaded")
                        clear_cache_reload()
with col2:
    delete_btn = st.button('Delete')
with col3:
    refresh_btn = st.button("Refresh")
    if refresh_btn:
        clear_cache_reload()
with col4:
    search_config_btn = st.button("Configure Search")
    if search_config_btn:
        configure_search(BACKEND_URL)
with col5:
    bot_btn = st.link_button("Open Bot", url=BOT_URL)

files = list_files(BACKEND_URL)
df = pd.DataFrame(files)
selection = dataframe_with_selections(df)
st.write("Your selection:")
st.write(selection)
selection_parsed = json.loads(selection.to_json(orient="records"))
if delete_btn:
    if delete_files(BACKEND_URL, selection_parsed):
        clear_cache_reload()

with st.sidebar:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    logo_path = f"{current_dir}/./images/Nov_logo_notif.png"
    st.image(logo_path)
