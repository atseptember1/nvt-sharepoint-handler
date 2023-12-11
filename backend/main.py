import os
from fastapi import FastAPI, UploadFile, File
from dotenv import load_dotenv
from src.FileManagement import FileHandler, FileManagementConfig, FileModelOut
from src.SearchServiceHandler import SearchServiceConfig
from src.OpenAIHandler import OpenAIConfig, OpenAI
from src.BlobStorage import BlobConfig
from src.AzureAuthentication import AzureAuthenticate
from src.model.input import OpenaiSummarizeIn, CustomSkillContentIn, SharepointHelperConfig, CognitveSearchConfig
from src.model.output import OpenAISummarizeOut
from src.model.common import SharepointSiteList
from src.CustomSkill import OpenAICustomSkill
from src.sharepoint.SharepointHelpers import SharepointHelper
from src.sharepoint.SharepointCognitiveSearchHandler import CognitiveSearch

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

SHAREPOINT_HELPER_CONFIG = SharepointHelperConfig(
    client_id=os.getenv("SHAREPOINT_APP_ID"),
    client_secret=os.getenv("SHAREPOINT_APP_SEC"),
    tenant_id=os.getenv("SHAREPOINT_TENANT_ID")
)

SHAREPOINT_COGSEARCH_CONFIG = CognitveSearchConfig(
    endpoint=os.getenv("AZURE_SEARCH_ENDPOINT"),
    index_name=os.getenv("AZURE_SEARCH_INDEX"),
    sharepoint_appid=os.getenv("SHAREPOINT_APP_ID"),
    sharepoint_appsec=os.getenv("SHAREPOINT_APP_SEC"),
    sharepoint_apptenantid=os.getenv("SHAREPOINT_TENANT_ID"),
    sharepoint_domain=os.getenv("SHAREPOINT_DOMAIN"),
    aoai_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    aoai_key=os.getenv("AZURE_OPENAI_KEY"),
    aoai_embed_deployment=os.getenv("AZURE_OPENAI_EMBED_DEPLOYMENT")
)


@app.post('/api/file/upload')
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

@app.post('/api/openai/summarize')
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

@app.post('/api/openai/question-generate')
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

@app.post('/api/customskill/question-generate')
def customskill_questiongen(input: CustomSkillContentIn):
    print(input)
    return input

@app.post('/api/customskill/summary')
def customskill_summarize(input: CustomSkillContentIn):
    print(input)
    return input

@app.get('/api/sharepoint/sites')
def list_sharepoint_site() -> SharepointSiteList:
    sharepoint_helper = SharepointHelper(config=SHAREPOINT_HELPER_CONFIG)
    return sharepoint_helper.list_sites()

@app.post('/api/sharepoint/indexer')
def create_sharepoint_indexer(input: SharepointSiteList):
    cognitive_search = CognitiveSearch(config=SHAREPOINT_COGSEARCH_CONFIG)
    for sharepoint_site in input.value:
        site_name = sharepoint_site.name
        cognitive_search.create_indexer_flow(sharepointsite_name=site_name.lower())
    return "200"

@app.delete('/api/sharepoint/indexer')
def create_sharepoint_indexer(input: SharepointSiteList):
    cognitive_search = CognitiveSearch(config=SHAREPOINT_COGSEARCH_CONFIG)
    for sharepoint_site in input.value:
        cognitive_search.delete_indexer_and_stuff(sharepointsite=sharepoint_site)
    return "200"

@app.get('/api/sharepoint/list-indexer')
def list_indexer():
    cognitive_search = CognitiveSearch(config=SHAREPOINT_COGSEARCH_CONFIG)
    return cognitive_search.list_indexer()