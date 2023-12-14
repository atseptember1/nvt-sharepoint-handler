import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from time import sleep
from datetime import timedelta
from AzureAuthentication import AzureAuthenticate
from model.input import CognitveSearchConfig
from model.common import SharepointSite, IndexerProp, IndexerList
from azure.core.exceptions import HttpResponseError
from azure.search.documents.indexes import SearchIndexerClient, SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndexerDataContainer, SearchIndex, SearchIndexer, SimpleField,
    SearchFieldDataType, InputFieldMappingEntry, OutputFieldMappingEntry,
    SearchIndexerSkillset, SearchIndexer, SearchableField, SearchField,
    IndexingParameters, SearchIndexerDataSourceConnection,
    IndexingParametersConfiguration, FieldMapping, FieldMappingFunction,
    AzureOpenAIEmbeddingSkill, SplitSkill, WebApiSkill, TextSplitMode,
    VectorSearch, HnswVectorSearchAlgorithmConfiguration, HnswParameters,
    AzureOpenAIVectorizer, AzureOpenAIParameters, IndexingSchedule,
    ExhaustiveKnnVectorSearchAlgorithmConfiguration, ExhaustiveKnnParameters,
    VectorSearchAlgorithmKind, VectorSearchProfile, VectorSearchVectorizerKind,
    SemanticConfiguration, SemanticField, SemanticSettings, PrioritizedFields,
    SearchIndexerIndexProjections, SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjectionsParameters, IndexProjectionMode)
from azure.search.documents import SearchClient


class CognitiveSearch(AzureAuthenticate):

    def __init__(self, config: CognitveSearchConfig) -> None:
        super().__init__()
        self.config = config

    def create_index(self) -> SearchIndex:
        fields = [
            SearchField(name="parent_id",
                        type=SearchFieldDataType.String,
                        sortable=True,
                        filterable=True,
                        facetable=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="metadata_spo_site_id",
                            type=SearchFieldDataType.String,
                            filterable=True),
            SimpleField(name="location", type=SearchFieldDataType.String),
            SearchField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                sortable=True,
                filterable=True,
                facetable=True,
                analyzer_name="keyword",
            ),
            SearchableField(name="chunk", type=SearchFieldDataType.String),
            SearchField(name="chunkVector",
                        type=SearchFieldDataType.Collection(
                            SearchFieldDataType.Single),
                        vector_search_dimensions=1536,
                        vector_search_profile="myHnswProfile")
        ]
        vector_search = VectorSearch(
            algorithms=[
                HnswVectorSearchAlgorithmConfiguration(
                    name="myHnsw",
                    kind=VectorSearchAlgorithmKind.HNSW,
                    parameters=HnswParameters(
                        m=4,
                        ef_construction=400,
                        ef_search=500,
                        metric="cosine",
                    ),
                ),
                ExhaustiveKnnVectorSearchAlgorithmConfiguration(
                    name="myExhaustiveKnn",
                    kind=VectorSearchAlgorithmKind.EXHAUSTIVE_KNN,
                    parameters=ExhaustiveKnnParameters(metric="cosine"),
                ),
            ],
            profiles=[
                VectorSearchProfile(
                    name="myHnswProfile",
                    algorithm="myHnsw",
                    vectorizer="myOpenAI",
                ),
                VectorSearchProfile(
                    name="myExhaustiveKnnProfile",
                    algorithm="myExhaustiveKnn",
                    vectorizer="myOpenAI",
                ),
            ],
            vectorizers=[
                AzureOpenAIVectorizer(
                    name="myOpenAI",
                    kind=VectorSearchVectorizerKind.AZURE_OPEN_AI,
                    azure_open_ai_parameters=AzureOpenAIParameters(
                        resource_uri=self.config.aoai_endpoint,
                        deployment_id=self.config.aoai_embed_deployment,
                        api_key=self.config.aoai_key,
                    ),
                ),
            ],
        )

        semantic_config = [
            SemanticConfiguration(
                name="my-semantic-config",
                prioritized_fields=PrioritizedFields(
                    prioritized_content_fields=[
                        SemanticField(field_name="chunk")
                    ]),
            )
        ]

        # Create the semantic settings with the configuration
        semantic_settings = SemanticSettings(configurations=semantic_config)

        try:
            index = SearchIndex(
                name=self.config.index_name,
                fields=fields,
                vector_search=vector_search,
                semantic_settings=semantic_settings,
            )
            index_client = SearchIndexClient(endpoint=self.config.endpoint,
                                             credential=self.credential)
            result = index_client.create_or_update_index(index=index)
            return result
        except Exception as generic_err:
            print(generic_err)
            raise (generic_err)

    def create_datasource(
            self, sharepointsite_name: str,
            domain_name: str) -> SearchIndexerDataSourceConnection:
        container_name = "allSiteLibraries"
        datasource_name = f"{sharepointsite_name}-datasource"
        connection_string = f"SharePointOnlineEndpoint=https://{domain_name}.sharepoint.com/sites/{sharepointsite_name}/;ApplicationId={self.config.sharepoint_appid};ApplicationSecret={self.config.sharepoint_appsec};TenantId={self.config.sharepoint_apptenantid}"
        try:
            ds_client = SearchIndexerClient(endpoint=self.config.endpoint,
                                            credential=self.credential)
            container = SearchIndexerDataContainer(name=container_name)
            data_source_connection = SearchIndexerDataSourceConnection(
                name=datasource_name,
                type="sharepoint",
                connection_string=connection_string,
                container=container,
            )
            data_source = ds_client.create_data_source_connection(
                data_source_connection)
            return data_source
        except HttpResponseError as genericErr:
            print(genericErr)
            if genericErr.status_code == 400:
                if genericErr.message.__contains__(
                        "data source with that name already exists"):
                    return ds_client.get_data_source_connection(
                        name=datasource_name)
            raise (genericErr)

    def create_skillset(self, index_name: str):
        # Split text into chunk skill
        split_skill = SplitSkill(
            description="Split skill to chunk documents",
            text_split_mode=TextSplitMode.PAGES,
            context="/document",
            maximum_page_length=5000,
            page_overlap_length=40,
            inputs=[
                InputFieldMappingEntry(name="text",
                                       source="/document/content"),
            ],
            outputs=[
                OutputFieldMappingEntry(name="textItems", target_name="pages")
            ],
        )

        # # Generate summarize from chunk with WebApiSkill using local api
        # generate_summarize_skill = WebApiSkill(  # TODO: implement this
        #     description=
        #     "skill to call web api for generate summarize using OpenAI",
        #     uri=
        #     "<uri>",
        #     http_method="POST",
        #     batch_size=10,
        #     context="/document/pages/*",
        #     inputs=[
        #         InputFieldMappingEntry(name="text",
        #                                source="/document/pages/*"),
        #     ],
        #     outputs=[
        #         OutputFieldMappingEntry(name="result",
        #                                 target_name="webApiResult"),
        #     ])

        # # Azure OpenAI embedding skill for generating vector
        embedding_skill = AzureOpenAIEmbeddingSkill(
            description="Skill to generate embeddings via Azure OpenAI",
            context="/document/pages/*",
            resource_uri=self.config.aoai_endpoint,
            deployment_id=self.config.aoai_embed_deployment,
            api_key=self.config.aoai_key,
            inputs=[
                InputFieldMappingEntry(name="text",
                                       source="/document/pages/*"),
            ],
            outputs=[
                OutputFieldMappingEntry(name="embedding",
                                        target_name="vector")
            ],
        )

        # Project all the skill results to index fields
        index_projections = SearchIndexerIndexProjections(
            selectors=[
                SearchIndexerIndexProjectionSelector(
                    target_index_name=index_name,
                    parent_key_field_name="parent_id",
                    source_context="/document/pages/*",
                    mappings=[
                        InputFieldMappingEntry(name="chunk",
                                               source="/document/pages/*"),
                        InputFieldMappingEntry(
                            name="chunkVector",
                            source="/document/pages/*/vector"),
                        InputFieldMappingEntry(
                            name="title",
                            source="/document/metadata_spo_item_name"),
                        InputFieldMappingEntry(
                            name="metadata_spo_site_id",
                            source="/document/metadata_spo_site_id"),
                        InputFieldMappingEntry(
                            name="location",
                            source="/document/metadata_spo_item_weburi")
                    ],
                ),
            ],
            parameters=SearchIndexerIndexProjectionsParameters(
                projection_mode=IndexProjectionMode.
                SKIP_INDEXING_PARENT_DOCUMENTS),
        )

        skillset_name = f"{self.config.index_name}-skillset"
        skillset = SearchIndexerSkillset(
            name=skillset_name,
            description="Skillset to chunk documents and generating embeddings",
            skills=[split_skill, embedding_skill],
            index_projections=index_projections)

        client = SearchIndexerClient(endpoint=self.config.endpoint,
                                     credential=self.credential)
        try:
            result = client.create_or_update_skillset(skillset=skillset)
            return result
        except HttpResponseError as generic_err:
            print(generic_err)
            if generic_err.status_code == 400:
                if generic_err.message.__contains__(
                        "skillset with that name already exists"):
                    return client.get_skillset(name=skillset_name)
            raise generic_err

    def create_indexer(self, sharepointsite_name: str, datasource_name: str,
                       target_index_name: str,
                       skillset_name: str) -> SearchIndexer:
        indexer_name = f"{sharepointsite_name}-indexer"
        configuration = IndexingParametersConfiguration(
            indexed_file_name_extensions=".pdf, .docx", query_timeout=None)
        parameters = IndexingParameters(configuration=configuration)
        indexer = SearchIndexer(
            name=indexer_name,
            data_source_name=datasource_name,
            target_index_name=target_index_name,
            skillset_name=skillset_name,  # TODO: implment this mother fucker
            parameters=parameters,
            # field_mappings=field_maps,
            schedule=IndexingSchedule(interval=timedelta(minutes=5)),
        )
        try:
            indexer_client = SearchIndexerClient(endpoint=self.config.endpoint,
                                                 credential=self.credential)
            result = indexer_client.create_or_update_indexer(indexer)
            return result
        except HttpResponseError as genericErr:
            print(genericErr)
            if genericErr.status_code == 400:
                if genericErr.message.__contains__(
                        "indexer with that name already exists"):
                    return indexer_client.get_indexer(name=indexer_name)
            raise (genericErr)

    def create_indexer_flow(self, sharepointsite_name: str) -> SearchIndexer:
        # create index
        index = self.create_index()
        # create data source
        datasource = self.create_datasource(
            sharepointsite_name=sharepointsite_name,
            domain_name=self.config.sharepoint_domain,
        )
        # create skillset
        skillset = self.create_skillset(index_name=index.name)
        # create indexer
        indexer = self.create_indexer(sharepointsite_name=sharepointsite_name,
                                      datasource_name=datasource.name,
                                      target_index_name=self.config.index_name,
                                      skillset_name=skillset.name)
        return indexer

    def delete_indexer_and_stuff(self, sharepointsite: SharepointSite):
        indexer_client = SearchIndexerClient(endpoint=self.config.endpoint,
                                             credential=self.credential)
        search_client = SearchClient(endpoint=self.config.endpoint,
                                     credential=self.credential,
                                     index_name=self.config.index_name)
        indexer_name = f"{sharepointsite.name.lower()}-indexer"
        datasource_name = f"{sharepointsite.name.lower()}-datasource"
        try:
            indexer_client.delete_data_source_connection(
                data_source_connection=datasource_name)
            indexer_client.delete_indexer(indexer=indexer_name)
            filter = f"metadata_spo_site_id eq '{sharepointsite.id}'"
            while True:
                r = search_client.search("",
                                         filter=filter,
                                         top=1000,
                                         include_total_count=True)
                if r.get_count() == 0:
                    break
                r = search_client.delete_documents(documents=[{
                    "id": d["id"]
                } for d in r])
                sleep(5)
        except HttpResponseError as genericErr:
            raise genericErr

    def list_indexer(self) -> IndexerList:
        indexer_client = SearchIndexerClient(endpoint=self.config.endpoint,
                                             credential=self.credential)
        try:
            indexers = indexer_client.get_indexers()
            indexers_prop_list = []
            for indexer in indexers:
                indexer_prop = IndexerProp(
                    name=indexer.name,
                    DataSourceName=indexer.data_source_name,
                    SkillSetName=indexer.skillset_name,
                    IndexName=indexer.target_index_name)
                indexers_prop_list.append(indexer_prop)
            result = IndexerList(value=indexers_prop_list)
            return result
        except HttpResponseError as genericErr:
            raise genericErr
