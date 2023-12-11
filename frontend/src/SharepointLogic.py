import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import requests
from pandas import DataFrame
import json


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

@st.cache_data
def get_sharepoint_list(backend_url: str):
    url = f"{backend_url}/api/sharepoint/sites"
    res_raw = requests.get(url=url)
    res = json.loads(res_raw.content)["value"]
    return res

def create_sharepoint_indexer(backend_url: str, site_list: list):
    url = f"{backend_url}/api/sharepoint/indexer"
    body = {"value": site_list}
    try:
        res_raw = requests.post(url=url, json=body)
        res_raw.raise_for_status()
    except requests.HTTPError as err:
        raise err
    
def delete_sharepoint_indexer(backend_url: str, site_list: list):
    url = f"{backend_url}/api/sharepoint/indexer"
    body = {"value": site_list}
    try:
        res_raw = requests.delete(url=url, json=body)
        res_raw.raise_for_status()
    except requests.HTTPError as err:
        raise err

@st.cache_data
def list_indexer(backend_url: str):
    url = f"{backend_url}/api/sharepoint/list-indexer"
    try:
        res_raw = requests.get(url=url)
        res_raw.raise_for_status()
        return json.loads(res_raw.content)["value"]
    except requests.HTTPError as err:
        raise err