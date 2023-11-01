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
    """
    A class for interacting with various models and APIs related to OpenAI.

    Attributes:
        endpoint (str): The endpoint URL for the OpenAI API.
        key (str): The API key for accessing the OpenAI API.
        chat_deployment (str): The deployment name for the chat model.
        chat_model (str): The name of the chat model.
        embed_deployment (str): The deployment name for the embedding model.
        embed_model (str): The name of the embedding model.
        chat (AzureChatOpenAI): An instance of the AzureChatOpenAI class for chat model interaction.
        embed (OpenAIEmbeddings): An instance of the OpenAIEmbeddings class for embedding model interaction.
        prompt_profiles (dict): A dictionary containing different prompt profiles for summarization and question generation.

    """

    def __init__(self, endpoint: str, key: str, chat_deployment: str, chat_model: str, embed_deployment: str, embed_model: str) -> None:
        """
        Initializes the OpenAI class.

        Args:
            endpoint (str): The endpoint URL for the OpenAI API.
            key (str): The API key for accessing the OpenAI API.
            chat_deployment (str): The deployment name for the chat model.
            chat_model (str): The name of the chat model.
            embed_deployment (str): The deployment name for the embedding model.
            embed_model (str): The name of the embedding model.

        Returns:
            None
        """
        self.api_type = 'azure'
        self.api_version = '2023-03-15-preview'
        self.api_base = endpoint
        self.api_key = key
        self.chat_deployment = chat_deployment
        self.chat_model = chat_model
        self.embed_deployment = embed_deployment
        self.embed_model = embed_model
        self.chat = self._init_chat_model()
        self.embed = self._init_embed_model()
        self.prompt_profiles = {
            'summarize': ChatPromptTemplate.from_messages([
                ('system', 'You are a helpful AI assistant, intended to summarize the content for provided paragraph. {language}'),
                ('human', '{paragrpah}')
            ]),
            'question_generate': ChatPromptTemplate.from_messages([
                ('system', 'Generate 10 questions that can be asked for paragrpah provided by the user. Write all the questions in one line. question in {language}'),
                ('human', '{paragrpah}')
            ])
        }

    def _init_chat_model(self) -> AzureChatOpenAI:
        """
        Initializes the chat model using the AzureChatOpenAI class.

        Returns:
            AzureChatOpenAI: An instance of the AzureChatOpenAI class.
        """
        try:
            chat = AzureChatOpenAI(openai_api_base=self.api_base, openai_api_key=self.api_key,
                                    openai_api_version=self.api_version, deployment_name=self.chat_deployment, model=self.chat_model)
        except Exception as err:
            raise(err)
        return chat
    
    def _init_embed_model(self) -> OpenAIEmbeddings:
        """
        Initializes the embedding model using the OpenAIEmbeddings class.

        Returns:
            OpenAIEmbeddings: An instance of the OpenAIEmbeddings class.
        """
        try:
            embed = OpenAIEmbeddings(openai_api_base=self.api_base, openai_api_key=self.api_key, openai_api_version=self.api_version,
                                                deployment=self.embed_deployment, model=self.embed_model)
        except Exception as err:
            raise(err)
        return embed

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def _chat_request(self, prompt) -> str:
        """
        Sends a chat request to the chat model.

        Args:
            prompt: The prompt for the chat request.

        Returns:
            str: The response from the chat model.
        """
        try:
            return self.chat(prompt).content
        except Exception as err:
            raise(err)

    def summarize_text(self, paragrpah: str, language: str) -> str:
        """
        Summarizes the given text paragraph.

        Args:
            paragrpah (str): The text paragraph to be summarized.
            language (str): The language of the text paragraph.

        Returns:
            str: The summarized text.
        """
        try:
            summarize_prompt = self.prompt_profiles['summarize'].format_messages(paragrpah=paragrpah, language=language)
            response = self._chat_request(summarize_prompt)
        except Exception as err:
            raise(err)
        print(f'summarize_text: {response}')
        return response
        
    def generate_question(self, paragrpah: str, language: str) -> str:
        """
        Generates questions for the given text paragraph.

        Args:
            paragrpah (str): The text paragraph to generate questions for.
            language (str): The language of the text paragraph.

        Returns:
            str: The generated questions.
        """
        try:
            question_prompt = self.prompt_profiles['question_generate'].format_messages(paragrpah=paragrpah, language=language)
            response = self._chat_request(question_prompt)
        except Exception as err:
            raise(err)
        print(f'generated_question: {response}')
        return response
        
    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def embedding_doc(self, document: list[str]) -> list[list[float]]:
        """
        Embeds the given list of documents.

        Args:
            document (list[str]): A list of text documents to be embedded.

        Returns:
            list[list[float]]: The embedded documents.
        """
        try:
            response = self.embed.embed_documents(texts=document)
        except Exception as err:
            raise(err)
        return response

    @retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
    def embedding_word(self, texts: str) -> list[float]:
        """
        Embeds the given word or phrase.

        Args:
            texts (str): The word or phrase to be embedded.

        Returns:
            list[float]: The embedded text.
        """
        try:
            response = self.embed.embed_query(text=texts)
        except Exception as err:
            raise(err)
        return response