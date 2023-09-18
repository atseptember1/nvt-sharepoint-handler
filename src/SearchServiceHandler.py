import os
import openai
import logging
from time import sleep
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes.models import (
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    SearchIndex,
    SemanticConfiguration,
    PrioritizedFields,
    SemanticField,
    SearchField,
    SemanticSettings,
    VectorSearch,
    HnswVectorSearchAlgorithmConfiguration
)
from tenacity import retry, wait_random_exponential, stop_after_attempt


class SearchService:
    def __init__(self, search_svc_endpoint: str, search_svc_key: str, search_index_name: str) -> None:
        self.endpoint = search_svc_endpoint
        self.key = search_svc_key
        self.index_name = search_index_name
        self._init_index_client(endpoint=self.endpoint, key=self.key)
        self._init_search_client(endpoint=search_svc_endpoint,index_name=self.index_name, key=search_svc_key)

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def _init_index_client(self, endpoint: str, key: str):
        try:
            self.index_client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key))
        except Exception as err:
            raise(err)
    
    def _init_search_client(self, endpoint: str, index_name: str, key: str):
        try:
            self.search_client = SearchClient(endpoint=endpoint,
                                        index_name=index_name,
                                        credential=AzureKeyCredential(key=key))
        except Exception as err:
            raise(err)

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def _create_search_index(self, index_name: str) -> bool:
        status = False
        if index_name not in self.index_client.list_index_names():
            index = SearchIndex(
                name=index_name,
                fields=[
                    SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                    SearchableField(name="content", type=SearchFieldDataType.String, searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                    SearchField(name="contentVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, dimensions=1536, vector_search_configuration="vectorConfig"),
                    SearchableField(name="questions", type=SearchFieldDataType.String, searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                    SearchField(name="questionsVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, dimensions=1536, vector_search_configuration="vectorConfig"),
                    SearchableField(name="summary", type=SearchFieldDataType.String, searchable=True, retrievable=True, analyzer_name="en.microsoft"),
                    SearchField(name="summaryVector", type=SearchFieldDataType.Collection(SearchFieldDataType.Single), searchable=True, dimensions=1536, vector_search_configuration="vectorConfig"),
                    SimpleField(name="sourcefile", type="Edm.String", filterable=True, facetable=True, SearchableField=True),
                ],
                vector_search=VectorSearch(
                    algorithm_configurations=[HnswVectorSearchAlgorithmConfiguration(name="vectorConfig", kind="hnsw")]),
                    semantic_settings = SemanticSettings(
                        configurations=[SemanticConfiguration(
                            name='semanticConfig',
                            prioritized_fields=PrioritizedFields(
                                title_field=None, prioritized_content_fields=[SemanticField(field_name='content')]))])
                )
            try:
                self.index_client.create_index(index)
                status = True
            except Exception as err:
                raise(err)
        else:
            status = True
            print(f"Search index {index_name} already exists")
        return status

    def index_sections(self, sections: list[dict]) -> bool:
        self._create_search_index(self.index_name)
        status = False
        try:
            i = 0
            batch = []
            for s in sections:
                batch.append(s)
                i += 1
                if i % 1000 == 0:
                    results = self.search_client.index_documents(batch=batch)
                    succeeded = sum([1 for r in results if r.succeeded])
                    print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
                    batch = []
                    status = True
            if len(batch) > 0:
                results = self.search_client.upload_documents(documents=batch)
                succeeded = sum([1 for r in results if r.succeeded])
                print(f"\tIndexed {len(results)} sections, {succeeded} succeeded")
                status = True
            print('Indexed sections succeeded')
        except Exception as err:
            raise(err)
        return status
