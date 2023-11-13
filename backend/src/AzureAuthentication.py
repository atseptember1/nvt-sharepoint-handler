from azure.identity import DefaultAzureCredential


class AzureAuthenticate:
    def __init__(self) -> None:
        self.credential = DefaultAzureCredential()
        self.get_openai_token()
    
    def get_openai_token(self):
        scope = "https://cognitiveservices.azure.com/.default"
        self.openai_acess_token = self.credential.get_token(scope)