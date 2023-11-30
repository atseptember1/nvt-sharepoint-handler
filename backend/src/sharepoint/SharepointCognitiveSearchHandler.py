import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import os
import datetime
from pydantic import BaseModel
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes.models import (
    SearchIndexerDataContainer,
    SearchIndex,
    SearchIndexer,
    SimpleField,
    SearchFieldDataType,
    EntityRecognitionSkill,
    InputFieldMappingEntry,
    OutputFieldMappingEntry,
    SearchIndexerSkillset,
    SearchableField,
    IndexingParameters,
    SearchIndexerDataSourceConnection,
    IndexingParametersConfiguration,
    FieldMapping,
    FieldMappingFunction,
    AzureOpenAIEmbeddingSkill,
    SplitSkill,
    WebApiSkill
)
from azure.search.documents.indexes import SearchIndexerClient, SearchIndexClient
from azure.core.exceptions import ResourceExistsError, HttpResponseError
from AzureAuthentication import AzureAuthenticate


class CognitveSearchConfig(BaseModel):
    endpoint: str
    index_name: str
    sharepoint_appid: str
    sharepoint_appsec: str
    sharepoint_apptenantid: str
    sharepoint_domain: str


class CognitiveSearch(AzureAuthenticate):
    def __init__(self, config: CognitveSearchConfig) -> None:
        super().__init__()
        self.config = config

    def create_index(self) -> SearchIndex:
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(
                name="metadata_spo_item_name", type=SearchFieldDataType.String
            ),
            SimpleField(name="metadata_spo_item_path", type=SearchFieldDataType.String),
            SearchableField(
                name="metadata_spo_site_id", type=SearchFieldDataType.String
            ),
            SimpleField(
                name="metadata_spo_item_weburi", type=SearchFieldDataType.String
            ),
            SearchableField(name="content", type=SearchFieldDataType.String),
        ]
        try:
            index = SearchIndex(name=self.config.index_name, fields=fields)
            index_client = SearchIndexClient(
                endpoint=self.config.endpoint, credential=self.credential
            )
            result = index_client.create_or_update_index(index=index)
            return result
        except ResourceExistsError as res_exist_err:
            print(res_exist_err)
            return index_client.get_index(name=self.config.index_name)
        except Exception as generic_err:
            print(generic_err)
            raise (generic_err)

    def create_datasource(
        self, sharepointsite_name: str, domain_name: str
    ) -> SearchIndexerDataSourceConnection:
        container_name = "allSiteLibraries"
        datasource_name = f"{sharepointsite_name}-datasource"
        connection_string = f"SharePointOnlineEndpoint=https://{domain_name}.sharepoint.com/sites/{sharepointsite_name}/;ApplicationId={self.config.sharepoint_appid};ApplicationSecret={self.config.sharepoint_appsec};TenantId={self.config.sharepoint_apptenantid}"
        try:
            ds_client = SearchIndexerClient(
                endpoint=self.config.endpoint, credential=self.credential
            )
            container = SearchIndexerDataContainer(name=container_name)
            data_source_connection = SearchIndexerDataSourceConnection(
                name=datasource_name,
                type="sharepoint",
                connection_string=connection_string,
                container=container,
            )
            data_source = ds_client.create_data_source_connection(
                data_source_connection
            )
            return data_source
        except HttpResponseError as genericErr:
            print(genericErr)
            if genericErr.status_code == 400:
                if genericErr.message.__contains__(
                    "data source with that name already exists"
                ):
                    return ds_client.get_data_source_connection(name=datasource_name)
            raise (genericErr)
        
    def create_skillset(self):
        # TODO: implment this
        client = SearchIndexerClient(endpoint=self.config.endpoint, credential=self.azure_search_token)
        inp = InputFieldMappingEntry(name="text", source="/document/lastRenovationDate")
        output = OutputFieldMappingEntry(name="dateTimes", target_name="RenovatedDate")
        s = EntityRecognitionSkill(name="merge-skill", inputs=[inp], outputs=[output])
        skillset = SearchIndexerSkillset(name="hotel-data-skill", skills=[s], description="example skillset")
        result = client.create_skillset(skillset)
        return result

    def create_indexer(
        self, sharepointsite_name: str, datasource_name: str, target_index_name: str
    ) -> SearchIndexer:
        indexer_name = f"{sharepointsite_name}-indexer"
        configuration = IndexingParametersConfiguration(
            indexed_file_name_extensions=".pdf, .docx", query_timeout=None
        )
        parameters = IndexingParameters(configuration=configuration)
        field_maps = [
            FieldMapping(
                source_field_name="metadata_spo_site_library_item_id",
                target_field_name="id",
                mapping_function=FieldMappingFunction(name="base64Encode"),
            )
        ]
        indexer = SearchIndexer(
            name=indexer_name,
            data_source_name=datasource_name,
            target_index_name=target_index_name,
            # skillset_name=skillset_name,  # TODO: implment this mother fucker
            parameters=parameters,
            field_mappings=field_maps,
        )
        try:
            indexer_client = SearchIndexerClient(
                endpoint=self.config.endpoint, credential=self.credential
            )
            indexer_client.create_indexer(indexer)  # create the indexer
        except HttpResponseError as genericErr:
            print(genericErr)
            if genericErr.status_code == 400:
                if genericErr.message.__contains__(
                    "indexer with that name already exists"
                ):
                    return indexer_client.get_indexer(name=indexer_name)
            raise (genericErr)

    def create_indexer_flow(self, sharepointsite_name: str):
        self.create_index()
        datasource = self.create_datasource(
            sharepointsite_name=sharepointsite_name,
            domain_name=self.config.sharepoint_domain,
        )
        indexer = self.create_indexer(
            sharepointsite_name=sharepointsite_name,
            datasource_name=datasource.name,
            target_index_name=self.config.index_name,
        )
        return indexer


if __name__ == "__main__":
    import sys
    from dotenv import load_dotenv
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    load_dotenv()
    SHAREPOINT_APP_ID = os.getenv("SHAREPOINT_APP_ID")
    SHAREPOINT_APP_SEC = os.getenv("SHAREPOINT_APP_SEC")
    SHAREPOINT_TENANT_ID = os.getenv("SHAREPOINT_TENANT_ID")
    SHAREPOINT_DOMAIN = os.getenv("SHAREPOINT_DOMAIN")
    AZURE_SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
    AZURE_SEARCH_INDEX = os.getenv("AZURE_SEARCH_INDEX")

    cog_search_config = CognitveSearchConfig(
        endpoint=AZURE_SEARCH_ENDPOINT,
        index_name=AZURE_SEARCH_INDEX,
        sharepoint_appid=SHAREPOINT_APP_ID,
        sharepoint_appsec=SHAREPOINT_APP_SEC,
        sharepoint_apptenantid=SHAREPOINT_TENANT_ID,
        sharepoint_domain=SHAREPOINT_DOMAIN,
    )

    cog_search = CognitiveSearch(config=cog_search_config)
    result = cog_search.create_indexer_flow(sharepointsite_name="test-site")
