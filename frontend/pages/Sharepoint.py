import os
from dotenv import load_dotenv
import streamlit as st
import json
import pandas as pd
import numpy as np
from src.SharepointLogic import (create_sharepoint_indexer,
                                 get_sharepoint_list,
                                 delete_sharepoint_indexer, list_indexer)
from src.common import dataframe_with_selections

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL")

col1, col2 = st.columns(spec=2)
with col1:
    create_indexer_btn = st.button(label="Create Indexer")
with col2:
    delete_btn = st.button('Delete')

sites = get_sharepoint_list(backend_url=BACKEND_URL)
df = pd.DataFrame(sites)
selection = dataframe_with_selections(df)
st.write("Your selection:")
st.write(selection)
a = selection.to_json(orient="records")
b = json.loads(a)

st.write("Current Indexers:")
indexers = list_indexer(backend_url=BACKEND_URL)
indexers_df = pd.DataFrame(indexers)
st.dataframe(data=indexers_df)
if create_indexer_btn:
    create_sharepoint_indexer(backend_url=BACKEND_URL, site_list=b)
if delete_btn:
    delete_sharepoint_indexer(backend_url=BACKEND_URL, site_list=b)
