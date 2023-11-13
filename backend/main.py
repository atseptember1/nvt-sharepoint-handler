import os
from fastapi import FastAPI, UploadFile
from pydantic import BaseModel
from dotenv import load_dotenv
from src.FileManagement import FileHandler, FileManagementConfig, FileModel, FileModelOut
from src.SearchServiceHandler import SearchServiceConfig
from src.OpenAIHandler import OpenAIConfig
from src.BlobStorage import BlobConfig
from src.AzureAuthentication import AzureAuthenticate

app = FastAPI(debug=True)
load_dotenv()

AZURE_CREDENTIAL = AzureAuthenticate()
SEARCH_CONFIG = SearchServiceConfig(
    endpoint=os.getenv('AZURE_SEARCH_ENDPOINT'),
    credential=AZURE_CREDENTIAL.credential,
    index_name=os.getenv('AZURE_SEARCH_INDEX')
)
OPENAI_CONFIG = OpenAIConfig(
    endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
    key=AZURE_CREDENTIAL.openai_acess_token.token,
    chat_deployment=os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT'),
    chat_model=os.getenv('AZURE_OPENAI_CHAT_MODEL'),
    embed_deployment=os.getenv('AZURE_OPENAI_EMBED_DEPLOYMENT'),
    embed_model=os.getenv('AZURE_OPENAI_EMBED_MODEL')
)
BLOB_CONFIG = BlobConfig(
    sa_name=os.getenv("AZURE_SA_NAME"),
    container_name=os.getenv("AZURE_SA_CONTAINER_NAME"),
    credential=AZURE_CREDENTIAL.credential
)
FILE_MANAGEMENT_CONFIG = FileManagementConfig(
    search_config=SEARCH_CONFIG,
    openai_config=OPENAI_CONFIG,
    blob_config=BLOB_CONFIG
)
FILE_MANAGEMENT = FileHandler(config=FILE_MANAGEMENT_CONFIG)


# class FileModel(BaseModel):
#     FileName: str

# class FileModelOut(BaseModel):
#     BlobUrl: str
#     FileName: str
#     Success: bool


@app.post('/file/upload')
async def upload_modify_file(file: FileModel, upload_file: UploadFile) -> FileModelOut:
    '''
    This function handle actions related to handling uoloading files.
    if upload, check if file exist, if not upload the file:
        if file exist already, delete all index related to the file based on file_name
    '''
    res = FILE_MANAGEMENT.upload_file(file=file.FileName, file_io=upload_file)
    return res