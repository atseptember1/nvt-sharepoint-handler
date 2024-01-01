from azure.core.credentials import AccessToken
from azure.identity import DefaultAzureCredential


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

    def get_openai_token(self) -> AccessToken:
        """
        Retrieves an access token for the OpenAI service.

        Returns:
            AccessToken: The access token for the OpenAI service.
        """
        scope = "https://cognitiveservices.azure.com/.default"
        self.openai_acess_token = self.credential.get_token(scope)
        return self.openai_acess_token
