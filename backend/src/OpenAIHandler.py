import json
from langchain.chat_models import AzureChatOpenAI
from langchain.llms import AzureOpenAI
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.schema import BaseMessage
from tenacity import retry, wait_random_exponential, stop_after_attempt
from pydantic import BaseModel


class OpenAIConfig(BaseModel):
    endpoint: str
    key: str
    chat_deployment: str
    chat_model: str
    embed_deployment: str
    embed_model: str
    api_type: str = "azure"
    api_version: str = "2023-03-15-preview"


class OpenAI:
    def __init__(self, config: OpenAIConfig) -> None:
        self.config = config
        self.chat = self._init_chat_model()
        self.embed = self._init_embed_model()
        self.prompt_profiles = {
            "summarize": ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "You are a helpful AI assistant, intended to summarize the content for provided paragraph. {language}",
                    ),
                    ("human", "{paragrpah}"),
                ]
            ),
            "question_generate": ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        "Generate 10 questions that can be asked for paragrpah provided by the user. Write all the questions in one line. question in {language}",
                    ),
                    ("human", "{paragrpah}"),
                ]
            ),
        }

    def _init_chat_model(self) -> AzureChatOpenAI:
        try:
            chat = AzureChatOpenAI(
                azure_endpoint=self.config.endpoint,
                openai_api_key=self.config.key,
                openai_api_version=self.config.api_version,
                openai_api_type=self.config.api_type,
                deployment_name=self.config.chat_deployment,
                model=self.config.chat_model,
            )
        except Exception as err:
            raise (err)
        return chat

    def _init_embed_model(self) -> AzureOpenAIEmbeddings:
        try:
            embed = AzureOpenAIEmbeddings(
                azure_endpoint=self.config.endpoint,
                api_key=self.config.key,
                openai_api_type=self.config.api_type,
                openai_api_version=self.config.api_version,
                deployment=self.config.embed_deployment,
                model=self.config.embed_model,
            )
        except Exception as err:
            raise (err)
        return embed

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def _chat_request(self, prompt) -> str:
        try:
            return self.chat(prompt).content
        except Exception as err:
            raise (err)

    def summarize_text(self, paragrpah: str, language: str) -> str:
        try:
            summarize_prompt = self.prompt_profiles["summarize"].format_messages(
                paragrpah=paragrpah, language=language
            )
            response = self._chat_request(summarize_prompt)
        except Exception as err:
            raise (err)
        print(f"summarize_text: {response}")
        return response

    def generate_question(self, paragrpah: str, language: str) -> str:
        try:
            question_prompt = self.prompt_profiles["question_generate"].format_messages(
                paragrpah=paragrpah, language=language
            )
            response = self._chat_request(question_prompt)
        except Exception as err:
            raise (err)
        print(f"generated_question: {response}")
        return response

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def embedding_doc(self, document: list[str]) -> list[list[float]]:
        try:
            response = self.embed.embed_documents(texts=document)
        except Exception as err:
            raise (err)
        return response

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def embedding_word(self, texts: str) -> list[float]:
        try:
            response = self.embed.embed_query(text=texts)
        except Exception as err:
            raise (err)
        return response
