import streamlit as st
from pandas import DataFrame


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

def clear_cache_reload():
    st.cache_data.clear()
    st.rerun()