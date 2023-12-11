import json
from langchain.chat_models import AzureChatOpenAI
from langchain.llms import AzureOpenAI
from langchain.embeddings import AzureOpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.schema import BaseMessage, HumanMessage
from tenacity import retry, wait_random_exponential, stop_after_attempt
from pydantic import BaseModel
from AzureAuthentication import AzureAuthenticate
from model.input import OpenAIConfig


class OpenAI(AzureAuthenticate):

    def __init__(self, config: OpenAIConfig) -> None:
        super().__init__()
        self.config = config
        self._init_chat_model()
        self._init_embed_model()
        self.prompt_profiles = {
            "summarize":
            ChatPromptTemplate.from_messages([
                (
                    "system",
                    "You are a helpful AI assistant, intended to summarize the content for provided paragraph.",
                ),
                ("human", "{paragrpah}"),
            ]),
            "question_generate":
            ChatPromptTemplate.from_messages([
                (
                    "system",
                    "Generate 10 questions that can be asked for paragrpah provided by the user. Write all the questions in one line",
                ),
                ("human", "{paragrpah}"),
            ]),
            "keyword_generate":
            ChatPromptTemplate.from_messages([
                (
                    "system",
                    "Generate 10 keywords for the paragraph provided by the user, keyword must be seperated by semicolon",
                ),
                ("human", "{paragraph}"),
            ]),
        }

    def _init_chat_model(self) -> AzureChatOpenAI:
        try:
            if self.config.key == None:
                self.chat = AzureChatOpenAI(
                    azure_endpoint=self.config.endpoint,
                    openai_api_key=self.get_openai_token().token,
                    openai_api_version=self.config.api_version,
                    openai_api_type=self.config.api_type,
                    deployment_name=self.config.chat_deployment,
                    model=self.config.chat_model,
                )
            else:
                self.chat = AzureChatOpenAI(
                    azure_endpoint=self.config.endpoint,
                    openai_api_key=self.config.key,
                    openai_api_version=self.config.api_version,
                    openai_api_type=self.config.api_type,
                    deployment_name=self.config.chat_deployment,
                    model=self.config.chat_model,
                )
            return self.chat
        except Exception as err:
            print(err)
            raise (err)

    def _init_embed_model(self) -> AzureOpenAIEmbeddings:
        try:
            if self.config.key == None:
                 self.embed = AzureOpenAIEmbeddings(
                    azure_endpoint=self.config.endpoint,
                    api_key=self.get_openai_token().token,
                    openai_api_type=self.config.api_type,
                    openai_api_version=self.config.api_version,
                    deployment=self.config.embed_deployment,
                    model=self.config.embed_model,
                )
            else:
                self.embed = AzureOpenAIEmbeddings(
                    azure_endpoint=self.config.endpoint,
                    api_key=self.config.key,
                    openai_api_type=self.config.api_type,
                    openai_api_version=self.config.api_version,
                    deployment=self.config.embed_deployment,
                    model=self.config.embed_model,
                )
            return self.embed
        except Exception as err:
            raise (err)

    @retry(wait=wait_random_exponential(min=1, max=20),
           stop=stop_after_attempt(6))
    def _chat_request(self, prompt) -> str:
        try:
            return self.chat(prompt).content
        except Exception as err:  # TODO: handle token expire
            raise (err)

    def chatting(self) -> str:
        human_mess = HumanMessage(
            content=
            "Translate this sentence from English to French. I love programming."
        )
        try:
            return self.chat(messages=[human_mess]).content
        except Exception as err:
            raise (err)

    def summarize_text(self, paragrpah: str) -> str:
        try:
            summarize_prompt = self.prompt_profiles[
                "summarize"].format_messages(paragrpah=paragrpah)
            response = self._chat_request(summarize_prompt)
            print(f"summarize_text: {response}")
            return response
        # except
        except Exception as err:
            print(err)
            raise (err)

    def generate_question(self, paragrpah: str) -> str:
        try:
            question_prompt = self.prompt_profiles[
                "question_generate"].format_messages(paragrpah=paragrpah)
            response = self._chat_request(question_prompt)
        except Exception as err:
            raise (err)
        print(f"generated_question: {response}")
        return response

    def generate_keyword(self, paragrpah: str) -> str:
        try:
            keyword_prompt = self.prompt_profiles[
                "keyword_generate"].format_messages(paragrpah=paragrpah)
            response = self._chat_request(keyword_prompt)
        except Exception as err:
            raise (err)
        print(f"generated_keyword: {response}")
        return response

    # @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def embedding_doc(self, document: list[str]) -> list[list[float]]:
        try:
            response = self.embed.embed_documents(texts=document)
        except Exception as err:  # TODO: handle token expire
            raise (err)
        return response

    # @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def embedding_word(self, texts: str) -> list[float]:
        try:
            response = self.embed.embed_query(text=texts)
        except Exception as err:  # TODO: handle token expire
            raise (err)
        return response
