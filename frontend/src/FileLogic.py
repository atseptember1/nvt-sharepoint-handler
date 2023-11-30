import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import requests
from pandas import DataFrame


def click_uploadbtn():
    if st.session_state.uploadbtn_state == False:
        st.session_state.uploadbtn_state = True
    else:
        st.session_state.uploadbtn_state = False


def dataframe_with_selections(df: DataFrame) -> DataFrame:
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={
            "Select": st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns
    )
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)


def upload_files(backend_url: str, file_list: list[UploadedFile]) -> requests.Response:
    upload_url = f"{backend_url}/file/upload"
    response_list = []
    for file in file_list:
        res = requests.post(url=upload_url, files={"file": (file.name, file.read())})
        response_list.append(res)
    return response_list
