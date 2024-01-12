from time import sleep

from azure.core.exceptions import HttpResponseError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexerClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchFieldDataType,
    InputFieldMappingEntry,
    SearchIndexerSkillset,
    SearchIndexer,
    SearchableField,
    SearchIndexerDataSourceConnection
)

from src.SearchHandler import SearchHandler
from src.model.common import SharepointSite
from src.model.config import SharepointSearchConfig, SearchConfig


class SharepointSearchHandler(SearchHandler):
    def __init__(self, config: SharepointSearchConfig) -> None:
        search_config = SearchConfig(
            Endpoint=config.Endpoint,
            IndexName=config.IndexName,
            AoaiEndpoint=config.AoaiEndpoint,
            AoaiKey=config.AoaiKey,
            AoaiEmbedDeployment=config.AoaiEmbedDeployment
        )
        super().__init__(search_config)
        self.config = config

    def create_spo_index(self) -> SearchIndex:
        fields = [
            SearchableField(name="metadata_spo_site_id", type=SearchFieldDataType.String, filterable=True),
        ]
        return self.create_index(fields)

    def create_spo_datasource(self, spo_name: str, domain: str) -> SearchIndexerDataSourceConnection:
        container_name = "allSiteLibraries"
        conn_str = f"SharePointOnlineEndpoint=https://{domain}.sharepoint.com/sites/{spo_name}/;ApplicationId={self.config.SharepointClientId};ApplicationSecret={self.config.SharepointClientSecret};TenantId={self.config.SharepointTenantId}"
        ds_type = "sharepoint"
        return self.create_datasource(ds_name=spo_name, container_name=container_name, conn_str=conn_str,
                                      ds_type=ds_type)

    def create_spo_skillset(self) -> SearchIndexerSkillset:
        projection_mapping = [
            InputFieldMappingEntry(name="title", source="/document/metadata_spo_item_name"),
            InputFieldMappingEntry(name="metadata_spo_site_id", source="/document/metadata_spo_site_id"),
            InputFieldMappingEntry(name="location", source="/document/metadata_spo_item_weburi")
        ]
        return self.create_skillset(projection_mapping)

    def create_indexer_flow(self, spo_name: str) -> SearchIndexer:
        index = self.create_spo_index()
        datasource = self.create_spo_datasource(spo_name, self.config.SharepointDomain)
        skillset = self.create_spo_skillset()
        indexer_name = datasource.name.lower().removesuffix("-datasource")
        return self.create_indexer(indexer_name,datasource.name, skillset.name)

    def delete_indexer_and_stuff(self, sharepointsite: SharepointSite):
        indexer_name = f"{sharepointsite.name.lower()}-indexer"
        datasource_name = f"{sharepointsite.name.lower()}-sharepoint-datasource"
        indexer_client = SearchIndexerClient(endpoint=self.config.Endpoint, credential=self.credential)
        search_client = SearchClient(endpoint=self.config.Endpoint, credential=self.credential,
                                     index_name=self.config.IndexName)
        try:
            indexer_client.delete_data_source_connection(datasource_name)
            indexer_client.delete_indexer(indexer_name)
            index_filter = f"metadata_spo_site_id eq '{sharepointsite.id}'"
            while True:
                r = search_client.search("", filter=index_filter, top=1000, include_total_count=True)
                if r.get_count() == 0:
                    break
                r = search_client.delete_documents(documents=[{"id": d["id"]} for d in r])
                sleep(5)
        except HttpResponseError as genericErr:
            raise genericErr
