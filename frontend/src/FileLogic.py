import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile
import requests


def click_uploadbtn():
    if st.session_state.uploadbtn_state == False: st.session_state.uploadbtn_state = True
    else: st.session_state.uploadbtn_state = False


def dataframe_with_selections(df):
    df_with_selections = df.copy()
    df_with_selections.insert(0, "Select", False)

    # Get dataframe row-selections from user with st.data_editor
    edited_df = st.data_editor(
        df_with_selections,
        hide_index=True,
        column_config={"Select": st.column_config.CheckboxColumn(required=True)},
        disabled=df.columns,
    )

    # Filter the dataframe using the temporary column, then drop the column
    selected_rows = edited_df[edited_df.Select]
    return selected_rows.drop('Select', axis=1)


def upload_files(backend_url: str, file_list: list[UploadedFile]):
    res = requests.post(url=backend_url, files=file_list)
    return res