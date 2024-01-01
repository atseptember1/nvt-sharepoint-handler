from azure.search.documents.indexes.models import (
    SearchIndex,
    InputFieldMappingEntry,
    SearchIndexerSkillset,
    SearchIndexer,
    SearchIndexerDataSourceConnection
)

from src.SearchHandler import SearchHandler
from src.model.config import StorageSearchConfig, SearchConfig


class StorageSearchHandler(SearchHandler):
    def __init__(self, config: StorageSearchConfig) -> None:
        search_config = SearchConfig(
            Endpoint=config.Endpoint,
            IndexName=config.IndexName,
            AoaiEndpoint=config.AoaiEndpoint,
            AoaiKey=config.AoaiKey,
            AoaiEmbedDeployment=config.AoaiEmbedDeployment,
        )
        super().__init__(search_config)
        self.config = config

    def create_storage_index(self) -> SearchIndex:
        fields = []
        return self.create_index(fields)

    def create_storage_datasource(self) -> SearchIndexerDataSourceConnection:
        container_name = self.config.ContainerName
        ds_type = "azureblob"
        if self.config.StorageConnStr:
            return self.create_datasource(ds_name=self.config.StorageName.lower(), container_name=container_name,
                                          conn_str=self.config.StorageConnStr, ds_type=ds_type)
        else:
            return self.create_datasource(ds_name=self.config.StorageName, container_name=container_name,
                                          identity=self.credential, ds_type=ds_type)

    def create_storage_skillset(self) -> SearchIndexerSkillset:
        projection_mapping = [
            InputFieldMappingEntry(name="title", source="/document/metadata_storage_name"),
            InputFieldMappingEntry(name="location", source="/document/metadata_storage_path")
        ]
        return self.create_skillset(projection_mapping)

    def create_indexer_flow(self) -> SearchIndexer:
        index = self.create_storage_index()
        datasource = self.create_storage_datasource()
        skillset = self.create_storage_skillset()
        indexer_name = datasource.name.removesuffix("-datasource")
        return self.create_indexer(indexer_name, datasource.name, skillset.name)
