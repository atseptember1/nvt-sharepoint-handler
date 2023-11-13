import os
from dotenv import load_dotenv
import streamlit as st
import json
import pandas as pd
import numpy as np
from src.FileLogic import (
    click_uploadbtn,
    dataframe_with_selections,
    upload_files
)


load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL")
ALLOWED_FILES = ["pdf", "docx", "xlsx", "xls"]

if 'uploadbtn_state' not in st.session_state: st.session_state.uploadbtn_state = False
col1, col2 = st.columns(spec=2)
with col1:
    upload_btn = st.button(label="Upload", key="upload_btn", on_click=click_uploadbtn)
    if st.session_state.uploadbtn_state == True:
        with st.sidebar:
            file_list = st.sidebar.file_uploader(label='Upload file', accept_multiple_files=True, type=ALLOWED_FILES)
            if len(file_list) > 0:
                st.button(label="Upload", on_click=upload_files(backend_url=BACKEND_URL,
                                                                file_list=file_list))
with col2: 
    delete_btn = st.button('Delete')

df = pd.DataFrame(
    [
        {"FileName": "cac.py", "FileUrl": "/Users/nam/coding-stuff/nvt-azure-chatbot-frontend/.venv/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py"},
        {"FileName": "loz.cac", "FileUrl": "/Users/nam/coding-stuff/nvt-azure-chatbot-frontend/.venv/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py"},
        {"FileName": "eheheh.loa", "FileUrl": "/Users/nam/coding-stuff/nvt-azure-chatbot-frontend/.venv/lib/python3.11/site-packages/streamlit/runtime/scriptrunner/script_runner.py"}
    ]
)
selection = dataframe_with_selections(df)
st.write("Your selection:")
st.write(selection)