import os
import openai
import logging
from time import sleep
from pathlib import Path
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents import SearchClient
from azure.identity import DefaultAzureCredential
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
    HnswVectorSearchAlgorithmConfiguration,
    ScoringProfile,
    TextWeights,
    FreshnessScoringFunction,
    FreshnessScoringParameters,
    HnswParameters,
    VectorSearchProfile,
)
from tenacity import retry, wait_random_exponential, stop_after_attempt
from pydantic import BaseModel
from langchain.vectorstores.azuresearch import AzureSearch
from OpenAIHandler import OpenAI


class SearchServiceConfig(BaseModel):
    endpoint: str
    credential: DefaultAzureCredential
    index_name: str

    class Config:
        arbitrary_types_allowed = True


class SearchService:
    def __init__(self, config: SearchServiceConfig) -> None:
        self.config = config
        self._init_index_client(
            endpoint=self.config.endpoint, credential=self.config.credential
        )
        self._init_search_client(
            endpoint=self.config.endpoint,
            index_name=self.config.index_name,
            credential=self.config.credential,
        )

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def _init_index_client(self, endpoint: str, credential: DefaultAzureCredential):
        try:
            self.index_client = SearchIndexClient(
                endpoint=endpoint, credential=credential
            )
        except Exception as err:
            raise (err)

    def _init_search_client(
        self, endpoint: str, index_name: str, credential: DefaultAzureCredential
    ):
        try:
            self.search_client = SearchClient(
                endpoint=endpoint, index_name=index_name, credential=credential
            )
        except Exception as err:
            raise (err)

    def _create_search_index(self) -> bool:
        status = False
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True,
                retrievable=True,
            ),
            SearchField(
                name="contentVector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile="default",
            ),
            SearchableField(
                name="questions",
                type=SearchFieldDataType.String,
                searchable=True,
                retrievable=True,
            ),
            SearchField(
                name="questionsVector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile="default",
            ),
            SearchableField(
                name="summary",
                type=SearchFieldDataType.String,
                searchable=True,
                retrievable=True,
            ),
            SearchField(
                name="summaryVector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile="default",
            ),
            SimpleField(
                name="sourcefile",
                type="Edm.String",
                filterable=True,
                facetable=True,
                SearchableField=True,
            ),
        ]

        vector_config = VectorSearch(
            algorithms=[
                HnswVectorSearchAlgorithmConfiguration(
                    name="algo",
                    kind="hnsw",
                    parameters=HnswParameters(metric="cosine")
                )
            ],
            profiles=[VectorSearchProfile(name="default", algorithm="algo")],
        )

        index = SearchIndex(
            name=self.config.index_name,
            fields=fields,
            vector_search=vector_config,
            # scoring_profiles=[sc]
        )
        try:
            self.index_client.create_or_update_index(index)
            status = True
        except Exception as err:
            raise (err)
        return status

    # @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def index_sections(self, sections: list[dict]) -> bool:
        self._create_search_index()
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
            print("Indexed sections succeeded")
        except Exception as err:
            raise (err)
        return status

    def create_sections(
        self, file_name: str, doc: list[str], openai: OpenAI
    ) -> list[dict]:
        section_list = []
        for counter, paragraph in enumerate(doc, start=1):
            questions = openai.generate_question(paragrpah=paragraph)
            summary = openai.summarize_text(paragrpah=paragraph)
            section = {
                "id": f"{file_name}-{counter}".replace(".", "_")
                .replace(" ", "_")
                .replace(":", "_")
                .replace("/", "_")
                .replace(",", "_")
                .replace("&", "_"),
                "content": paragraph,
                "contentVector": openai.embedding_word(texts=paragraph),
                "questions": questions,
                "questionsVector": openai.embedding_word(texts=questions),
                "summary": summary,
                "summaryVector": openai.embedding_word(texts=summary),
                "sourcefile": Path(file_name).name,
            }
            section_list.append(section)
        print(f"created section with len: f{len(section_list)}")
        print(f"section list: {section_list}")
        return section_list
