from azure.identity import DefaultAzureCredential
from azure.core.credentials import TokenCredential, AccessToken


class AzureAuthenticate:
    def __init__(self) -> None:
        self.credential = DefaultAzureCredential()
    
    def get_openai_token(self) -> AccessToken:
        scope = "https://cognitiveservices.azure.com/.default"
        self.openai_acess_token = self.credential.get_token(scope)
        return self.openai_acess_token
