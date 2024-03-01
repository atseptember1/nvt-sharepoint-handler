import json

import requests
import streamlit as st


@st.cache_data
def get_sharepoint_list(backend_url: str):
    url = f"{backend_url}/api/sharepoint/sites"
    res_raw = requests.get(url=url)
    res = json.loads(res_raw.content)["Value"]
    return res


def create_sharepoint_indexer(backend_url: str, site_list: list):
    url = f"{backend_url}/api/sharepoint/indexer"
    body = {"Value": site_list}
    try:
        res_raw = requests.post(url=url, json=body)
        res_raw.raise_for_status()
        return True
    except requests.HTTPError as err:
        raise err


def delete_sharepoint_indexer(backend_url: str, site_list: list):
    url = f"{backend_url}/api/sharepoint/indexer"
    body = {"Value": site_list}
    try:
        res_raw = requests.delete(url=url, json=body)
        res_raw.raise_for_status()
        return True
    except requests.HTTPError as err:
        raise err


@st.cache_data
def list_indexer(backend_url: str):
    url = f"{backend_url}/api/sharepoint/list-indexer"
    try:
        res_raw = requests.get(url=url)
        res_raw.raise_for_status()
        return json.loads(res_raw.content)["Value"]
    except requests.HTTPError as err:
        raise err
