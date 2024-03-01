from pydantic import BaseModel


class SharepointToken(BaseModel):
    """
    Represents a SharePoint access token.

    Attributes:
        token_type (str): The type of the token.
        expires_in (int): The expiration time of the token.
        ext_expires_in (int): The extended expiration time of the token.
        access_token (str): The access token value.
    """
    token_type: str
    expires_in: int
    ext_expires_in: int
    access_token: str


class SharepointSite(BaseModel):
    """
    Represents a SharePoint site.

    Attributes:
        displayName (str): The display name of the site.
        name (str): The name of the site.
        webUrl (str): The web URL of the site.
        id (str): The ID of the site.
        companyId (str): The company ID of the site.
        siteId1 (str): The first site ID.
        siteId2 (str): The second site ID.
    """
    displayName: str
    name: str
    webUrl: str
    id: str
    companyId: str
    siteId1: str
    siteId2: str


class SharepointSiteList(BaseModel):
    """
    Represents a list of SharePoint sites.

    Attributes:
        Value (list[SharepointSite]): The list of SharePoint sites.
    """
    Value: list[SharepointSite]


class AzureADGroup(BaseModel):
    """
    Represents an Azure AD group.

    Attributes:
        displayName (str): The display name of the group.
        id (str): The ID of the group.
        proxyAddresses (list[str]): The list of proxy addresses of the group.
    """
    displayName: str
    id: str
    proxyAddresses: list[str]


class AzureADGroupList(BaseModel):
    """
    Represents a list of Azure AD groups.

    Attributes:
        value (list[AzureADGroup]): The list of Azure AD groups.
    """
    Value: list[AzureADGroup]


class IndexerProp(BaseModel):
    """
    Represents properties of an indexer.

    Attributes:
        Name (str): The name of the indexer.
        DataSourceName (str): The name of the data source.
        SkillSetName (str): The name of the skill set.
        IndexName (str): The name of the index.
    """
    Name: str
    DataSourceName: str
    SkillSetName: str
    IndexName: str


class IndexerList(BaseModel):
    """
    Represents a list of indexers.

    Attributes:
        value (list[IndexerProp]): The list of indexers.
    """
    Value: list[IndexerProp]


class BlobHandlerUploadBlob(BaseModel):
    """
    Represents the result of a blob upload operation.

    Attributes:
        Status (bool): The status of the upload operation.
        BlobUrl (str): The URL of the uploaded blob.
    """
    Status: bool
    BlobUrl: str


class BlobProperties(BaseModel):
    """
    Represents properties of a blob.

    Attributes:
        Name (str): The name of the blob.
        BlobUrl (str): The URL of the blob.
    """
    Name: str
    BlobUrl: str
