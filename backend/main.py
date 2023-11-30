import os
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from dotenv import load_dotenv
from src.FileManagement import FileHandler, FileManagementConfig, FileModelOut
from src.SearchServiceHandler import SearchServiceConfig
from src.OpenAIHandler import OpenAIConfig, OpenAI
from src.BlobStorage import BlobConfig
from src.AzureAuthentication import AzureAuthenticate
from src.model.input import OpenaiSummarizeIn
from src.model.output import OpenAISummarizeOut

load_dotenv()
app = FastAPI(debug=True)

def init() -> FileHandler:
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
    return FILE_MANAGEMENT


@app.post('/file/upload')
async def upload_file(file: UploadFile) -> FileModelOut:
    '''
    This function handle actions related to handling uoloading files.
    if upload, check if file exist, if not upload the file:
        if file exist already, delete all index related to the file based on file_name
    '''
    file_management = init()
    upload_result = file_management.upload_file(file_io=file)
    print(upload_result)
    return upload_result


# class OpenaiSummarizeIn(BaseModel):
#     paragraph: str

# class OpenAISummarizeOut(BaseModel):
#     content: str

@app.post('openai/summarize')
async def openai_summarize(input: OpenaiSummarizeIn) -> OpenAISummarizeOut:
    AZURE_CREDENTIAL = AzureAuthenticate()
    OPENAI_CONFIG = OpenAIConfig(
        endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        key=AZURE_CREDENTIAL.openai_acess_token.token,
        chat_deployment=os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT'),
        chat_model=os.getenv('AZURE_OPENAI_CHAT_MODEL'),
        embed_deployment=os.getenv('AZURE_OPENAI_EMBED_DEPLOYMENT'),
        embed_model=os.getenv('AZURE_OPENAI_EsMBED_MODEL')
    )
    AI = OpenAI(config=OPENAI_CONFIG)
    output = OpenAISummarizeOut(content=AI.summarize_text(input.paragraph))
    return output

@app.post('openai/question-generate')
async def openai_summarize(input: OpenaiSummarizeIn) -> OpenAISummarizeOut:
    AZURE_CREDENTIAL = AzureAuthenticate()
    OPENAI_CONFIG = OpenAIConfig(
        endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
        key=AZURE_CREDENTIAL.openai_acess_token.token,
        chat_deployment=os.getenv('AZURE_OPENAI_CHAT_DEPLOYMENT'),
        chat_model=os.getenv('AZURE_OPENAI_CHAT_MODEL'),
        embed_deployment=os.getenv('AZURE_OPENAI_EMBED_DEPLOYMENT'),
        embed_model=os.getenv('AZURE_OPENAI_EsMBED_MODEL')
    )
    AI = OpenAI(config=OPENAI_CONFIG)
    output = OpenAISummarizeOut(content=AI.generate_question(input.paragraph))
    return output