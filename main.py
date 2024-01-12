import os

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile

from src.LocalFileAndFolderOps import write_to_file
from src.StorageHandler import StorageHandler
from src.model.common import SharepointSiteList
from src.model.config import (
    SharepointSearchConfig,
    SharepointHelperConfig,
    StorageConfig,
    StorageSearchConfig,
    SearchConfig
)
from src.model.input import (
    ListUserSiteApiIn,
    BlobPropertiesApiIn
)
from src.sharepoint.SharepointHelpers import SharepointHelper
from src.sharepoint.SharepointSearchHandler import SharepointSearchHandler
from src.StorageSearchHandler import StorageSearchHandler
from src.SearchHandler import SearchHandler

app = FastAPI(debug=True)
load_dotenv()

# env configuration
AZURE_STORAGE_ENV = {
    "StorageName": os.environ["AZURE_SA"],
    "StorageConnStr": os.environ["AZURE_SA_CONN_STR"],
    "ContainerName": os.environ["AZURE_SA_CONTAINER"],
}
SHAREPOINT_ENV = {
    "ClientId": os.environ["SHAREPOINT_CLIENT_ID"],
    "ClientSecret": os.environ["SHAREPOINT_CLIENT_SECRET"],
    "TenantId": os.environ["SHAREPOINT_TENANT_ID"],
    "Domain": os.environ["SHAREPOINT_DOMAIN"]
}
AZURE_SEARCH_ENV = {
    "Endpoint": os.environ["AZURE_SEARCH_ENDPOINT"],
    "IndexName": os.environ["AZURE_SEARCH_INDEX"]
}
AZURE_OPENAI_ENV = {
    "Endpoint": os.environ["AZURE_OPENAI_ENDPOINT"],
    "Key": os.environ["AZURE_OPENAI_KEY"],
    "EmbedDeployment": os.environ["AZURE_OPENAI_EMBED_DEPLOYMENT"]
}

# Initiate configuration
STORAGE_ENABLED = False
if AZURE_STORAGE_ENV["StorageName"] and AZURE_STORAGE_ENV["ContainerName"]:
    STORAGE_ENABLED = True
    STORAGE_CONFIG = StorageConfig(
        StorageName=AZURE_STORAGE_ENV["StorageName"],
        ContainerName=AZURE_STORAGE_ENV["ContainerName"]
    )
    STORAGE_SEARCH_CONFIG = StorageSearchConfig(
        Endpoint=AZURE_SEARCH_ENV["Endpoint"],
        IndexName=AZURE_SEARCH_ENV["IndexName"],
        AoaiEndpoint=AZURE_OPENAI_ENV["Endpoint"],
        AoaiKey=AZURE_OPENAI_ENV["Key"],
        AoaiEmbedDeployment=AZURE_OPENAI_ENV["EmbedDeployment"],
        StorageName=AZURE_STORAGE_ENV["StorageName"],
        ContainerName=AZURE_STORAGE_ENV["ContainerName"],
    )
    if AZURE_STORAGE_ENV["StorageConnStr"]:
        STORAGE_CONFIG.StorageConnStr = AZURE_STORAGE_ENV["StorageConnStr"]
        STORAGE_SEARCH_CONFIG.StorageConnStr = AZURE_STORAGE_ENV["StorageConnStr"]

SHAREPOINT_ENABLED = False
if SHAREPOINT_ENV["ClientId"] and SHAREPOINT_ENV["ClientSecret"] and SHAREPOINT_ENV["TenantId"] and SHAREPOINT_ENV["Domain"]:
    SHAREPOINT_ENABLED = True
    SHAREPOINT_HELPER_CONFIG = SharepointHelperConfig(
        ClientId=SHAREPOINT_ENV["ClientId"],
        ClientSecret=SHAREPOINT_ENV["ClientSecret"],
        TenantId=SHAREPOINT_ENV["TenantId"]
    )
    SHAREPOINT_SEARCH_CONFIG = SharepointSearchConfig(
        Endpoint=AZURE_SEARCH_ENV["Endpoint"],
        IndexName=AZURE_SEARCH_ENV["IndexName"],
        AoaiEndpoint=AZURE_OPENAI_ENV["Endpoint"],
        AoaiKey=AZURE_OPENAI_ENV["Key"],
        AoaiEmbedDeployment=AZURE_OPENAI_ENV["EmbedDeployment"],
        SharepointClientId=SHAREPOINT_ENV["ClientId"],
        SharepointClientSecret=SHAREPOINT_ENV["ClientSecret"],
        SharepointTenantId=SHAREPOINT_ENV["TenantId"],
        SharepointDomain=SHAREPOINT_ENV["Domain"]
    )

if STORAGE_ENABLED or SHAREPOINT_ENABLED:
    SEARCH_CONFIG = SearchConfig(
        Endpoint=AZURE_SEARCH_ENV["Endpoint"],
        IndexName=AZURE_SEARCH_ENV["IndexName"],
        AoaiEndpoint=AZURE_OPENAI_ENV["Endpoint"],
        AoaiKey=AZURE_OPENAI_ENV["Key"],
        AoaiEmbedDeployment=AZURE_OPENAI_ENV["EmbedDeployment"]
    )
else:
    raise SystemExit("No Azure Search configuration found")

# Storage APIs
if STORAGE_ENABLED:
    @app.post('/api/files/')
    def upload_file(file: UploadFile):
        storage_helper = StorageHandler(STORAGE_CONFIG)
        file_path = write_to_file(file.filename, file)
        return storage_helper.upload_blob(file_path)

    @app.delete('/api/files/')
    def delete_file(file_list: BlobPropertiesApiIn):
        storage_helper = StorageHandler(STORAGE_CONFIG)
        for file in file_list.Value:
            storage_helper.delete_blob(file.Name)
        return True

    @app.get('/api/files/')
    def list_blob():
        storage_helper = StorageHandler(STORAGE_CONFIG)
        return storage_helper.list_blobs()

    @app.post('/api/files/indexer')
    def create_storage_indexer():
        cognitive_search = StorageSearchHandler(config=STORAGE_SEARCH_CONFIG)
        cognitive_search.create_indexer_flow()
        return "200"

# Sharepoint APIs
if SHAREPOINT_ENABLED:
    @app.get('/api/sharepoint/sites')
    def list_sharepoint_site() -> SharepointSiteList:
        sharepoint_helper = SharepointHelper(config=SHAREPOINT_HELPER_CONFIG)
        return sharepoint_helper.list_sites()

    @app.post('/api/sharepoint/indexer')
    def create_sharepoint_indexer(body: SharepointSiteList):
        cognitive_search = SharepointSearchHandler(config=SHAREPOINT_SEARCH_CONFIG)
        for sharepoint_site in body.value:
            site_name = sharepoint_site.name
            cognitive_search.create_indexer_flow(spo_name=site_name.lower())
        return "200"

    @app.delete('/api/sharepoint/indexer')
    def delete_sharepoint_indexer(body: SharepointSiteList):
        cognitive_search = SharepointSearchHandler(config=SHAREPOINT_SEARCH_CONFIG)
        for sharepoint_site in body.value:
            cognitive_search.delete_indexer_and_stuff(sharepointsite=sharepoint_site)
        return "200"

    @app.get('/api/sharepoint/list-indexer')
    def list_indexer():
        cognitive_search = SharepointSearchHandler(config=SHAREPOINT_SEARCH_CONFIG)
        return cognitive_search.list_indexer()

    @app.get('/api/sharepoint/list-user-site')
    def list_user_site(body: ListUserSiteApiIn) -> SharepointSiteList:
        cognitive_search = SharepointSearchHandler(config=SHAREPOINT_SEARCH_CONFIG)
        sharepoint_helper = SharepointHelper(config=SHAREPOINT_HELPER_CONFIG)
        indexer_list = cognitive_search.list_indexer()
        site_name_list = []
        for indexer in indexer_list.value:
            site_name = indexer.DataSourceName.removesuffix("-datasource")
            site_name_list.append(site_name)
        return sharepoint_helper.check_user_belong_to_site_flow(body.userId, site_name_list)


@app.get('/api/sharepoint/list-indexer')
def list_indexer():
    search_handler = SearchHandler(config=SEARCH_CONFIG)
    return search_handler.list_indexer()


if __name__ == '__main__':
    import uvicorn
    try:
        uvicorn.run(app=app, host="0.0.0.0", port=8000)
    except Exception as err:
        raise err
