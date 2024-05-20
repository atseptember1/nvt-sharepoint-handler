import os
from azure.core.credentials import AccessToken, AzureKeyCredential, AzureNamedKeyCredential
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv


class AzureAuthenticate:
    """
    Initializes an instance of the AzureAuthenticate class.
    """

    def __init__(self) -> None:
        """
        Initializes an instance of the AzureAuthenticate class.
        """
        self.openai_acess_token = None
        self.credential = DefaultAzureCredential()
        self.search_credential = self.get_search_credential()
        self.storage_credential = self.get_storage_credental()

    def get_openai_token(self) -> AccessToken:
        """
        Retrieves an access token for the OpenAI service.

        Returns:
            AccessToken: The access token for the OpenAI service.
        """
        scope = "https://cognitiveservices.azure.com/.default"
        self.openai_acess_token = self.credential.get_token(scope)
        return self.openai_acess_token

    def get_search_credential(self) -> AzureKeyCredential | DefaultAzureCredential:
        """
        Retrieves the search credential for the Azure service.

        Returns:
            None
        """
        load_dotenv()
        if os.environ.get("AZURE_SEARCH_KEY") is not None:
            search_credential = AzureKeyCredential(os.environ.get("AZURE_SEARCH_KEY"))
        else:
            search_credential = DefaultAzureCredential()
        return search_credential

    def get_storage_credental(self) -> str | DefaultAzureCredential:
        if os.environ.get("AZURE_SA_KEY") is not None:
            storage_credential = str(os.environ.get("AZURE_SA_KEY"))
        else:
            storage_credential = DefaultAzureCredential()
        return storage_credential
