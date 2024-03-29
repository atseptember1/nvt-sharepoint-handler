import os
import streamlit as st


current_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = f"{current_dir}/./pages/images/Nov_logo_notif.png"
architecture_path = f"{current_dir}/./pages/images/architecture.png"

st.image(logo_path)
st.title('Sharepoint Chatbot')
st.write("- interchatbot that is powered by Azure OpenAI and Azure AI Search.")
st.write("- This chatbot is integrated with Sharepoint sites and has document level security.")
st.write("- It provides quick and accurate responses to user queries and is capable of understanding natural language.")
st.write("Give it a try today and see how it can help you!")

st.header("High level architecture")
st.image(architecture_path)
