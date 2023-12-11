import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import requests


def click_uploadbtn():
    if st.session_state.uploadbtn_state == False:
        st.session_state.uploadbtn_state = True
    else:
        st.session_state.uploadbtn_state = False


def upload_files(backend_url: str, file_list: list[UploadedFile]) -> requests.Response:
    upload_url = f"{backend_url}/file/upload"
    response_list = []
    for file in file_list:
        res = requests.post(url=upload_url, files={"file": (file.name, file.read())})
        response_list.append(res)
    return response_list
