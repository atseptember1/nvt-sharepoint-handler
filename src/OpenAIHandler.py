import json
from langchain.chat_models import AzureChatOpenAI
from langchain.llms import AzureOpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.schema import BaseMessage
from tenacity import (
    retry, 
    wait_random_exponential,
    stop_after_attempt
)


class OpenAI:
    def __init__(self, endpoint: str, key: str, chat_deployment: str, chat_model: str, embed_deployment: str, embed_model: str) -> None:
        self.api_type = 'azure'
        self.api_version = '2023-03-15-preview'
        self.api_base = endpoint
        self.api_key = key
        self.chat_deployment = chat_deployment
        self.chat_model = chat_model
        self.embed_deployment = embed_deployment
        self.embed_model = embed_model
        self.chat = self._init_model('gptchat')
        self.embed = self._init_model('embed')
        self.prompt_profiles = {
            'summarize': ChatPromptTemplate.from_messages([
                ('system', 'You are a helpful AI assistant, intended to summarize the content for provided paragraph. Answer in Vietnamese'),
                ('human', '{paragrpah}')
            ]),
            'question_generate': ChatPromptTemplate.from_messages([
                ('system', 'Generate 10 questions that can be asked for paragrpah provided by the user. Write all the questions in one line. question in Vietnamese'),
                ('human', '{paragrpah}')
            ])
        }

    def _init_model(self, model_type: str) -> AzureChatOpenAI | OpenAIEmbeddings:
        if model_type == 'gptchat':
            try:
                chat = AzureChatOpenAI(openai_api_base=self.api_base, openai_api_key=self.api_key, openai_api_version=self.api_version, 
                                                  deployment_name=self.chat_deployment, model_name=self.chat_model)
            except Exception as err:
                raise(err)
            return chat
        elif model_type == 'embed':
            try:
                embed = OpenAIEmbeddings(openai_api_base=self.api_base, openai_api_key=self.api_key, openai_api_version=self.api_version,
                                                    deployment=self.embed_deployment, model=self.embed_model)
            except Exception as err:
                raise(err)
            return embed
        else: raise ValueError('model_type is not valid')

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def _chat_request(self, prompt) -> BaseMessage:
        try:
            return self.chat(prompt).content
        except Exception as err:
            raise(err)

    def summarize_text(self, paragrpah: str) -> BaseMessage:
        try:
            summarize_prompt = self.prompt_profiles['summarize'].format_messages(paragrpah=paragrpah)
            response = self._chat_request(summarize_prompt)
        except Exception as err:
            raise(err)
        print(f'summarize_text: {response}')
        return response
        
    def generate_question(self, paragrpah: str) -> BaseMessage:
        try:
            question_prompt = self.prompt_profiles['question_generate'].format_messages(paragrpah=paragrpah)
            response = self._chat_request(question_prompt)
        except Exception as err:
            raise(err)
        print(f'generated_question: {response}')
        return response
        
    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def embedding(self, texts: str | list[str]) -> list[list[float]]:
        if isinstance(texts, str):
            try:
                response = self.embed.embed_query(text=texts)
            except Exception as err:
                raise(err)
            return response.content
        elif isinstance(texts, list):
            try:
                response = self.embed.embed_documents(texts=texts)
            except Exception as err:
                raise(err)
            return response.content
        else: raise ValueError(f'param texts type is not valid')
