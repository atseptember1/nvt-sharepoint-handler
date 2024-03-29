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
        """
        Uploads a file to the Azure Blob Storage container.

        Args:
            file (UploadFile): The file to be uploaded.

        Returns:
            BlobHandlerUploadBlob: An object containing the upload status and blob URL.
        """
        storage_helper = StorageHandler(STORAGE_CONFIG)
        file_path = write_to_file(file.filename, file)
        return storage_helper.upload_blob(file_path)

    @app.delete('/api/files/')
    def delete_file(file_list: BlobPropertiesApiIn):
        """
        Deletes multiple blobs from the Azure Blob Storage container.

        Args:
            file_list (BlobPropertiesApiIn): A BlobPropertiesApiIn object containing a list of BlobProperties objects, each representing a blob to be deleted.

        Returns:
            bool: True if all blobs are successfully deleted, False otherwise.

        Raises:
            HttpResponseError: If there is an error while deleting a blob.
        """
        storage_helper = StorageHandler(STORAGE_CONFIG)
        for file in file_list.Value:
            storage_helper.delete_blob(file.Name)
        return True

    @app.get('/api/files/')
    def list_blob():
        """
            Retrieves a list of blobs from the Azure Blob Storage container.

            Returns:
                BlobPropertiesApiOut: A BlobPropertiesApiOut object containing a list of BlobProperties objects.
                    Each BlobProperties object contains the name and URL of a blob.
        """
        storage_helper = StorageHandler(STORAGE_CONFIG)
        return storage_helper.list_blobs()

    @app.post('/api/files/indexer')
    def create_storage_indexer():
        """
        Creates a storage indexer for Azure Blob Storage.

        Returns:
            str: The HTTP status code indicating the success of the operation.

        Raises:
            Exception: If there is an error while creating the storage indexer.
        """
        cognitive_search = StorageSearchHandler(config=STORAGE_SEARCH_CONFIG)
        cognitive_search.create_indexer_flow()
        return "200"

# Sharepoint APIs
if SHAREPOINT_ENABLED:
    @app.get('/api/sharepoint/sites')
    def list_sharepoint_site() -> SharepointSiteList:
        """
        Retrieves a list of SharePoint sites.

        Returns:
            SharepointSiteList: A SharepointSiteList object containing a list of SharePoint sites.
                Each SharePoint site object contains the display name, ID, name, and web URL of a site.

        Raises:
            requests.HTTPError: If there is an error while making the API request to retrieve the site list.
        """
        sharepoint_helper = SharepointHelper(config=SHAREPOINT_HELPER_CONFIG)
        return sharepoint_helper.list_sites()

    @app.post('/api/sharepoint/indexer')
    def create_sharepoint_indexer(body: SharepointSiteList):
        """
        Creates a SharePoint indexer for Azure Cognitive Search.

        Args:
            body (SharepointSiteList): A SharepointSiteList object containing a list of SharePoint sites.
                Each SharePoint site object contains the display name, ID, name, and web URL of a site.

        Returns:
            str: The HTTP status code indicating the success of the operation.

        Raises:
            Exception: If there is an error while creating the SharePoint indexer.
        """
        cognitive_search = SharepointSearchHandler(config=SHAREPOINT_SEARCH_CONFIG)
        for sharepoint_site in body.Value:
            site_name = sharepoint_site.name
            cognitive_search.create_indexer_flow(spo_name=site_name.lower())
        return "200"

    @app.delete('/api/sharepoint/indexer')
    def delete_sharepoint_indexer(body: SharepointSiteList):
        """
        Deletes a SharePoint indexer for Azure Cognitive Search.

        Args:
            body (SharepointSiteList): A SharepointSiteList object containing a list of SharePoint sites.
                Each SharePoint site object contains the display name, ID, name, and web URL of a site.

        Returns:
            str: The HTTP status code indicating the success of the operation.

        Raises:
            HttpResponseError: If there is an error while deleting the SharePoint indexer.
        """
        cognitive_search = SharepointSearchHandler(config=SHAREPOINT_SEARCH_CONFIG)
        for sharepoint_site in body.Value:
            cognitive_search.delete_indexer_and_stuff(sharepointsite=sharepoint_site)
        return "200"

    @app.get('/api/sharepoint/list-indexer')
    def list_sharepoint_indexer():
        """
        Retrieves a list of SharePoint indexers for Azure Cognitive Search.

        Returns:
            List[SearchIndexer]: A list of SearchIndexer objects representing the SharePoint indexers.
                Each SearchIndexer object contains information about the indexer, such as its name, data source name, and skillset name.

        Raises:
            Exception: If there is an error while retrieving the SharePoint indexers.
        """
        cognitive_search = SharepointSearchHandler(config=SHAREPOINT_SEARCH_CONFIG)
        return cognitive_search.list_indexer()

    @app.get('/api/sharepoint/list-user-site')
    def list_user_site(body: ListUserSiteApiIn) -> SharepointSiteList:
        """
        Retrieve the list of SharePoint sites that a user belongs to.

        Parameters:
        - body (ListUserSiteApiIn): The request body containing the user ID.

        Returns:
        - SharepointSiteList: The list of SharePoint sites that the user belongs to.
        """
        cognitive_search = SharepointSearchHandler(config=SHAREPOINT_SEARCH_CONFIG)
        sharepoint_helper = SharepointHelper(config=SHAREPOINT_HELPER_CONFIG)
        indexer_list = cognitive_search.list_indexer()
        site_name_list = []
        for indexer in indexer_list.Value:
            site_name = indexer.DataSourceName.removesuffix("-datasource")
            site_name = site_name.removesuffix("-sharepoint")
            site_name_list.append(site_name)
        return sharepoint_helper.check_user_belong_to_site_flow(body.userId, site_name_list)


if __name__ == '__main__':
    import uvicorn
    try:
        uvicorn.run(app=app, host="localhost", port=8501)
    except Exception as err:
        raise err
