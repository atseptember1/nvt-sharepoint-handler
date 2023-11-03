import os
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from dotenv import load_dotenv
from src import (
    FileManagement,
    SearchServiceConfig,
    OpenAIConfig
)


app = FastAPI()
load_dotenv()

search_config = SearchServiceConfig(
    endpoint=os.getenv('AZURE_SEARCH_ENDPOINT'),
    key=os.getenv('AZURE_SEARCH_KEY'),
    index_name=os.getenv('AZURE_SEARCH_INDEX')
)
openai_config = OpenAIConfig(
    endpoint=os.getenv('AZURE_OPENAI_ENDPOINT')
    key=os.getenv('AZURE_OPENAI_KEY')
    chat_deployment=os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT')
    chat_model=os.getenv('AZURE_OPENAI_CHAT_MODEL')
    embed_deployment=os.getenv('AZURE_OPENAI_EMBED_DEPLOYMENT')
    embed_model=os.getenv('AZURE_OPENAI_EMBED_MODEL')
)
FILE_MANAGEMENT = FileManagement(search_config=search_config, openai_config=openai_config)


class FileModel(BaseModel):
    FileList: list[str]
    FileName: str
    Size: float

@app.post('/files/')
async def upload_modify_file(files: FileModel, upload_file: UploadFile):
    '''
    This function handle actions related to handling uoloading files.
    if upload, check if file exist, if not upload the file:
        if file exist already, delete all index related to the file based on file_name
    '''
    FILE_MANAGEMENT.batch_upload(file_name=files.FileName, file_io=upload_file)


# @app.delete('/files/')
# async def delete_file(file_name: str):
#     '''
#     if delete:
#         Query in search service to find all file match the file_name then delete
#     '''