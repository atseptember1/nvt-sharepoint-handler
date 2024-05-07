from datetime import timedelta

from azure.core.exceptions import HttpResponseError
from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexerClient, SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndexerDataContainer, SearchIndex, SimpleField,
    SearchFieldDataType, InputFieldMappingEntry, OutputFieldMappingEntry,
    SearchIndexerSkillset, SearchIndexer, SearchableField, SearchField,
    IndexingParameters, SearchIndexerDataSourceConnection,
    IndexingParametersConfiguration,
    AzureOpenAIEmbeddingSkill, SplitSkill, TextSplitMode,
    VectorSearch, HnswVectorSearchAlgorithmConfiguration, HnswParameters,
    AzureOpenAIVectorizer, AzureOpenAIParameters, IndexingSchedule,
    ExhaustiveKnnVectorSearchAlgorithmConfiguration, ExhaustiveKnnParameters,
    VectorSearchAlgorithmKind, VectorSearchProfile, VectorSearchVectorizerKind,
    SemanticConfiguration, SemanticField, SemanticSettings, PrioritizedFields,
    SearchIndexerIndexProjections, SearchIndexerIndexProjectionSelector,
    SearchIndexerIndexProjectionsParameters, IndexProjectionMode
)

from src.AzureAuthentication import AzureAuthenticate
from src.model.common import IndexerProp, IndexerList
from src.model.config import SearchConfig


class SearchHandler(AzureAuthenticate):
    """
    The `SearchHandler` class is responsible for creating and managing search indexes, 
    data source connections, and skillsets in Azure Cognitive Search. 
    It extends the `AzureAuthenticate` class for authentication purposes.

    Example Usage:
        config = SearchConfig(...)
        search_handler = SearchHandler(config)
        add_fields = [SearchField(name="custom_field", type=SearchFieldDataType.String)]
        result = search_handler.create_index(add_fields)
        print(result)

    Methods: - create_index(add_fields: list[SearchField] = None) -> SearchIndex: Creates a search index in Azure
    Cognitive Search with default and additional fields. - create_datasource(ds_name: str, container_name: str,
    ds_type: str, conn_str: str = None, identity: DefaultAzureCredential = None) ->
    SearchIndexerDataSourceConnection: Creates a data source connection for Azure Cognitive Search. -
    create_skillset(add_projection_mapping: list[InputFieldMappingEntry]) -> SearchIndexerSkillset: Creates a
    skillset with split and embedding skills for document processing.

    Fields: - config: An instance of the `SearchConfig` class that holds the configuration settings for Azure
    Cognitive Search. - openai_acess_token: The access token for the OpenAI service. - credential: The Azure
    credential for authentication.
    """

    def __init__(self, config: SearchConfig) -> None:
        super().__init__()
        self.config = config

    def create_index(self, add_fields: list[SearchField] = None) -> SearchIndex:
        """
        Creates a search index in Azure Cognitive Search.

        Args:
            add_fields (list[SearchField], optional): A list of additional fields to be added to the search index.
            Defaults to None.

        Returns:
            SearchIndex: The created search index.

        Example Usage:
            config = SearchConfig(...)
            search_handler = SearchHandler(config)
            add_fields = [SearchField(name="custom_field", type=SearchFieldDataType.String)]
            result = search_handler.create_index(add_fields)
            print(result)

        Code Analysis: - Initializes a list of default fields for the search index. - If additional fields are
        provided, they are appended to the default fields list. - Creates a VectorSearch object with two vector
        search algorithms, profiles, and an Azure OpenAI vectorizer. - Creates a SemanticConfiguration object with a
        prioritized field for chunk. - Creates a SemanticSettings object with the semantic configuration. - Creates a
        SearchIndex object with the specified name, default fields, vector search, and semantic settings. - Creates a
        SearchIndexClient object and calls the create_or_update_index method to create the search index. - Returns
        the created search index.
        """
        default_fields = [
            SearchField(name="parent_id",
                        type=SearchFieldDataType.String,
                        sortable=True,
                        filterable=True,
                        facetable=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
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
        if add_fields:
            default_fields = default_fields + add_fields

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
                        resource_uri=self.config.AoaiEndpoint,
                        deployment_id=self.config.AoaiEmbedDeployment,
                        api_key=self.config.AoaiKey,
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
                    ]
                ),
            )
        ]

        semantic_settings = SemanticSettings(configurations=semantic_config)
        index_client = SearchIndexClient(endpoint=self.config.Endpoint, credential=self.credential)
        try:
            index = SearchIndex(
                name=self.config.IndexName,
                fields=default_fields,
                vector_search=vector_search,
                semantic_settings=semantic_settings,
            )
            result = index_client.create_or_update_index(index)
            return result
        except HttpResponseError as generic_err:
            print(generic_err.message)
            if generic_err.message.__contains__("Existing field(s)"):
                return index_client.get_index(self.config.IndexName)
            raise generic_err

    def create_datasource(self, ds_name: str, container_name: str, ds_type: str,
                          conn_str: str = None,
                          identity: DefaultAzureCredential = None) -> SearchIndexerDataSourceConnection:
        """
        Creates a data source connection for Azure Cognitive Search.

        Args:
            ds_name (str): The name of the data source.
            container_name (str): The name of the container within the data source.
            ds_type (str): The type of the data source.
            conn_str (str, optional): The connection string for the data source. Defaults to None.
            identity (DefaultAzureCredential, optional): The identity for the data source. Defaults to None.

        Returns:
            SearchIndexerDataSourceConnection: The created data source connection.

        Raises:
            ValueError: If neither conn_str nor identity is provided.

        Example Usage:
            config = SearchConfig(...)
            search_handler = SearchHandler(config)
            ds_name = "my_datasource"
            container_name = "my_container"
            ds_type = "my_type"
            conn_str = "my_connection_string"
            result = search_handler.create_datasource(ds_name, container_name, ds_type, conn_str)
            print(result)
        """
        datasource_name = f"{ds_name.lower()}-{ds_type}-datasource"
        container = SearchIndexerDataContainer(name=container_name, query=None)
        if conn_str is not None:
            data_source_connection = SearchIndexerDataSourceConnection(
                name=datasource_name,
                type=ds_type,
                connection_string=conn_str,
                container=container,
            )
        elif identity is not None:
            data_source_connection = SearchIndexerDataSourceConnection(
                name=datasource_name,
                type=ds_type,
                connection_string=conn_str,
                identity=identity,
                container=container
            )
        else:
            raise ValueError("Please provide either a conn_str or identity")
        ds_client = SearchIndexerClient(endpoint=self.config.Endpoint, credential=self.credential)
        if ds_type == "azureblob":
            data_source_connection.data_change_detection_policy = {
               "@odata.type": "#Microsoft.Azure.Search.SoftDeleteColumnDeletionDetectionPolicy",
                    "softDeleteColumnName": "IsDeleted",
                    "softDeleteMarkerValue": "true"
            }
        try:
            data_source = ds_client.create_data_source_connection(data_source_connection)
            return data_source
        except HttpResponseError as genericErr:
            print(genericErr)
            if genericErr.status_code == 400:
                if genericErr.message.__contains__("data source with that name already exists"):
                    return ds_client.get_data_source_connection(datasource_name)
            raise genericErr

    def create_skillset(self, add_projection_mapping: list[InputFieldMappingEntry]) -> SearchIndexerSkillset:
        """
        Creates a search indexer skillset with two skills: a split skill and an Azure OpenAI embedding skill.

        Args: add_projection_mapping (list[InputFieldMappingEntry]): A list of InputFieldMappingEntry objects that
        define the input field mappings for the skillset.

        Returns:
            SearchIndexerSkillset: The created skillset object.
        """

        # Split text into chunk skill
        split_skill = SplitSkill(
            description="Split skill to chunk documents",
            text_split_mode=TextSplitMode.PAGES,
            context="/document",
            maximum_page_length=3000,
            page_overlap_length=40,
            inputs=[
                InputFieldMappingEntry(name="text", source="/document/content"),
            ],
            outputs=[
                OutputFieldMappingEntry(name="textItems", target_name="pages")
            ],
        )

        # Azure OpenAI embedding skill for generating vector
        embedding_skill = AzureOpenAIEmbeddingSkill(
            description="Skill to generate embeddings via Azure OpenAI",
            context="/document/pages/*",
            resource_uri=self.config.AoaiEndpoint,
            deployment_id=self.config.AoaiEmbedDeployment,
            api_key=self.config.AoaiKey,
            inputs=[
                InputFieldMappingEntry(name="text", source="/document/pages/*"),
            ],
            outputs=[
                OutputFieldMappingEntry(name="embedding", target_name="vector")
            ],
        )

        # Field mapping for additional metdata ex: file location for reference, file name,...
        default_projection_mapping = [
            InputFieldMappingEntry(name="chunk", source="/document/pages/*"),
            InputFieldMappingEntry(name="chunkVector", source="/document/pages/*/vector"),
        ]
        if not add_projection_mapping:
            raise ValueError("No projection")  # because we are missing required fields (location,...)
        else:
            default_projection_mapping = default_projection_mapping + add_projection_mapping

        # Project all the skill results to index fields
        index_projections = SearchIndexerIndexProjections(
            selectors=[
                SearchIndexerIndexProjectionSelector(
                    target_index_name=self.config.IndexName,
                    parent_key_field_name="parent_id",
                    source_context="/document/pages/*",
                    mappings=default_projection_mapping
                ),
            ],
            parameters=SearchIndexerIndexProjectionsParameters(
                projection_mode=IndexProjectionMode.SKIP_INDEXING_PARENT_DOCUMENTS),
        )

        skillset_name = f"{self.config.IndexName}-skillset"
        skillset = SearchIndexerSkillset(
            name=skillset_name,
            description="Skillset to chunk documents and generating embeddings",
            skills=[split_skill, embedding_skill],
            index_projections=index_projections)
        client = SearchIndexerClient(endpoint=self.config.Endpoint, credential=self.credential)
        try:
            result = client.create_or_update_skillset(skillset)
            return result
        except HttpResponseError as generic_err:
            print(generic_err)
            if generic_err.status_code == 400:
                if generic_err.message.__contains__("skillset with that name already exists"):
                    return client.get_skillset(skillset_name)
            raise generic_err

    def create_indexer(self, indexer_name: str, ds_name: str,  skillset_name: str) -> SearchIndexer:
        """
        Creates a search indexer in Azure Cognitive Search with the specified data source, skillset, and indexing
        parameters.

        Args:
            indexer_name (str): The name of the indexer.
            ds_name (str): The name of the data source
            skillset_name (str): The name of the skillset.

        Returns:
            SearchIndexer: The created or updated search indexer.
        """
        indexer_name = f"{indexer_name.lower()}-indexer"
        configuration = IndexingParametersConfiguration(indexed_file_name_extensions=".pdf, .docx, .doc, .xlsx, .xls",
                                                        query_timeout=None)
        parameters = IndexingParameters(configuration=configuration)
        indexer = SearchIndexer(
            name=indexer_name,
            data_source_name=ds_name,
            target_index_name=self.config.IndexName,
            skillset_name=skillset_name,
            parameters=parameters,
            schedule=IndexingSchedule(interval=timedelta(minutes=5)),
        )
        indexer_client = SearchIndexerClient(endpoint=self.config.Endpoint, credential=self.credential)
        try:
            result = indexer_client.create_indexer(indexer)
            return result
        except HttpResponseError as genericErr:
            print(genericErr)
            if genericErr.status_code == 400:
                if genericErr.message.__contains__("indexer with that name already exists"):
                    return indexer_client.get_indexer(indexer_name)
            raise genericErr

    def list_indexer(self, ds_type: str = None) -> IndexerList:
        """
        Retrieves a list of indexers from Azure Cognitive Search.

        Returns:
            IndexerList: A list of IndexerProp objects containing information about each indexer.

        Example Usage:
            config = SearchConfig(...)
            search_handler = SearchHandler(config)
            result = search_handler.list_indexer()
            print(result)

        Output: IndexerList(value=[ IndexerProp(Name="indexer1", DataSourceName="datasource1",
        SkillSetName="skillset1", IndexName="index1"), IndexerProp(Name="indexer2", DataSourceName="datasource2",
        SkillSetName="skillset2", IndexName="index2"), ] )

        Raises:
            HttpResponseError: If an error occurs while retrieving the indexers.
        """
        indexer_client = SearchIndexerClient(endpoint=self.config.Endpoint, credential=self.credential)
        try:
            indexers = indexer_client.get_indexers()
            indexers_prop_list = []
            for indexer in indexers:
                if ds_type:
                    if ds_type not in indexer.data_source_name:
                        continue
                indexer_prop = IndexerProp(
                    Name=indexer.name,
                    DataSourceName=indexer.data_source_name,
                    SkillSetName=indexer.skillset_name,
                    IndexName=indexer.target_index_name)
                indexers_prop_list.append(indexer_prop)
            return IndexerList(Value=indexers_prop_list)
        except HttpResponseError as genericErr:
            raise genericErr
