import json

import requests
import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile


def click_uploadbtn():
    if not st.session_state.uploadbtn_state:
        st.session_state.uploadbtn_state = True
    else:
        st.session_state.uploadbtn_state = False


def upload_files(backend_url: str, file_list: list[UploadedFile]) -> list[requests.Response]:
    upload_url = f"{backend_url}/api/files/"
    response_list = []
    for file in file_list:
        res = requests.post(url=upload_url, files={"file": (file.name, file.read())})
        response_list.append(res)
    return response_list


@st.cache_data
def list_files(backend_url: str):
    list_files_url = f"{backend_url}/api/files/"
    try:
        res_raw = requests.get(url=list_files_url)
        res_raw.raise_for_status()
        return json.loads(res_raw.content)["Value"]
    except requests.HTTPError as err:
        raise err


def delete_files(backend_url: str, list_files: list):
    delete_files_url = f"{backend_url}/api/files/"
    body = {"Value": list_files}
    try:
        res_raw = requests.delete(url=delete_files_url, json=body)
        res_raw.raise_for_status()
        return True
    except requests.HTTPError as err:
        raise err
