import os
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from dotenv import load_dotenv
from src import FileManagement


app = FastAPI()
load_dotenv()


FILE_MANAGEMENT = FileManagement(search_endpoint=os.getenv('AZURE_SEARCH_ENDPOINT'), search_key=os.getenv('AZURE_SEARCH_KEY'), search_index_name=os.getenv('AZURE_SEARCH_INDEX'),
                                 openai_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'), openai_key=os.getenv('AZURE_OPENAI_KEY'), openai_chat_model=os.getenv('AZURE_OPENAI_CHAT_MODEL'),
                                 openai_chat_deployment=os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT'), openai_embed_model=os.getenv('AZURE_OPENAI_EMBED_MODEL'), openai_embed_deployment=os.getenv('AZURE_OPENAI_EMBED_DEPLOYMENT'))


@app.post('/files/')
async def upload_modify_file(file_name: str, overwrite: bool = True, upload_file: UploadFile = None):
    '''
    This function handle actions related to handling files (upload, modify).
    if upload, check if file exist, if not upload the file:
        Else if overwrite is set to true, delete all index related to the file based on file_name
        If overwrite is false then we must provide a new name for the file... -> randomize or sequence?
    if modify:
        ????
    '''
    FILE_MANAGEMENT.upload_file(file_name=file_name, file_io=upload_file)
    # Check if file exist, if overwrite is false then we must provide a new name for the file... -> randomize or sequence?


# @app.delete('/files/')
# async def delete_file(file_name: str):
#     '''
#     if delete:
#         Query in search service to find all file match the file_name then delete
#     '''